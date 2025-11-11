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
from app.providers.factory import get_provider
from app.pipeline.epub_io import EPUBProcessor
from app.pipeline.html_segment import HTMLSegmenter
from app.pipeline.translate import TranslationOrchestrator
from app.pricing import calculate_provider_cost_cents
from app.logger import get_logger, set_request_id, setup_logging

# Initialize logging for worker process
setup_logging()

logger = get_logger(__name__)
print("🔧 WORKER MODULE LOADED - DIAGNOSTICS ENABLED", flush=True)
logger.info("🔧 Worker module loaded with logging configured - diagnostics enabled")


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
        logger.info(f"📥 WORKER READ FROM DB: job_id={job_id}, output_format={repr(job.output_format)}")
        
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

            # Full book translations ALWAYS use Gemini for best quality
            # (provider_name is set to "gemini" in checkout.py and skip_payment.py)
            # Fallback to Groq only for error recovery (should rarely happen)
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

            # Check output format (for user download access control)
            output_format = getattr(job, 'output_format', 'translation')
            logger.info(f"🔍 User purchased format: {repr(output_format)}")
            logger.info(f"📦 Generating ALL 6 files (3 translation + 3 bilingual) regardless of purchase")

            # ALWAYS generate both translation and bilingual versions
            from app.pipeline.bilingual_html import create_bilingual_documents

            # Reconstruct standard translation documents
            translated_docs = segmenter.reconstruct_documents(
                translated_segments, reconstruction_maps, spine_docs
            )

            # Apply RTL layout if needed
            if orchestrator.should_use_rtl_layout(target_lang):
                translated_docs = _apply_rtl_layout(translated_docs)

            # Create bilingual documents
            bilingual_docs = create_bilingual_documents(
                original_segments=segments,
                translated_segments=translated_segments,
                reconstruction_maps=reconstruction_maps,
                spine_docs=spine_docs,
                source_lang=job.source_lang or "en",
                target_lang=target_lang
            )

            # Step 5: Generate all outputs (6 files total)
            job.progress_step = "uploading"
            job.progress_percent = 80
            db.commit()

            # Generate all 6 files
            output_keys = _generate_both_outputs(
                job_id, temp_dir, original_book,
                translated_docs, translated_segments,
                bilingual_docs,
                job.source_lang or "en", target_lang
            )

            # Update job with output keys
            # For "both" format, we generate 6 files but only store the primary 3 in database
            # The additional bilingual files are accessible via status endpoint
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
    import asyncio
    from pathlib import Path

    # Add common modules to path
    common_path = Path(__file__).parent.parent.parent.parent.parent / "common"
    sys.path.insert(0, str(common_path))

    from common.outputs import generate_outputs_with_metadata, OutputGenerator

    # Initialize storage
    storage = get_storage()
    output_keys = {}

    try:
        # Use common output generation function
        results = asyncio.run(generate_outputs_with_metadata(
            output_dir=temp_dir,
            job_id=job_id,
            original_book=original_book,
            translated_docs=translated_docs,
            translated_segments=translated_segments
        ))

        # Upload successful outputs to storage
        output_generator = OutputGenerator()
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
            if storage.upload_file(file_paths["txt"], txt_key, "text/plain; charset=utf-8"):
                output_keys["txt"] = txt_key
                logger.info(f"Uploaded TXT: {txt_key}")
        
        logger.info(f"Generated outputs: {list(output_keys.keys())}")

    except Exception as e:
        logger.error(f"Failed to generate outputs using shared module: {e}")
        # Re-raise exception instead of using legacy fallback
        # This ensures consistent output quality and reveals issues early
        raise

    return output_keys


