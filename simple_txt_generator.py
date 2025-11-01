#!/usr/bin/env python3
"""
Simple TXT generation from EPUB documents
"""
import sys
from pathlib import Path
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent / "apps" / "api"))
from app.pipeline.epub_io import EPUBProcessor

def generate_simple_txt(epub_path: str, output_path: str, title: str = "Converted Text"):
    """Generate a simple TXT file from EPUB"""
    
    processor = EPUBProcessor()
    book, docs = processor.read_epub(epub_path)
    
    content_lines = [
        f"{'='*60}",
        title.upper(),
        f"{'='*60}",
        "",
        ""
    ]
    
    for i, doc in enumerate(docs):
        if not doc['content']:
            continue
            
        soup = BeautifulSoup(doc['content'], 'html.parser')
        
        # Extract text content
        text = soup.get_text()
        
        # Clean up whitespace
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        if lines:
            # Add chapter separator if needed
            if i > 0:
                content_lines.extend(["", "-" * 40, ""])
            
            content_lines.extend(lines)
            content_lines.append("")
    
    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(content_lines))
    
    return len(content_lines)

if __name__ == "__main__":
    epub_path = "test_outputs/original/original.epub"
    output_path = "test_outputs/original/original.txt"
    
    lines = generate_simple_txt(epub_path, output_path, "The Jungle Book - Original English Edition")
    print(f"Generated TXT with {lines} lines: {output_path}")
    
    file_size = Path(output_path).stat().st_size / 1024
    print(f"File size: {file_size:.1f} KB")