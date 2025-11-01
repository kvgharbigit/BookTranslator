#!/usr/bin/env python3
"""
Debug translation content and reconstruction
"""
import sys
import os
import asyncio
from pathlib import Path

# Add the API to path
sys.path.insert(0, str(Path(__file__).parent / "apps" / "api"))

from app.config import settings
from app.pipeline.epub_io import EPUBProcessor
from app.pipeline.html_segment import HTMLSegmenter
from app.pipeline.translate import TranslationOrchestrator
from app.providers.gemini import GeminiFlashProvider

async def debug_translation_content():
    """Debug the translation content generation."""
    
    print("🔍 Debug Translation Content Generation")
    print("=" * 50)
    
    epub_path = "/Users/kayvangharbi/PycharmProjects/BookTranslator/sample_books/Sway.epub"
    
    try:
        # 1. Read EPUB
        print("📚 Reading EPUB...")
        processor = EPUBProcessor()
        original_book, docs = processor.read_epub(epub_path)
        print(f"   Found {len(docs)} documents")
        
        # 2. Focus on just one document for debugging
        test_doc = docs[1]  # Copyright page - has good text content
        print(f"\n🔍 Testing with document: {test_doc['href']}")
        print(f"   Original content length: {len(test_doc['content'])} chars")
        print(f"   Original preview: {test_doc['content'][:300]}...")
        
        # 3. Segment the document
        print("\n✂️  Segmenting document...")
        segmenter = HTMLSegmenter()
        segments, reconstruction_maps = segmenter.segment_documents([test_doc])
        print(f"   Created {len(segments)} segments")
        
        for i, segment in enumerate(segments[:5]):
            print(f"     Segment {i}: '{segment}'")
        
        # 4. Translate segments
        print(f"\n🌐 Translating {len(segments)} segments...")
        provider = GeminiFlashProvider(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model
        )
        
        orchestrator = TranslationOrchestrator()
        translated_segments, tokens_used, provider_used = await orchestrator.translate_segments(
            segments=segments,
            target_lang="es",
            primary_provider=provider
        )
        
        print(f"✅ Translation completed: {len(translated_segments)} segments")
        print(f"   Tokens used: {tokens_used}")
        
        for i, (orig, trans) in enumerate(zip(segments[:5], translated_segments[:5])):
            print(f"     {i}: '{orig}' → '{trans}'")
        
        # 5. Reconstruct document
        print(f"\n📝 Reconstructing document...")
        translated_docs = segmenter.reconstruct_documents(translated_segments, reconstruction_maps, [test_doc])
        
        if translated_docs:
            reconstructed = translated_docs[0]
            print(f"   Reconstructed content length: {len(reconstructed['content'])} chars")
            print(f"   Reconstructed preview: {reconstructed['content'][:500]}...")
            
            # 6. Test EPUB writing with this one document
            print(f"\n💾 Testing EPUB writing with reconstructed content...")
            output_path = "/Users/kayvangharbi/PycharmProjects/BookTranslator/debug_single_doc.epub"
            
            success = processor.write_epub(original_book, translated_docs, output_path)
            
            if success:
                print(f"✅ Single document EPUB written successfully")
                
                # Verify content
                import zipfile
                with zipfile.ZipFile(output_path, 'r') as z:
                    html_files = [f for f in z.namelist() if f.endswith('.html')]
                    if html_files:
                        content = z.read(html_files[0]).decode('utf-8')
                        print(f"   Verification: {len(content)} chars in first HTML file")
                        if len(content) > 0:
                            print(f"   Content looks good: {content[:200]}...")
                        else:
                            print("   ⚠️ File is empty!")
            else:
                print("❌ EPUB writing failed")
        else:
            print("❌ Document reconstruction failed")
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_translation_content())