def _generate_bilingual_outputs(
    job_id: str,
    temp_dir: str,
    original_book,
    bilingual_docs: list,
    source_lang: str,
    target_lang: str
) -> dict:
    """Generate bilingual EPUB, PDF, and TXT outputs."""

    storage = get_storage()
    output_keys = {}

    try:
        # Import shared modules
        import sys
        import asyncio
        from pathlib import Path

        # Add common modules to path
        common_path = Path(__file__).parent.parent.parent.parent.parent / "common"
        sys.path.insert(0, str(common_path))

        from common.outputs import generate_outputs_with_metadata, OutputGenerator

        # First, generate the bilingual EPUB
        epub_processor = EPUBProcessor()
        epub_path = os.path.join(temp_dir, f"{job_id}.epub")

        success = epub_processor.write_bilingual_epub(
            original_book=original_book,
            bilingual_docs=bilingual_docs,
            source_lang=source_lang,
            target_lang=target_lang,
            output_path=epub_path
        )

        if not success or not os.path.exists(epub_path):
            raise Exception("Failed to generate bilingual EPUB")

        # Extract translated text for TXT generation
        # For bilingual, we'll extract just the translated text (target language)
        translated_segments = []
        for doc in bilingual_docs:
            # Parse the bilingual HTML and extract only translated text
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(doc['content'], 'lxml-xml')
            # Find all text content (will include both languages, but that's ok for TXT)
            text = soup.get_text(separator=' ', strip=True)
            translated_segments.append(text)

        # Upload the bilingual EPUB we already created
        epub_key = f"outputs/{job_id}.epub"
        if storage.upload_file(epub_path, epub_key, "application/epub+zip"):
            output_keys["epub"] = epub_key
            logger.info(f"Uploaded bilingual EPUB: {epub_key}")

        # Generate PDF and TXT using shared module (but skip EPUB since we already have it)
        results = asyncio.run(generate_outputs_with_metadata(
            output_dir=temp_dir,
            job_id=job_id,
            original_book=original_book,
            translated_docs=bilingual_docs,
            translated_segments=translated_segments
        ))

        # Upload successful outputs to storage
        output_generator = OutputGenerator()
        file_paths = output_generator.get_output_files(temp_dir, job_id)

        # Upload PDF
        if results.get("pdf") and file_paths.get("pdf"):
            pdf_key = f"outputs/{job_id}.pdf"
            if storage.upload_file(file_paths["pdf"], pdf_key, "application/pdf"):
                output_keys["pdf"] = pdf_key
                logger.info(f"Uploaded bilingual PDF: {pdf_key}")

        # Upload TXT
        if results.get("txt") and file_paths.get("txt"):
            txt_key = f"outputs/{job_id}.txt"
            if storage.upload_file(file_paths["txt"], txt_key, "text/plain; charset=utf-8"):
                output_keys["txt"] = txt_key
                logger.info(f"Uploaded bilingual TXT: {txt_key}")

        logger.info(f"Generated bilingual outputs: {list(output_keys.keys())}")

    except Exception as e:
        logger.error(f"Failed to generate bilingual outputs: {e}")
        raise

    return output_keys


