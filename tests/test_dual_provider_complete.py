#!/usr/bin/env python3
"""
Comprehensive dual provider test with all outputs (EPUB, PDF, TXT)
Tests both Gemini and Groq providers with cost analysis and quality comparison
"""
import sys
import os
import asyncio
import time
import json
import logging
import re
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

# Add the API to path and set working directory
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir / "apps" / "api"))

# Change to root directory to find .env file
os.chdir(root_dir)

# Import after path setup
from app.config import settings
from app.pipeline.epub_io import EPUBProcessor
from app.pipeline.html_segment import HTMLSegmenter
from app.pipeline.translate import TranslationOrchestrator
from app.providers.factory import get_provider  # Import from centralized factory
from app.pricing import calculate_provider_cost_cents, calculate_price_cents

# Import shared test utilities
from test_utils import analyze_translation_quality, print_comparison_summary

# Check if Calibre is available for PDF generation
import subprocess
try:
    result = subprocess.run(['which', 'ebook-convert'], capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Calibre ebook-convert available for PDF generation")
    else:
        print("⚠️  Calibre not found - PDF generation will be skipped")
except Exception as e:
    print(f"⚠️  Error checking for Calibre: {e}")

from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
)

async def test_provider(provider_name: str, provider, epub_path: str, target_lang: str = "es") -> Dict[str, Any]:
    """Test a single provider and return comprehensive results."""
    
    print(f"\n🔄 Testing {provider_name.upper()} Provider")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # Step 1: Read and process EPUB
        print("📚 Reading EPUB...")
        processor = EPUBProcessor()
        original_book, docs = processor.read_epub(epub_path)
        print(f"   Found {len(docs)} documents")
        
        # Step 2: Segment documents
        print("✂️  Segmenting documents...")
        segmenter = HTMLSegmenter()
        segments, reconstruction_maps = segmenter.segment_documents(docs)
        print(f"   Created {len(segments)} segments")
        
        # Calculate estimated tokens (rough estimate: 4 chars per token)
        total_chars = sum(len(segment) for segment in segments)
        estimated_tokens = total_chars // 4
        print(f"   Estimated input tokens: {estimated_tokens:,}")
        
        # Step 3: Translate
        print(f"🌐 Translating with {provider_name}...")
        translation_start = time.time()
        
        orchestrator = TranslationOrchestrator()
        translated_segments, tokens_used, provider_used = await orchestrator.translate_segments(
            segments=segments,
            target_lang=target_lang,
            primary_provider=provider
        )
        
        translation_time = time.time() - translation_start
        print(f"✅ Translation completed in {translation_time:.2f}s")
        print(f"   Actual tokens used: {tokens_used:,}")
        print(f"   Provider used: {provider_used}")
        
        # Calculate comprehensive cost analysis
        provider_cost_cents = calculate_provider_cost_cents(tokens_used, provider_used)
        provider_cost_usd = provider_cost_cents / 100
        
        # Calculate what user would pay
        user_price_cents = calculate_price_cents(tokens_used, provider_used)
        user_price_usd = user_price_cents / 100
        
        # Calculate profit margin
        profit_cents = user_price_cents - provider_cost_cents
        profit_usd = profit_cents / 100
        profit_margin_pct = (profit_cents / user_price_cents * 100) if user_price_cents > 0 else 0
        
        print(f"💰 Cost Analysis:")
        print(f"   Total tokens: {tokens_used:,}")
        print(f"   Provider cost: ${provider_cost_usd:.4f} USD ({provider_cost_cents} cents)")
        print(f"   User pays: ${user_price_usd:.2f} USD ({user_price_cents} cents)")
        print(f"   Profit: ${profit_usd:.4f} USD ({profit_cents} cents)")
        print(f"   Profit margin: {profit_margin_pct:.1f}%")
        print(f"   Provider rate: ${(provider_cost_cents / tokens_used * 1000000):.2f} per 1M tokens")
        
        # Step 4: Reconstruct documents
        print("📝 Reconstructing documents...")
        translated_docs = segmenter.reconstruct_documents(translated_segments, reconstruction_maps, docs)
        
        # Step 5: Generate outputs
        output_dir = root_dir / "test_outputs" / f"{provider_name.lower()}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        outputs_generated = await generate_all_outputs(
            provider_name, str(output_dir), original_book, translated_docs, translated_segments
        )
        
        total_time = time.time() - start_time
        
        # Step 6: Quality analysis
        quality_metrics = analyze_translation_quality(segments[:10], translated_segments[:10], provider_name)
        
        return {
            "provider": provider_name,
            "success": True,
            "documents": len(docs),
            "segments": len(segments),
            "tokens_used": tokens_used,
            "provider_cost_cents": provider_cost_cents,
            "provider_cost_usd": provider_cost_usd,
            "user_price_cents": user_price_cents,
            "user_price_usd": user_price_usd,
            "profit_cents": profit_cents,
            "profit_usd": profit_usd,
            "profit_margin_pct": profit_margin_pct,
            "translation_time": translation_time,
            "total_time": total_time,
            "outputs": outputs_generated,
            "quality": quality_metrics,
            "provider_used": provider_used,
            "output_dir": str(output_dir)
        }
        
    except Exception as e:
        print(f"❌ {provider_name} failed: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "provider": provider_name,
            "success": False,
            "error": str(e),
            "provider_cost_cents": 0,
            "provider_cost_usd": 0.0,
            "user_price_cents": 0,
            "user_price_usd": 0.0,
            "profit_cents": 0,
            "profit_usd": 0.0,
            "profit_margin_pct": 0.0
        }

