#!/usr/bin/env python3
"""
Analyze and compare original vs translated EPUB files
"""
import sys
import zipfile
import os
from pathlib import Path
from bs4 import BeautifulSoup

def analyze_epub_structure(epub_path, label):
    """Analyze EPUB internal structure."""
    print(f"\n📚 {label}: {os.path.basename(epub_path)}")
    print("=" * 50)
    
    try:
        with zipfile.ZipFile(epub_path, 'r') as epub_zip:
            file_list = epub_zip.namelist()
            print(f"Files in EPUB: {len(file_list)}")
            
            # Look for content files
            html_files = [f for f in file_list if f.endswith('.html') or f.endswith('.xhtml')]
            print(f"HTML/XHTML files: {len(html_files)}")
            
            for html_file in html_files[:5]:  # Show first 5
                try:
                    content = epub_zip.read(html_file).decode('utf-8')
                    soup = BeautifulSoup(content, 'html.parser')
                    text_content = soup.get_text(strip=True)
                    
                    print(f"\n📄 {html_file}:")
                    print(f"   HTML size: {len(content)} chars")
                    print(f"   Text size: {len(text_content)} chars")
                    
                    if len(text_content) > 0:
                        preview = text_content[:200] + "..." if len(text_content) > 200 else text_content
                        print(f"   Text preview: {preview}")
                    else:
                        print(f"   ⚠️ No text content found!")
                        # Show HTML structure instead
                        print(f"   HTML preview: {content[:300]}...")
                        
                except Exception as e:
                    print(f"   ❌ Error reading {html_file}: {e}")
            
            # Check manifest
            try:
                opf_files = [f for f in file_list if f.endswith('.opf')]
                if opf_files:
                    opf_content = epub_zip.read(opf_files[0]).decode('utf-8')
                    print(f"\n📋 Manifest file: {opf_files[0]}")
                    print(f"   OPF size: {len(opf_content)} chars")
            except Exception as e:
                print(f"   ❌ Error reading manifest: {e}")
                
    except Exception as e:
        print(f"❌ Error analyzing EPUB: {e}")

def compare_epub_files():
    """Compare original and translated EPUB files."""
    original_path = "/Users/kayvangharbi/PycharmProjects/BookTranslator/sample_books/Sway.epub"
    translated_path = "/Users/kayvangharbi/PycharmProjects/BookTranslator/apps/api/complete_output/complete_translated_es.epub"
    
    print("🔍 EPUB File Analysis & Comparison")
    print("=" * 60)
    
    if not os.path.exists(original_path):
        print(f"❌ Original EPUB not found: {original_path}")
        return
        
    if not os.path.exists(translated_path):
        print(f"❌ Translated EPUB not found: {translated_path}")
        return
    
    # Analyze original
    analyze_epub_structure(original_path, "ORIGINAL EPUB")
    
    # Analyze translated
    analyze_epub_structure(translated_path, "TRANSLATED EPUB")
    
    # Compare file sizes
    orig_size = os.path.getsize(original_path)
    trans_size = os.path.getsize(translated_path)
    
    print(f"\n📊 File Size Comparison:")
    print(f"Original:   {orig_size:,} bytes")
    print(f"Translated: {trans_size:,} bytes")
    print(f"Difference: {trans_size - orig_size:+,} bytes")
    
    # Try to identify the issue
    print(f"\n🔍 Diagnosis:")
    if trans_size < orig_size * 0.5:
        print("⚠️ Translated file is much smaller - likely missing content")
    elif trans_size > orig_size * 2:
        print("⚠️ Translated file is much larger - possible duplication")
    else:
        print("✅ File sizes are reasonable")

if __name__ == "__main__":
    compare_epub_files()