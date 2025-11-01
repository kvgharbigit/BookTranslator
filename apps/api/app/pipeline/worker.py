import os
import tempfile
import uuid
from datetime import datetime, timedelta
from typing import Optional

# Conditional WeasyPrint import to avoid crashes when PDF disabled
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except Exception:
    HTML = None
    WEASYPRINT_AVAILABLE = False
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.config import settings
from app.db import SessionLocal
from app.models import Job
from app.storage import storage
from app.deps import get_provider
from app.pipeline.epub_io import EPUBProcessor
from app.pipeline.html_segment import HTMLSegmenter
from app.pipeline.translate import TranslationOrchestrator
from app.pricing import calculate_provider_cost_cents
from app.logger import get_logger, set_request_id

logger = get_logger(__name__)


async def translate_epub(
    job_id: str,
    source_key: str,
    target_lang: str,
    provider_name: str,
    email: Optional[str] = None
):
    """Main worker function to translate EPUB files.
    
    This function:
    1. Downloads EPUB from R2
    2. Extracts and segments content
    3. Translates with provider validation
    4. Generates EPUB + PDF + TXT outputs
    5. Uploads results and updates database
    6. Sends email notification
    """
    
    # Set request ID for logging correlation
    set_request_id(job_id[:8])
    
    db = SessionLocal()
    try:
        # Get job from database
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found")
            return
        
        logger.info(f"Starting translation job {job_id}")
        
        # Update job status
        job.status = "processing"
        job.progress_step = "unzipping"
        db.commit()
        
        # Step 1: Download and validate EPUB
        with tempfile.TemporaryDirectory() as temp_dir:
            epub_path = os.path.join(temp_dir, "input.epub")
            
            # Download from R2
            if not storage.download_file(source_key, epub_path):
                raise Exception("Failed to download EPUB from storage")
            
            # Step 2: Read and segment EPUB
            job.progress_step = "segmenting"
            db.commit()
            
            epub_processor = EPUBProcessor()
            segmenter = HTMLSegmenter()
            
            original_book, spine_docs = epub_processor.read_epub(epub_path)
            segments, reconstruction_maps = segmenter.segment_documents(spine_docs)
            
            if not segments:
                raise Exception("No translatable content found in EPUB")
            
            # Step 3: Translate content
            job.progress_step = "translating"
            db.commit()
            
            primary_provider = get_provider(provider_name)
            fallback_provider = get_provider("groq" if provider_name == "gemini" else "gemini")
            
            orchestrator = TranslationOrchestrator()
            
            translated_segments, tokens_actual, provider_used = await orchestrator.translate_segments(
                segments=segments,
                target_lang=target_lang,
                primary_provider=primary_provider,
                fallback_provider=fallback_provider,
                source_lang=job.source_lang
            )
            
            # Update job with actual usage
            job.tokens_actual = tokens_actual
            job.provider = provider_used
            job.provider_cost_cents = calculate_provider_cost_cents(tokens_actual, provider_used)
            
            # Handle provider fallback tracking
            if provider_used != provider_name:
                job.failover_count += 1
            
            # Step 4: Reconstruct documents
            job.progress_step = "assembling"
            db.commit()
            
            translated_docs = segmenter.reconstruct_documents(
                translated_segments, reconstruction_maps, spine_docs
            )
            
            # Apply RTL layout if needed
            if orchestrator.should_use_rtl_layout(target_lang):
                translated_docs = _apply_rtl_layout(translated_docs)
            
            # Step 5: Generate multi-format outputs
            job.progress_step = "uploading"
            db.commit()
            
            output_keys = await _generate_outputs(
                job_id, temp_dir, original_book, translated_docs, translated_segments
            )
            
            # Update job with output keys
            job.output_epub_key = output_keys.get("epub")
            job.output_pdf_key = output_keys.get("pdf")
            job.output_txt_key = output_keys.get("txt")
            
            # Step 6: Complete job
            job.status = "done"
            job.progress_step = "done"
            db.commit()
            
            logger.info(f"Job {job_id} completed successfully")
            
            # Step 7: Send email notification
            if email:
                try:
                    await _send_completion_email(job, email)
                except Exception as e:
                    logger.error(f"Failed to send email notification: {e}")
                    # Don't fail the job for email issues
    
    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        
        # Update job status
        job.status = "failed"
        job.error = str(e)
        db.commit()
        
        # Send failure email if provided
        if email:
            try:
                await _send_failure_email(job, email, str(e))
            except Exception as email_error:
                logger.error(f"Failed to send failure email: {email_error}")
    
    finally:
        db.close()