async def generate_all_outputs(provider_name: str, output_dir: str, original_book, translated_docs: list, translated_segments: list) -> Dict[str, bool]:
    """Generate EPUB, PDF, and TXT outputs using shared common function."""

    print(f"💾 Generating outputs for {provider_name}...")

    # Import shared modules
    from pathlib import Path
    sys.path.insert(0, str(root_dir / "common"))
    from common.outputs import generate_outputs_with_metadata, OutputGenerator

    # Use job_id format for file naming (provider_name lowercase)
    job_id = f"translated_{provider_name.lower()}"

    # Use common output generation function (same as production)
    results = await generate_outputs_with_metadata(
        output_dir=output_dir,
        job_id=job_id,
        original_book=original_book,
        translated_docs=translated_docs,
        translated_segments=translated_segments
    )

    # Print file info for successful outputs
    output_generator = OutputGenerator()
    file_paths = output_generator.get_output_files(output_dir, job_id)
    for format_type, path in file_paths.items():
        if path and os.path.exists(path):
            if format_type in ["epub", "pdf"]:
                file_size = os.path.getsize(path) / 1024 / 1024  # MB
                print(f"   ✅ {format_type.upper()}: {path} ({file_size:.1f} MB)")
            else:  # txt
                file_size = os.path.getsize(path) / 1024  # KB
                print(f"   ✅ {format_type.upper()}: {path} ({file_size:.1f} KB)")

    return results


# Functions now imported from test_utils

