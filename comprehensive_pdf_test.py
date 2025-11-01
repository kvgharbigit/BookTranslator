#!/usr/bin/env python3
"""
Comprehensive PDF generation testing with multiple approaches
"""
import os
import sys
import tempfile
import zipfile
import base64
import subprocess
from pathlib import Path
import json
from datetime import datetime

# Add the API to path
sys.path.insert(0, str(Path(__file__).parent / "apps" / "api"))

from bs4 import BeautifulSoup

def create_test_results_dir():
    """Create timestamped results directory"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = f"pdf_test_results_{timestamp}"
    os.makedirs(results_dir, exist_ok=True)
    return results_dir

def extract_epub_content(epub_path, results_dir):
    """Extract EPUB content and images for testing"""
    print(f"📚 Extracting EPUB content from {epub_path}")
    
    images_dir = os.path.join(results_dir, "extracted_images")
    html_dir = os.path.join(results_dir, "extracted_html")
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(html_dir, exist_ok=True)
    
    extracted_images = {}
    html_files = []
    
    with zipfile.ZipFile(epub_path, 'r') as epub:
        # Extract images (check for common image extensions)
        for file_info in epub.infolist():
            if (file_info.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.svg')) 
                and not file_info.is_dir() and 'OEBPS/' in file_info.filename):
                try:
                    image_data = epub.read(file_info.filename)
                    image_name = os.path.basename(file_info.filename)
                    image_path = os.path.join(images_dir, image_name)
                    
                    with open(image_path, 'wb') as f:
                        f.write(image_data)
                    
                    relative_key = os.path.basename(file_info.filename)
                    extracted_images[relative_key] = {
                        'path': image_path,
                        'size': len(image_data),
                        'name': image_name
                    }
                    print(f"   📷 Extracted {image_name} ({len(image_data):,} bytes)")
                except Exception as e:
                    print(f"   ⚠️  Failed to extract {file_info.filename}: {e}")
        
        # Extract HTML files
        for file_info in epub.infolist():
            if file_info.filename.endswith('.html') and 'OEBPS' in file_info.filename:
                try:
                    html_data = epub.read(file_info.filename).decode('utf-8')
                    html_name = os.path.basename(file_info.filename)
                    html_path = os.path.join(html_dir, html_name)
                    
                    with open(html_path, 'w', encoding='utf-8') as f:
                        f.write(html_data)
                    
                    html_files.append({
                        'path': html_path,
                        'name': html_name,
                        'content': html_data,
                        'size': len(html_data)
                    })
                    print(f"   📄 Extracted {html_name} ({len(html_data):,} chars)")
                except Exception as e:
                    print(f"   ⚠️  Failed to extract {file_info.filename}: {e}")
    
    print(f"   ✅ Extracted {len(extracted_images)} images and {len(html_files)} HTML files")
    return extracted_images, html_files

def test_weasyprint_base64(results_dir, extracted_images, html_files):
    """Test WeasyPrint with base64 embedded images"""
    print("\n🧪 Testing WeasyPrint with Base64 Images")
    
    try:
        from weasyprint import HTML, CSS
        
        if not html_files:
            print("   ❌ No HTML files to process")
            return False
        
        # Take first HTML file with substantial content
        main_html = max(html_files, key=lambda x: x['size'])
        soup = BeautifulSoup(main_html['content'], 'html.parser')
        
        # Convert images to base64 and embed
        images_embedded = 0
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if src in extracted_images:
                image_path = extracted_images[src]['path']
                image_name = extracted_images[src]['name']
                
                # Determine MIME type
                if image_name.lower().endswith(('.jpg', '.jpeg')):
                    mime_type = 'image/jpeg'
                elif image_name.lower().endswith('.png'):
                    mime_type = 'image/png'
                elif image_name.lower().endswith('.gif'):
                    mime_type = 'image/gif'
                elif image_name.lower().endswith('.svg'):
                    mime_type = 'image/svg+xml'
                else:
                    mime_type = 'image/jpeg'
                
                # Read and encode image
                with open(image_path, 'rb') as f:
                    image_data = f.read()
                    b64_data = base64.b64encode(image_data).decode('utf-8')
                    data_uri = f"data:{mime_type};base64,{b64_data}"
                    img['src'] = data_uri
                    images_embedded += 1
                    print(f"   🔄 Embedded {image_name} as base64")
        
        # Add styling for better PDF output
        head = soup.find('head')
        if head:
            style = soup.new_tag('style')
            style.string = """
                body { font-family: 'Times New Roman', serif; line-height: 1.6; margin: 2cm; }
                img { max-width: 100%; height: auto; margin: 1em auto; display: block; }
                h1, h2, h3 { color: #333; margin-top: 2em; }
                p { margin-bottom: 1em; text-align: justify; }
            """
            head.append(style)
        
        # Generate PDF
        output_path = os.path.join(results_dir, "weasyprint_base64.pdf")
        HTML(string=str(soup)).write_pdf(output_path)
        
        file_size = os.path.getsize(output_path)
        print(f"   ✅ PDF generated: {file_size:,} bytes")
        print(f"   📊 Images embedded: {images_embedded}")
        
        # Save processing info
        info = {
            'approach': 'WeasyPrint Base64',
            'images_embedded': images_embedded,
            'file_size': file_size,
            'source_html': main_html['name'],
            'success': True
        }
        
        with open(os.path.join(results_dir, "weasyprint_base64_info.json"), 'w') as f:
            json.dump(info, f, indent=2)
        
        return True
        
    except ImportError as e:
        print(f"   ⚠️  WeasyPrint not available: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_reportlab(results_dir, extracted_images, html_files):
    """Test ReportLab PDF generation"""
    print("\n🧪 Testing ReportLab PDF Generation")
    
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        
        if not html_files:
            print("   ❌ No HTML files to process")
            return False
        
        output_path = os.path.join(results_dir, "reportlab.pdf")
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Create custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=20,
            textColor=colors.darkblue
        )
        
        images_added = 0
        paragraphs_added = 0
        
        # Process HTML files
        for html_file in html_files:
            soup = BeautifulSoup(html_file['content'], 'html.parser')
            
            # Add title
            title = html_file['name'].replace('.html', '').replace('_', ' ').title()
            story.append(Paragraph(title, title_style))
            story.append(Spacer(1, 12))
            
            # Process elements
            for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'img', 'div']):
                try:
                    if element.name == 'img':
                        src = element.get('src', '')
                        if src in extracted_images:
                            image_path = extracted_images[src]['path']
                            # Add image with size constraints
                            img = RLImage(image_path, width=4*inch, height=3*inch)
                            story.append(img)
                            story.append(Spacer(1, 12))
                            images_added += 1
                            print(f"   🖼️  Added image: {src}")
                    else:
                        text = element.get_text().strip()
                        if text and len(text) > 5:  # Only substantial text
                            if element.name.startswith('h'):
                                style = styles['Heading2']
                            else:
                                style = styles['Normal']
                            
                            # Clean text for ReportLab
                            text = text.replace('\n', ' ').replace('\t', ' ')
                            text = ' '.join(text.split())  # Normalize whitespace
                            
                            para = Paragraph(text, style)
                            story.append(para)
                            story.append(Spacer(1, 6))
                            paragraphs_added += 1
                            
                except Exception as e:
                    print(f"   ⚠️  Error processing element: {e}")
                    continue
        
        # Build PDF
        doc.build(story)
        
        file_size = os.path.getsize(output_path)
        print(f"   ✅ PDF generated: {file_size:,} bytes")
        print(f"   📊 Images added: {images_added}")
        print(f"   📊 Paragraphs added: {paragraphs_added}")
        
        # Save processing info
        info = {
            'approach': 'ReportLab',
            'images_added': images_added,
            'paragraphs_added': paragraphs_added,
            'file_size': file_size,
            'html_files_processed': len(html_files),
            'success': True
        }
        
        with open(os.path.join(results_dir, "reportlab_info.json"), 'w') as f:
            json.dump(info, f, indent=2)
        
        return True
        
    except ImportError as e:
        print(f"   ⚠️  ReportLab not available: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_html_to_pdf_direct(results_dir, extracted_images, html_files):
    """Test direct HTML to PDF using various command line tools"""
    print("\n🧪 Testing HTML to PDF Direct Conversion")
    
    if not html_files:
        print("   ❌ No HTML files to process")
        return False
    
    # Create a combined HTML file with embedded images
    main_html = max(html_files, key=lambda x: x['size'])
    soup = BeautifulSoup(main_html['content'], 'html.parser')
    
    # Fix image paths to absolute paths
    images_fixed = 0
    for img in soup.find_all('img'):
        src = img.get('src', '')
        if src in extracted_images:
            absolute_path = os.path.abspath(extracted_images[src]['path'])
            img['src'] = f"file://{absolute_path}"
            images_fixed += 1
            print(f"   🔄 Fixed image path: {src}")
    
    # Save modified HTML
    html_output_path = os.path.join(results_dir, "combined_with_images.html")
    with open(html_output_path, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    
    print(f"   📄 Created HTML with {images_fixed} fixed image paths")
    
    # Try different conversion tools
    tools_tested = []
    
    # Test wkhtmltopdf if available
    try:
        result = subprocess.run(['which', 'wkhtmltopdf'], capture_output=True)
        if result.returncode == 0:
            pdf_path = os.path.join(results_dir, "wkhtmltopdf.pdf")
            cmd = ['wkhtmltopdf', '--enable-local-file-access', html_output_path, pdf_path]
            result = subprocess.run(cmd, capture_output=True, timeout=30)
            
            if result.returncode == 0 and os.path.exists(pdf_path):
                file_size = os.path.getsize(pdf_path)
                print(f"   ✅ wkhtmltopdf: {file_size:,} bytes")
                tools_tested.append({'tool': 'wkhtmltopdf', 'success': True, 'size': file_size})
            else:
                print(f"   ❌ wkhtmltopdf failed: {result.stderr.decode()}")
                tools_tested.append({'tool': 'wkhtmltopdf', 'success': False, 'error': result.stderr.decode()})
        else:
            print("   ⚠️  wkhtmltopdf not available")
    except Exception as e:
        print(f"   ❌ wkhtmltopdf error: {e}")
        tools_tested.append({'tool': 'wkhtmltopdf', 'success': False, 'error': str(e)})
    
    # Test Prince XML if available
    try:
        result = subprocess.run(['which', 'prince'], capture_output=True)
        if result.returncode == 0:
            pdf_path = os.path.join(results_dir, "prince.pdf")
            cmd = ['prince', html_output_path, '-o', pdf_path]
            result = subprocess.run(cmd, capture_output=True, timeout=30)
            
            if result.returncode == 0 and os.path.exists(pdf_path):
                file_size = os.path.getsize(pdf_path)
                print(f"   ✅ Prince XML: {file_size:,} bytes")
                tools_tested.append({'tool': 'prince', 'success': True, 'size': file_size})
            else:
                print(f"   ❌ Prince XML failed: {result.stderr.decode()}")
                tools_tested.append({'tool': 'prince', 'success': False, 'error': result.stderr.decode()})
        else:
            print("   ⚠️  Prince XML not available")
    except Exception as e:
        print(f"   ❌ Prince XML error: {e}")
        tools_tested.append({'tool': 'prince', 'success': False, 'error': str(e)})
    
    # Save results
    info = {
        'approach': 'HTML to PDF Direct',
        'images_fixed': images_fixed,
        'tools_tested': tools_tested,
        'html_file_created': html_output_path,
        'success': len([t for t in tools_tested if t['success']]) > 0
    }
    
    with open(os.path.join(results_dir, "html_to_pdf_info.json"), 'w') as f:
        json.dump(info, f, indent=2)
    
    return info['success']

def test_calibre_if_available(results_dir, epub_path):
    """Test Calibre ebook-convert if available"""
    print("\n🧪 Testing Calibre ebook-convert")
    
    try:
        # Check if calibre is available
        result = subprocess.run(['which', 'ebook-convert'], capture_output=True)
        if result.returncode != 0:
            print("   ⚠️  Calibre not available")
            return False
        
        output_path = os.path.join(results_dir, "calibre_convert.pdf")
        
        # Convert with various options
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
            '--pdf-serif-family', 'Times New Roman'
        ]
        
        print(f"   🔄 Running Calibre conversion...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0 and os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"   ✅ Calibre PDF: {file_size:,} bytes")
            
            info = {
                'approach': 'Calibre ebook-convert',
                'file_size': file_size,
                'command': ' '.join(cmd),
                'success': True
            }
            
            with open(os.path.join(results_dir, "calibre_info.json"), 'w') as f:
                json.dump(info, f, indent=2)
            
            return True
        else:
            print(f"   ❌ Calibre failed: {result.stderr}")
            return False
        
    except subprocess.TimeoutExpired:
        print("   ⚠️  Calibre conversion timed out")
        return False
    except Exception as e:
        print(f"   ❌ Calibre error: {e}")
        return False

def create_comparison_report(results_dir):
    """Create a comprehensive comparison report"""
    print("\n📊 Creating Comparison Report")
    
    report = {
        'test_timestamp': datetime.now().isoformat(),
        'results_directory': results_dir,
        'approaches_tested': [],
        'recommendations': []
    }
    
    # Collect results from all approaches
    for info_file in os.listdir(results_dir):
        if info_file.endswith('_info.json'):
            try:
                with open(os.path.join(results_dir, info_file), 'r') as f:
                    approach_info = json.load(f)
                    report['approaches_tested'].append(approach_info)
            except Exception as e:
                print(f"   ⚠️  Could not read {info_file}: {e}")
    
    # Analyze results and create recommendations
    successful_approaches = [a for a in report['approaches_tested'] if a.get('success', False)]
    
    if successful_approaches:
        # Sort by file size (larger usually means better image preservation)
        successful_approaches.sort(key=lambda x: x.get('file_size', 0), reverse=True)
        
        report['recommendations'] = [
            f"Best approach: {successful_approaches[0]['approach']} (largest file size: {successful_approaches[0].get('file_size', 0):,} bytes)",
            f"Total successful approaches: {len(successful_approaches)}/{len(report['approaches_tested'])}"
        ]
        
        if len(successful_approaches) > 1:
            report['recommendations'].append(f"Alternative: {successful_approaches[1]['approach']}")
    else:
        report['recommendations'] = ["No approaches were successful"]
    
    # Save report
    report_path = os.path.join(results_dir, "comparison_report.json")
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Create human-readable summary
    summary_path = os.path.join(results_dir, "SUMMARY.md")
    with open(summary_path, 'w') as f:
        f.write(f"# PDF Generation Test Results\\n\\n")
        f.write(f"**Test Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n\\n")
        f.write(f"## Results Summary\\n\\n")
        
        for approach in report['approaches_tested']:
            status = "✅ SUCCESS" if approach.get('success', False) else "❌ FAILED"
            size = approach.get('file_size', 0)
            f.write(f"- **{approach['approach']}**: {status}")
            if size > 0:
                f.write(f" ({size:,} bytes)")
            f.write("\\n")
        
        f.write("\\n## Recommendations\\n\\n")
        for rec in report['recommendations']:
            f.write(f"- {rec}\\n")
        
        f.write("\\n## Files Generated\\n\\n")
        for file in os.listdir(results_dir):
            if file.endswith('.pdf'):
                size = os.path.getsize(os.path.join(results_dir, file))
                f.write(f"- `{file}` ({size:,} bytes)\\n")
    
    print(f"   ✅ Report saved: {report_path}")
    print(f"   ✅ Summary saved: {summary_path}")

def main():
    print("🔬 COMPREHENSIVE PDF GENERATION TESTING")
    print("=" * 60)
    
    # Setup
    epub_path = "sample_books/pg236_first20pages_with_images.epub"
    if not os.path.exists(epub_path):
        print(f"❌ EPUB file not found: {epub_path}")
        return
    
    results_dir = create_test_results_dir()
    print(f"📁 Results will be saved to: {results_dir}")
    
    # Extract EPUB content
    extracted_images, html_files = extract_epub_content(epub_path, results_dir)
    
    # Run all tests
    print("\\n" + "=" * 60)
    print("🧪 RUNNING ALL TESTS")
    print("=" * 60)
    
    test_results = {}
    
    # Test 1: WeasyPrint with Base64
    test_results['weasyprint'] = test_weasyprint_base64(results_dir, extracted_images, html_files)
    
    # Test 2: ReportLab
    test_results['reportlab'] = test_reportlab(results_dir, extracted_images, html_files)
    
    # Test 3: HTML to PDF tools
    test_results['html_tools'] = test_html_to_pdf_direct(results_dir, extracted_images, html_files)
    
    # Test 4: Calibre
    test_results['calibre'] = test_calibre_if_available(results_dir, epub_path)
    
    # Create comparison report
    create_comparison_report(results_dir)
    
    print("\\n" + "=" * 60)
    print("🎉 ALL TESTS COMPLETED")
    print("=" * 60)
    print(f"📁 Results saved in: {results_dir}")
    print(f"📊 Check SUMMARY.md for recommendations")
    
    # Show quick summary
    successful = [k for k, v in test_results.items() if v]
    print(f"\\n✅ Successful approaches: {len(successful)}/{len(test_results)}")
    for approach in successful:
        print(f"   - {approach}")

if __name__ == "__main__":
    main()