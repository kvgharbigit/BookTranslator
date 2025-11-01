#!/usr/bin/env python3
"""
Generate original formats (PDF, TXT) from the source EPUB for comparison
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "apps" / "api"))

from app.pipeline.epub_io import EPUBProcessor
from enhanced_txt_generator import EnhancedTXTGenerator
from epub_to_pdf_with_images import convert_epub_to_pdf

def generate_original_formats():
    """Generate PDF and TXT from original EPUB"""
    
    print("📚 Generating Original Format Outputs")
    print("=" * 50)
    
    original_epub = "test_outputs/original/original.epub"
    
    if not Path(original_epub).exists():
        print(f"❌ Original EPUB not found: {original_epub}")
        return
    
    # Generate PDF
    print("🔄 Converting original EPUB to PDF...")
    try:
        pdf_path = convert_epub_to_pdf(original_epub, "test_outputs/original")
        print(f"✅ Original PDF: {pdf_path}")
    except Exception as e:
        print(f"❌ PDF generation failed: {e}")
    
    # Generate TXT
    print("🔄 Converting original EPUB to TXT...")
    try:
        processor = EPUBProcessor()
        book, docs = processor.read_epub(original_epub)
        
        # Generate text output using enhanced generator
        txt_generator = EnhancedTXTGenerator()
        txt_content = txt_generator.generate_enhanced_txt(docs, "Original English Edition")
        
        txt_path = "test_outputs/original/original.txt"
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(txt_content)
        
        txt_size = Path(txt_path).stat().st_size / 1024
        print(f"✅ Original TXT: {txt_path} ({txt_size:.1f} KB)")
        
    except Exception as e:
        print(f"❌ TXT generation failed: {e}")
    
    print("\n📁 Original directory contents:")
    original_dir = Path("test_outputs/original")
    for file in original_dir.iterdir():
        if file.is_file():
            size = file.stat().st_size / (1024 * 1024) if file.suffix == '.pdf' else file.stat().st_size / 1024
            unit = 'MB' if file.suffix == '.pdf' else 'KB'
            print(f"   {file.name}: {size:.1f} {unit}")

if __name__ == "__main__":
    generate_original_formats()