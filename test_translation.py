#!/usr/bin/env python3
"""
Direct translation test script - bypasses UI and tests core functionality
"""
import sys
import os
import shutil
import uuid
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

def test_translation(epub_path: str, target_lang: str = "es", output_dir: str = "test_output"):
    """Test EPUB translation directly without UI."""
    
    print(f"🧪 Testing EPUB Translation")
    print(f"📖 Source: {epub_path}")
    print(f"🌍 Target Language: {target_lang}")
    print(f"📁 Output Directory: {output_dir}")
    print()
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # 1. Process EPUB
        print("📚 Processing EPUB...")
        processor = EPUBProcessor()
        original_book, docs = processor.read_epub(epub_path)
        print(f"   Found {len(docs)} translatable documents")
        
        # 2. Segment content
        print("✂️  Segmenting content...")
        segmenter = HTMLSegmenter()
        segments, reconstruction_maps = segmenter.segment_documents(docs)
        print(f"   Created {len(segments)} translation segments")
        
        # 3. Setup provider
        print("🤖 Setting up Gemini provider...")
        provider = GeminiFlashProvider(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model
        )
        
        # 4. Translate
        print("🌐 Translating content...")
        orchestrator = TranslationOrchestrator()
        
        # This is async, so we need to use asyncio
        import asyncio
        translated_segments = asyncio.run(orchestrator.translate_segments(
            segments=segments,
            target_lang=target_lang,
            primary_provider=provider,
            source_lang=None  # Auto-detect
        ))
        print(f"   Translated {len(translated_segments)} segments")
        
        # 5. Reconstruct documents
        print("📝 Reconstructing documents...")
        translated_docs = segmenter.reconstruct_documents(translated_segments, reconstruction_maps, docs)
        
        # 6. Generate outputs  
        print("💾 Generating output files...")
        
        # Use the original book we already have
        
        # EPUB output
        epub_output = os.path.join(output_dir, f"translated_{target_lang}.epub")
        processor.write_epub(original_book, translated_docs, epub_output)
        print(f"   ✅ EPUB: {epub_output}")
        
        # TXT output (extract plain text from HTML)
        txt_output = os.path.join(output_dir, f"translated_{target_lang}.txt")
        with open(txt_output, 'w', encoding='utf-8') as f:
            for doc in translated_docs:
                f.write(f"=== {doc['title']} ===\n\n")
                
                # Extract plain text from HTML
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(doc['content'], 'html.parser')
                plain_text = soup.get_text(separator=' ', strip=True)
                f.write(plain_text)
                f.write("\n\n")
        print(f"   ✅ TXT: {txt_output}")
        
        # Sample content preview
        print("\n📄 Sample translated content:")
        print("-" * 50)
        sample_text = translated_segments[0][:300] if translated_segments else "No content"
        print(sample_text + "..." if len(sample_text) == 300 else sample_text)
        print("-" * 50)
        
        print(f"\n🎉 Translation completed successfully!")
        print(f"📁 Check output files in: {os.path.abspath(output_dir)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Translation failed: {e}")
        logger.error(f"Translation test failed: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    # Test with your sample book
    epub_path = "/Users/kayvangharbi/PycharmProjects/BookTranslator/sample_books/Sway.epub"
    
    if not os.path.exists(epub_path):
        print(f"❌ EPUB file not found: {epub_path}")
        sys.exit(1)
    
    success = test_translation(epub_path, target_lang="es")
    sys.exit(0 if success else 1)