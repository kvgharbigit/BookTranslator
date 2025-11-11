#!/usr/bin/env python3
"""
Inspect the actual production bilingual EPUB to verify the fix is working.
Downloads from S3 and checks for:
1. External CSS file (styles/bilingual.css)
2. CSS links in <head> tags
3. Bilingual subtitle spans
"""

import sys
import os
import zipfile
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.deps import get_storage
from app.logger import get_logger
from bs4 import BeautifulSoup

logger = get_logger(__name__)

def inspect_bilingual_epub():
    """Download and inspect production bilingual EPUB."""

    # Job ID for the most recent bilingual job
    job_id = "e493f144-3638-4e35-bdf1-d470be0a381a"
    s3_key = f"outputs/{job_id}.epub"

    logger.info(f"Downloading production bilingual EPUB: {s3_key}")

    # Get storage instance
    from app.storage import R2Storage
    storage = R2Storage()

    # Download to temp file
    with tempfile.NamedTemporaryFile(suffix='.epub', delete=False) as temp_file:
        temp_path = temp_file.name

    try:
        success = storage.download_file(s3_key, temp_path)
        if not success:
            logger.error(f"Failed to download {s3_key}")
            return

        logger.info(f"Downloaded to: {temp_path}")

        # Extract EPUB
        extract_dir = tempfile.mkdtemp(prefix='inspect_production_')
        logger.info(f"Extracting to: {extract_dir}")

        with zipfile.ZipFile(temp_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        # Check 1: Does styles/bilingual.css exist?
        css_path = Path(extract_dir) / "EPUB" / "styles" / "bilingual.css"
        if css_path.exists():
            logger.info("✅ CHECK 1 PASSED: External CSS file exists at EPUB/styles/bilingual.css")
            with open(css_path, 'r', encoding='utf-8') as f:
                css_content = f.read()
                if '.bilingual-subtitle' in css_content:
                    logger.info("   ✅ CSS contains .bilingual-subtitle styles")
                else:
                    logger.warning("   ⚠️  CSS missing .bilingual-subtitle styles")
        else:
            logger.error("❌ CHECK 1 FAILED: No external CSS file found")

        # Check 2: Do HTML files have CSS links in <head>?
        html_files = list(Path(extract_dir).rglob("*.html")) + list(Path(extract_dir).rglob("*.xhtml"))
        content_files = [f for f in html_files if 'EPUB' in str(f) and 'nav' not in str(f).lower()]

        logger.info(f"\nFound {len(content_files)} content HTML files")

        has_css_link = False
        for html_file in content_files[:3]:  # Check first 3 files
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
                soup = BeautifulSoup(content, 'xml')

                head = soup.find('head')
                if head:
                    link_tags = head.find_all('link', {'rel': 'stylesheet'})
                    if link_tags:
                        has_css_link = True
                        logger.info(f"✅ CHECK 2 PASSED: {html_file.name} has CSS link in <head>")
                        for link in link_tags:
                            logger.info(f"   Link: {link.get('href')}")
                    else:
                        logger.warning(f"⚠️  {html_file.name} has <head> but no CSS links")
                else:
                    logger.warning(f"⚠️  {html_file.name} has no <head> tag")

        if not has_css_link:
            logger.error("❌ CHECK 2 FAILED: No CSS links found in any HTML files")

        # Check 3: Do bilingual subtitle spans exist?
        has_bilingual_spans = False
        for html_file in content_files[:3]:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'bilingual-subtitle' in content:
                    has_bilingual_spans = True
                    logger.info(f"✅ CHECK 3 PASSED: {html_file.name} has bilingual-subtitle spans")

                    # Show a sample
                    soup = BeautifulSoup(content, 'xml')
                    subtitle_span = soup.find('span', class_='bilingual-subtitle')
                    if subtitle_span:
                        parent = subtitle_span.parent
                        logger.info(f"   Sample: {parent.get_text()[:100]}...")
                    break

        if not has_bilingual_spans:
            logger.error("❌ CHECK 3 FAILED: No bilingual-subtitle spans found")

        logger.info(f"\n📁 Extracted EPUB available at: {extract_dir}")
        logger.info("You can inspect the files manually if needed.")

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
            logger.info(f"Cleaned up temp file: {temp_path}")

if __name__ == "__main__":
    inspect_bilingual_epub()
