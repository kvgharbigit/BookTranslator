#!/usr/bin/env python3
"""
Comprehensive test comparing Gemini and Llama providers
Tests translation quality, cost, and generates all output formats (EPUB, PDF, TXT)
"""
import sys
import os
import asyncio
import time
import json
import logging
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

# Add the API to path and set working directory
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir / "apps" / "api"))

# Change to root directory to find .env file
import os
os.chdir(root_dir)

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'/Users/kayvangharbi/PycharmProjects/BookTranslator/logs/test_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

from app.config import settings
from app.pipeline.epub_io import EPUBProcessor
from app.pipeline.html_segment import HTMLSegmenter
from app.pipeline.translate import TranslationOrchestrator
from app.providers.gemini import GeminiFlashProvider
from app.providers.groq import GroqLlamaProvider
from app.pricing import calculate_provider_cost_cents, calculate_provider_cost_display, calculate_price_cents

# WeasyPrint setup with environment variable
os.environ['DYLD_LIBRARY_PATH'] = "/opt/homebrew/lib:" + os.environ.get('DYLD_LIBRARY_PATH', '')

try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except Exception as e:
    print(f"⚠️  WeasyPrint not available: {e}")
    WEASYPRINT_AVAILABLE = False

from bs4 import BeautifulSoup

