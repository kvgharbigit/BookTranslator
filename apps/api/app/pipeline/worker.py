import os
import tempfile
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Optional

# Enhanced PDF generation import
try:
    import sys
    from pathlib import Path
    # Add root directory to path for enhanced PDF converter
    root_dir = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(root_dir))
    from epub_to_pdf_with_images import convert_epub_to_pdf
    ENHANCED_PDF_AVAILABLE = True
except Exception:
    convert_epub_to_pdf = None
    ENHANCED_PDF_AVAILABLE = False
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.config import settings
from app.db import SessionLocal
from app.models import Job
from app.storage import get_storage
from app.deps import get_provider
from app.pipeline.epub_io import EPUBProcessor
from app.pipeline.html_segment import HTMLSegmenter
from app.pipeline.translate import TranslationOrchestrator
from app.pricing import calculate_provider_cost_cents
from app.logger import get_logger, set_request_id

logger = get_logger(__name__)


def translate_epub(job_id: str):
    """Main worker function to translate EPUB files.
    
    This function:
    1. Retrieves job details from database
    2. Downloads EPUB from storage
    3. Extracts and segments content
    4. Translates with provider validation
    5. Generates EPUB + PDF + TXT outputs
    6. Uploads results and updates database
    7. Sends email notification
    """
    
    # Set request ID for logging correlation
    set_request_id(job_id[:8])
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Retrieve job details from database
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found in database")
            return
            
        logger.info(f"🚀 Starting translation │ Job: {job_id[:13]}... │ Lang: {job.target_lang} │ Provider: {job.provider}")
        
        # Extract job parameters
        source_key = job.source_key
        target_lang = job.target_lang
        provider_name = job.provider
        email = job.email
        
        # Update job status to processing
        job.status = "processing"
        job.progress_step = "starting"
        job.progress_percent = 10
        db.commit()
        logger.info(f"Job {job_id} status updated to processing")
        
        # Initialize storage
        storage = get_storage()
        
        # Step 1: Download and validate EPUB
        with tempfile.TemporaryDirectory() as temp_dir:
            epub_path = os.path.join(temp_dir, "input.epub")
            
            # Download from R2
            if not storage.download_file(source_key, epub_path):
                raise Exception("Failed to download EPUB from storage")
            
            # Step 2: Read and segment EPUB
            job.progress_step = "segmenting"
            job.progress_percent = 20
            db.commit()
            
            epub_processor = EPUBProcessor()
            segmenter = HTMLSegmenter()
            
            original_book, spine_docs = epub_processor.read_epub(epub_path)
            segments, reconstruction_maps = segmenter.segment_documents(spine_docs)
            
            if not segments:
                raise Exception("No translatable content found in EPUB")
            
            # Step 3: Translate content
            job.progress_step = "translating"
            job.progress_percent = 30
            db.commit()

            primary_provider = get_provider(provider_name)
            fallback_provider = get_provider("groq" if provider_name == "gemini" else "gemini")

            orchestrator = TranslationOrchestrator()

            # Create progress callback for batch-level updates
            def update_translation_progress(batch_index: int, total_batches: int):
                """Update job progress based on batch completion."""
                # Translation phase is 30%-60% of total progress
                progress = 30 + int((batch_index / total_batches) * 30)
                job.progress_percent = min(progress, 60)  # Cap at 60%
                db.commit()
                logger.info(f"⚡ Translation progress: {job.progress_percent}% │ Batch: {batch_index}/{total_batches} │ Job: {job_id[:13]}...")

            translated_segments, tokens_actual, provider_used = asyncio.run(
                orchestrator.translate_segments(
                    segments=segments,
                    target_lang=target_lang,
                    primary_provider=primary_provider,
                    fallback_provider=fallback_provider,
                    source_lang=job.source_lang,
                    progress_callback=update_translation_progress
                )
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
            job.progress_percent = 60
            db.commit()
            
            translated_docs = segmenter.reconstruct_documents(
                translated_segments, reconstruction_maps, spine_docs
            )
            
            # Apply RTL layout if needed
            if orchestrator.should_use_rtl_layout(target_lang):
                translated_docs = _apply_rtl_layout(translated_docs)
            
            # Step 5: Generate multi-format outputs
            job.progress_step = "uploading"
            job.progress_percent = 80
            db.commit()
            
            output_keys = _generate_outputs(
                job_id, temp_dir, original_book, translated_docs, translated_segments
            )
            
            # Update job with output keys
            job.output_epub_key = output_keys.get("epub")
            job.output_pdf_key = output_keys.get("pdf")
            job.output_txt_key = output_keys.get("txt")
            
            # Step 6: Complete job
            job.status = "done"
            job.progress_step = "done"
            job.progress_percent = 100
            db.commit()
            
            logger.info(f"✅ Job completed │ {job_id[:13]}... │ Tokens: {tokens_actual} │ Provider: {provider_used}")
            
            # Step 7: Send email notification
            if email:
                try:
                    _send_completion_email(job, email)
                except Exception as e:
                    logger.error(f"Failed to send email notification: {e}")
                    # Don't fail the job for email issues
    
    except Exception as e:
        logger.error(f"❌ Job failed │ {job_id[:13]}... │ Error: {str(e)[:100]}")
        
        # Update job status
        job.status = "failed"
        job.error = str(e)
        db.commit()
        
        # Send failure email if provided
        if email:
            try:
                _send_failure_email(job, email, str(e))
            except Exception as email_error:
                logger.error(f"Failed to send failure email: {email_error}")
    
    finally:
        db.close()


def _generate_outputs(
    job_id: str,
    temp_dir: str,
    original_book,
    translated_docs: list,
    translated_segments: list
) -> dict:
    """Generate EPUB, PDF, and TXT outputs using shared output generator."""
    
    # Import shared modules
    import sys
    from pathlib import Path
    
    # Add common modules to path
    common_path = Path(__file__).parent.parent.parent.parent.parent / "common"
    sys.path.insert(0, str(common_path))
    
    from common.outputs import OutputGenerator
    
    # Initialize storage and output generator
    storage = get_storage()
    output_generator = OutputGenerator()
    
    output_keys = {}
    
    try:
        # Extract metadata for formatting
        metadata = {
            "title": "Traducción de Libro",
            "author": "Autor Desconocido",
            "original_title": "Original Book"
        }
        
        # Try to extract actual metadata from original book
        try:
            if hasattr(original_book, 'get_metadata'):
                book_metadata = original_book.get_metadata('DC', 'title')
                if book_metadata:
                    metadata["original_title"] = book_metadata[0][0]
                
                author_metadata = original_book.get_metadata('DC', 'creator')
                if author_metadata:
                    metadata["author"] = author_metadata[0][0]
                    
                # Set translated title based on original
                if "jungle" in metadata["original_title"].lower():
                    metadata["title"] = "EL LIBRO DE LA SELVA"
        except Exception as e:
            logger.debug(f"Could not extract book metadata: {e}")
        
        # Generate all outputs using shared module
        import asyncio
        results = asyncio.run(output_generator.generate_all_outputs(
            output_dir=temp_dir,
            original_book=original_book,
            translated_docs=translated_docs,
            provider_name=job_id,  # Use job_id as provider name for file naming
            metadata=metadata
        ))
        
        # Upload successful outputs to storage
        file_paths = output_generator.get_output_files(temp_dir, job_id)
        
        # Upload EPUB
        if results.get("epub") and file_paths.get("epub"):
            epub_key = f"outputs/{job_id}.epub"
            if storage.upload_file(file_paths["epub"], epub_key, "application/epub+zip"):
                output_keys["epub"] = epub_key
                logger.info(f"Uploaded EPUB: {epub_key}")
        
        # Upload PDF
        if results.get("pdf") and file_paths.get("pdf"):
            pdf_key = f"outputs/{job_id}.pdf"
            if storage.upload_file(file_paths["pdf"], pdf_key, "application/pdf"):
                output_keys["pdf"] = pdf_key
                logger.info(f"Uploaded PDF: {pdf_key}")
        
        # Upload TXT
        if results.get("txt") and file_paths.get("txt"):
            txt_key = f"outputs/{job_id}.txt"
            if storage.upload_file(file_paths["txt"], txt_key, "text/plain"):
                output_keys["txt"] = txt_key
                logger.info(f"Uploaded TXT: {txt_key}")
        
        logger.info(f"Generated outputs: {list(output_keys.keys())}")
        
    except Exception as e:
        logger.error(f"Failed to generate outputs using shared module: {e}")
        # Fallback to legacy generation if shared module fails
        return _generate_outputs_legacy(job_id, temp_dir, original_book, translated_docs, translated_segments)
    
    return output_keys


def _generate_outputs_legacy(
    job_id: str,
    temp_dir: str,
    original_book,
    translated_docs: list,
    translated_segments: list
) -> dict:
    """Legacy output generation as fallback."""
    
    # Initialize storage
    storage = get_storage()
    
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
    
    # Generate enhanced PDF
    if settings.generate_pdf and output_keys.get("epub"):
        try:
            if ENHANCED_PDF_AVAILABLE:
                # Use enhanced PDF generation with Calibre/WeasyPrint/ReportLab
                epub_path = os.path.join(temp_dir, f"{job_id}.epub")
                pdf_path = convert_epub_to_pdf(epub_path, temp_dir)
                
                pdf_key = f"outputs/{job_id}.pdf"
                if storage.upload_file(pdf_path, pdf_key, "application/pdf"):
                    output_keys["pdf"] = pdf_key
                    logger.info(f"Uploaded enhanced PDF: {pdf_key}")
            else:
                logger.warning("Enhanced PDF generation not available, skipping PDF")
                
        except Exception as e:
            logger.error(f"Failed to generate enhanced PDF: {e}")
    
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


# Legacy PDF generation function removed - now using enhanced PDF generation


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


def _send_completion_email(job: Job, email: str):
    """Send completion email with download links."""
    
    # Initialize storage
    storage = get_storage()
    
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
        success = asyncio.run(email_service.send_completion_email(
            to_email=email,
            download_urls=download_urls,
            job_id=job.id
        ))
        
        if success:
            logger.info(f"📧 Sent completion email │ To: {email} │ {len(download_urls)} download links │ Job: {job.id[:13]}...")
        else:
            logger.error(f"Failed to send completion email to {email}")
    else:
        logger.error(f"No download URLs available for job {job.id}")


def _send_failure_email(job: Job, email: str, error_message: str):
    """Send failure notification email."""
    
    from app.email import email_service
    
    success = asyncio.run(email_service.send_failure_email(
        to_email=email,
        job_id=job.id,
        error_message=error_message
    ))
    
    if success:
        logger.info(f"Sent failure email to {email} for job {job.id}")
    else:
        logger.error(f"Failed to send failure email to {email}")