import asyncio
import httpx
from typing import List, Optional, Dict
from app.providers.base import TranslationProvider
from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)


class GeminiFlashProvider(TranslationProvider):
    """Gemini 2.5 Flash-Lite translation provider."""
    
    name = "gemini"
    
    def __init__(self, api_key: str, model: str):
        super().__init__(api_key, model)
        self.base_url = "https://generativelanguage.googleapis.com/v1/models"
        self.max_batch_tokens = settings.max_batch_tokens
        self.retry_limit = settings.retry_limit
        # Gemini 2.5 Flash-Lite Tier 1: 4,000 RPM, 4M TPM (work at 80% to avoid errors)
        self.requests_per_minute = 3200  # 80% of 4,000 RPM
        self.tokens_per_minute = 3200000  # 80% of 4M TPM
    
    async def translate_segments(
        self,
        segments: List[str],
        src_lang: Optional[str],
        tgt_lang: str,
        system_hint: Optional[str] = None,
        glossary: Optional[Dict[str, str]] = None,
    ) -> List[str]:
        """Translate segments using Gemini Flash-Lite with batching and retries."""
        
        if not segments:
            return []
        
        if system_hint is None:
            system_hint = self.get_default_system_hint(tgt_lang)
        
        # Process in batches to stay within token limits
        batches = self._create_batches(segments)
        logger.info(f"Processing {len(segments)} segments in {len(batches)} batches")
        translated_batches = []
        
        for i, batch in enumerate(batches):
            logger.info(f"Translating batch {i+1}/{len(batches)} with {len(batch)} segments")
            
            # Rate limiting: 3,200 RPM (80% of limit) = 1 request every 0.01875 seconds
            # Conservative approach: 1 request every 0.02 seconds (50 RPM safe rate)
            if i > 0:
                await asyncio.sleep(0.02)  # 20ms delay = max 50 requests/second = 3,000 RPM
            
            translated_batch = await self._translate_batch_with_retry(
                batch, src_lang, tgt_lang, system_hint
            )
            logger.info(f"Batch {i+1} completed: {len(translated_batch)} translations")
            translated_batches.extend(translated_batch)
        
        logger.info(f"Translated {len(segments)} segments → {len(translated_batches)} results via Gemini")
        return translated_batches
    
    def _create_batches(self, segments: List[str]) -> List[List[str]]:
        """Split segments into batches based on token estimates."""
        batches = []
        current_batch = []
        current_tokens = 0
        
        for segment in segments:
            # Rough token estimate: ~4 chars per token
            segment_tokens = len(segment) // 4
            
            if current_tokens + segment_tokens > self.max_batch_tokens and current_batch:
                batches.append(current_batch)
                current_batch = [segment]
                current_tokens = segment_tokens
            else:
                current_batch.append(segment)
                current_tokens += segment_tokens
        
        if current_batch:
            batches.append(current_batch)
        
        logger.info(f"Created {len(batches)} batches from {len(segments)} segments")
        return batches
    
    async def _translate_batch_with_retry(
        self,
        batch: List[str],
        src_lang: Optional[str],
        tgt_lang: str,
        system_hint: str
    ) -> List[str]:
        """Translate a batch with exponential backoff retry."""
        
        for attempt in range(self.retry_limit):
            try:
                return await self._translate_batch(batch, src_lang, tgt_lang, system_hint)
            except Exception as e:
                error_msg = str(e)
                
                # Handle rate limits with longer delays for Gemini
                if "rate limit" in error_msg.lower() or "429" in error_msg or "quota" in error_msg.lower():
                    wait_time = (2 ** attempt) * 5  # 5s, 10s, 20s for rate limits
                else:
                    wait_time = 2 ** attempt  # 1s, 2s, 4s for other errors
                
                logger.warning(
                    f"Gemini translation attempt {attempt + 1} failed: {e}. "
                    f"Retrying in {wait_time}s..."
                )
                
                if attempt < self.retry_limit - 1:
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Gemini translation failed after {self.retry_limit} attempts")
                    raise
    
    async def _translate_batch(
        self,
        batch: List[str],
        src_lang: Optional[str],
        tgt_lang: str,
        system_hint: str
    ) -> List[str]:
        """Translate a single batch via Gemini API."""
        
        # Combine segments with separators for batch processing
        separator = "\n---SEGMENT---\n"
        combined_text = separator.join(batch)
        
        prompt = f"{system_hint}\n\nTranslate this text:\n{combined_text}"
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": len(combined_text) * 2,  # Conservative estimate
            }
        }
        
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.base_url}/{self.model}:generateContent?key={self.api_key}",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 429:
                raise Exception("Rate limited by Gemini API")
            
            response.raise_for_status()
            result = response.json()
            
            if "candidates" not in result or not result["candidates"]:
                raise Exception("No translation candidates returned")
            
            translated_text = result["candidates"][0]["content"]["parts"][0]["text"]
            
            # Split back into segments
            translated_segments = translated_text.split(separator)
            
            # Validate segment count matches
            if len(translated_segments) != len(batch):
                logger.warning(
                    f"Segment count mismatch: input {len(batch)}, output {len(translated_segments)}"
                )
                # Pad or truncate to match input length
                while len(translated_segments) < len(batch):
                    translated_segments.append(batch[len(translated_segments)])
                translated_segments = translated_segments[:len(batch)]
            
            return translated_segments