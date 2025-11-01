#!/usr/bin/env python3
"""
Debug EPUB writing process
"""
import sys
import os
from pathlib import Path

# Add the API to path
sys.path.insert(0, str(Path(__file__).parent / "apps" / "api"))

from app.pipeline.epub_io import EPUBProcessor
import ebooklib
from ebooklib import epub

def debug_epub_write():
    """Debug the EPUB writing process."""
    
    print("🔍 Debug EPUB Writing Process")
    print("=" * 50)
    
    epub_path = "/Users/kayvangharbi/PycharmProjects/BookTranslator/sample_books/Sway.epub"
    
    try:
        # 1. Read original
        print("📚 Reading original EPUB...")
        processor = EPUBProcessor()
        original_book, docs = processor.read_epub(epub_path)
        print(f"   Found {len(docs)} documents")
        
        # 2. Show original structure
        print("🔍 Original document structure:")
        for i, doc in enumerate(docs[:3]):  # First 3 docs
            print(f"   Doc {i}:")
            print(f"     ID: {doc['id']}")
            print(f"     Href: {doc['href']}")
            print(f"     Title: {doc['title']}")
            print(f"     Content length: {len(doc['content'])} chars")
            if len(doc['content']) > 0:
                preview = doc['content'][:200] + "..." if len(doc['content']) > 200 else doc['content']
                print(f"     Content preview: {preview}")
            print()
        
        # 3. Create minimal translated docs (just modify a few words)
        print("✏️  Creating test translated docs...")
        translated_docs = []
        for doc in docs:
            # Simple test translation - replace some English words
            content = doc['content']
            content = content.replace("Copyright", "Derechos de autor")
            content = content.replace("All rights reserved", "Todos los derechos reservados")
            content = content.replace("THE HOUSES", "LAS CASAS")
            
            translated_docs.append({
                'id': doc['id'],
                'href': doc['href'], 
                'title': doc['title'],
                'content': content
            })
        
        print(f"   Created {len(translated_docs)} translated documents")
        
        # 4. Test EPUB writing with debug
        print("💾 Testing EPUB writing...")
        output_path = "/Users/kayvangharbi/PycharmProjects/BookTranslator/debug_output.epub"
        
        try:
            # Create new book with same metadata  
            new_book = epub.EpubBook()
            
            # Copy metadata
            print("   Copying metadata...")
            new_book.set_identifier(original_book.get_metadata('DC', 'identifier')[0][0])
            new_book.set_title(original_book.get_metadata('DC', 'title')[0][0])
            new_book.set_language(original_book.get_metadata('DC', 'language')[0][0])
            
            # Copy authors
            for author in original_book.get_metadata('DC', 'creator'):
                new_book.add_author(author[0])
            
            # Copy all non-document items (CSS, images, fonts, etc.)
            print("   Copying non-document items...")
            for item in original_book.get_items():
                if item.get_type() != ebooklib.ITEM_DOCUMENT:
                    new_book.add_item(item)
                    print(f"     Copied: {item.get_name()} ({item.get_type()})")
            
            # Add translated documents with debug
            print("   Adding translated documents...")
            spine = []
            for i, doc in enumerate(translated_docs):
                print(f"     Processing doc {i}: {doc['href']}")
                print(f"       Content length: {len(doc['content'])} chars")
                
                # Create new EPUB item
                chapter = epub.EpubHtml(
                    title=doc['title'] or f"Chapter {i}",
                    file_name=doc['href'],
                    lang='es'  # Force Spanish
                )
                
                # Set content with debug
                chapter.content = doc['content'].encode('utf-8') if isinstance(doc['content'], str) else doc['content']
                print(f"       Set content: {len(chapter.content)} bytes")
                
                new_book.add_item(chapter)
                spine.append(chapter)
                print(f"       Added to book and spine")
            
            # Set spine
            print("   Setting spine...")
            new_book.spine = spine
            print(f"   Spine has {len(new_book.spine)} items")
            
            # Write EPUB with debug
            print("   Writing EPUB file...")
            epub.write_epub(output_path, new_book)
            
            print(f"✅ Debug EPUB written to: {output_path}")
            
            # Verify the output
            if os.path.exists(output_path):
                size = os.path.getsize(output_path)
                print(f"   File size: {size:,} bytes")
                
                # Quick check of content
                import zipfile
                with zipfile.ZipFile(output_path, 'r') as z:
                    html_files = [f for f in z.namelist() if f.endswith('.html')]
                    print(f"   HTML files in output: {len(html_files)}")
                    
                    if html_files:
                        test_content = z.read(html_files[0]).decode('utf-8')
                        print(f"   First file content length: {len(test_content)} chars")
                        if len(test_content) > 0:
                            print(f"   Content preview: {test_content[:200]}...")
                        else:
                            print("   ⚠️ File is empty!")
            
        except Exception as e:
            print(f"❌ EPUB writing failed: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_epub_write()