def generate_original_formats(epub_path: str):
    """Generate original formats (EPUB, PDF, TXT) for comparison."""
    print("\n📚 GENERATING ORIGINAL FORMATS FOR COMPARISON")
    print("=" * 60)
    
    # Create original directory
    original_dir = root_dir / "test_outputs" / "original"
    original_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy original EPUB
    import shutil
    original_epub_path = original_dir / "original.epub"
    shutil.copy2(epub_path, original_epub_path)
    
    epub_size = Path(epub_path).stat().st_size / (1024 * 1024)
    print(f"   ✅ EPUB: {original_epub_path} ({epub_size:.1f} MB)")
    
    # Generate PDF from original using Calibre
    try:
        print("🔄 Converting original EPUB to PDF...")
        pdf_path = original_dir / "original.pdf"

        result = subprocess.run(
            ['ebook-convert', str(original_epub_path), str(pdf_path),
             '--paper-size', 'a5',
             '--pdf-page-margin-bottom', '36',
             '--pdf-page-margin-top', '36',
             '--pdf-page-margin-left', '36',
             '--pdf-page-margin-right', '36'],
            check=True,
            capture_output=True,
            text=True
        )

        if pdf_path.exists():
            pdf_size = pdf_path.stat().st_size / (1024 * 1024)
            print(f"   ✅ PDF: {pdf_path} ({pdf_size:.1f} MB)")
        else:
            print("   ❌ PDF generation failed")
    except Exception as e:
        print(f"   ❌ PDF error: {e}")
    
    # Generate TXT from original
    try:
        print("🔄 Converting original EPUB to TXT...")
        processor = EPUBProcessor()
        original_book, docs = processor.read_epub(str(original_epub_path))
        
        # Generate English TXT with same structure as translations
        formatted_content = [
            "=" * 70,
            "THE JUNGLE BOOK".center(70),
            "=" * 70,
            "",
            "Original Title: The Jungle Book",
            "Author: Rudyard Kipling",
            "Language: English", 
            "Source: Project Gutenberg",
            "",
            "This is the original English text for comparison purposes.",
            "",
            "=" * 70,
            "",
            ""
        ]
        
        actual_chapter_count = 0
        for i, doc in enumerate(docs):
            content = doc.get('content', '')
            
            # Skip metadata documents
            if len(content.strip()) < 500 or 'gutenberg' in content.lower() or 'ebook' in content.lower():
                if any(keyword in content.lower() for keyword in ['contents', 'table']):
                    formatted_content.append(f"\n{'='*60}")
                    formatted_content.append("TABLE OF CONTENTS".center(60))
                    formatted_content.append(f"{'='*60}\n")
                    
                    # Add original TOC entries
                    try:
                        soup = BeautifulSoup(doc['content'], 'xml')
                        for element in soup.find_all(['p', 'div', 'li', 'a']):
                            text = element.get_text(strip=True)
                            if text and len(text) > 3 and len(text) < 100:
                                if not any(skip in text.lower() for skip in ['project gutenberg', 'ebook']):
                                    formatted_content.append(f"• {text}")
                        formatted_content.append("")
                    except:
                        formatted_content.append("Content available in main document")
                        formatted_content.append("")
                else:
                    continue
            else:
                # This is actual chapter content
                actual_chapter_count += 1
                
                # Extract first heading as chapter title
                chapter_title = None
                try:
                    soup = BeautifulSoup(doc['content'], 'xml')
                    for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                        heading_text = heading.get_text(strip=True)
                        if (heading_text and len(heading_text) > 3 and 
                            not any(skip in heading_text.lower() for skip in ['project gutenberg', 'ebook', 'contents', 'table'])):
                            chapter_title = heading_text.strip()
                            break
                except:
                    pass
                
                # Add chapter header
                if chapter_title:
                    formatted_content.append(f"\n{'='*60}")
                    formatted_content.append(f"{chapter_title.upper().center(60)}")
                    formatted_content.append(f"{'='*60}\n")
                else:
                    formatted_content.append(f"\n{'='*60}")
                    formatted_content.append(f"CHAPTER {actual_chapter_count}".center(60))
                    formatted_content.append(f"{'='*60}\n")
                
                # Extract content with proper structure
                try:
                    # Preserve line breaks from <br> tags
                    content = doc['content']
                    content = content.replace('<br>', '\n').replace('<br/>', '\n').replace('<br />', '\n')
                    soup = BeautifulSoup(content, 'xml')
                    seen_texts = set()
                    first_heading_used = False
                    
                    for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'blockquote']):
                        if element.name == 'div' and element.find(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                            continue
                            
                        text = element.get_text(separator=' ', strip=True)
                        if not text or len(text) < 3:
                            continue
                        
                        text_key = text.lower().replace(' ', '')[:100]
                        if text_key in seen_texts:
                            continue
                        seen_texts.add(text_key)
                        
                        if any(keyword in text.lower() for keyword in ['project gutenberg', 'ebook #', 'gutenberg.org']):
                            continue
                        
                        if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                            if chapter_title and not first_heading_used and text.strip() == chapter_title:
                                first_heading_used = True
                                continue
                            
                            formatted_content.append(f"\n{text.upper()}")
                            formatted_content.append("-" * min(len(text), 40))
                            formatted_content.append("")
                        
                        elif element.name in ['p', 'blockquote']:
                            clean_text = ' '.join(text.split())
                            if len(clean_text) > 15:
                                if len(clean_text) > 500:
                                    sentences = []
                                    current_sentence = ""
                                    words = clean_text.split()
                                    
                                    for word in words:
                                        current_sentence += word + " "
                                        if word.endswith(('.', '!', '?', '."', '!"', '?"')) and len(current_sentence) > 100:
                                            sentences.append(current_sentence.strip())
                                            current_sentence = ""
                                    
                                    if current_sentence.strip():
                                        sentences.append(current_sentence.strip())
                                    
                                    for sentence in sentences:
                                        if len(sentence) > 15:
                                            formatted_content.append(sentence)
                                            if len(sentence) > 200:
                                                formatted_content.append("")
                                else:
                                    formatted_content.append(clean_text)
                                
                                formatted_content.append("")
                except:
                    # Fallback
                    try:
                        # Preserve line breaks from <br> tags in fallback case
                        content_fb = doc['content'].replace('<br>', '\n').replace('<br/>', '\n').replace('<br />', '\n')
                        text = BeautifulSoup(content_fb, 'xml').get_text(separator='\n', strip=True)
                        paragraphs = [p.strip() for p in text.split('\n') if p.strip() and len(p.strip()) > 15]
                        for para in paragraphs[:20]:  # Limit for safety
                            if not any(keyword in para.lower() for keyword in ['project gutenberg', 'ebook #']):
                                formatted_content.append(para)
                                formatted_content.append("")
                    except:
                        formatted_content.append("Content could not be processed")
                        formatted_content.append("")
        
        # Save TXT file
        txt_path = original_dir / "original.txt"
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(formatted_content))
        
        txt_size = txt_path.stat().st_size / 1024
        print(f"   ✅ TXT: {txt_path} ({txt_size:.1f} KB)")
        
    except Exception as e:
        print(f"   ❌ TXT error: {e}")
    
    print(f"\n📁 Original formats ready in: {original_dir}")

