#!/usr/bin/env python3
"""
Debug translation test with detailed logging
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

async def debug_translation_small():
    """Test translation with just a few segments for debugging."""
    
    print("🔍 DEBUG: Small Translation Test")
    print("=" * 50)
    
    try:
        # 1. Create test segments (small number for debugging)
        test_segments = [
            "This is a test sentence.",
            "The quick brown fox jumps over the lazy dog.", 
            "Hello world, how are you today?"
        ]
        
        print(f"📝 Test segments: {len(test_segments)}")
        for i, seg in enumerate(test_segments):
            print(f"   {i+1}: {seg}")
        print()
        
        # 2. Setup provider with logging
        print("🤖 Setting up Gemini provider...")
        provider = GeminiFlashProvider(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model
        )
        print(f"   Model: {settings.gemini_model}")
        print(f"   Max batch tokens: {settings.max_batch_tokens}")
        print()
        
        # 3. Test direct provider translation
        print("🌐 Testing direct provider translation...")
        translated_direct = await provider.translate_segments(
            segments=test_segments,
            src_lang=None,  # Auto-detect
            tgt_lang="es"
        )
        
        print(f"✅ Direct translation results ({len(translated_direct)} segments):")
        for i, (orig, trans) in enumerate(zip(test_segments, translated_direct)):
            print(f"   {i+1}: '{orig}' → '{trans}'")
        print()
        
        # 4. Test orchestrator
        print("🎭 Testing orchestrator translation...")
        orchestrator = TranslationOrchestrator()
        translated_orchestrated, tokens_used, provider_used = await orchestrator.translate_segments(
            segments=test_segments,
            target_lang="es",
            primary_provider=provider
        )
        
        print(f"✅ Orchestrated translation results:")
        print(f"   Segments: {len(translated_orchestrated)}")
        print(f"   Tokens used: {tokens_used}")
        print(f"   Provider: {provider_used}")
        for i, (orig, trans) in enumerate(zip(test_segments, translated_orchestrated)):
            print(f"   {i+1}: '{orig}' → '{trans}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Debug translation failed: {e}")
        logger.error(f"Debug translation failed: {e}", exc_info=True)
        return False

async def debug_translation_epub():
    """Test with actual EPUB but limited segments."""
    
    print("\n🔍 DEBUG: EPUB Translation Test")
    print("=" * 50)
    
    epub_path = "/Users/kayvangharbi/PycharmProjects/BookTranslator/sample_books/Sway.epub"
    
    if not os.path.exists(epub_path):
        print(f"❌ EPUB file not found: {epub_path}")
        return False
    
    try:
        # 1. Process EPUB
        print("📚 Processing EPUB...")
        processor = EPUBProcessor()
        original_book, docs = processor.read_epub(epub_path)
        print(f"   Found {len(docs)} documents")
        
        # 2. Segment content (find document with actual text)
        print("✂️  Finding document with text content...")
        segmenter = HTMLSegmenter()
        
        # Find first document with meaningful text
        text_doc = None
        for i, doc in enumerate(docs):
            test_segments, _ = segmenter.segment_documents([doc])
            if len(test_segments) > 0:
                print(f"   Document {i} ({doc['title']}) has {len(test_segments)} segments")
                text_doc = doc
                break
            else:
                print(f"   Document {i} ({doc['title']}) has no text segments")
        
        if not text_doc:
            print("   ❌ No documents with text found!")
            return False
            
        # Segment the text document
        segments, reconstruction_maps = segmenter.segment_documents([text_doc])
        print(f"   Using document: {text_doc['title']}")
        print(f"   Created {len(segments)} segments")
        
        # Limit to first 5 segments for debugging
        if len(segments) > 5:
            segments = segments[:5]
            print(f"   🔍 Limiting to first 5 segments for debugging")
        
        for i, seg in enumerate(segments):
            print(f"   {i+1}: {seg[:100]}{'...' if len(seg) > 100 else ''}")
        print()
        
        # 3. Translate with logging
        print("🌐 Translating segments...")
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
        
        print(f"✅ Translation completed:")
        print(f"   Input segments: {len(segments)}")
        print(f"   Output segments: {len(translated_segments)}")
        print(f"   Tokens used: {tokens_used}")
        print(f"   Provider: {provider_used}")
        print()
        
        # 4. Show translation quality
        print("📄 Translation quality sample:")
        print("-" * 50)
        for i, (orig, trans) in enumerate(zip(segments[:3], translated_segments[:3])):
            print(f"Original {i+1}: {orig}")
            print(f"Spanish {i+1}:  {trans}")
            print()
        
        # 5. Test reconstruction
        print("📝 Testing reconstruction...")
        
        # Pad translated_segments to match original if needed
        if len(translated_segments) < len(segments):
            print(f"   ⚠️  Padding {len(segments) - len(translated_segments)} missing translations")
            translated_segments.extend(segments[len(translated_segments):])
        
        translated_docs = segmenter.reconstruct_documents(translated_segments, reconstruction_maps, [text_doc])
        print(f"   Reconstructed {len(translated_docs)} documents")
        
        # 6. Show final output sample
        if translated_docs:
            print("\n📄 Final HTML output sample:")
            print("-" * 50)
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(translated_docs[0]['content'], 'html.parser')
            plain_text = soup.get_text(separator=' ', strip=True)[:500]
            print(plain_text + "..." if len(plain_text) == 500 else plain_text)
        
        return True
        
    except Exception as e:
        print(f"❌ EPUB debug failed: {e}")
        logger.error(f"EPUB debug failed: {e}", exc_info=True)
        return False

async def main():
    """Run debug tests."""
    
    print("🧪 EPUB Translator Debug Suite")
    print("=" * 60)
    print(f"Environment: {settings.env}")
    print(f"Gemini Model: {settings.gemini_model}")
    print(f"Max Batch Tokens: {settings.max_batch_tokens}")
    print(f"API Key: {settings.gemini_api_key[:10]}...")
    print("=" * 60)
    
    # Test 1: Simple segments
    success1 = await debug_translation_small()
    
    # Test 2: Real EPUB (limited)
    success2 = await debug_translation_epub()
    
    if success1 and success2:
        print("\n🎉 All debug tests passed!")
        return True
    else:
        print("\n❌ Some debug tests failed!")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)