#!/usr/bin/env python3
"""
Inspect EPUB structure to understand content
"""
import sys
from pathlib import Path
from bs4 import BeautifulSoup

# Add the API to path
sys.path.insert(0, str(Path(__file__).parent / "apps" / "api"))

from app.pipeline.epub_io import EPUBProcessor

def inspect_epub():
    """Inspect EPUB structure."""
    
    epub_path = "/Users/kayvangharbi/PycharmProjects/BookTranslator/sample_books/Sway.epub"
    
    print("🔍 EPUB Content Inspector")
    print("=" * 60)
    
    processor = EPUBProcessor()
    original_book, docs = processor.read_epub(epub_path)
    
    print(f"📚 Total documents: {len(docs)}")
    print()
    
    for i, doc in enumerate(docs):
        print(f"📄 Document {i}: {doc['title'] or 'Untitled'}")
        print(f"   ID: {doc['id']}")
        print(f"   Href: {doc['href']}")
        print(f"   Content length: {len(doc['content'])} chars")
        
        # Parse content
        soup = BeautifulSoup(doc['content'], 'html.parser')
        
        # Count different elements
        images = soup.find_all(['img', 'image', 'svg'])
        text_elements = soup.find_all(string=True)
        text_content = [t.strip() for t in text_elements if t.strip()]
        
        print(f"   Images/SVG: {len(images)}")
        print(f"   Text strings: {len(text_content)}")
        
        # Show first few text pieces
        if text_content:
            print(f"   Text preview:")
            for j, text in enumerate(text_content[:3]):
                preview = text[:50] + "..." if len(text) > 50 else text
                print(f"     {j+1}: '{preview}' (len: {len(text)})")
        else:
            print(f"   ⚠️  No text content found")
            
        # Show HTML structure preview
        if len(doc['content']) < 500:
            print(f"   HTML preview:")
            print(f"   {doc['content']}")
        else:
            print(f"   HTML preview (first 300 chars):")
            print(f"   {doc['content'][:300]}...")
            
        print("-" * 40)
        print()

if __name__ == "__main__":
    inspect_epub()