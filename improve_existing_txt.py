#!/usr/bin/env python3
"""
Improve existing TXT files by cleaning up formatting issues
"""
import re
import os

def improve_txt_formatting(input_path: str, output_path: str) -> bool:
    """Clean up and improve existing TXT file formatting."""
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Error reading {input_path}: {e}")
        return False
    
    print(f"📝 Processing {input_path} ({len(content)/1024:.1f} KB)")
    
    # Split into lines for processing
    lines = content.split('\n')
    cleaned_lines = []
    seen_lines = set()
    
    # Track state
    in_metadata_section = False
    chapter_count = 0
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Skip empty lines (we'll add them back strategically)
        if not line:
            continue
            
        # Skip pure separators temporarily
        if line.startswith('===') or line.startswith('~~~'):
            continue
            
        # Detect and skip Project Gutenberg metadata
        if any(keyword in line.lower() for keyword in [
            'project gutenberg', 'ebook #', 'gutenberg.org', 
            'updated most recently', 'language: english', 'titleautor'
        ]):
            in_metadata_section = True
            continue
            
        # Skip metadata sections
        if in_metadata_section:
            # End metadata section when we hit substantial content
            if len(line) > 50 and not any(keyword in line.lower() for keyword in [
                'title', 'author', 'language', 'release date', 'updated'
            ]):
                in_metadata_section = False
            else:
                continue
        
        # Skip duplicate lines
        line_key = line.lower().replace(' ', '')[:50]
        if line_key in seen_lines:
            continue
        seen_lines.add(line_key)
        
        # Detect chapter beginnings
        if any(keyword in line.lower() for keyword in ['los hermanos de mowgli', 'contents', 'contenidos']):
            if 'hermanos' in line.lower():
                chapter_count += 1
                cleaned_lines.extend([
                    "",
                    "=" * 60,
                    f"CAPÍTULO {chapter_count}: LOS HERMANOS DE MOWGLI".center(60),
                    "=" * 60,
                    ""
                ])
                continue
            elif 'contents' in line.lower() or 'contenidos' in line.lower():
                cleaned_lines.extend([
                    "",
                    "=" * 60,
                    "TABLA DE CONTENIDOS".center(60),
                    "=" * 60,
                    ""
                ])
                continue
        
        # Clean up the line
        line = re.sub(r'\s+', ' ', line)  # Normalize whitespace
        
        # Skip very short lines that are likely formatting artifacts
        if len(line) < 3:
            continue
            
        # Add the line
        cleaned_lines.append(line)
        
        # Add paragraph break for substantial content
        if len(line) > 50:
            cleaned_lines.append("")
    
    # Create final content
    final_content = []
    
    # Add header
    final_content.extend([
        "=" * 70,
        "EL LIBRO DE LA SELVA".center(70),
        "Traducido por IA (Gemini/Groq)".center(70) if 'gemini' in input_path.lower() or 'groq' in input_path.lower() else "Texto Original".center(70),
        "=" * 70,
        "",
        ""
    ])
    
    # Add cleaned content
    final_content.extend(cleaned_lines)
    
    # Clean up excessive whitespace
    final_text = '\n'.join(final_content)
    final_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', final_text)  # Max 2 consecutive newlines
    
    # Write output
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_text)
        
        file_size = os.path.getsize(output_path) / 1024
        print(f"   ✅ Improved: {output_path} ({file_size:.1f} KB)")
        return True
        
    except Exception as e:
        print(f"❌ Error writing {output_path}: {e}")
        return False

def main():
    """Improve all existing TXT files."""
    
    print("🔧 Improving Existing TXT Files")
    print("=" * 40)
    
    files_to_improve = [
        ("test_outputs/gemini/translated_gemini.txt", "test_outputs/gemini/translated_gemini_clean.txt"),
        ("test_outputs/groq/translated_groq.txt", "test_outputs/groq/translated_groq_clean.txt")
    ]
    
    success_count = 0
    for input_path, output_path in files_to_improve:
        if os.path.exists(input_path):
            if improve_txt_formatting(input_path, output_path):
                success_count += 1
        else:
            print(f"❌ File not found: {input_path}")
    
    print(f"\n✅ Improved {success_count}/{len(files_to_improve)} TXT files")

if __name__ == "__main__":
    main()