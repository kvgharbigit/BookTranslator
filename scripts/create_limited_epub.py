#!/usr/bin/env python3
"""
Create a limited version of an EPUB with only the first N pages for testing.
"""
import sys
import os
import zipfile
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "api"))

from app.pipeline.epub_io import EPUBProcessor

def create_limited_epub(input_epub_path: str, output_epub_path: str, max_documents: int = 3):
    """Create a limited EPUB with only the first few documents."""
    
    processor = EPUBProcessor()
    
    # Read the original EPUB
    print(f"📖 Reading original EPUB: {input_epub_path}")
    original_book, original_docs = processor.read_epub(input_epub_path)
    
    print(f"   Found {len(original_docs)} documents total")
    
    # Limit to first N documents (approximately 20 pages)
    limited_docs = original_docs[:max_documents]
    
    print(f"   Using first {len(limited_docs)} documents (~20 pages)")
    
    # Calculate approximate character count
    total_chars = sum(len(doc['content']) for doc in limited_docs)
    estimated_tokens = total_chars // 4
    
    print(f"   Estimated content: {total_chars:,} characters (~{estimated_tokens:,} tokens)")
    
    # Write the limited EPUB
    success = processor.write_epub(original_book, limited_docs, output_epub_path)
    
    if success:
        file_size = os.path.getsize(output_epub_path)
        print(f"✅ Created limited EPUB: {output_epub_path} ({file_size:,} bytes)")
        return True
    else:
        print(f"❌ Failed to create limited EPUB")
        return False

if __name__ == "__main__":
    input_file = "/Users/kayvangharbi/PycharmProjects/BookTranslator/sample_books/pg236-images.epub"
    output_file = "/Users/kayvangharbi/PycharmProjects/BookTranslator/sample_books/pg236_limited.epub"
    
    if create_limited_epub(input_file, output_file, max_documents=3):
        print(f"\n🎯 Ready for testing with: {output_file}")
    else:
        print(f"\n❌ Failed to create limited version")
        sys.exit(1)