async def test_provider(provider_name: str, provider, epub_path: str, target_lang: str = "es") -> Dict[str, Any]:
    """Test a single provider and return comprehensive results."""
    
    print(f"\n🔄 Testing {provider_name.upper()} Provider")
    print("=" * 60)
    logger.info(f"Starting {provider_name} provider test")
    
    start_time = time.time()
    
    try:
        # Step 1: Read and process EPUB
        print("📚 Reading EPUB...")
        logger.info(f"Reading EPUB file: {epub_path}")
        processor = EPUBProcessor()
        original_book, docs = processor.read_epub(epub_path)
        print(f"   Found {len(docs)} documents")
        logger.info(f"Successfully read {len(docs)} documents from EPUB")
        
        # Step 2: Segment documents
        print("✂️  Segmenting documents...")
        logger.info("Starting document segmentation")
        segmenter = HTMLSegmenter()
        segments, reconstruction_maps = segmenter.segment_documents(docs)
        print(f"   Created {len(segments)} segments")
        logger.info(f"Segmentation completed: {len(segments)} segments created")
        
        # Calculate estimated tokens (rough estimate: 4 chars per token)
        total_chars = sum(len(segment) for segment in segments)
        estimated_tokens = total_chars // 4
        print(f"   Estimated input tokens: {estimated_tokens:,}")
        logger.info(f"Token estimation: {total_chars:,} chars = ~{estimated_tokens:,} tokens")
        
        # Step 3: Translate
        print(f"🌐 Translating with {provider_name}...")
        logger.info(f"Starting translation with {provider_name} provider")
        translation_start = time.time()
        
        orchestrator = TranslationOrchestrator()
        logger.info(f"Translating {len(segments)} segments to {target_lang}")
        translated_segments, tokens_used, provider_used = await orchestrator.translate_segments(
            segments=segments,
            target_lang=target_lang,
            primary_provider=provider
        )
        
        translation_time = time.time() - translation_start
        print(f"✅ Translation completed in {translation_time:.2f}s")
        print(f"   Actual tokens used: {tokens_used:,}")
        print(f"   Provider used: {provider_used}")
        logger.info(f"Translation completed: {tokens_used:,} tokens in {translation_time:.2f}s using {provider_used}")
        
        # Calculate precise costs with sub-cent granularity
        provider_cost_decimal = calculate_provider_cost_cents(tokens_used, provider_used)
        provider_cost_display = calculate_provider_cost_display(tokens_used, provider_used)
        user_price_cents = calculate_price_cents(tokens_used)
        user_price_usd = user_price_cents / 100
        
        # Calculate profit with decimal precision
        profit_decimal = user_price_usd - float(provider_cost_decimal)
        profit_margin_pct = (profit_decimal / user_price_usd * 100) if user_price_usd > 0 else 0
        
        # Convert to micro-USD for precise tracking
        provider_cost_micro_usd = int(provider_cost_decimal * 1_000_000)
        profit_micro_usd = int(profit_decimal * 1_000_000)
        
        print(f"💰 Enhanced Cost Analysis (Sub-Cent Precision):")
        print(f"   Total tokens: {tokens_used:,}")
        print(f"   Provider cost: {provider_cost_display} ({provider_cost_micro_usd:,} micro-USD)")
        print(f"   User pays: ${user_price_usd:.2f} ({user_price_cents} cents)")
        print(f"   Profit: ${profit_decimal:.6f} ({profit_micro_usd:,} micro-USD)")
        print(f"   Profit margin: {profit_margin_pct:.2f}%")
        print(f"   Cost per 1M tokens: ${float(provider_cost_decimal) * 1_000_000 / tokens_used:.6f}")
        
        logger.info(f"Enhanced cost analysis for {provider_name}:")
        logger.info(f"  Tokens: {tokens_used:,}")
        logger.info(f"  Provider cost: {provider_cost_display} ({provider_cost_micro_usd:,} micro-USD)")
        logger.info(f"  User price: ${user_price_usd:.2f} ({user_price_cents} cents)")
        logger.info(f"  Profit: ${profit_decimal:.6f} ({profit_margin_pct:.2f}% margin)")
        
        # Step 4: Reconstruct documents
        print("📝 Reconstructing documents...")
        logger.info("Starting document reconstruction")
        translated_docs = segmenter.reconstruct_documents(translated_segments, reconstruction_maps, docs)
        logger.info(f"Document reconstruction completed: {len(translated_docs)} documents")
        
        # Step 5: Generate outputs
        output_dir = f"/Users/kayvangharbi/PycharmProjects/BookTranslator/outputs/{provider_name.lower()}"
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Output directory created: {output_dir}")
        
        outputs_generated = await generate_all_outputs(
            provider_name, output_dir, original_book, translated_docs, translated_segments, epub_path
        )
        
        # Also generate original input files for comparison
        original_outputs = await generate_original_outputs(output_dir, original_book, docs, segments, epub_path)
        logger.info(f"Output generation completed for {provider_name}: {outputs_generated}")
        
        # Perform targeted PDF image testing
        pdf_test_results = await test_pdf_image_quality(output_dir, provider_name)
        
        total_time = time.time() - start_time
        
        # Step 6: Quality analysis
        quality_metrics = analyze_translation_quality(segments[:10], translated_segments[:10], provider_name)
        
        # Step 7: Qualitative analysis
        qualitative_analysis = perform_qualitative_analysis(segments, translated_segments, provider_name)
        
        return {
            "provider": provider_name,
            "success": True,
            "documents": len(docs),
            "segments": len(segments),
            "tokens_used": tokens_used,
            "provider_cost_decimal": float(provider_cost_decimal),
            "provider_cost_usd": float(provider_cost_decimal),
            "provider_cost_micro_usd": provider_cost_micro_usd,
            "provider_cost_display": provider_cost_display,
            "user_price_cents": user_price_cents,
            "user_price_usd": user_price_usd,
            "profit_decimal": profit_decimal,
            "profit_usd": profit_decimal,
            "profit_micro_usd": profit_micro_usd,
            "profit_margin_pct": profit_margin_pct,
            "translation_time": translation_time,
            "total_time": total_time,
            "outputs": outputs_generated,
            "original_outputs": original_outputs,
            "pdf_image_test": pdf_test_results,
            "quality": quality_metrics,
            "qualitative": qualitative_analysis,
            "provider_used": provider_used
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

async def generate_all_outputs(provider_name: str, output_dir: str, original_book, translated_docs: list, translated_segments: list, epub_path: str = None) -> Dict[str, bool]:
    """Generate EPUB, PDF, and TXT outputs."""
    
    print(f"💾 Generating outputs for {provider_name}...")
    logger.info(f"Starting output generation for {provider_name} in {output_dir}")
    outputs = {}
    
    # Generate EPUB
    try:
        epub_path = os.path.join(output_dir, f"translated_{provider_name.lower()}.epub")
        processor = EPUBProcessor()
        success = processor.write_epub(original_book, translated_docs, epub_path)
        outputs["epub"] = success
        if success:
            file_size = os.path.getsize(epub_path) / 1024 / 1024  # MB
            print(f"   ✅ EPUB: {epub_path} ({file_size:.1f} MB)")
        else:
            print(f"   ❌ EPUB generation failed")
    except Exception as e:
        print(f"   ❌ EPUB error: {e}")
        outputs["epub"] = False
    
    # Generate PDF using best available method
    try:
        epub_output_path = os.path.join(output_dir, f"translated_{provider_name.lower()}.epub")
        if outputs.get("epub", False) and os.path.exists(epub_output_path):
            # Use improved PDF generation with multiple methods
            # Add root directory to path for the enhanced PDF converter
            import sys
            from pathlib import Path
            root_dir = Path(__file__).parent.parent
            sys.path.insert(0, str(root_dir))
            from epub_to_pdf_with_images import convert_epub_to_pdf
            
            try:
                pdf_path = convert_epub_to_pdf(epub_output_path, output_dir)
                outputs["pdf"] = True
                file_size = os.path.getsize(pdf_path) / 1024 / 1024  # MB
                print(f"   ✅ PDF (enhanced): {pdf_path} ({file_size:.1f} MB)")
            except Exception as pdf_error:
                print(f"   ⚠️  Enhanced PDF failed, trying fallback: {pdf_error}")
                # Fallback to WeasyPrint if enhanced method fails
                if WEASYPRINT_AVAILABLE:
                    pdf_path = os.path.join(output_dir, f"translated_{provider_name.lower()}_fallback.pdf")
                    combined_html = combine_docs_for_pdf(translated_docs, original_book, output_dir, epub_path)
                    HTML(string=combined_html).write_pdf(pdf_path)
                    outputs["pdf"] = True
                    file_size = os.path.getsize(pdf_path) / 1024 / 1024  # MB
                    print(f"   ✅ PDF (fallback): {pdf_path} ({file_size:.1f} MB)")
                else:
                    outputs["pdf"] = False
                    print(f"   ❌ PDF generation failed - no methods available")
        else:
            print(f"   ⚠️  PDF skipped - EPUB not generated")
            outputs["pdf"] = False
    except Exception as e:
        print(f"   ❌ PDF error: {e}")
        outputs["pdf"] = False
    
    # Generate TXT
    try:
        txt_path = os.path.join(output_dir, f"translated_{provider_name.lower()}.txt")
        
        # Create formatted text with document separators
        formatted_content = []
        for i, doc in enumerate(translated_docs):
            if doc.get('title') and doc['title'] != 'Untitled':
                formatted_content.append(f"=== {doc['title']} ===\n")
            else:
                formatted_content.append(f"=== Document {i+1} ===\n")
            
            # Extract text from HTML content
            try:
                soup = BeautifulSoup(doc['content'], 'xml')
                text = soup.get_text(separator='\n', strip=True)
                formatted_content.append(text)
            except:
                formatted_content.append(doc['content'])
            
            formatted_content.append("\n\n")
        
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write('\n'.join(formatted_content))
        
        outputs["txt"] = True
        file_size = os.path.getsize(txt_path) / 1024  # KB
        print(f"   ✅ TXT: {txt_path} ({file_size:.1f} KB)")
    except Exception as e:
        print(f"   ❌ TXT error: {e}")
        outputs["txt"] = False
    
    return outputs

async def generate_original_outputs(output_dir: str, original_book, original_docs: list, original_segments: list, epub_path: str) -> Dict[str, bool]:
    """Generate original input files for comparison."""
    
    print(f"📄 Generating original input files for comparison...")
    outputs = {}
    
    # Copy original EPUB
    try:
        import shutil
        original_epub_path = os.path.join(output_dir, "original.epub")
        shutil.copy2(epub_path, original_epub_path)
        outputs["original_epub"] = True
        file_size = os.path.getsize(original_epub_path) / 1024 / 1024  # MB
        print(f"   ✅ Original EPUB: {original_epub_path} ({file_size:.1f} MB)")
    except Exception as e:
        print(f"   ❌ Original EPUB copy error: {e}")
        outputs["original_epub"] = False
    
    # Generate original PDF using enhanced method
    try:
        original_epub_path = os.path.join(output_dir, "original.epub")
        if outputs.get("original_epub", False) and os.path.exists(original_epub_path):
            # Use improved PDF generation
            # Add root directory to path for the enhanced PDF converter
            import sys
            from pathlib import Path
            root_dir = Path(__file__).parent.parent
            sys.path.insert(0, str(root_dir))
            from epub_to_pdf_with_images import convert_epub_to_pdf
            
            try:
                original_pdf_path = convert_epub_to_pdf(original_epub_path, output_dir)
                outputs["original_pdf"] = True
                file_size = os.path.getsize(original_pdf_path) / 1024 / 1024  # MB
                print(f"   ✅ Original PDF (enhanced): {original_pdf_path} ({file_size:.1f} MB)")
            except Exception as pdf_error:
                print(f"   ⚠️  Enhanced original PDF failed, trying fallback: {pdf_error}")
                # Fallback to WeasyPrint
                if WEASYPRINT_AVAILABLE:
                    original_pdf_path = os.path.join(output_dir, "original_fallback.pdf")
                    combined_html = combine_docs_for_pdf(original_docs, original_book, output_dir, epub_path)
                    HTML(string=combined_html).write_pdf(original_pdf_path)
                    outputs["original_pdf"] = True
                    file_size = os.path.getsize(original_pdf_path) / 1024 / 1024  # MB
                    print(f"   ✅ Original PDF (fallback): {original_pdf_path} ({file_size:.1f} MB)")
                else:
                    outputs["original_pdf"] = False
                    print(f"   ❌ Original PDF generation failed - no methods available")
        else:
            print(f"   ⚠️  Original PDF skipped - original EPUB not available")
            outputs["original_pdf"] = False
    except Exception as e:
        print(f"   ❌ Original PDF error: {e}")
        outputs["original_pdf"] = False
    
    # Generate original TXT
    try:
        original_txt_path = os.path.join(output_dir, "original.txt")
        
        # Create formatted text with document separators
        formatted_content = []
        for i, doc in enumerate(original_docs):
            if doc.get('title') and doc['title'] != 'Untitled':
                formatted_content.append(f"=== {doc['title']} ===\n")
            else:
                formatted_content.append(f"=== Document {i+1} ===\n")
            
            # Extract text from HTML content
            try:
                soup = BeautifulSoup(doc['content'], 'xml')
                text = soup.get_text(separator='\n', strip=True)
                formatted_content.append(text)
            except:
                formatted_content.append(doc['content'])
            
            formatted_content.append("\n\n")
        
        with open(original_txt_path, "w", encoding="utf-8") as f:
            f.write('\n'.join(formatted_content))
        
        outputs["original_txt"] = True
        file_size = os.path.getsize(original_txt_path) / 1024  # KB
        print(f"   ✅ Original TXT: {original_txt_path} ({file_size:.1f} KB)")
    except Exception as e:
        print(f"   ❌ Original TXT error: {e}")
        outputs["original_txt"] = False
    
    return outputs

def combine_docs_for_pdf(translated_docs: list, original_book=None, output_dir=None, epub_path=None) -> str:
    """Combine translated documents into single HTML for PDF generation."""
    
    # Extract images from EPUB if available
    extracted_images = {}
    if original_book and output_dir:
        try:
            import zipfile
            import base64
            
            # Create images subdirectory
            images_dir = os.path.join(output_dir, "images")
            os.makedirs(images_dir, exist_ok=True)
            
            # Extract images from the original EPUB (updated for new structure)
            if epub_path and os.path.exists(epub_path):
                with zipfile.ZipFile(epub_path, 'r') as epub:
                    for file_info in epub.infolist():
                        if (file_info.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.svg')) 
                            and not file_info.is_dir() and 'OEBPS/' in file_info.filename):
                            # Extract image
                            image_data = epub.read(file_info.filename)
                            
                            # Save to output directory
                            image_name = os.path.basename(file_info.filename)
                            image_path = os.path.join(images_dir, image_name)
                            with open(image_path, 'wb') as f:
                                f.write(image_data)
                            
                            # Store mapping for URL replacement
                            relative_path = f"images/{image_name}"
                            extracted_images[relative_path] = image_path
                            
        except Exception as e:
            print(f"   ⚠️  Could not extract images: {e}")
    
    html_parts = [
        '<!DOCTYPE html>',
        '<html>',
        '<head>',
        '<meta charset="utf-8">',
        '<title>Translated Book</title>',
        '<style>',
        'body { font-family: "Times New Roman", serif; line-height: 1.6; margin: 2cm; color: #333; }',
        'h1, h2, h3, h4, h5, h6 { color: #222; margin-top: 2em; margin-bottom: 0.5em; }',
        '.chapter { page-break-before: always; margin-top: 2em; }',
        '.document-title { font-size: 1.2em; font-weight: bold; margin: 2em 0 1em 0; color: #555; }',
        'p { margin-bottom: 1em; text-align: justify; }',
        'img { max-width: 100%; height: auto; margin: 2em auto; display: block; border: 1px solid #ddd; border-radius: 4px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }',
        '.cover-image { max-width: 60%; margin: 3em auto; page-break-after: always; }',
        '@page { margin: 2cm; }',
        '</style>',
        '</head>',
        '<body>'
    ]
    
    for i, doc in enumerate(translated_docs):
        if i > 0:
            html_parts.append('<div class="chapter">')
        
        # Add document title
        title = doc.get('title', f'Document {i+1}')
        if title and title != 'Untitled':
            html_parts.append(f'<div class="document-title">{title}</div>')
        
        # Extract and clean body content
        try:
            soup = BeautifulSoup(doc['content'], 'xml')
            body = soup.find('body')
            content = str(body) if body else doc['content']
            
            # Fix image paths
            for relative_path, absolute_path in extracted_images.items():
                content = content.replace(f'src="{relative_path}"', f'src="file://{absolute_path}"')
                content = content.replace(f"src='{relative_path}'", f'src="file://{absolute_path}"')
                # Fix SVG xlink:href paths
                content = content.replace(f'xlink:href="{relative_path}"', f'xlink:href="file://{absolute_path}"')
                content = content.replace(f"xlink:href='{relative_path}'", f'xlink:href="file://{absolute_path}"')
            
            # Remove script and style tags
            soup = BeautifulSoup(content, 'xml')
            for tag in soup.find_all(['script', 'style']):
                tag.decompose()
            
            html_parts.append(str(soup))
        except Exception as e:
            print(f"   ⚠️  Error processing document {i}: {e}")
            html_parts.append(doc['content'])
        
        if i > 0:
            html_parts.append('</div>')
    
    html_parts.extend(['</body>', '</html>'])
    
    return '\n'.join(html_parts)

async def test_pdf_image_quality(output_dir: str, provider_name: str) -> Dict[str, Any]:
    """Test PDF image quality and formatting."""
    
    print(f"🔍 Testing PDF image quality for {provider_name}...")
    test_results = {}
    
    try:
        # Check if images directory was created
        images_dir = os.path.join(output_dir, "images")
        if os.path.exists(images_dir):
            image_files = [f for f in os.listdir(images_dir) if f.lower().endswith(('.jpg', '.png', '.gif', '.svg'))]
            test_results["images_extracted"] = len(image_files)
            print(f"   ✅ Images extracted: {len(image_files)} files")
            
            for img_file in image_files:
                img_path = os.path.join(images_dir, img_file)
                img_size = os.path.getsize(img_path)
                print(f"     📷 {img_file}: {img_size:,} bytes")
        else:
            test_results["images_extracted"] = 0
            print(f"   ⚠️  No images directory found")
        
        # Check PDF file size and compare to original
        pdf_files = {
            "translated": os.path.join(output_dir, f"translated_{provider_name.lower()}.pdf"),
            "original": os.path.join(output_dir, "original.pdf")
        }
        
        for pdf_type, pdf_path in pdf_files.items():
            if os.path.exists(pdf_path):
                pdf_size = os.path.getsize(pdf_path)
                test_results[f"{pdf_type}_pdf_size"] = pdf_size
                print(f"   📄 {pdf_type.title()} PDF: {pdf_size:,} bytes ({pdf_size/1024:.1f} KB)")
            else:
                test_results[f"{pdf_type}_pdf_size"] = 0
                print(f"   ❌ {pdf_type.title()} PDF not found")
        
        # Compare PDF sizes (images should make them similar)
        if test_results.get("translated_pdf_size", 0) > 0 and test_results.get("original_pdf_size", 0) > 0:
            size_ratio = test_results["translated_pdf_size"] / test_results["original_pdf_size"]
            test_results["size_ratio"] = size_ratio
            if 0.8 <= size_ratio <= 1.2:
                print(f"   ✅ Size ratio: {size_ratio:.2f} (similar sizes - images likely preserved)")
            else:
                print(f"   ⚠️  Size ratio: {size_ratio:.2f} (significant difference)")
        
        # Test image accessibility
        try:
            import zipfile
            # Check if PDF contains image references by examining size
            translated_pdf_path = pdf_files["translated"]
            if os.path.exists(translated_pdf_path) and test_results["translated_pdf_size"] > 50000:  # >50KB suggests images
                test_results["likely_contains_images"] = True
                print(f"   ✅ PDF size suggests images are embedded")
            else:
                test_results["likely_contains_images"] = False
                print(f"   ⚠️  PDF size suggests images may not be embedded")
                
        except Exception as e:
            print(f"   ⚠️  Could not analyze PDF content: {e}")
        
    except Exception as e:
        print(f"   ❌ PDF testing error: {e}")
        test_results["error"] = str(e)
    
    return test_results

def analyze_translation_quality(original_segments: list, translated_segments: list, provider_name: str) -> Dict[str, Any]:
    """Analyze translation quality metrics."""
    
    if not original_segments or not translated_segments:
        return {"error": "No segments to analyze"}
    
    # Calculate basic metrics
    avg_original_length = sum(len(s) for s in original_segments) / len(original_segments)
    avg_translated_length = sum(len(s) for s in translated_segments) / len(translated_segments)
    length_ratio = avg_translated_length / avg_original_length if avg_original_length > 0 else 0
    
    # Count segments with substantial content
    substantial_segments = sum(1 for s in translated_segments if len(s.strip()) > 10)
    
    return {
        "segments_analyzed": len(original_segments),
        "avg_original_length": round(avg_original_length, 1),
        "avg_translated_length": round(avg_translated_length, 1),
        "length_ratio": round(length_ratio, 2),
        "substantial_segments": substantial_segments,
        "sample_translations": [
            {"original": orig[:100] + "..." if len(orig) > 100 else orig,
             "translated": trans[:100] + "..." if len(trans) > 100 else trans}
            for orig, trans in zip(original_segments[:3], translated_segments[:3])
            if len(orig.strip()) > 5
        ]
    }

def perform_qualitative_analysis(original_segments: list, translated_segments: list, provider_name: str) -> Dict[str, Any]:
    """Perform qualitative analysis of translation quality."""
    
    if not original_segments or not translated_segments:
        return {"error": "No segments to analyze"}
    
    # Select diverse samples for analysis
    samples = []
    step = max(1, len(original_segments) // 10)  # Sample ~10 segments
    
    for i in range(0, min(len(original_segments), len(translated_segments)), step):
        orig = original_segments[i].strip()
        trans = translated_segments[i].strip()
        
        if len(orig) > 20 and len(trans) > 5:  # Substantial content
            # Analyze characteristics
            analysis = {
                "index": i,
                "original": orig,
                "translated": trans,
                "length_change": len(trans) - len(orig),
                "characteristics": []
            }
            
            # Check for common quality indicators
            if any(word in trans.lower() for word in ['sin embargo', 'no obstante', 'además', 'por tanto']):
                analysis["characteristics"].append("uses_complex_connectors")
            
            if '"' in orig and ('«' in trans or '»' in trans or '"' in trans):
                analysis["characteristics"].append("handles_quotes")
            
            if orig.count(',') > 2 and trans.count(',') >= orig.count(',') - 1:
                analysis["characteristics"].append("preserves_punctuation")
            
            if any(char.isupper() for char in orig) and any(char.isupper() for char in trans):
                analysis["characteristics"].append("maintains_capitalization")
            
            # Check for potential issues
            if len(trans) < len(orig) * 0.3:
                analysis["characteristics"].append("possibly_truncated")
            
            if orig.lower() == trans.lower():
                analysis["characteristics"].append("untranslated")
            
            if any(word in trans for word in orig.split() if len(word) > 3):
                analysis["characteristics"].append("contains_english_words")
            
            samples.append(analysis)
    
    # Calculate overall quality indicators
    total_samples = len(samples)
    quality_scores = {
        "complex_connectors": sum(1 for s in samples if "uses_complex_connectors" in s["characteristics"]),
        "quote_handling": sum(1 for s in samples if "handles_quotes" in s["characteristics"]),
        "punctuation_preserved": sum(1 for s in samples if "preserves_punctuation" in s["characteristics"]),
        "capitalization_maintained": sum(1 for s in samples if "maintains_capitalization" in s["characteristics"]),
        "potential_truncations": sum(1 for s in samples if "possibly_truncated" in s["characteristics"]),
        "untranslated_segments": sum(1 for s in samples if "untranslated" in s["characteristics"]),
        "english_contamination": sum(1 for s in samples if "contains_english_words" in s["characteristics"])
    }
    
    return {
        "provider": provider_name,
        "samples_analyzed": total_samples,
        "quality_indicators": {k: f"{v}/{total_samples}" for k, v in quality_scores.items()},
        "quality_percentages": {k: round(v/total_samples*100, 1) if total_samples > 0 else 0 
                               for k, v in quality_scores.items()},
        "sample_translations": samples[:5],  # Show first 5 for detailed review
        "overall_assessment": assess_overall_quality(quality_scores, total_samples)
    }

def assess_overall_quality(quality_scores: dict, total_samples: int) -> str:
    """Provide an overall quality assessment."""
    if total_samples == 0:
        return "No samples to assess"
    
    # Calculate quality score (0-100)
    positive_indicators = quality_scores["complex_connectors"] + quality_scores["quote_handling"] + quality_scores["punctuation_preserved"] + quality_scores["capitalization_maintained"]
    negative_indicators = quality_scores["potential_truncations"] + quality_scores["untranslated_segments"] + quality_scores["english_contamination"]
    
    quality_score = max(0, (positive_indicators - negative_indicators * 2) / total_samples * 100)
    
    if quality_score >= 80:
        return f"Excellent ({quality_score:.1f}/100) - Professional literary quality"
    elif quality_score >= 60:
        return f"Good ({quality_score:.1f}/100) - Solid translation with minor issues"
    elif quality_score >= 40:
        return f"Fair ({quality_score:.1f}/100) - Acceptable but needs improvement"
    else:
        return f"Poor ({quality_score:.1f}/100) - Significant translation issues"

def print_comparison_summary(gemini_results: Dict[str, Any], llama_results: Dict[str, Any]):
    """Print detailed comparison between providers."""
    
    print("\n" + "=" * 80)
    print("📊 PROVIDER COMPARISON SUMMARY")
    print("=" * 80)
    
    # Success comparison
    print(f"Success Rate:")
    print(f"  Gemini:  {'✅ Success' if gemini_results.get('success') else '❌ Failed'}")
    print(f"  Llama:   {'✅ Success' if llama_results.get('success') else '❌ Failed'}")
    
    if gemini_results.get('success') and llama_results.get('success'):
        # Enhanced cost comparison
        print(f"\n💰 Cost Analysis & Business Metrics:")
        print(f"  {'Metric':<25} {'Gemini':<15} {'Llama':<15} {'Difference'}")
        print(f"  {'-'*25} {'-'*15} {'-'*15} {'-'*15}")
        
        # Tokens
        g_tokens = gemini_results['tokens_used']
        l_tokens = llama_results['tokens_used']
        print(f"  {'Tokens Used':<25} {g_tokens:,} {' ' * (15 - len(f'{g_tokens:,}'))} {l_tokens:,} {' ' * (15 - len(f'{l_tokens:,}'))} {abs(g_tokens-l_tokens):,}")
        
        # Provider costs (what we pay) - enhanced precision
        g_provider_cost = gemini_results['provider_cost_usd']
        l_provider_cost = llama_results['provider_cost_usd']
        g_micro_usd = gemini_results.get('provider_cost_micro_usd', 0)
        l_micro_usd = llama_results.get('provider_cost_micro_usd', 0)
        print(f"  {'Provider Cost':<25} ${g_provider_cost:.6f:<14} ${l_provider_cost:.6f:<14} ${abs(g_provider_cost-l_provider_cost):.6f}")
        print(f"  {'  (micro-USD)':<25} {g_micro_usd:,:<15} {l_micro_usd:,:<15} {abs(g_micro_usd-l_micro_usd):,}")
        
        # User price (what they pay)
        g_user_price = gemini_results['user_price_usd']
        l_user_price = llama_results['user_price_usd']
        print(f"  {'User Pays':<25} ${g_user_price:.2f:<14} ${l_user_price:.2f:<14} ${abs(g_user_price-l_user_price):.2f}")
        
        # Profit - enhanced precision
        g_profit = gemini_results['profit_usd']
        l_profit = llama_results['profit_usd']
        g_profit_micro = gemini_results.get('profit_micro_usd', 0)
        l_profit_micro = llama_results.get('profit_micro_usd', 0)
        print(f"  {'Profit':<25} ${g_profit:.6f:<14} ${l_profit:.6f:<14} ${abs(g_profit-l_profit):.6f}")
        print(f"  {'  (micro-USD)':<25} {g_profit_micro:,:<15} {l_profit_micro:,:<15} {abs(g_profit_micro-l_profit_micro):,}")
        
        # Profit margin
        g_margin = gemini_results['profit_margin_pct']
        l_margin = llama_results['profit_margin_pct']
        print(f"  {'Profit Margin':<25} {g_margin:.1f}%{'':<11} {l_margin:.1f}%{'':<11} {abs(g_margin-l_margin):.1f}%")
        
        # Enhanced business insights with sub-cent precision
        print(f"\n💡 Enhanced Business Insights:")
        g_markup = g_user_price / g_provider_cost if g_provider_cost > 0 else 0
        l_markup = l_user_price / l_provider_cost if l_provider_cost > 0 else 0
        
        if g_provider_cost < l_provider_cost:
            savings = l_provider_cost - g_provider_cost
            print(f"  • Gemini saves ${savings:.6f} in provider costs ({(savings/l_provider_cost*100):.2f}% cheaper)")
        else:
            savings = g_provider_cost - l_provider_cost
            print(f"  • Llama saves ${savings:.6f} in provider costs ({(savings/g_provider_cost*100):.2f}% cheaper)")
        
        print(f"  • Gemini markup: {g_markup:.2f}x | Llama markup: {l_markup:.2f}x")
        print(f"  • Sub-cent tracking enables precise cost optimization")
        
        if g_profit > l_profit:
            profit_diff = g_profit - l_profit
            print(f"  • Gemini generates ${profit_diff:.4f} more profit per translation")
        else:
            profit_diff = l_profit - g_profit
            print(f"  • Llama generates ${profit_diff:.4f} more profit per translation")
        
        # Performance comparison
        print(f"\n⚡ Performance Comparison:")
        print(f"  Gemini:  {gemini_results['translation_time']:.1f}s translation, {gemini_results['total_time']:.1f}s total")
        print(f"  Llama:   {llama_results['translation_time']:.1f}s translation, {llama_results['total_time']:.1f}s total")
        
        # Token efficiency
        g_rate = gemini_results['tokens_used'] / gemini_results['translation_time']
        l_rate = llama_results['tokens_used'] / llama_results['translation_time']
        print(f"  Gemini:  {g_rate:.0f} tokens/sec")
        print(f"  Llama:   {l_rate:.0f} tokens/sec")
        
        # Output comparison
        print(f"\n📄 Output Generation:")
        g_outputs = gemini_results.get('outputs', {})
        l_outputs = llama_results.get('outputs', {})
        
        for format_type in ['epub', 'pdf', 'txt']:
            g_status = "✅" if g_outputs.get(format_type) else "❌"
            l_status = "✅" if l_outputs.get(format_type) else "❌"
            print(f"  {format_type.upper()}: Gemini {g_status} | Llama {l_status}")
        
        # PDF Image Testing Results
        print(f"\n🖼️ PDF Image Quality:")
        g_pdf_test = gemini_results.get('pdf_image_test', {})
        l_pdf_test = llama_results.get('pdf_image_test', {})
        
        if g_pdf_test or l_pdf_test:
            print(f"  {'Metric':<20} {'Gemini':<15} {'Llama':<15}")
            print(f"  {'-'*20} {'-'*15} {'-'*15}")
            print(f"  {'Images Extracted':<20} {g_pdf_test.get('images_extracted', 0):<15} {l_pdf_test.get('images_extracted', 0):<15}")
            
            g_size = g_pdf_test.get('translated_pdf_size', 0)
            l_size = l_pdf_test.get('translated_pdf_size', 0)
            print(f"  {'PDF Size (KB)':<20} {g_size//1024 if g_size else 0:<15} {l_size//1024 if l_size else 0:<15}")
            
            g_ratio = g_pdf_test.get('size_ratio', 0)
            l_ratio = l_pdf_test.get('size_ratio', 0)
            print(f"  {'Size Ratio':<20} {g_ratio:.2f}{'':11} {l_ratio:.2f}")
            
            g_images = "✅" if g_pdf_test.get('likely_contains_images') else "❌"
            l_images = "✅" if l_pdf_test.get('likely_contains_images') else "❌"
            print(f"  {'Images Embedded':<20} {g_images:<15} {l_images:<15}")
        
        # Qualitative comparison
        print(f"\n🎯 Translation Quality Analysis:")
        g_qual = gemini_results.get('qualitative', {})
        l_qual = llama_results.get('qualitative', {})
        
        if g_qual and l_qual:
            print(f"  {'Quality Metric':<25} {'Gemini':<15} {'Llama':<15}")
            print(f"  {'-'*25} {'-'*15} {'-'*15}")
            
            g_pct = g_qual.get('quality_percentages', {})
            l_pct = l_qual.get('quality_percentages', {})
            
            metrics = [
                ('Complex Connectors', 'complex_connectors'),
                ('Quote Handling', 'quote_handling'),
                ('Punctuation', 'punctuation_preserved'),
                ('Capitalization', 'capitalization_maintained'),
                ('Truncations', 'potential_truncations'),
                ('Untranslated', 'untranslated_segments'),
                ('English Words', 'english_contamination')
            ]
            
            for label, key in metrics:
                g_val = g_pct.get(key, 0)
                l_val = l_pct.get(key, 0)
                print(f"  {label:<25} {g_val:.1f}%{'':<11} {l_val:.1f}%")
            
            print(f"\n🏆 Overall Assessment:")
            print(f"  Gemini: {g_qual.get('overall_assessment', 'N/A')}")
            print(f"  Llama:  {l_qual.get('overall_assessment', 'N/A')}")
            
            # Sample comparison
            print(f"\n📝 Side-by-Side Sample:")
            g_samples = g_qual.get('sample_translations', [])
            l_samples = l_qual.get('sample_translations', [])
            
            if g_samples and l_samples:
                sample_g = g_samples[0]
                sample_l = l_samples[0]
                print(f"  Original: {sample_g['original'][:150]}...")
                print(f"  Gemini:   {sample_g['translated'][:150]}...")
                print(f"  Llama:    {sample_l['translated'][:150]}...")
    
    print("\n" + "=" * 80)

def save_test_results(gemini_results: Dict[str, Any], llama_results: Dict[str, Any], epub_path: str):
    """Save detailed test results to JSON file."""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"/Users/kayvangharbi/PycharmProjects/BookTranslator/outputs/comparison_results_{timestamp}.json"
    
    results = {
        "timestamp": timestamp,
        "test_configuration": {
            "epub_file": epub_path,
            "target_language": "Spanish (es)",
            "gemini_model": settings.gemini_model,
            "llama_model": settings.groq_model
        },
        "gemini_results": gemini_results,
        "llama_results": llama_results,
        "comparison": {
            "cost_difference_usd": abs(gemini_results.get('provider_cost_usd', 0) - llama_results.get('provider_cost_usd', 0)),
            "profit_difference_usd": abs(gemini_results.get('profit_usd', 0) - llama_results.get('profit_usd', 0)),
            "speed_difference_sec": abs(gemini_results.get('translation_time', 0) - llama_results.get('translation_time', 0))
        }
    }
    
    try:
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n📄 Results saved to: {results_file}")
        logger.info(f"Test results saved to {results_file}")
    except Exception as e:
        logger.error(f"Failed to save results: {e}")

async def main():
    """Run comprehensive dual-provider test."""
    
    print("🚀 DUAL PROVIDER TRANSLATION TEST")
    print("Testing both Gemini and Llama with cost analysis")
    print("=" * 80)
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        epub_path = sys.argv[1]
    else:
        epub_path = "/Users/kayvangharbi/PycharmProjects/BookTranslator/sample_books/pg236_first20pages.epub"
    
    if not os.path.exists(epub_path):
        print(f"❌ EPUB file not found: {epub_path}")
        return
    
    # Initialize providers
    gemini_provider = GeminiFlashProvider(
        api_key=settings.gemini_api_key,
        model=settings.gemini_model
    )
    
    groq_provider = GroqLlamaProvider(
        api_key=settings.groq_api_key,
        model=settings.groq_model
    )
    
    # Test both providers
    print(f"📖 Testing with: {epub_path}")
    print(f"🎯 Target language: Spanish (es)")
    print(f"🔧 Gemini model: {settings.gemini_model}")
    print(f"🔧 Llama model: {settings.groq_model}")
    
    # Run tests
    gemini_results = await test_provider("Gemini", gemini_provider, epub_path)
    llama_results = await test_provider("Llama", groq_provider, epub_path)
    
    # Print comparison
    print_comparison_summary(gemini_results, llama_results)
    
    # Save detailed results
    save_test_results(gemini_results, llama_results, epub_path)
    
    # Print file locations
    print(f"\n📁 Output Files:")
    print(f"  Gemini outputs: /Users/kayvangharbi/PycharmProjects/BookTranslator/outputs/gemini/")
    print(f"  Llama outputs:  /Users/kayvangharbi/PycharmProjects/BookTranslator/outputs/llama/")
    print(f"  Test logs:      /Users/kayvangharbi/PycharmProjects/BookTranslator/logs/")
    
    logger.info("Dual provider test completed successfully")

if __name__ == "__main__":
    asyncio.run(main())