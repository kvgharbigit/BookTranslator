#!/usr/bin/env python3
"""
Production-ready EPUB to PDF converter with image preservation
Uses the best working approaches: Calibre (primary) and ReportLab (fallback)
"""
import os
import sys
import subprocess
import tempfile
import zipfile
import base64
from pathlib import Path
from datetime import datetime

# Set environment for WeasyPrint
os.environ['DYLD_LIBRARY_PATH'] = "/opt/homebrew/lib:" + os.environ.get('DYLD_LIBRARY_PATH', '')

from bs4 import BeautifulSoup

def epub_to_pdf_calibre(epub_path: str, output_path: str) -> bool:
    """Convert EPUB to PDF using Calibre - best quality and image preservation"""
    print("🔄 Converting with Calibre (best quality)...")
    
    try:
        # Check if calibre is available
        result = subprocess.run(['which', 'ebook-convert'], capture_output=True)
        if result.returncode != 0:
            print("❌ Calibre not available")
            return False
        
        # Convert with optimal settings for image preservation
        cmd = [
            'ebook-convert',
            epub_path,
            output_path,
            '--paper-size', 'a4',
            '--preserve-cover-aspect-ratio',
            '--embed-all-fonts', 
            '--margin-left', '0.5',
            '--margin-right', '0.5', 
            '--margin-top', '0.5',
            '--margin-bottom', '0.5',
            '--pdf-page-numbers',
            '--pdf-sans-family', 'Arial',
            '--pdf-serif-family', 'Times New Roman',
            '--enable-heuristics',  # Better image handling
            '--pdf-add-toc'         # Add table of contents
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0 and os.path.exists(output_path):
            file_size = os.path.getsize(output_path) / 1024
            print(f"✅ Calibre PDF created: {file_size:.1f} KB")
            return True
        else:
            print(f"❌ Calibre failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Calibre error: {e}")
        return False

def epub_to_pdf_reportlab(epub_path: str, output_path: str) -> bool:
    """Convert EPUB to PDF using ReportLab - good fallback with programmatic control"""
    print("🔄 Converting with ReportLab (fallback)...")
    
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        
        # Extract content
        temp_dir = tempfile.mkdtemp()
        extracted_images = {}
        
        with zipfile.ZipFile(epub_path, 'r') as epub:
            # Extract images
            for file_info in epub.infolist():
                if (file_info.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')) 
                    and not file_info.is_dir() and 'OEBPS/' in file_info.filename):
                    image_data = epub.read(file_info.filename)
                    image_name = os.path.basename(file_info.filename)
                    image_path = os.path.join(temp_dir, image_name)
                    
                    with open(image_path, 'wb') as f:
                        f.write(image_data)
                    extracted_images[image_name] = image_path
            
            # Create PDF
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=20,
                textColor=colors.darkblue
            )
            
            images_added = 0
            
            # Process HTML files
            for file_info in epub.infolist():
                if file_info.filename.endswith('.html') and 'OEBPS' in file_info.filename:
                    html_data = epub.read(file_info.filename).decode('utf-8')
                    soup = BeautifulSoup(html_data, 'html.parser')
                    
                    # Process elements
                    for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'img', 'div']):
                        try:
                            if element.name == 'img':
                                src = element.get('src', '')
                                image_name = os.path.basename(src)
                                if image_name in extracted_images:
                                    img = RLImage(extracted_images[image_name], 
                                                width=5*inch, height=4*inch)
                                    story.append(img)
                                    story.append(Spacer(1, 12))
                                    images_added += 1
                            else:
                                text = element.get_text().strip()
                                if text and len(text) > 5:
                                    if element.name.startswith('h'):
                                        style = styles['Heading2']
                                    else:
                                        style = styles['Normal']
                                    
                                    text = text.replace('\n', ' ').replace('\t', ' ')
                                    text = ' '.join(text.split())
                                    
                                    para = Paragraph(text, style)
                                    story.append(para)
                                    story.append(Spacer(1, 6))
                        except Exception as e:
                            continue
            
            doc.build(story)
            
        file_size = os.path.getsize(output_path) / 1024
        print(f"✅ ReportLab PDF created: {file_size:.1f} KB ({images_added} images)")
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
        return True
        
    except ImportError:
        print("❌ ReportLab not available")
        return False
    except Exception as e:
        print(f"❌ ReportLab error: {e}")
        return False

