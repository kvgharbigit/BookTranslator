"""
HTML to PDF converter for ALL book translations.

This module converts both bilingual and regular translation HTML to PDF using
WeasyPrint, which provides vastly superior CSS rendering compared to Calibre.

Features:
- Bilingual PDFs: Preserves subtitle styling (0.85em, gray, italic)
- Regular translations: Professional typography and layout
- RTL language support (Arabic, Hebrew, Farsi, Urdu)
- Base64 image embedding
- Optimized margins (1.5cm top/bottom, 2cm left/right)
- Page numbers and proper typography

WeasyPrint is the standard for ALL PDF generation in BookTranslator.
"""

import os
import tempfile
from typing import List
from pathlib import Path

from app.logger import get_logger

logger = get_logger(__name__)


def convert_bilingual_html_to_pdf(
    bilingual_docs: List[dict],
    css_content: str,
    output_path: str,
    source_lang: str = "en",
    target_lang: str = "es",
    original_book = None
) -> bool:
    """
    Convert bilingual HTML documents to PDF with preserved CSS styling.

    This function generates a PDF from bilingual HTML documents, preserving
    the bilingual subtitle styling (smaller, gray, italic) that gets lost
    when converting EPUB to PDF via Calibre.

    Args:
        bilingual_docs: List of bilingual document dicts with 'content' key
        css_content: CSS content to apply (includes original EPUB CSS + bilingual CSS)
        output_path: Path where PDF should be written
        source_lang: Source language code (default: "en")
        target_lang: Target language code (default: "es")
        original_book: Optional EpubBook object for extracting images

    Returns:
        True if conversion succeeded, False otherwise
    """
    try:
        from weasyprint import HTML, CSS
        from weasyprint.text.fonts import FontConfiguration
    except ImportError:
        logger.error("WeasyPrint not available - cannot generate PDF from HTML")
        return False

    try:
        import base64
        import re
        import ebooklib

        logger.info(f"Converting {len(bilingual_docs)} bilingual documents to PDF")

        # Extract images from EPUB as base64 data URIs (if original_book provided)
        image_map = {}
        if original_book:
            logger.info("Extracting images from EPUB...")
            for item in original_book.get_items():
                if item.get_type() == ebooklib.ITEM_IMAGE:
                    try:
                        img_path = item.get_name()
                        img_content = item.get_content()

                        # Determine MIME type
                        ext = img_path.lower().split('.')[-1]
                        mime_types = {
                            'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
                            'png': 'image/png', 'gif': 'image/gif',
                            'svg': 'image/svg+xml', 'webp': 'image/webp'
                        }
                        mime_type = mime_types.get(ext, 'image/jpeg')

                        # Encode as base64 data URI
                        img_base64 = base64.b64encode(img_content).decode('utf-8')
                        data_uri = f"data:{mime_type};base64,{img_base64}"

                        # Store with multiple path variations for matching
                        image_map[img_path] = data_uri
                        image_map[img_path.lstrip('/')] = data_uri
                        image_map[img_path.lstrip('../')] = data_uri
                        image_map[os.path.basename(img_path)] = data_uri

                    except Exception as e:
                        logger.warning(f"Failed to extract image {item.get_name()}: {e}")

            logger.info(f"Extracted {len(set(image_map.values()))} unique images")

        # Combine all document contents and replace image sources
        combined_html_parts = []

        for i, doc in enumerate(bilingual_docs):
            content = doc.get('content', '')

            # Replace image src attributes with base64 data URIs
            if image_map:
                def replace_img_src(match):
                    img_tag = match.group(0)
                    src_match = re.search(r'src=(?:"([^"]*)"|\'([^\']*)\')', img_tag, re.IGNORECASE)
                    if not src_match:
                        return img_tag

                    src = src_match.group(1) or src_match.group(2)

                    # Try different path variations
                    for variant in [src, src.lstrip('/'), src.lstrip('../'), os.path.basename(src)]:
                        if variant in image_map:
                            data_uri = image_map[variant]
                            return img_tag.replace(f'src="{src}"', f'src="{data_uri}"').replace(f"src='{src}'", f"src='{data_uri}'")

                    return img_tag

                content = re.sub(r'<img[^>]*>', replace_img_src, content, flags=re.IGNORECASE)

            # Add page break between chapters (except first)
            if i > 0:
                combined_html_parts.append('<div style="page-break-before: always;"></div>')

            combined_html_parts.append(content)

        combined_html = '\n'.join(combined_html_parts)

        # Determine if RTL language
        rtl_languages = {'ar', 'he', 'fa', 'ur'}
        is_rtl = target_lang.lower() in rtl_languages

        # Set HTML attributes for RTL support
        dir_attr = ' dir="rtl"' if is_rtl else ''
        lang_attr = f' lang="{target_lang}"'
        direction_css = 'rtl' if is_rtl else 'ltr'
        text_align = 'right' if is_rtl else 'left'

        # Create complete HTML document with CSS
        full_html = f"""<!DOCTYPE html>
<html{lang_attr}{dir_attr}>
<head>
    <meta charset="UTF-8">
    <style>
        /* Original EPUB CSS + Bilingual CSS */
        {css_content}

        /* PDF-specific enhancements */
        @page {{
            size: A4;
            margin: 1.5cm 2cm;  /* Top/bottom: 1.5cm, Left/right: 2cm */
            @bottom-center {{
                content: counter(page);
                font-size: 10pt;
                color: #666;
            }}
        }}

        body {{
            font-family: 'Times New Roman', 'Georgia', 'Garamond', serif;
            line-height: 1.6;
            direction: {direction_css};
            text-align: {text_align};
            font-size: 14pt;
            max-width: 100%;
            margin: 0;
            padding: 0;
        }}

        /* Ensure bilingual subtitles are preserved in PDF */
        .bilingual-subtitle {{
            display: block !important;
            font-size: 0.85em !important;
            font-style: italic !important;
            color: #666 !important;
            margin: 0.3em 0 0 0 !important;
            padding: 0 !important;
            line-height: 1.4 !important;
            font-weight: normal !important;
        }}

        /* PDF page breaking */
        h1, h2, h3 {{
            page-break-after: avoid;
            page-break-inside: avoid;
        }}

        p {{
            orphans: 2;
            widows: 2;
        }}

        img {{
            max-width: 100%;
            height: auto;
            page-break-inside: avoid;
        }}

        /* Chapter breaks */
        .chapter {{
            page-break-before: always;
        }}
    </style>
</head>
<body>
{combined_html}
</body>
</html>"""

        # Convert HTML to PDF using WeasyPrint
        logger.info("Rendering HTML to PDF with WeasyPrint...")

        # Create font configuration for better font rendering
        font_config = FontConfiguration()

        # Generate PDF
        html_obj = HTML(string=full_html)
        html_obj.write_pdf(
            output_path,
            font_config=font_config
        )

        # Check file was created
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
            logger.info(f"✅ Bilingual PDF generated: {file_size:.2f} MB")
            logger.info(f"   Bilingual subtitle styling preserved in PDF")
            return True
        else:
            logger.error("PDF file was not created")
            return False

    except Exception as e:
        logger.error(f"Failed to convert bilingual HTML to PDF: {e}", exc_info=True)
        return False


