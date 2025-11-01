import math
from typing import Optional

from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)


def estimate_tokens_from_size(size_bytes: int) -> int:
    """Estimate token count from file size.
    
    Rough heuristic: 1 token ≈ 4 characters ≈ 4 bytes for most languages.
    """
    tokens_est = size_bytes // 4
    logger.info(f"Estimated {tokens_est} tokens from {size_bytes} bytes")
    return tokens_est


def calculate_price_cents(tokens_est: int) -> int:
    """Calculate price in cents from estimated tokens.
    
    Uses single business knob: PRICE_CENTS_PER_MILLION_TOKENS
    Enforces minimum price: MIN_PRICE_CENTS
    """
    # Calculate base price from tokens
    price_from_tokens = math.ceil(
        tokens_est / 1_000_000 * settings.price_cents_per_million_tokens
    )
    
    # Apply minimum price (for Stripe micro-payment requirements)
    final_price = max(settings.min_price_cents, price_from_tokens)
    
    logger.info(
        f"Price calculation: {tokens_est} tokens -> "
        f"${price_from_tokens/100:.2f} -> final: ${final_price/100:.2f}"
    )
    
    return final_price


def estimate_price_from_size(size_bytes: int) -> tuple[int, int]:
    """Estimate both tokens and price from file size.
    
    Returns:
        tuple: (tokens_estimated, price_cents)
    """
    tokens_est = estimate_tokens_from_size(size_bytes)
    price_cents = calculate_price_cents(tokens_est)
    
    return tokens_est, price_cents


def validate_price_match(
    size_bytes: int, 
    expected_price_cents: int, 
    tolerance_cents: int = 10
) -> bool:
    """Validate that expected price matches server-side calculation.
    
    Used to prevent client-side price tampering.
    """
    _, calculated_price = estimate_price_from_size(size_bytes)
    
    price_diff = abs(calculated_price - expected_price_cents)
    is_valid = price_diff <= tolerance_cents
    
    if not is_valid:
        logger.warning(
            f"Price validation failed: expected {expected_price_cents}, "
            f"calculated {calculated_price}, diff {price_diff}"
        )
    
    return is_valid


def calculate_provider_cost_cents(tokens_actual: int, provider: str) -> int:
    """Calculate actual provider cost in cents.
    
    Used for margin tracking and cost monitoring.
    """
    # Rough cost estimates (update based on actual provider pricing)
    cost_per_million_tokens = {
        "gemini": 15,  # ~$0.15 per 1M tokens for Flash-Lite
        "groq": 5,     # ~$0.05 per 1M tokens for Llama-3.1-8b
    }
    
    rate = cost_per_million_tokens.get(provider, 15)  # Default to higher cost
    cost_cents = math.ceil(tokens_actual / 1_000_000 * rate)
    
    logger.info(f"Provider cost: {tokens_actual} tokens via {provider} = ${cost_cents/100:.2f}")
    
    return cost_cents