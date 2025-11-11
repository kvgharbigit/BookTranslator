#!/usr/bin/env python3
"""Quick inspection script for the test bilingual EPUB."""

import zipfile
import tempfile
from pathlib import Path
from bs4 import BeautifulSoup

epub_path = Path(__file__).parent / "test_output_complete_pipeline.epub"

print(f"📦 Inspecting: {epub_path.name}")
print(f"   Size: {epub_path.stat().st_size / (1024*1024):.2f} MB\n")

with tempfile.TemporaryDirectory() as temp_dir:
    # Extract
    with zipfile.ZipFile(epub_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)

    # Check CSS
    css_path = Path(temp_dir) / "EPUB" / "styles" / "bilingual.css"

    if css_path.exists():
        print("✅ External CSS file found at: EPUB/styles/bilingual.css")
        with open(css_path, 'r', encoding='utf-8') as f:
            css_content = f.read()

        print(f"   CSS size: {len(css_content)} bytes")
        print("\n📄 CSS Content (first 500 chars):")
        print(css_content[:500])
        print("...")
    else:
        print("❌ No external CSS file found!")

    # Check HTML files
    html_files = list(Path(temp_dir).rglob("*.xhtml")) + list(Path(temp_dir).rglob("*.html"))
    content_files = [f for f in html_files if 'EPUB' in str(f) and 'nav' not in str(f).lower()]

    print(f"\n📄 Found {len(content_files)} content files")

    if content_files:
        # Check first file
        first_file = content_files[0]
        with open(first_file, 'r', encoding='utf-8') as f:
            html_content = f.read()

        soup = BeautifulSoup(html_content, 'xml')

        # Check for CSS link
        head = soup.find('head')
        if head:
            css_links = head.find_all('link', {'rel': 'stylesheet'})
            if css_links:
                print(f"\n✅ {first_file.name} has CSS links:")
                for link in css_links:
                    print(f"   - {link.get('href')}")
            else:
                print(f"\n⚠️  {first_file.name} has no CSS links")

        # Check for bilingual spans
        if 'bilingual-subtitle' in html_content:
            print(f"\n✅ {first_file.name} contains bilingual-subtitle spans")

            # Show a sample
            subtitle = soup.find('span', class_='bilingual-subtitle')
            if subtitle:
                parent = subtitle.parent
                sample = parent.get_text()[:200].replace('\n', ' ')
                print(f"\n📝 Sample bilingual content:")
                print(f"   {sample}...")

print("\n✅ Inspection complete!")
print(f"💾 EPUB file: {epub_path}")
