import asyncio
import httpx
from typing import List, Optional, Dict, Callable
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
        # Groq Developer tier: 1K RPM, 250K TPM - work at 95% safety barrier
        self.max_batch_tokens = min(settings.max_batch_tokens, 950)  # Max 950 tokens per batch (95% of safe limit)
        self.requests_per_minute = 950  # 95% of 1,000 RPM
        self.tokens_per_minute = 237500  # 95% of 250K TPM
        self.retry_limit = settings.retry_limit
    
    async def translate_segments(
        self,
        segments: List[str],
        src_lang: Optional[str],
        tgt_lang: str,
        system_hint: Optional[str] = None,
        glossary: Optional[Dict[str, str]] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[str]:
        """Translate segments using Groq Llama with batching and retries."""
        
        if not segments:
            return []
        
        if system_hint is None:
            system_hint = self.get_default_system_hint(tgt_lang)
        
        # Process in batches to stay within token limits
        batches = self._create_batches(segments)
        translated_batches = []
        
        logger.info(f"Processing {len(segments)} segments in {len(batches)} batches")
        
        for i, batch in enumerate(batches):
            logger.info(f"Translating batch {i+1}/{len(batches)} with {len(batch)} segments")

            # Add delay between batches to respect Groq rate limits
            # 950 safe RPM = 1 request every 0.063 seconds = 15.8 RPS
            # Safe approach: 1 request every 0.065 seconds = 15.4 RPS = 924 RPM (within 95% limit)
            if i > 0:
                await asyncio.sleep(0.065)  # 65ms delay = max 15.4 requests/second = 924 RPM

            translated_batch = await self._translate_batch_with_retry(
                batch, src_lang, tgt_lang, system_hint
            )
            translated_batches.extend(translated_batch)

            logger.info(f"Batch {i+1} completed: {len(translated_batch)} translations")

            # Report progress after each batch
            if progress_callback:
                progress_callback(i + 1, len(batches))
        
        logger.info(f"Translated {len(segments)} segments → {len(translated_batches)} results via Groq")
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
                
                # Handle rate limits with longer delays (Groq is strict)
                if "rate limit" in error_msg.lower() or "429" in error_msg:
                    wait_time = (2 ** attempt) * 5  # 5s, 10s, 20s for rate limits
                else:
                    wait_time = 2 ** attempt  # 1s, 2s, 4s for other errors
                
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
        
        # Use numbered segments for better parsing
        separator = "\n---SEGMENT---\n"
        
        # Number each segment for better tracking
        numbered_segments = []
        for i, segment in enumerate(batch, 1):
            numbered_segments.append(f"[{i}] {segment}")
        
        combined_text = separator.join(numbered_segments)
        
        # Create more specific instructions for segment preservation
        user_prompt = f"""Translate the following {len(batch)} text segments to {tgt_lang}.
IMPORTANT: Keep the exact same number of segments and preserve the [number] markers.

{combined_text}

Return exactly {len(batch)} translated segments, each starting with its [number] marker."""

        messages = [
            {"role": "system", "content": system_hint},
            {"role": "user", "content": user_prompt}
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
            
            # Split back into segments and clean up
            translated_segments = translated_text.split(separator)
            
            # Clean up numbered markers
            cleaned_segments = []
            for segment in translated_segments:
                # Remove [number] markers
                cleaned = segment.strip()
                if cleaned.startswith('[') and '] ' in cleaned:
                    cleaned = cleaned.split('] ', 1)[1] if '] ' in cleaned else cleaned
                cleaned_segments.append(cleaned.strip())
            
            # Validate segment count matches
            if len(cleaned_segments) != len(batch):
                logger.warning(
                    f"Segment count mismatch: input {len(batch)}, output {len(cleaned_segments)}"
                )
                
                # Try to fix by falling back to individual translation
                if len(cleaned_segments) == 1 and len(batch) > 1:
                    logger.info(f"Attempting individual segment translation for batch of {len(batch)}")
                    return await self._translate_segments_individually(batch, src_lang, tgt_lang, system_hint)
                
                # Pad or truncate to match input length
                while len(cleaned_segments) < len(batch):
                    idx = len(cleaned_segments)
                    fallback = batch[idx] if idx < len(batch) else ""
                    cleaned_segments.append(fallback)
                    logger.warning(f"Padded missing segment {idx+1} with original text")
                
                cleaned_segments = cleaned_segments[:len(batch)]
            
            return cleaned_segments
    
    async def _translate_segments_individually(
        self,
        batch: List[str],
        src_lang: Optional[str],
        tgt_lang: str,
        system_hint: str
    ) -> List[str]:
        """Fallback: translate each segment individually."""
        
        logger.info(f"Translating {len(batch)} segments individually")
        translated = []
        
        for i, segment in enumerate(batch):
            try:
                # Add delay between individual requests (Groq: 600 safe RPM = 0.1s minimum)
                if i > 0:
                    await asyncio.sleep(0.15)  # 150ms delay for individual fallback requests
                
                messages = [
                    {"role": "system", "content": system_hint},
                    {"role": "user", "content": f"Translate to {tgt_lang}: {segment}"}
                ]
                
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.1,
                    "max_tokens": len(segment) * 2,
                }
                
                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        json=payload,
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json"
                        }
                    )
                    
                    if response.status_code == 429:
                        logger.warning(f"Rate limited on segment {i+1}, waiting 10s")
                        await asyncio.sleep(10)  # Wait for rate limits
                        # Retry once
                        response = await client.post(
                            f"{self.base_url}/chat/completions",
                            json=payload,
                            headers={
                                "Authorization": f"Bearer {self.api_key}",
                                "Content-Type": "application/json"
                            }
                        )
                    
                    response.raise_for_status()
                    result = response.json()
                    
                    if "choices" in result and result["choices"]:
                        translated_text = result["choices"][0]["message"]["content"].strip()
                        translated.append(translated_text)
                    else:
                        logger.warning(f"No translation for segment {i+1}, using original")
                        translated.append(segment)
                        
            except Exception as e:
                logger.warning(f"Failed to translate segment {i+1}: {e}, using original")
                translated.append(segment)
        
        logger.info(f"Individual translation completed: {len(translated)} segments")
        return translated