def test_bilingual_pdf():
    """Test the bilingual HTML to PDF conversion."""
    import sys
    from pathlib import Path

    # Add project root to path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    from app.pipeline.epub_io import EPUBProcessor
    from app.pipeline.html_segment import HTMLSegmenter
    from app.pipeline.bilingual_html import create_bilingual_documents

    logger.info("=" * 80)
    logger.info("🧪 TESTING BILINGUAL HTML-TO-PDF CONVERSION")
    logger.info("=" * 80)

    # Use sample book
    sample_book = Path(__file__).parent.parent.parent / "sample_books" / "pg236_first20pages.epub"

    if not sample_book.exists():
        logger.error(f"Sample book not found: {sample_book}")
        return False

    logger.info(f"📚 Using: {sample_book.name}")

    # Load and process EPUB
    processor = EPUBProcessor()
    original_book, spine_docs = processor.read_epub(str(sample_book))

    # Segment ALL documents (not just first 3)
    segmenter = HTMLSegmenter()
    segments, reconstruction_maps = segmenter.segment_documents(spine_docs)

    logger.info(f"✅ Extracted {len(segments)} segments from {len(spine_docs)} documents")

    # Create mock translations
    translated_segments = [f"Traducción: {seg}" for seg in segments]

    # Create bilingual documents
    bilingual_docs = create_bilingual_documents(
        original_segments=segments,
        translated_segments=translated_segments,
        reconstruction_maps=reconstruction_maps,
        spine_docs=spine_docs,
        source_lang="en",
        target_lang="es"
    )

    logger.info(f"✅ Created {len(bilingual_docs)} bilingual documents")

    # Get combined CSS (original + bilingual)
    original_css = processor.extract_all_css_from_book(original_book)

    from app.pipeline.bilingual_html import BilingualHTMLGenerator
    gen = BilingualHTMLGenerator()
    bilingual_css = gen.css

    combined_css = f"{original_css}\n\n/* Bilingual Layout */\n{bilingual_css}"

    logger.info(f"✅ Combined CSS: {len(combined_css)} bytes")

    # Convert to PDF
    output_path = Path(__file__).parent / "test_bilingual_from_html.pdf"

    logger.info(f"\n📝 Converting to PDF: {output_path.name}")

    success = convert_bilingual_html_to_pdf(
        bilingual_docs=bilingual_docs,
        css_content=combined_css,
        output_path=str(output_path),
        source_lang="en",
        target_lang="es",
        original_book=original_book
    )

    if success:
        logger.info("\n" + "=" * 80)
        logger.info("🎉 SUCCESS!")
        logger.info("=" * 80)
        logger.info(f"📄 PDF: {output_path}")
        logger.info("\n✅ This PDF should have:")
        logger.info("   • Spanish translations (normal text)")
        logger.info("   • English subtitles (smaller, gray, italic)")
        logger.info("   • Preserved CSS styling")
        logger.info("=" * 80)

        # Open the PDF
        import subprocess
        subprocess.run(["open", str(output_path)])
        return True
    else:
        logger.error("❌ PDF generation failed")
        return False