def _generate_both_outputs(
    job_id: str,
    temp_dir: str,
    original_book,
    translated_docs: list,
    translated_segments: list,
    bilingual_docs: list,
    source_lang: str,
    target_lang: str
) -> dict:
    """Generate both standard translation AND bilingual outputs (6 files total).

    Files generated:
    - Translation: {job_id}.epub, {job_id}.pdf, {job_id}.txt
    - Bilingual: {job_id}_bilingual.epub, {job_id}_bilingual.pdf, {job_id}_bilingual.txt
    """
    import sys
    import asyncio
    from pathlib import Path

    # Add common modules to path
    common_path = Path(__file__).parent.parent.parent.parent.parent / "common"
    sys.path.insert(0, str(common_path))

    from common.outputs import generate_outputs_with_metadata, OutputGenerator

    storage = get_storage()
    output_keys = {}

    try:
        # Generate standard translation outputs (3 files)
        logger.info("Generating standard translation outputs...")
        translation_results = asyncio.run(generate_outputs_with_metadata(
            output_dir=temp_dir,
            job_id=job_id,
            original_book=original_book,
            translated_docs=translated_docs,
            translated_segments=translated_segments
        ))

        # Generate bilingual outputs (3 files) - CRITICAL: Use write_bilingual_epub for proper CSS
        logger.info("Generating bilingual outputs with external CSS...")

        # Create bilingual EPUB with external CSS (EPUB standard)
        from app.pipeline.epub_io import EPUBProcessor
        epub_processor = EPUBProcessor()

        bilingual_epub_path = os.path.join(temp_dir, f"{job_id}_bilingual.epub")
        logger.info(f"Creating bilingual EPUB with external CSS at: {bilingual_epub_path}")

        epub_processor.write_bilingual_epub(
            original_book=original_book,
            bilingual_docs=bilingual_docs,
            output_path=bilingual_epub_path,
            source_lang=source_lang,
            target_lang=target_lang
        )
        logger.info("Created bilingual EPUB with external CSS file")

        # Upload bilingual EPUB
        epub_key = f"outputs/{job_id}_bilingual.epub"
        if storage.upload_file(bilingual_epub_path, epub_key, "application/epub+zip"):
            output_keys["bilingual_epub"] = epub_key
            logger.info(f"Uploaded bilingual EPUB: {epub_key}")

        # Generate bilingual PDF from the EPUB we just created
        try:
            if ENHANCED_PDF_AVAILABLE:
                bilingual_pdf_path = convert_epub_to_pdf(bilingual_epub_path, temp_dir)
            else:
                raise Exception("Enhanced PDF converter not available")

            if bilingual_pdf_path and os.path.exists(bilingual_pdf_path):
                pdf_key = f"outputs/{job_id}_bilingual.pdf"
                if storage.upload_file(bilingual_pdf_path, pdf_key, "application/pdf"):
                    output_keys["bilingual_pdf"] = pdf_key
                    logger.info(f"Uploaded bilingual PDF: {pdf_key}")
        except Exception as e:
            logger.error(f"Failed to generate bilingual PDF: {e}")

        # Generate bilingual TXT from documents
        try:
            bilingual_text = []
            for doc in bilingual_docs:
                soup = BeautifulSoup(doc['content'], 'lxml-xml')
                text = soup.get_text(separator=' ', strip=True)
                bilingual_text.append(text)

            bilingual_txt_path = os.path.join(temp_dir, f"{job_id}_bilingual.txt")
            with open(bilingual_txt_path, "w", encoding="utf-8") as f:
                f.write("\n\n".join(bilingual_text))

            txt_key = f"outputs/{job_id}_bilingual.txt"
            if storage.upload_file(bilingual_txt_path, txt_key, "text/plain; charset=utf-8"):
                output_keys["bilingual_txt"] = txt_key
                logger.info(f"Uploaded bilingual TXT: {txt_key}")
        except Exception as e:
            logger.error(f"Failed to generate bilingual TXT: {e}")

        # Upload all translation outputs to storage
        output_generator = OutputGenerator()
        trans_files = output_generator.get_output_files(temp_dir, job_id)

        if translation_results.get("epub") and trans_files.get("epub"):
            epub_key = f"outputs/{job_id}.epub"
            if storage.upload_file(trans_files["epub"], epub_key, "application/epub+zip"):
                output_keys["epub"] = epub_key
                logger.info(f"Uploaded translation EPUB: {epub_key}")

        if translation_results.get("pdf") and trans_files.get("pdf"):
            pdf_key = f"outputs/{job_id}.pdf"
            if storage.upload_file(trans_files["pdf"], pdf_key, "application/pdf"):
                output_keys["pdf"] = pdf_key
                logger.info(f"Uploaded translation PDF: {pdf_key}")

        if translation_results.get("txt") and trans_files.get("txt"):
            txt_key = f"outputs/{job_id}.txt"
            if storage.upload_file(trans_files["txt"], txt_key, "text/plain; charset=utf-8"):
                output_keys["txt"] = txt_key
                logger.info(f"Uploaded translation TXT: {txt_key}")

        logger.info(f"Generated both formats: {list(output_keys.keys())}")

    except Exception as e:
        logger.error(f"Failed to generate both outputs: {e}")
        raise

    return output_keys


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

    # Always include primary outputs
    if job.output_epub_key:
        download_urls["epub"] = storage.generate_presigned_download_url(job.output_epub_key)
    if job.output_pdf_key:
        download_urls["pdf"] = storage.generate_presigned_download_url(job.output_pdf_key)
    if job.output_txt_key:
        download_urls["txt"] = storage.generate_presigned_download_url(job.output_txt_key)

    # For "bilingual" format, rename the standard outputs to bilingual keys
    # For "both" format, also include bilingual outputs with _bilingual suffix
    output_format = getattr(job, 'output_format', 'translation')

    if output_format == "bilingual":
        # For bilingual-only, the standard keys contain bilingual content
        # Rename them in the download_urls dict so the email displays them correctly
        if download_urls.get("epub"):
            download_urls["bilingual_epub"] = download_urls.pop("epub")
        if download_urls.get("pdf"):
            download_urls["bilingual_pdf"] = download_urls.pop("pdf")
        if download_urls.get("txt"):
            download_urls["bilingual_txt"] = download_urls.pop("txt")

    elif output_format == "both":
        # Generate URLs for bilingual files (with _bilingual suffix)
        bilingual_epub_key = f"outputs/{job.id}_bilingual.epub"
        bilingual_pdf_key = f"outputs/{job.id}_bilingual.pdf"
        bilingual_txt_key = f"outputs/{job.id}_bilingual.txt"

        download_urls["bilingual_epub"] = storage.generate_presigned_download_url(bilingual_epub_key)
        download_urls["bilingual_pdf"] = storage.generate_presigned_download_url(bilingual_pdf_key)
        download_urls["bilingual_txt"] = storage.generate_presigned_download_url(bilingual_txt_key)

    if download_urls:
        success = asyncio.run(email_service.send_completion_email(
            to_email=email,
            download_urls=download_urls,
            job_id=job.id,
            output_format=output_format
        ))

        if success:
            logger.info(f"📧 Sent completion email │ To: {email} │ {len(download_urls)} download links │ Format: {output_format} │ Job: {job.id[:13]}...")
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