#!/usr/bin/env python3
"""Download and inspect the production bilingual EPUB and PDF."""

import sys
import os
import zipfile
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.storage import R2Storage
from app.logger import get_logger
from bs4 import BeautifulSoup

logger = get_logger(__name__)

def inspect_production_files():
    """Download and inspect production bilingual files."""

    job_id = "81323a6b-cd10-4866-881a-8338a51319a8"

    storage = R2Storage()

    # Download bilingual EPUB
    epub_key = f"outputs/{job_id}_bilingual.epub"
    epub_path = f"/tmp/production_bilingual_{job_id}.epub"

    logger.info(f"📥 Downloading {epub_key}...")
    if not storage.download_file(epub_key, epub_path):
        logger.error("Failed to download EPUB")
        return

    logger.info(f"✅ Downloaded to {epub_path}")

    # Extract and inspect
    extract_dir = tempfile.mkdtemp(prefix='inspect_bilingual_')

    with zipfile.ZipFile(epub_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)

    logger.info(f"📦 Extracted to {extract_dir}")

    # Check CSS
    css_path = Path(extract_dir) / "EPUB" / "styles" / "bilingual.css"

    if css_path.exists():
        logger.info("✅ External CSS file found")
        with open(css_path, 'r') as f:
            css_content = f.read()

        logger.info(f"📄 CSS size: {len(css_content)} bytes")

        if '.bilingual-subtitle' in css_content:
            logger.info("✅ CSS contains .bilingual-subtitle styles")

            # Show the actual CSS
            logger.info("\n📝 Bilingual CSS:")
            for line in css_content.split('\n'):
                if 'bilingual-subtitle' in line or (line.strip() and line[0] not in ['}', '/']):
                    logger.info(f"   {line}")
        else:
            logger.error("❌ CSS missing .bilingual-subtitle")
    else:
        logger.error("❌ No external CSS file")

    # Check HTML structure
    html_files = list(Path(extract_dir).rglob("*.html")) + list(Path(extract_dir).rglob("*.xhtml"))
    content_files = [f for f in html_files if 'EPUB' in str(f) and 'nav' not in str(f).lower()]

    if content_files:
        sample_file = content_files[-1]  # Get last file (should have content)
        logger.info(f"\n📄 Checking {sample_file.name}...")

        with open(sample_file, 'r') as f:
            html = f.read()

        soup = BeautifulSoup(html, 'xml')

        # Check for CSS link
        head = soup.find('head')
        if head:
            links = head.find_all('link', {'rel': 'stylesheet'})
            if links:
                logger.info(f"✅ CSS links found: {[l.get('href') for l in links]}")
            else:
                logger.error("❌ No CSS links in <head>")

        # Show sample subtitle
        subtitles = soup.find_all('span', class_='bilingual-subtitle')
        if subtitles:
            logger.info(f"✅ Found {len(subtitles)} bilingual subtitle spans")

            # Show sample
            sample = subtitles[0]
            parent = sample.parent
            logger.info(f"\n📝 Sample HTML structure:")
            logger.info(f"   {parent.prettify()[:500]}")
        else:
            logger.error("❌ No bilingual-subtitle spans found")

    # Download PDF for comparison
    pdf_key = f"outputs/{job_id}_bilingual.pdf"
    pdf_path = f"/tmp/production_bilingual_{job_id}.pdf"

    logger.info(f"\n📥 Downloading {pdf_key}...")
    if storage.download_file(pdf_key, pdf_path):
        size_mb = Path(pdf_path).stat().st_size / (1024 * 1024)
        logger.info(f"✅ Downloaded PDF: {pdf_path} ({size_mb:.2f} MB)")

        # Open both files
        logger.info("\n📱 Opening EPUB and PDF for comparison...")
        import subprocess
        subprocess.run(["open", epub_path])
        subprocess.run(["open", pdf_path])

        logger.info("\n" + "=" * 80)
        logger.info("🔍 COMPARISON:")
        logger.info("=" * 80)
        logger.info("EPUB: Should show Spanish text with English subtitles below in gray italic")
        logger.info("PDF:  Check if the formatting is preserved from EPUB")
        logger.info("")
        logger.info("If PDF lost formatting, we need to adjust the PDF converter settings")
        logger.info("=" * 80)

    logger.info(f"\n📁 Files available:")
    logger.info(f"   EPUB: {epub_path}")
    logger.info(f"   PDF:  {pdf_path}")
    logger.info(f"   Extracted: {extract_dir}")

if __name__ == "__main__":
    inspect_production_files()
