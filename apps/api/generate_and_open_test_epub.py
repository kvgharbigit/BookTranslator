"""Generate test EPUB and keep it for manual inspection"""
import sys
sys.path.insert(0, '/Users/kayvangharbi/PycharmProjects/BookTranslator/apps/api')

from app.pipeline.html_segment import HTMLSegmenter
from app.pipeline.bilingual_html import create_bilingual_documents
from app.pipeline.epub_io import EPUBProcessor
from ebooklib import epub

# Create test data with more content
spine_docs = [{
    'id': 'ch1',
    'href': 'chapter1.xhtml',
    'title': 'Chapter 1',
    'content': '''<?xml version='1.0' encoding='utf-8'?>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>Mowgli's Brothers</title></head>
<body>
<h1>Mowgli's Brothers</h1>
<p>Now Rann the Kite brings home the night that Mang the Bat sets free. The herds are shut in byre and hut, for loosed till dawn are we.</p>
<p>This is the hour of pride and power, talon and tush and claw. Oh, hear the call! Good hunting all that keep the Jungle Law!</p>
<p>It was seven o'clock of a very warm evening in the Seeonee hills when Father Wolf woke up from his day's rest.</p>
</body>
</html>'''
}]

print("Generating test bilingual EPUB...")

# Segment
segmenter = HTMLSegmenter()
segments, reconstruction_maps = segmenter.segment_documents(spine_docs)

print(f"Found {len(segments)} segments:")
for i, seg in enumerate(segments):
    print(f"  {i+1}. {seg[:60]}...")

# Create matching translations
translated_segments = [
    "Los Hermanos de Mowgli",
    "Los Hermanos de Mowgli",
    "Ahora Rann el Cernícalo trae la noche que Mang el Murciélago libera. Los rebaños están encerrados en establos y chozas, porque liberados hasta el amanecer estamos nosotros.",
    "Esta es la hora del orgullo y el poder, garra y colmillo y zarpa. ¡Oh, escucha el llamado! ¡Buena caza a todos los que guardan la Ley de la Selva!",
    "Eran las siete en punto de una tarde muy cálida en las colinas de Seeonee cuando Padre Lobo se despertó de su descanso diurno."
]

# Adjust if needed
if len(segments) != len(translated_segments):
    print(f"WARNING: Adjusting translations from {len(translated_segments)} to {len(segments)}")
    while len(translated_segments) < len(segments):
        translated_segments.append(f"Translation {len(translated_segments) + 1}")
    translated_segments = translated_segments[:len(segments)]

# Create bilingual
bilingual_docs = create_bilingual_documents(
    original_segments=segments,
    translated_segments=translated_segments,
    reconstruction_maps=reconstruction_maps,
    spine_docs=spine_docs,
    source_lang="en",
    target_lang="es"
)

# Create original book
original_book = epub.EpubBook()
original_book.set_identifier('test-bilingual-123')
original_book.set_title('The Jungle Book')
original_book.set_language('en')
original_book.add_author('Rudyard Kipling')

# Generate EPUB
output_path = '/Users/kayvangharbi/PycharmProjects/BookTranslator/apps/api/test_bilingual_for_inspection.epub'

processor = EPUBProcessor()
success = processor.write_bilingual_epub(
    original_book=original_book,
    bilingual_docs=bilingual_docs,
    source_lang='en',
    target_lang='es',
    output_path=output_path
)

if success:
    print(f"\n✅ EPUB created: {output_path}")
    print("\nOpening in default EPUB reader...")
else:
    print("\n❌ Failed to create EPUB")