async def main():
    """Run comprehensive dual-provider test."""
    
    print("🚀 DUAL PROVIDER TRANSLATION TEST")
    print("Testing both Gemini and Groq with all output formats")
    print("=" * 80)
    
    # Check for test EPUB files
    possible_paths = [
        root_dir / "sample_books" / "pg236_first20pages.epub",
        root_dir / "sample_books" / "pg236-images.epub", 
        root_dir / "sample_books" / "Sway.epub"
    ]
    
    epub_path = None
    for path in possible_paths:
        if path.exists():
            epub_path = str(path)
            break
    
    if not epub_path:
        print(f"❌ No EPUB file found in sample_books/")
        print(f"   Looked for: {[str(p) for p in possible_paths]}")
        return
    
    print(f"📖 Testing with: {epub_path}")
    print(f"🎯 Target language: Spanish (es)")
    print(f"🔧 Gemini model: {settings.gemini_model}")
    print(f"🔧 Groq model: {settings.groq_model}")
    
    # Initialize providers using common base
    gemini_provider = get_provider("gemini")
    groq_provider = get_provider("groq")
    
    # Generate original formats for comparison
    generate_original_formats(epub_path)
    
    # Run tests
    gemini_results = await test_provider("Gemini", gemini_provider, epub_path)
    groq_results = await test_provider("Groq", groq_provider, epub_path)
    
    # Print comparison
    print_comparison_summary(gemini_results, groq_results)
    
    # Save results to JSON
    results = {
        "timestamp": datetime.now().isoformat(),
        "epub_file": epub_path,
        "target_language": "es",
        "gemini": gemini_results,
        "groq": groq_results
    }
    
    results_file = root_dir / "test_outputs" / f"comparison_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {results_file}")

if __name__ == "__main__":
    asyncio.run(main())