#!/bin/bash
# Generate all 6 files (regular + bilingual) for The Jungle Book
# Uses the actual worker code to test the "both" output format

echo "============================================="
echo "Generating ALL 6 files from Jungle Book"
echo "============================================="
echo ""
echo "This will create:"
echo "  Regular:    EPUB, PDF, TXT"
echo "  Bilingual:  EPUB, PDF, TXT (with subtitles)"
echo ""

cd "$(dirname "$0")/apps/api"

# Load environment
export $(cat .env.local | grep -v '^#' | xargs)

# Go back to root
cd ../..

# Run Python worker simulation with Poetry
cd apps/api
export PYTHONPATH=.
poetry run python3 << 'PYTHON_SCRIPT'
import sys
import uuid
from pathlib import Path

from app.pipeline.worker import translate_epub
from app.db import SessionLocal, create_tables
from app.models import Job
from app.deps import get_storage
import os

# Create tables
create_tables()

# Configuration
input_epub = "../../sample_books/pg236_first20pages.epub"
job_id = str(uuid.uuid4())

print(f"📖 Using: {input_epub}")
print(f"🆔 Job ID: {job_id}")
print("")

# Upload to storage
storage = get_storage()
source_key = f"uploads/{job_id}.epub"

print(f"📤 Uploading to storage...")
if not storage.upload_file(input_epub, source_key, "application/epub+zip"):
    print("❌ Upload failed")
    sys.exit(1)
print(f"✅ Uploaded to: {source_key}")
print("")

# Create job in database
db = SessionLocal()
try:
    job = Job(
        id=job_id,
        source_key=source_key,
        target_lang="es",
        source_lang="en",
        output_format="both",  # GENERATE ALL 6 FILES
        provider="groq",  # Using Groq (Gemini quota exceeded)
        status="queued",
        size_bytes=os.path.getsize(input_epub),
        tokens_est=10000,
        price_charged_cents=50
    )

    db.add(job)
    db.commit()

    print(f"✅ Created job with output_format='both'")
    print("")
    print("="*60)
    print("🚀 Starting translation worker...")
    print("="*60)
    print("")

    # Run the worker!
    translate_epub(job_id)

    # Check results
    db.refresh(job)

    print("")
    print("="*60)
    print("📊 RESULTS")
    print("="*60)

    files_generated = 0

    print("\n✅ Regular files:")
    if job.output_epub_key:
        print(f"   - EPUB: {job.output_epub_key}")
        files_generated += 1
    if job.output_pdf_key:
        print(f"   - PDF:  {job.output_pdf_key}")
        files_generated += 1
    if job.output_txt_key:
        print(f"   - TXT:  {job.output_txt_key}")
        files_generated += 1

    print("\n✅ Bilingual files:")
    if job.bilingual_epub_key:
        print(f"   - EPUB: {job.bilingual_epub_key}")
        files_generated += 1
    if job.bilingual_pdf_key:
        print(f"   - PDF:  {job.bilingual_pdf_key}")
        files_generated += 1
    if job.bilingual_txt_key:
        print(f"   - TXT:  {job.bilingual_txt_key}")
        files_generated += 1

    print(f"\n📈 Total: {files_generated}/6 files generated")

    if files_generated == 6:
        print("\n🎉 SUCCESS! All 6 files generated correctly!")

        # Download files locally to test_outputs
        print("")
        print("="*60)
        print("📥 Downloading files to test_outputs/...")
        print("="*60)

        output_dir = Path("../../test_outputs")
        output_dir.mkdir(exist_ok=True)

        downloaded = 0

        # Download regular files
        if job.output_epub_key:
            local_path = output_dir / f"{job_id}.epub"
            if storage.download_file(job.output_epub_key, str(local_path)):
                print(f"✅ Downloaded: {local_path}")
                downloaded += 1

        if job.output_pdf_key:
            local_path = output_dir / f"{job_id}.pdf"
            if storage.download_file(job.output_pdf_key, str(local_path)):
                print(f"✅ Downloaded: {local_path}")
                downloaded += 1

        if job.output_txt_key:
            local_path = output_dir / f"{job_id}.txt"
            if storage.download_file(job.output_txt_key, str(local_path)):
                print(f"✅ Downloaded: {local_path}")
                downloaded += 1

        # Download bilingual files
        if job.bilingual_epub_key:
            local_path = output_dir / f"{job_id}_bilingual.epub"
            if storage.download_file(job.bilingual_epub_key, str(local_path)):
                print(f"✅ Downloaded: {local_path}")
                downloaded += 1

        if job.bilingual_pdf_key:
            local_path = output_dir / f"{job_id}_bilingual.pdf"
            if storage.download_file(job.bilingual_pdf_key, str(local_path)):
                print(f"✅ Downloaded: {local_path}")
                downloaded += 1

        if job.bilingual_txt_key:
            local_path = output_dir / f"{job_id}_bilingual.txt"
            if storage.download_file(job.bilingual_txt_key, str(local_path)):
                print(f"✅ Downloaded: {local_path}")
                downloaded += 1

        print(f"\n📦 Downloaded {downloaded}/6 files to test_outputs/")
    else:
        print(f"\n❌ FAILURE! Only {files_generated}/6 files generated")

    print("="*60)

finally:
    db.close()

PYTHON_SCRIPT
