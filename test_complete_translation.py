#!/usr/bin/env python3
"""
Complete translation test - handle all documents with mixed content
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
from app.logger import get_logger

logger = get_logger(__name__)

async def test_complete_translation(epub_path: str, target_lang: str = "es", output_dir: str = "complete_output"):
    """Test complete EPUB translation with mixed content support."""
    
    print(f"🧪 Complete EPUB Translation Test")
    print(f"📖 Source: {epub_path}")
    print(f"🌍 Target Language: {target_lang}")
    print(f"📁 Output Directory: {output_dir}")
    print("=" * 60)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # 1. Process EPUB
        print("📚 Processing EPUB...")
        processor = EPUBProcessor()
        original_book, docs = processor.read_epub(epub_path)
        print(f"   Found {len(docs)} documents")
        
        # 2. Analyze all documents
        print("🔍 Analyzing document content...")
        segmenter = HTMLSegmenter()
        
        for i, doc in enumerate(docs):
            segments, _ = segmenter.segment_documents([doc])
            title = doc['title'] or f"Document {i}"
            print(f"   Doc {i}: '{title}' - {len(segments)} segments")
        
        # 3. Segment ALL documents
        print("✂️  Segmenting all documents...")
        all_segments, reconstruction_maps = segmenter.segment_documents(docs)
        print(f"   Total segments from all documents: {len(all_segments)}")
        
        # Show segment distribution
        for map_info in reconstruction_maps:
            doc_title = map_info['doc_title'] or f"Doc {map_info['doc_idx']}"
            segment_count = map_info['segment_count']
            print(f"     {doc_title}: {segment_count} segments")
        
        if len(all_segments) == 0:
            print("❌ No translatable content found!")
            return False
        
        # 4. Translate all segments
        print(f"🌐 Translating {len(all_segments)} segments...")
        provider = GeminiFlashProvider(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model
        )
        
        orchestrator = TranslationOrchestrator()
        translated_segments, tokens_used, provider_used = await orchestrator.translate_segments(
            segments=all_segments,
            target_lang=target_lang,
            primary_provider=provider
        )
        
        print(f"✅ Translation completed:")
        print(f"   Input segments: {len(all_segments)}")
        print(f"   Output segments: {len(translated_segments)}")
        print(f"   Tokens used: {tokens_used}")
        print(f"   Provider: {provider_used}")
        
        if len(translated_segments) != len(all_segments):
            print(f"⚠️  Segment count mismatch! Expected {len(all_segments)}, got {len(translated_segments)}")
            return False
        
        # 5. Reconstruct all documents
        print("📝 Reconstructing all documents...")
        translated_docs = segmenter.reconstruct_documents(translated_segments, reconstruction_maps, docs)
        print(f"   Reconstructed {len(translated_docs)} documents")
        
        # 6. Generate outputs
        print("💾 Generating output files...")
        
        # EPUB output
        epub_output = os.path.join(output_dir, f"complete_translated_{target_lang}.epub")
        success = processor.write_epub(original_book, translated_docs, epub_output)
        if success:
            print(f"   ✅ EPUB: {epub_output}")
        else:
            print(f"   ❌ EPUB generation failed")
        
        # TXT output (extract plain text from HTML)
        txt_output = os.path.join(output_dir, f"complete_translated_{target_lang}.txt")
        with open(txt_output, 'w', encoding='utf-8') as f:
            for doc in translated_docs:
                f.write(f"=== {doc['title'] or 'Untitled'} ===\n\n")
                
                # Extract plain text from HTML
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(doc['content'], 'html.parser')
                plain_text = soup.get_text(separator=' ', strip=True)
                
                if plain_text.strip():  # Only write if there's actual text
                    f.write(plain_text)
                    f.write("\n\n")
                else:
                    f.write("[Document contains only images/formatting]\n\n")
                    
        print(f"   ✅ TXT: {txt_output}")
        
        # 7. Quality analysis
        print("\n📊 Translation Quality Analysis:")
        print("-" * 50)
        
        # Count documents with actual translations
        text_docs = 0
        image_docs = 0
        
        for doc in translated_docs:
            soup = BeautifulSoup(doc['content'], 'html.parser')
            plain_text = soup.get_text(separator=' ', strip=True)
            if plain_text.strip():
                text_docs += 1
            else:
                image_docs += 1
        
        print(f"Documents with text: {text_docs}")
        print(f"Documents with only images: {image_docs}")
        print(f"Total segments translated: {len(translated_segments)}")
        print(f"Translation tokens used: {tokens_used}")
        print(f"Estimated cost: ${tokens_used * 0.075 / 1000000:.4f}")
        
        # Show sample translation
        if len(all_segments) > 0 and len(translated_segments) > 0:
            print(f"\n📄 Sample translations:")
            print("-" * 50)
            for i in range(min(3, len(all_segments))):
                orig = all_segments[i][:100] + "..." if len(all_segments[i]) > 100 else all_segments[i]
                trans = translated_segments[i][:100] + "..." if len(translated_segments[i]) > 100 else translated_segments[i]
                print(f"Original: {orig}")
                print(f"Spanish:  {trans}")
                print()
        
        print(f"🎉 Complete translation successful!")
        print(f"📁 Check output files in: {os.path.abspath(output_dir)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Complete translation failed: {e}")
        logger.error(f"Complete translation failed: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    epub_path = "/Users/kayvangharbi/PycharmProjects/BookTranslator/sample_books/Sway.epub"
    
    if not os.path.exists(epub_path):
        print(f"❌ EPUB file not found: {epub_path}")
        sys.exit(1)
    
    success = asyncio.run(test_complete_translation(epub_path))
    sys.exit(0 if success else 1)