async def _generate_outputs(
    job_id: str,
    temp_dir: str,
    original_book,
    translated_docs: list,
    translated_segments: list
) -> dict:
    """Generate EPUB, PDF, and TXT outputs."""
    
    output_keys = {}
    epub_processor = EPUBProcessor()
    
    # Generate EPUB
    if settings.generate_pdf or True:  # Always generate EPUB
        epub_path = os.path.join(temp_dir, f"{job_id}.epub")
        
        if epub_processor.write_epub(original_book, translated_docs, epub_path):
            epub_key = f"outputs/{job_id}.epub"
            if storage.upload_file(epub_path, epub_key, "application/epub+zip"):
                output_keys["epub"] = epub_key
                logger.info(f"Uploaded EPUB: {epub_key}")
    
    # Generate PDF
    if settings.generate_pdf:
        try:
            # Combine translated documents into single HTML
            combined_html = _combine_docs_for_pdf(translated_docs)
            
            pdf_path = os.path.join(temp_dir, f"{job_id}.pdf")
            HTML(string=combined_html).write_pdf(pdf_path)
            
            pdf_key = f"outputs/{job_id}.pdf"
            if storage.upload_file(pdf_path, pdf_key, "application/pdf"):
                output_keys["pdf"] = pdf_key
                logger.info(f"Uploaded PDF: {pdf_key}")
                
        except Exception as e:
            logger.error(f"Failed to generate PDF: {e}")
    
    # Generate TXT
    if settings.generate_txt:
        try:
            # Extract plain text from translated segments
            plain_text = "\n\n".join(translated_segments)
            
            txt_path = os.path.join(temp_dir, f"{job_id}.txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(plain_text)
            
            txt_key = f"outputs/{job_id}.txt"
            if storage.upload_file(txt_path, txt_key, "text/plain"):
                output_keys["txt"] = txt_key
                logger.info(f"Uploaded TXT: {txt_key}")
                
        except Exception as e:
            logger.error(f"Failed to generate TXT: {e}")
    
    return output_keys


def _combine_docs_for_pdf(translated_docs: list) -> str:
    """Combine translated documents into single HTML for PDF generation."""
    
    html_parts = [
        '<!DOCTYPE html>',
        '<html>',
        '<head>',
        '<meta charset="utf-8">',
        '<style>',
        'body { font-family: serif; line-height: 1.6; margin: 2cm; }',
        'h1, h2, h3, h4, h5, h6 { color: #333; margin-top: 2em; }',
        '.chapter { page-break-before: always; }',
        '</style>',
        '</head>',
        '<body>'
    ]
    
    for i, doc in enumerate(translated_docs):
        if i > 0:
            html_parts.append('<div class="chapter">')
        
        # Extract body content
        soup = BeautifulSoup(doc['content'], 'xml')
        body = soup.find('body')
        if body:
            html_parts.append(str(body))
        else:
            html_parts.append(doc['content'])
        
        if i > 0:
            html_parts.append('</div>')
    
    html_parts.extend(['</body>', '</html>'])
    
    return '\n'.join(html_parts)


def _apply_rtl_layout(translated_docs: list) -> list:
    """Apply RTL layout to translated documents."""
    
    for doc in translated_docs:
        try:
            soup = BeautifulSoup(doc['content'], 'xml')
            
            # Set dir="rtl" on html or body element
            html_tag = soup.find('html')
            if html_tag:
                html_tag['dir'] = 'rtl'
            else:
                body_tag = soup.find('body')
                if body_tag:
                    body_tag['dir'] = 'rtl'
            
            doc['content'] = str(soup)
            
        except Exception as e:
            logger.warning(f"Failed to apply RTL layout: {e}")
    
    return translated_docs


async def _send_completion_email(job: Job, email: str):
    """Send completion email with download links."""
    
    from app.email import email_service
    
    # Generate download URLs
    download_urls = {}
    
    if job.output_epub_key:
        download_urls["epub"] = storage.generate_presigned_download_url(job.output_epub_key)
    if job.output_pdf_key:
        download_urls["pdf"] = storage.generate_presigned_download_url(job.output_pdf_key)
    if job.output_txt_key:
        download_urls["txt"] = storage.generate_presigned_download_url(job.output_txt_key)
    
    if download_urls:
        success = await email_service.send_completion_email(
            to_email=email,
            download_urls=download_urls,
            job_id=job.id
        )
        
        if success:
            logger.info(f"Sent completion email to {email} with {len(download_urls)} download links")
        else:
            logger.error(f"Failed to send completion email to {email}")
    else:
        logger.error(f"No download URLs available for job {job.id}")


async def _send_failure_email(job: Job, email: str, error_message: str):
    """Send failure notification email."""
    
    from app.email import email_service
    
    success = await email_service.send_failure_email(
        to_email=email,
        job_id=job.id,
        error_message=error_message
    )
    
    if success:
        logger.info(f"Sent failure email to {email} for job {job.id}")
    else:
        logger.error(f"Failed to send failure email to {email}")