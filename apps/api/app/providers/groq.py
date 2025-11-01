import asyncio
import httpx
from typing import List, Optional, Dict
from app.providers.base import TranslationProvider
from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)


class GroqLlamaProvider(TranslationProvider):
    """Groq Llama-3.x translation provider."""
    
    name = "groq"
    
    def __init__(self, api_key: str, model: str):
        super().__init__(api_key, model)
        self.base_url = "https://api.groq.com/openai/v1"
        self.max_batch_tokens = settings.max_batch_tokens
        self.retry_limit = settings.retry_limit
    
    async def translate_segments(
        self,
        segments: List[str],
        src_lang: Optional[str],
        tgt_lang: str,
        system_hint: Optional[str] = None,
        glossary: Optional[Dict[str, str]] = None,
    ) -> List[str]:
        """Translate segments using Groq Llama with batching and retries."""
        
        if not segments:
            return []
        
        if system_hint is None:
            system_hint = self.get_default_system_hint(tgt_lang)
        
        # Process in batches to stay within token limits
        batches = self._create_batches(segments)
        translated_batches = []
        
        for batch in batches:
            translated_batch = await self._translate_batch_with_retry(
                batch, src_lang, tgt_lang, system_hint
            )
            translated_batches.extend(translated_batch)
        
        logger.info(f"Translated {len(segments)} segments via Groq")
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
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                logger.warning(
                    f"Groq translation attempt {attempt + 1} failed: {e}. "
                    f"Retrying in {wait_time}s..."
                )
                
                if attempt < self.retry_limit - 1:
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Groq translation failed after {self.retry_limit} attempts")
                    raise
    
    async def _translate_batch(
        self,
        batch: List[str],
        src_lang: Optional[str],
        tgt_lang: str,
        system_hint: str
    ) -> List[str]:
        """Translate a single batch via Groq API."""
        
        # Combine segments with separators for batch processing
        separator = "\n---SEGMENT---\n"
        combined_text = separator.join(batch)
        
        messages = [
            {"role": "system", "content": system_hint},
            {"role": "user", "content": f"Translate this text:\n{combined_text}"}
        ]
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": len(combined_text) * 2,  # Conservative estimate
        }
        
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code == 429:
                raise Exception("Rate limited by Groq API")
            
            response.raise_for_status()
            result = response.json()
            
            if "choices" not in result or not result["choices"]:
                raise Exception("No translation choices returned")
            
            translated_text = result["choices"][0]["message"]["content"]
            
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