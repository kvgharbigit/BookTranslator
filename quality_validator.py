#!/usr/bin/env python3
"""
Quality validation and content checks for generated files
"""
import os
import re
import zipfile
from pathlib import Path

class QualityValidator:
    def __init__(self):
        self.results = {}
    
    def validate_epub(self, epub_path: str) -> dict:
        """Validate EPUB file quality."""
        print(f"🔍 Validating EPUB: {os.path.basename(epub_path)}")
        
        result = {
            'file_exists': os.path.exists(epub_path),
            'file_size_mb': 0,
            'is_valid_zip': False,
            'has_mimetype': False,
            'has_content_opf': False,
            'has_toc_ncx': False,
            'file_count': 0,
            'issues': []
        }
        
        if not result['file_exists']:
            result['issues'].append("File does not exist")
            return result
        
        # Check file size
        result['file_size_mb'] = round(os.path.getsize(epub_path) / 1024 / 1024, 1)
        
        try:
            # Test if it's a valid ZIP
            with zipfile.ZipFile(epub_path, 'r') as epub:
                result['is_valid_zip'] = True
                file_list = epub.namelist()
                result['file_count'] = len(file_list)
                
                # Check required files
                result['has_mimetype'] = 'mimetype' in file_list
                result['has_content_opf'] = any('content.opf' in f for f in file_list)
                result['has_toc_ncx'] = any('toc.ncx' in f for f in file_list)
                
                # Validate mimetype
                if result['has_mimetype']:
                    mimetype_content = epub.read('mimetype').decode('utf-8')
                    if mimetype_content.strip() != 'application/epub+zip':
                        result['issues'].append("Invalid mimetype content")
                
                # Check for images
                image_count = sum(1 for f in file_list if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')))
                result['image_count'] = image_count
                
        except Exception as e:
            result['issues'].append(f"ZIP validation error: {e}")
        
        # Quality assessment
        if result['file_size_mb'] < 1:
            result['issues'].append("File size suspiciously small")
        elif result['file_size_mb'] > 50:
            result['issues'].append("File size very large")
        
        if not result['has_mimetype']:
            result['issues'].append("Missing mimetype file")
        if not result['has_content_opf']:
            result['issues'].append("Missing content.opf file")
        if not result['has_toc_ncx']:
            result['issues'].append("Missing toc.ncx file")
        
        print(f"   Size: {result['file_size_mb']} MB, Files: {result['file_count']}, Issues: {len(result['issues'])}")
        return result
    
    def validate_pdf(self, pdf_path: str) -> dict:
        """Validate PDF file quality."""
        print(f"🔍 Validating PDF: {os.path.basename(pdf_path)}")
        
        result = {
            'file_exists': os.path.exists(pdf_path),
            'file_size_mb': 0,
            'is_pdf': False,
            'issues': []
        }
        
        if not result['file_exists']:
            result['issues'].append("File does not exist")
            return result
        
        # Check file size
        result['file_size_mb'] = round(os.path.getsize(pdf_path) / 1024 / 1024, 1)
        
        # Check PDF signature
        try:
            with open(pdf_path, 'rb') as f:
                header = f.read(10)
                if header.startswith(b'%PDF-'):
                    result['is_pdf'] = True
                else:
                    result['issues'].append("Invalid PDF header")
        except Exception as e:
            result['issues'].append(f"Error reading file: {e}")
        
        # Quality assessment
        if result['file_size_mb'] < 0.5:
            result['issues'].append("PDF file suspiciously small")
        elif result['file_size_mb'] > 20:
            result['issues'].append("PDF file very large")
        
        print(f"   Size: {result['file_size_mb']} MB, Valid PDF: {result['is_pdf']}, Issues: {len(result['issues'])}")
        return result
    
    def validate_txt(self, txt_path: str) -> dict:
        """Validate TXT file quality."""
        print(f"🔍 Validating TXT: {os.path.basename(txt_path)}")
        
        result = {
            'file_exists': os.path.exists(txt_path),
            'file_size_kb': 0,
            'char_count': 0,
            'word_count': 0,
            'line_count': 0,
            'is_spanish': False,
            'has_structure': False,
            'issues': []
        }
        
        if not result['file_exists']:
            result['issues'].append("File does not exist")
            return result
        
        try:
            with open(txt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            result['file_size_kb'] = round(len(content.encode('utf-8')) / 1024, 1)
            result['char_count'] = len(content)
            result['word_count'] = len(content.split())
            result['line_count'] = len(content.split('\n'))
            
            # Check for Spanish content
            spanish_indicators = ['el ', 'la ', 'los ', 'las ', 'de ', 'que ', 'y ', 'a ', 'en ', 'un ', 'es ', 'se ', 'no ', 'te ', 'lo ', 'le ', 'da ', 'su ', 'por ', 'son ', 'con ', 'para ', 'este ', 'está ', 'como ', 'pero ', 'sus ', 'una ', 'muy ', 'todo ', 'más ', 'bien ', 'era ', 'ella ', 'cuando ', 'donde ', 'cada ', 'porque ', 'habían', 'había']
            spanish_count = sum(1 for indicator in spanish_indicators if indicator in content.lower())
            result['is_spanish'] = spanish_count >= 10
            
            # Check for structural elements
            structure_indicators = ['CAPÍTULO', 'TABLA DE CONTENIDOS', '===', '---', 'Los hermanos']
            structure_count = sum(1 for indicator in structure_indicators if indicator in content)
            result['has_structure'] = structure_count >= 3
            
        except Exception as e:
            result['issues'].append(f"Error reading file: {e}")
            return result
        
        # Quality assessment
        if result['word_count'] < 100:
            result['issues'].append("Very few words - possible incomplete file")
        elif result['word_count'] < 1000:
            result['issues'].append("Low word count - file may be truncated")
        
        if not result['is_spanish'] and 'original' not in txt_path:
            result['issues'].append("Content does not appear to be Spanish")
        
        if not result['has_structure']:
            result['issues'].append("Missing structural formatting elements")
        
        print(f"   Size: {result['file_size_kb']} KB, Words: {result['word_count']}, Spanish: {result['is_spanish']}, Issues: {len(result['issues'])}")
        return result
    
    def generate_quality_report(self, output_dir: str) -> None:
        """Generate comprehensive quality report."""
        
        print("\n📊 COMPREHENSIVE QUALITY VALIDATION REPORT")
        print("=" * 60)
        
        # Find all files to validate
        files_to_check = []
        
        for root, dirs, files in os.walk('test_outputs'):
            for file in files:
                file_path = os.path.join(root, file)
                if file.endswith('.epub'):
                    files_to_check.append(('epub', file_path))
                elif file.endswith('.pdf'):
                    files_to_check.append(('pdf', file_path))
                elif file.endswith('.txt'):
                    files_to_check.append(('txt', file_path))
        
        print(f"Found {len(files_to_check)} files to validate\n")
        
        # Validate each file
        validation_results = {}
        for file_type, file_path in files_to_check:
            if file_type == 'epub':
                validation_results[file_path] = self.validate_epub(file_path)
            elif file_type == 'pdf':
                validation_results[file_path] = self.validate_pdf(file_path)
            elif file_type == 'txt':
                validation_results[file_path] = self.validate_txt(file_path)
        
        # Generate summary
        print(f"\n📋 VALIDATION SUMMARY")
        print("=" * 40)
        
        total_files = len(validation_results)
        files_with_issues = sum(1 for r in validation_results.values() if r.get('issues'))
        
        print(f"Total files validated: {total_files}")
        print(f"Files with issues: {files_with_issues}")
        print(f"Success rate: {((total_files - files_with_issues) / total_files * 100):.1f}%")
        
        # Detailed issues
        if files_with_issues > 0:
            print(f"\n⚠️  FILES WITH ISSUES:")
            for file_path, result in validation_results.items():
                if result.get('issues'):
                    print(f"\n📁 {os.path.basename(file_path)}:")
                    for issue in result['issues']:
                        print(f"   • {issue}")
        
        print(f"\n✅ Quality validation completed!")

def main():
    """Run quality validation on all generated files."""
    validator = QualityValidator()
    validator.generate_quality_report('test_outputs')

if __name__ == "__main__":
    main()