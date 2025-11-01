from typing import List, Dict, Tuple
from bs4 import BeautifulSoup, NavigableString, Tag

from app.logger import get_logger

logger = get_logger(__name__)


class HTMLSegmenter:
    """DOM-aware HTML segmentation that preserves structure."""
    
    def __init__(self):
        # Tags that should not be translated (preserve content)
        self.no_translate_tags = {'pre', 'code', 'table', 'script', 'style', 'svg', 'image', 'img'}
        
        # Block-level tags that define segment boundaries
        self.block_tags = {
            'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
            'div', 'section', 'article', 'blockquote', 'li'
        }
    
    def segment_documents(self, docs: List[Dict]) -> Tuple[List[str], List[Dict]]:
        """Segment multiple HTML documents into translatable text segments.
        
        Returns:
            tuple: (segments, reconstruction_maps)
        """
        all_segments = []
        reconstruction_maps = []
        
        for doc_idx, doc in enumerate(docs):
            segments, doc_map = self.segment_html(doc['content'], doc_idx)
            all_segments.extend(segments)
            reconstruction_maps.append({
                'doc_idx': doc_idx,
                'doc_id': doc['id'],
                'doc_href': doc['href'],
                'doc_title': doc['title'],
                'segment_map': doc_map,
                'segment_start': len(all_segments) - len(segments),
                'segment_count': len(segments)
            })
        
        logger.info(f"Segmented {len(docs)} documents into {len(all_segments)} segments")
        return all_segments, reconstruction_maps
    
    def segment_html(self, html_content: str, doc_idx: int) -> Tuple[List[str], Dict]:
        """Segment single HTML document into translatable segments."""
        
        try:
            soup = BeautifulSoup(html_content, 'xml')
            segments = []
            segment_map = {}
            
            # Find all text-containing elements
            for idx, element in enumerate(soup.find_all(string=True)):
                if isinstance(element, NavigableString) and element.strip():
                    parent = element.parent
                    
                    # Skip non-translatable content
                    if self._should_skip_translation(parent):
                        continue
                    
                    text = element.strip()
                    # More permissive: include any meaningful text (3+ chars)
                    # Skip HTML artifacts and pure numbers
                    if (len(text) >= 3 and 
                        not text.isdigit() and 
                        text.lower() not in ['html', 'head', 'body', 'div', 'span']):  # Skip HTML tag names
                        segment_id = f"doc_{doc_idx}_seg_{len(segments)}"
                        segments.append(text)
                        
                        # Store reconstruction info
                        segment_map[segment_id] = {
                            'original_text': text,
                            'element_idx': idx,
                            'parent_tag': parent.name if parent else None,
                            'segment_idx': len(segments) - 1
                        }
            
            logger.info(f"Extracted {len(segments)} segments from document {doc_idx}")
            return segments, segment_map
            
        except Exception as e:
            logger.error(f"Failed to segment HTML: {e}")
            return [], {}
    
    def _should_skip_translation(self, element: Tag) -> bool:
        """Check if element content should be skipped for translation."""
        if not element:
            return True
        
        # Check if element or any parent is in no-translate tags
        current = element
        while current:
            if hasattr(current, 'name') and current.name in self.no_translate_tags:
                return True
            current = current.parent if hasattr(current, 'parent') else None
        
        return False
    
    def reconstruct_documents(
        self, 
        translated_segments: List[str],
        reconstruction_maps: List[Dict],
        original_docs: List[Dict]
    ) -> List[Dict]:
        """Reconstruct HTML documents with translated segments."""
        
        reconstructed_docs = []
        
        for doc_map in reconstruction_maps:
            doc_idx = doc_map['doc_idx']
            original_doc = original_docs[doc_idx]
            segment_start = doc_map['segment_start']
            segment_count = doc_map['segment_count']
            
            # Get translated segments for this document
            doc_translated_segments = translated_segments[
                segment_start:segment_start + segment_count
            ]
            
            # Reconstruct HTML
            reconstructed_content = self._reconstruct_html(
                original_doc['content'],
                doc_translated_segments,
                doc_map['segment_map']
            )
            
            reconstructed_docs.append({
                'id': doc_map['doc_id'],
                'href': doc_map['doc_href'],
                'title': doc_map['doc_title'],
                'content': reconstructed_content
            })
        
        logger.info(f"Reconstructed {len(reconstructed_docs)} documents")
        return reconstructed_docs
    
    def _reconstruct_html(
        self, 
        original_html: str, 
        translated_segments: List[str],
        segment_map: Dict
    ) -> str:
        """Reconstruct HTML with translated segments."""
        
        try:
            soup = BeautifulSoup(original_html, 'xml')
            segment_idx = 0
            
            # Replace text content with translations
            for element in soup.find_all(string=True):
                if isinstance(element, NavigableString) and element.strip():
                    parent = element.parent
                    
                    if self._should_skip_translation(parent):
                        continue
                    
                    text = element.strip()
                    # Use same criteria as segmentation to maintain alignment
                    if (len(text) >= 3 and 
                        not text.isdigit() and 
                        text.lower() not in ['html', 'head', 'body', 'div', 'span'] and 
                        segment_idx < len(translated_segments)):
                        # Replace with translated text
                        element.replace_with(translated_segments[segment_idx])
                        segment_idx += 1
            
            return str(soup)
            
        except Exception as e:
            logger.error(f"Failed to reconstruct HTML: {e}")
            return original_html