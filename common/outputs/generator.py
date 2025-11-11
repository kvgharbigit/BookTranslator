"""
Unified output generator for all translation formats
Handles EPUB, PDF, and TXT generation with consistent formatting
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Add API to path
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir / "apps" / "api"))

from app.pipeline.epub_io import EPUBProcessor
from ..formatting.text import TextFormatter

logger = logging.getLogger(__name__)


class OutputGenerator:
    """Handles generation of EPUB, PDF, and TXT outputs with consistent formatting."""
    
    def __init__(self):
        self.epub_processor = EPUBProcessor()
        self.text_formatter = TextFormatter()
        
        # Try to import PDF converter
        self.pdf_converter = None
        try:
            sys.path.insert(0, str(root_dir))
            from epub_to_pdf_with_images import convert_epub_to_pdf
            self.pdf_converter = convert_epub_to_pdf
            logger.info("Enhanced PDF converter available")
        except Exception as e:
            logger.warning(f"Enhanced PDF converter not available: {e}")
    
    async def generate_all_outputs(
        self,
        output_dir: str,
        original_book: Any,
        translated_docs: List[Dict],
        provider_name: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, bool]:
        """
        Generate EPUB, PDF, and TXT outputs with consistent formatting.
        
        Args:
            output_dir: Directory to save outputs
            original_book: Original EPUB book object
            translated_docs: List of translated document dictionaries
            provider_name: Name of AI provider used
            metadata: Optional metadata for formatting
            
        Returns:
            Dictionary indicating success/failure for each format
        """
        results = {"epub": False, "pdf": False, "txt": False}
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate EPUB
        try:
            epub_path = await self.generate_epub(
                output_dir, original_book, translated_docs, provider_name
            )
            results["epub"] = bool(epub_path)
            logger.info(f"EPUB generation: {'✅' if results['epub'] else '❌'}")
        except Exception as e:
            logger.error(f"EPUB generation failed: {e}")
        
        # Generate PDF (requires EPUB)
        if results["epub"]:
            try:
                pdf_path = await self.generate_pdf(output_dir, epub_path, provider_name)
                results["pdf"] = bool(pdf_path)
                logger.info(f"PDF generation: {'✅' if results['pdf'] else '❌'}")
            except Exception as e:
                logger.error(f"PDF generation failed: {e}")
        
        # Generate TXT
        try:
            txt_path = await self.generate_txt(
                output_dir, translated_docs, provider_name, metadata
            )
            results["txt"] = bool(txt_path)
            logger.info(f"TXT generation: {'✅' if results['txt'] else '❌'}")
        except Exception as e:
            logger.error(f"TXT generation failed: {e}")
        
        return results
    
    async def generate_epub(
        self,
        output_dir: str,
        original_book: Any,
        translated_docs: List[Dict],
        provider_name: str
    ) -> Optional[str]:
        """Generate EPUB file from translated documents."""
        
        epub_filename = f"translated_{provider_name.lower()}.epub"
        epub_path = os.path.join(output_dir, epub_filename)
        
        # Write translated EPUB
        success = self.epub_processor.write_epub(
            original_book=original_book,
            translated_docs=translated_docs,
            output_path=epub_path
        )
        
        if success:
            file_size = Path(epub_path).stat().st_size / (1024 * 1024)  # MB
            logger.info(f"✅ EPUB: {epub_path} ({file_size:.1f} MB)")
            return epub_path
        else:
            logger.error(f"❌ EPUB generation failed")
            return None
    
    async def generate_pdf(
        self,
        output_dir: str,
        epub_path: str,
        provider_name: str
    ) -> Optional[str]:
        """Generate PDF from EPUB using enhanced converter."""
        
        if not self.pdf_converter:
            logger.error("PDF converter not available")
            return None
        
        try:
            pdf_path = self.pdf_converter(epub_path, output_dir)
            
            if pdf_path and os.path.exists(pdf_path):
                file_size = Path(pdf_path).stat().st_size / (1024 * 1024)  # MB
                logger.info(f"✅ PDF: {pdf_path} ({file_size:.1f} MB)")
                return pdf_path
            else:
                logger.error("PDF conversion failed - no output file")
                return None
                
        except Exception as e:
            logger.error(f"PDF generation error: {e}")
            return None
    
    async def generate_txt(
        self,
        output_dir: str,
        translated_docs: List[Dict],
        provider_name: str,
        metadata: Optional[Dict] = None
    ) -> Optional[str]:
        """Generate formatted TXT file from translated documents."""
        
        txt_filename = f"translated_{provider_name.lower()}.txt"
        txt_path = os.path.join(output_dir, txt_filename)
        
        # Extract metadata
        book_title = metadata.get("title", "Traducción de Libro") if metadata else "Traducción de Libro"
        author = metadata.get("author", "Autor Desconocido") if metadata else "Autor Desconocido"
        original_title = metadata.get("original_title", "Título Original") if metadata else "Título Original"
        
        # Generate formatted text content
        formatted_content = self.text_formatter.generate_formatted_book(
            docs=translated_docs,
            book_title=book_title,
            author=author,
            original_title=original_title,
            target_lang="Español",
            provider_name=provider_name
        )
        
        try:
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(formatted_content)
            
            file_size = Path(txt_path).stat().st_size / 1024  # KB
            logger.info(f"✅ TXT: {txt_path} ({file_size:.1f} KB)")
            return txt_path
            
        except Exception as e:
            logger.error(f"TXT file write error: {e}")
            return None
    
    def get_output_files(self, output_dir: str, provider_name: str) -> Dict[str, Optional[str]]:
        """Get paths to generated output files."""
        
        base_name = f"translated_{provider_name.lower()}"
        
        # Check for EPUB
        epub_path = os.path.join(output_dir, f"{base_name}.epub")
        epub_exists = epub_path if os.path.exists(epub_path) else None
        
        # Check for TXT
        txt_path = os.path.join(output_dir, f"{base_name}.txt")
        txt_exists = txt_path if os.path.exists(txt_path) else None
        
        # Check for PDF (multiple possible names due to timestamping)
        pdf_path = None
        for file in Path(output_dir).glob(f"{base_name}*.pdf"):
            pdf_path = str(file)
            break
        
        return {
            "epub": epub_exists,
            "pdf": pdf_path,
            "txt": txt_exists
        }
    
    def calculate_file_sizes(self, file_paths: Dict[str, Optional[str]]) -> Dict[str, str]:
        """Calculate and format file sizes."""
        
        sizes = {}
        
        for format_name, path in file_paths.items():
            if path and os.path.exists(path):
                file_size = Path(path).stat().st_size
                
                # Format size appropriately
                if format_name == "pdf" and file_size > 1024 * 1024:
                    sizes[format_name] = f"{file_size / (1024 * 1024):.1f} MB"
                else:
                    sizes[format_name] = f"{file_size / 1024:.1f} KB"
            else:
                sizes[format_name] = "Not generated"

        return sizes


async def generate_outputs_with_metadata(
    output_dir: str,
    job_id: str,
    original_book: Any,
    translated_docs: List[Dict],
    translated_segments: List[str]
) -> Dict[str, bool]:
    """
    Common function for generating outputs with automatic metadata extraction.

    This function is used by both production (worker.py) and testing pipelines
    to ensure identical output generation behavior.

    Args:
        output_dir: Directory to save outputs
        job_id: Job/provider identifier for file naming
        original_book: Original EPUB book object
        translated_docs: List of translated document dictionaries
        translated_segments: List of translated text segments (not used currently)

    Returns:
        Dictionary indicating success/failure for each format
    """
    # Initialize output generator
    output_generator = OutputGenerator()

    # Extract metadata for formatting
    metadata = {
        "title": "Traducción de Libro",
        "author": "Autor Desconocido",
        "original_title": "Original Book"
    }

    # Try to extract actual metadata from original book
    try:
        if hasattr(original_book, 'get_metadata'):
            book_metadata = original_book.get_metadata('DC', 'title')
            if book_metadata:
                metadata["original_title"] = book_metadata[0][0]

            author_metadata = original_book.get_metadata('DC', 'creator')
            if author_metadata:
                metadata["author"] = author_metadata[0][0]

            # Set translated title based on original
            if "jungle" in metadata["original_title"].lower():
                metadata["title"] = "EL LIBRO DE LA SELVA"
    except Exception as e:
        logger.debug(f"Could not extract book metadata: {e}")

    # Generate all outputs using shared module
    results = await output_generator.generate_all_outputs(
        output_dir=output_dir,
        original_book=original_book,
        translated_docs=translated_docs,
        provider_name=job_id,
        metadata=metadata
    )

    return results