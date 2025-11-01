#!/usr/bin/env python3
"""
Inspect translated EPUB to identify untranslated chapter titles and broken TOC links
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "apps" / "api"))

from app.pipeline.epub_io import EPUBProcessor
from bs4 import BeautifulSoup

def inspect_translated_epub():
    """Inspect the translated EPUB for issues."""
    
    print("🔍 Inspecting Translated EPUB Issues")
    print("=" * 60)
    
    # Use latest translated EPUB
    epub_path = "test_outputs/gemini/translated_gemini.epub"
    
    if not Path(epub_path).exists():
        print(f"❌ Translated EPUB not found: {epub_path}")
        return
    
    processor = EPUBProcessor()
    book, docs = processor.read_epub(epub_path)
    
    print(f"📚 Loaded EPUB with {len(docs)} documents")
    
    # 1. Check for untranslated chapter titles in content
    print("\n📄 CHECKING CHAPTER TITLES IN CONTENT")
    print("-" * 40)
    
    english_patterns = [
        "Mowgli's Brothers", "Hunting-Song", "Kaa's Hunting", 
        "Road-Song", "Tiger! Tiger!", "The White Seal",
        "Rikki-Tikki-Tavi", "Toomai of the Elephants",
        "Her Majesty's Servants"
    ]
    
    untranslated_titles = []
    for i, doc in enumerate(docs):
        soup = BeautifulSoup(doc['content'], 'html.parser')
        
        # Find headings that might be chapter titles
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        for heading in headings:
            text = heading.get_text().strip()
            for pattern in english_patterns:
                if pattern in text:
                    untranslated_titles.append({
                        'doc': i,
                        'href': doc['href'],
                        'heading': heading.name,
                        'text': text,
                        'pattern': pattern
                    })
                    print(f"   ❌ Found untranslated: '{text}' in {doc['href']}")
    
    if not untranslated_titles:
        print("   ✅ No obviously untranslated chapter titles found")
    
    # 2. Check TOC structure and links
    print("\n📑 CHECKING TOC STRUCTURE AND LINKS")
    print("-" * 40)
    
    if hasattr(book, 'toc') and book.toc:
        print(f"TOC has {len(book.toc)} items")
        
        # Get actual spine document names
        spine_docs = []
        if hasattr(book, 'spine') and book.spine:
            for spine_item in book.spine:
                if isinstance(spine_item, tuple):
                    item_id, linear = spine_item
                    item = book.get_item_with_id(item_id)
                    if item:
                        spine_docs.append(item.get_name())
                else:
                    if hasattr(spine_item, 'get_name'):
                        spine_docs.append(spine_item.get_name())
        
        print(f"Spine documents: {spine_docs}")
        
        # Check each TOC item
        broken_links = []
        for i, toc_item in enumerate(book.toc):
            if hasattr(toc_item, 'href') and hasattr(toc_item, 'title'):
                href = toc_item.href.split('#')[0]  # Remove anchor
                title = toc_item.title
                
                if href not in spine_docs:
                    broken_links.append({
                        'index': i,
                        'title': title,
                        'href': href,
                        'exists': False
                    })
                    print(f"   ❌ Broken link: '{title}' -> {href}")
                else:
                    print(f"   ✅ Valid link: '{title}' -> {href}")
                    
                # Check if title is translated
                is_english = any(pattern in title for pattern in english_patterns)
                if is_english:
                    print(f"   ⚠️  Untranslated TOC title: '{title}'")
        
        print(f"\nSummary: {len(broken_links)} broken links out of {len(book.toc)} TOC items")
    else:
        print("❌ No TOC found in EPUB")
    
    # 3. Check actual document content for chapter markers
    print("\n🏷️  CHECKING DOCUMENT CONTENT FOR CHAPTER MARKERS")
    print("-" * 50)
    
    for i, doc in enumerate(docs):
        soup = BeautifulSoup(doc['content'], 'html.parser')
        
        # Look for chapter-like content
        title_elem = soup.find('title')
        title_text = title_elem.get_text() if title_elem else "No title"
        
        # Find the first significant heading or paragraph
        first_content = None
        for elem in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p']):
            text = elem.get_text().strip()
            if text and len(text) > 5:  # Skip very short content
                first_content = text[:100] + "..." if len(text) > 100 else text
                break
        
        print(f"   Doc {i} ({doc['href']}):")
        print(f"      Title: {title_text}")
        print(f"      First content: {first_content}")
        
        # Check if this looks like a chapter with English content
        if first_content:
            has_english = any(pattern in first_content for pattern in english_patterns)
            if has_english:
                print(f"      ⚠️  Contains English chapter title")

if __name__ == "__main__":
    inspect_translated_epub()