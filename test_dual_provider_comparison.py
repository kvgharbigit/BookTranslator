#!/usr/bin/env python3
"""
Comprehensive test comparing Gemini and Llama providers
Tests translation quality, cost, and generates all output formats (EPUB, PDF, TXT)
"""
import sys
import os
import asyncio
import time
from pathlib import Path
from typing import Dict, Any

# Add the API to path
sys.path.insert(0, str(Path(__file__).parent / "apps" / "api"))

from app.config import settings
from app.pipeline.epub_io import EPUBProcessor
from app.pipeline.html_segment import HTMLSegmenter
from app.pipeline.translate import TranslationOrchestrator
from app.providers.gemini import GeminiFlashProvider
from app.providers.groq import GroqProvider
from app.pricing import calculate_provider_cost_cents, calculate_price_cents

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
        user_price_cents = calculate_price_cents(tokens_used)
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
        output_dir = f"/Users/kayvangharbi/PycharmProjects/BookTranslator/test_outputs_{provider_name.lower()}"
        os.makedirs(output_dir, exist_ok=True)
        
        outputs_generated = await generate_all_outputs(
            provider_name, output_dir, original_book, translated_docs, translated_segments
        )
        
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

async def generate_all_outputs(provider_name: str, output_dir: str, original_book, translated_docs: list, translated_segments: list) -> Dict[str, bool]:
    """Generate EPUB, PDF, and TXT outputs."""
    
    print(f"💾 Generating outputs for {provider_name}...")
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
    
    # Generate PDF
    try:
        if WEASYPRINT_AVAILABLE:
            pdf_path = os.path.join(output_dir, f"translated_{provider_name.lower()}.pdf")
            combined_html = combine_docs_for_pdf(translated_docs)
            HTML(string=combined_html).write_pdf(pdf_path)
            outputs["pdf"] = True
            file_size = os.path.getsize(pdf_path) / 1024 / 1024  # MB
            print(f"   ✅ PDF: {pdf_path} ({file_size:.1f} MB)")
        else:
            print(f"   ⚠️  PDF skipped - WeasyPrint not available")
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

def combine_docs_for_pdf(translated_docs: list) -> str:
    """Combine translated documents into single HTML for PDF generation."""
    
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
        'img { max-width: 100%; height: auto; margin: 1em 0; }',
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
            if body:
                # Remove script and style tags
                for tag in body.find_all(['script', 'style']):
                    tag.decompose()
                html_parts.append(str(body))
            else:
                html_parts.append(doc['content'])
        except:
            html_parts.append(doc['content'])
        
        if i > 0:
            html_parts.append('</div>')
    
    html_parts.extend(['</body>', '</html>'])
    
    return '\n'.join(html_parts)

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
        print(f"  {'Tokens Used':<25} {g_tokens:,:<15} {l_tokens:,:<15} {abs(g_tokens-l_tokens):,}")
        
        # Provider costs (what we pay)
        g_provider_cost = gemini_results['provider_cost_usd']
        l_provider_cost = llama_results['provider_cost_usd']
        print(f"  {'Provider Cost':<25} ${g_provider_cost:.4f:<14} ${l_provider_cost:.4f:<14} ${abs(g_provider_cost-l_provider_cost):.4f}")
        
        # User price (what they pay)
        g_user_price = gemini_results['user_price_usd']
        l_user_price = llama_results['user_price_usd']
        print(f"  {'User Pays':<25} ${g_user_price:.2f:<14} ${l_user_price:.2f:<14} ${abs(g_user_price-l_user_price):.2f}")
        
        # Profit
        g_profit = gemini_results['profit_usd']
        l_profit = llama_results['profit_usd']
        print(f"  {'Profit':<25} ${g_profit:.4f:<14} ${l_profit:.4f:<14} ${abs(g_profit-l_profit):.4f}")
        
        # Profit margin
        g_margin = gemini_results['profit_margin_pct']
        l_margin = llama_results['profit_margin_pct']
        print(f"  {'Profit Margin':<25} {g_margin:.1f}%{'':<11} {l_margin:.1f}%{'':<11} {abs(g_margin-l_margin):.1f}%")
        
        # Best option analysis
        print(f"\n💡 Business Insights:")
        if g_provider_cost < l_provider_cost:
            savings = l_provider_cost - g_provider_cost
            print(f"  • Gemini saves ${savings:.4f} in provider costs ({(savings/l_provider_cost*100):.1f}% cheaper)")
        else:
            savings = g_provider_cost - l_provider_cost
            print(f"  • Llama saves ${savings:.4f} in provider costs ({(savings/g_provider_cost*100):.1f}% cheaper)")
        
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

async def main():
    """Run comprehensive dual-provider test."""
    
    print("🚀 DUAL PROVIDER TRANSLATION TEST")
    print("Testing both Gemini and Llama with cost analysis")
    print("=" * 80)
    
    epub_path = "/Users/kayvangharbi/PycharmProjects/BookTranslator/sample_books/Sway.epub"
    
    if not os.path.exists(epub_path):
        print(f"❌ EPUB file not found: {epub_path}")
        return
    
    # Initialize providers
    gemini_provider = GeminiFlashProvider(
        api_key=settings.gemini_api_key,
        model=settings.gemini_model
    )
    
    groq_provider = GroqProvider(
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
    
    # Print file locations
    print(f"\n📁 Output Files:")
    print(f"  Gemini outputs: /Users/kayvangharbi/PycharmProjects/BookTranslator/test_outputs_gemini/")
    print(f"  Llama outputs:  /Users/kayvangharbi/PycharmProjects/BookTranslator/test_outputs_llama/")

if __name__ == "__main__":
    asyncio.run(main())