def convert_html_to_pdf(
    translated_docs: List[dict],
    css_content: str,
    output_path: str,
    target_lang: str = "es",
    original_book = None
) -> bool:
    """
    Convert regular (non-bilingual) translation HTML to PDF with WeasyPrint.

    This provides superior CSS rendering compared to Calibre's EPUB→PDF conversion.

    Args:
        translated_docs: List of translated document dicts with 'content' key
        css_content: CSS content to apply (original EPUB CSS)
        output_path: Path where PDF should be written
        target_lang: Target language code (default: "es")
        original_book: Optional EpubBook object for extracting images

    Returns:
        True if conversion succeeded, False otherwise
    """
    try:
        from weasyprint import HTML, CSS
        from weasyprint.text.fonts import FontConfiguration
    except ImportError:
        logger.error("WeasyPrint not available - cannot generate PDF from HTML")
        return False

    try:
        import base64
        import re
        import ebooklib

        logger.info(f"Converting {len(translated_docs)} translated documents to PDF")

        # Extract images from EPUB as base64 data URIs (if original_book provided)
        image_map = {}
        if original_book:
            logger.info("Extracting images from EPUB...")
            for item in original_book.get_items():
                if item.get_type() == ebooklib.ITEM_IMAGE:
                    try:
                        img_path = item.get_name()
                        img_content = item.get_content()

                        # Determine MIME type
                        ext = img_path.lower().split('.')[-1]
                        mime_types = {
                            'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
                            'png': 'image/png', 'gif': 'image/gif',
                            'svg': 'image/svg+xml', 'webp': 'image/webp'
                        }
                        mime_type = mime_types.get(ext, 'image/jpeg')

                        # Encode as base64 data URI
                        img_base64 = base64.b64encode(img_content).decode('utf-8')
                        data_uri = f"data:{mime_type};base64,{img_base64}"

                        # Store with multiple path variations for matching
                        image_map[img_path] = data_uri
                        image_map[img_path.lstrip('/')] = data_uri
                        image_map[img_path.lstrip('../')] = data_uri
                        image_map[os.path.basename(img_path)] = data_uri

                    except Exception as e:
                        logger.warning(f"Failed to extract image {item.get_name()}: {e}")

            logger.info(f"Extracted {len(set(image_map.values()))} unique images")

        # Combine all document contents and replace image sources
        combined_html_parts = []

        for i, doc in enumerate(translated_docs):
            content = doc.get('content', '')

            # Replace image src attributes with base64 data URIs
            if image_map:
                def replace_img_src(match):
                    img_tag = match.group(0)
                    src_match = re.search(r'src=(?:"([^"]*)"|\'([^\']*)\')', img_tag, re.IGNORECASE)
                    if not src_match:
                        return img_tag

                    src = src_match.group(1) or src_match.group(2)

                    # Try different path variations
                    for variant in [src, src.lstrip('/'), src.lstrip('../'), os.path.basename(src)]:
                        if variant in image_map:
                            data_uri = image_map[variant]
                            return img_tag.replace(f'src="{src}"', f'src="{data_uri}"').replace(f"src='{src}'", f"src='{data_uri}'")

                    return img_tag

                content = re.sub(r'<img[^>]*>', replace_img_src, content, flags=re.IGNORECASE)

            # Add page break between chapters (except first)
            if i > 0:
                combined_html_parts.append('<div style="page-break-before: always;"></div>')

            combined_html_parts.append(content)

        combined_html = '\n'.join(combined_html_parts)

        # Determine if RTL language
        rtl_languages = {'ar', 'he', 'fa', 'ur'}
        is_rtl = target_lang.lower() in rtl_languages

        # Set HTML attributes for RTL support
        dir_attr = ' dir="rtl"' if is_rtl else ''
        lang_attr = f' lang="{target_lang}"'
        direction_css = 'rtl' if is_rtl else 'ltr'
        text_align = 'right' if is_rtl else 'left'

        # Create complete HTML document with CSS
        full_html = f"""<!DOCTYPE html>
<html{lang_attr}{dir_attr}>
<head>
    <meta charset="UTF-8">
    <style>
        /* Original EPUB CSS */
        {css_content}

        /* PDF-specific enhancements */
        @page {{
            size: A4;
            margin: 1.5cm 2cm;  /* Top/bottom: 1.5cm, Left/right: 2cm */
            @bottom-center {{
                content: counter(page);
                font-size: 10pt;
                color: #666;
            }}
        }}

        body {{
            font-family: 'Times New Roman', 'Georgia', 'Garamond', serif;
            line-height: 1.6;
            direction: {direction_css};
            text-align: {text_align};
            font-size: 14pt;
            max-width: 100%;
            margin: 0;
            padding: 0;
        }}

        /* PDF page breaking */
        h1, h2, h3 {{
            page-break-after: avoid;
            page-break-inside: avoid;
        }}

        p {{
            orphans: 2;
            widows: 2;
        }}

        img {{
            max-width: 100%;
            height: auto;
            page-break-inside: avoid;
        }}

        /* Chapter breaks */
        .chapter {{
            page-break-before: always;
        }}
    </style>
</head>
<body>
{combined_html}
</body>
</html>"""

        # Convert HTML to PDF using WeasyPrint
        logger.info("Rendering HTML to PDF with WeasyPrint...")

        # Create font configuration for better font rendering
        font_config = FontConfiguration()

        # Generate PDF
        html_obj = HTML(string=full_html)
        html_obj.write_pdf(
            output_path,
            font_config=font_config
        )

        # Check file was created
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
            logger.info(f"✅ Translation PDF generated with WeasyPrint: {file_size:.2f} MB")
            return True
        else:
            logger.error("PDF file was not created")
            return False

    except Exception as e:
        logger.error(f"Failed to convert HTML to PDF: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    import sys
    sys.exit(0 if test_bilingual_pdf() else 1)
