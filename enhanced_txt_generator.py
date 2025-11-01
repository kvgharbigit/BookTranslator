#!/usr/bin/env python3
"""
Enhanced TXT generation with proper content filtering and organization
"""
import sys
import os
import re
from pathlib import Path
from bs4 import BeautifulSoup

# Add API to path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir / "apps" / "api"))
os.chdir(root_dir)

from app.pipeline.epub_io import EPUBProcessor

class EnhancedTXTGenerator:
    def __init__(self):
        self.metadata_keywords = [
            'project gutenberg', 'gutenberg.org', 'ebook #', 'etext #',
            'copyright', 'license', 'disclaimer', 'terms of use',
            'www.gutenberg', 'email', '@', 'http://', 'https://'
        ]
        
        self.content_indicators = [
            'chapter', 'capítulo', 'part', 'parte', 'book', 'libro',
            'section', 'sección', 'story', 'historia', 'tale', 'cuento'
        ]

    def is_metadata_content(self, content: str) -> bool:
        """Determine if content is primarily metadata."""
        content_lower = content.lower()
        
        # Check length - very short or very long metadata sections
        if len(content.strip()) < 200:
            return True
            
        # Check for metadata keywords
        metadata_count = sum(1 for keyword in self.metadata_keywords 
                           if keyword in content_lower)
        
        # High concentration of metadata keywords
        if metadata_count >= 3:
            return True
            
        # Check if it's primarily copyright/license info
        if any(term in content_lower for term in ['copyright', 'license', 'terms of use']):
            if len(content.strip()) < 1000:  # Short legal text
                return True
                
        return False

    def is_table_of_contents(self, content: str) -> bool:
        """Determine if content is a table of contents."""
        content_lower = content.lower()
        
        # Look for TOC indicators
        toc_indicators = ['contents', 'table of contents', 'índice', 'contenidos']
        if any(indicator in content_lower for indicator in toc_indicators):
            return True
            
        # Count chapter-like entries
        lines = content.split('\n')
        chapter_lines = sum(1 for line in lines 
                          if any(indicator in line.lower() 
                               for indicator in ['chapter', 'capítulo', 'part', 'parte']))
        
        # If many chapter references in short content, likely TOC
        if chapter_lines >= 3 and len(content) < 2000:
            return True
            
        return False

    def extract_chapter_title(self, content: str) -> str:
        """Extract a meaningful chapter title from content."""
        soup = BeautifulSoup(content, 'html.parser')
        
        # Look for heading tags first
        for tag in ['h1', 'h2', 'h3']:
            heading = soup.find(tag)
            if heading:
                title = heading.get_text(strip=True)
                if len(title) > 3 and len(title) < 100:
                    return title
        
        # Look for first substantial paragraph
        paragraphs = soup.find_all('p')
        for p in paragraphs:
            text = p.get_text(strip=True)
            if len(text) > 10 and len(text) < 200:
                # Check if it looks like a title
                if text.count('.') <= 1 and text.count('\n') == 0:
                    return text
                    
        return None

    def clean_and_format_content(self, content: str) -> list:
        """Clean content and return formatted paragraphs."""
        soup = BeautifulSoup(content, 'html.parser')
        formatted_lines = []
        seen_text = set()
        
        # Process elements in order
        for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div']):
            text = element.get_text(strip=True)
            
            # Skip empty, very short, or duplicate content
            if not text or len(text) < 10:
                continue
                
            # Create a key for duplicate detection (first 100 chars, normalized)
            text_key = re.sub(r'\s+', ' ', text.lower())[:100]
            if text_key in seen_text:
                continue
            seen_text.add(text_key)
            
            # Skip metadata content
            if any(keyword in text.lower() for keyword in self.metadata_keywords):
                continue
            
            # Format based on element type
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                # Heading
                formatted_lines.append("")
                formatted_lines.append(text.upper())
                formatted_lines.append("-" * min(len(text), 50))
                formatted_lines.append("")
            else:
                # Paragraph
                # Clean up whitespace
                clean_text = re.sub(r'\s+', ' ', text).strip()
                if len(clean_text) > 20:  # Only substantial content
                    formatted_lines.append(clean_text)
                    formatted_lines.append("")
        
        return formatted_lines

    def generate_enhanced_txt(self, epub_path: str, output_path: str) -> bool:
        """Generate enhanced TXT with proper content organization."""
        
        print(f"📖 Processing {epub_path}...")
        
        # Read EPUB
        processor = EPUBProcessor()
        if not processor.validate_epub_safety(epub_path):
            print(f"❌ EPUB validation failed")
            return False
        
        book, docs = processor.read_epub(epub_path)
        print(f"   Found {len(docs)} documents")
        
        # Organize content
        table_of_contents = None
        chapters = []
        
        for i, doc in enumerate(docs):
            content = doc.get('content', '')
            title = doc.get('title', f'Document {i+1}')
            
            print(f"   Analyzing: {title} ({len(content)} chars)")
            
            # Categorize content
            if self.is_metadata_content(content):
                print(f"      → Skipping metadata")
                continue
            elif self.is_table_of_contents(content):
                print(f"      → Found table of contents")
                table_of_contents = content
            else:
                print(f"      → Adding as chapter content")
                # Try to extract a better title
                extracted_title = self.extract_chapter_title(content)
                if extracted_title:
                    title = extracted_title
                
                chapters.append({
                    'title': title,
                    'content': content,
                    'formatted_content': self.clean_and_format_content(content)
                })
        
        # Generate final TXT
        final_content = []
        
        # Add book title/header
        final_content.extend([
            "=" * 70,
            "EL LIBRO DE LA SELVA".center(70),
            "by Rudyard Kipling".center(70),
            "=" * 70,
            "",
            ""
        ])
        
        # Add table of contents if found
        if table_of_contents:
            final_content.extend([
                "=" * 60,
                "TABLA DE CONTENIDOS".center(60),
                "=" * 60,
                ""
            ])
            
            # Extract and clean TOC
            toc_lines = self.clean_and_format_content(table_of_contents)
            final_content.extend(toc_lines)
            final_content.extend(["", "~" * 60, "", ""])
        
        # Add chapters
        for i, chapter in enumerate(chapters):
            # Chapter header
            chapter_title = chapter['title']
            if 'untitled' in chapter_title.lower() or chapter_title.startswith('Document'):
                chapter_title = f"CAPÍTULO {i+1}"
            
            final_content.extend([
                "",
                "=" * 60,
                chapter_title.upper().center(60),
                "=" * 60,
                ""
            ])
            
            # Chapter content
            final_content.extend(chapter['formatted_content'])
            
            # Chapter separator
            final_content.extend(["", "~" * 60, ""])
        
        # Clean up excessive whitespace
        final_text = '\n'.join(final_content)
        final_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', final_text)
        
        # Write output
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_text)
        
        file_size = os.path.getsize(output_path) / 1024
        print(f"   ✅ Generated: {output_path} ({file_size:.1f} KB)")
        
        return True

def main():
    """Generate enhanced TXT files for all translations."""
    
    print("🚀 Generating Enhanced TXT Files")
    print("=" * 50)
    
    generator = EnhancedTXTGenerator()
    
    # Process all EPUB files
    files_to_process = [
        ("test_outputs/original/original.epub", "test_outputs/original/original_enhanced.txt"),
        ("test_outputs/gemini/translated_gemini.epub", "test_outputs/gemini/translated_gemini_enhanced.txt"),
        ("test_outputs/groq/translated_groq.epub", "test_outputs/groq/translated_groq_enhanced.txt")
    ]
    
    success_count = 0
    for epub_path, txt_path in files_to_process:
        if os.path.exists(epub_path):
            if generator.generate_enhanced_txt(epub_path, txt_path):
                success_count += 1
        else:
            print(f"❌ File not found: {epub_path}")
    
    print(f"\n✅ Generated {success_count}/{len(files_to_process)} enhanced TXT files")

if __name__ == "__main__":
    main()