def epub_to_pdf_weasyprint(epub_path: str, output_path: str) -> bool:
    """Convert EPUB to PDF using WeasyPrint - excellent CSS support"""
    print("🔄 Converting with WeasyPrint (CSS support)...")
    
    try:
        from weasyprint import HTML
        
        # Extract and process content
        temp_dir = tempfile.mkdtemp()
        extracted_images = {}
        
        with zipfile.ZipFile(epub_path, 'r') as epub:
            # Extract images as base64
            for file_info in epub.infolist():
                if (file_info.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')) 
                    and not file_info.is_dir() and 'OEBPS/' in file_info.filename):
                    image_data = epub.read(file_info.filename)
                    image_name = os.path.basename(file_info.filename)
                    
                    # Determine MIME type
                    if image_name.lower().endswith(('.jpg', '.jpeg')):
                        mime_type = 'image/jpeg'
                    elif image_name.lower().endswith('.png'):
                        mime_type = 'image/png'
                    elif image_name.lower().endswith('.gif'):
                        mime_type = 'image/gif'
                    else:
                        mime_type = 'image/jpeg'
                    
                    b64_data = base64.b64encode(image_data).decode('utf-8')
                    data_uri = f"data:{mime_type};base64,{b64_data}"
                    extracted_images[image_name] = data_uri
            
            # Process HTML and embed images
            combined_html = ""
            images_embedded = 0
            
            for file_info in epub.infolist():
                if file_info.filename.endswith('.html') and 'OEBPS' in file_info.filename:
                    html_data = epub.read(file_info.filename).decode('utf-8')
                    soup = BeautifulSoup(html_data, 'html.parser')
                    
                    # Replace image sources with base64
                    for img in soup.find_all('img'):
                        src = img.get('src', '')
                        image_name = os.path.basename(src)
                        if image_name in extracted_images:
                            img['src'] = extracted_images[image_name]
                            images_embedded += 1
                    
                    # Add enhanced CSS
                    head = soup.find('head')
                    if not head:
                        head = soup.new_tag('head')
                        soup.insert(0, head)
                    
                    style = soup.new_tag('style')
                    style.string = """
                        body { 
                            font-family: 'Times New Roman', serif; 
                            line-height: 1.6; 
                            margin: 2cm; 
                            font-size: 12pt;
                        }
                        img { 
                            max-width: 100%; 
                            height: auto; 
                            margin: 1em auto; 
                            display: block; 
                            page-break-inside: avoid;
                        }
                        h1, h2, h3 { 
                            color: #333; 
                            margin-top: 2em; 
                            page-break-after: avoid;
                        }
                        p { 
                            margin-bottom: 1em; 
                            text-align: justify; 
                            orphans: 2;
                            widows: 2;
                        }
                        @page {
                            margin: 2cm;
                            @bottom-center {
                                content: counter(page);
                            }
                        }
                    """
                    head.append(style)
                    
                    combined_html += str(soup) + "\n"
            
            # Generate PDF
            HTML(string=combined_html).write_pdf(output_path)
            
        file_size = os.path.getsize(output_path) / 1024
        print(f"✅ WeasyPrint PDF created: {file_size:.1f} KB ({images_embedded} images)")
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
        return True
        
    except ImportError:
        print("❌ WeasyPrint not available")
        return False
    except Exception as e:
        print(f"❌ WeasyPrint error: {e}")
        return False

def convert_epub_to_pdf(epub_path: str, output_dir: str = "outputs") -> str:
    """
    Convert EPUB to PDF using the best available method
    Returns path to generated PDF
    """
    if not os.path.exists(epub_path):
        raise FileNotFoundError(f"EPUB file not found: {epub_path}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate output filename
    epub_name = Path(epub_path).stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print(f"📚 Converting {epub_path} to PDF...")
    print("=" * 60)
    
    # Try methods in order of quality
    methods = [
        ("calibre", epub_to_pdf_calibre),
        ("weasyprint", epub_to_pdf_weasyprint), 
        ("reportlab", epub_to_pdf_reportlab)
    ]
    
    for method_name, method_func in methods:
        output_path = os.path.join(output_dir, f"{epub_name}_{method_name}_{timestamp}.pdf")
        
        if method_func(epub_path, output_path):
            file_size = os.path.getsize(output_path) / (1024 * 1024)
            print(f"\n🎉 SUCCESS: PDF created using {method_name}")
            print(f"📁 Output: {output_path}")
            print(f"📦 Size: {file_size:.2f} MB")
            return output_path
    
    raise RuntimeError("❌ All PDF conversion methods failed")

if __name__ == "__main__":
    # Test with the image-rich EPUB
    epub_path = "sample_books/pg236_first20pages_with_images.epub"
    
    try:
        pdf_path = convert_epub_to_pdf(epub_path)
        print(f"\n✅ Conversion complete: {pdf_path}")
    except Exception as e:
        print(f"\n❌ Conversion failed: {e}")
        sys.exit(1)