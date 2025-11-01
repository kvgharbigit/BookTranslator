import math
from typing import Optional
from decimal import Decimal, ROUND_HALF_UP

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


def calculate_price_cents(tokens_est: int, provider: str = "gemini") -> int:
    """Calculate price using 5-tier pricing model with token caps.
    
    Tiers (aligned with word ranges):
    - Short Novel (0-42K tokens / 0-56K words): $0.50
    - Novel (42K-84K tokens / 56K-112K words): $0.75
    - Long Novel (84K-169K tokens / 112K-225K words): $1.00
    - Epic Novel (169K-282K tokens / 225K-375K words): $1.25
    - Epic Series (282K-1M tokens / 375K-750K words): $1.50
    - Files over 1M tokens (~750K+ words): Rejected (too large for profitable processing)
    
    Ensures excellent margins while preventing losses on massive files.
    """
    # Check maximum token limit first
    if tokens_est > settings.max_file_tokens:
        logger.warning(f"File rejected: {tokens_est:,} tokens exceeds {settings.max_file_tokens:,} token limit")
        raise ValueError(f"File too large: {tokens_est:,} tokens. Maximum allowed: {settings.max_file_tokens:,} tokens (~{settings.max_file_tokens//1333:,}K words)")
    
    # 5-tier pricing structure aligned with word ranges
    # Word ranges: 0-56K, 56K-112K, 112K-225K, 225K-375K, 375K-750K
    # Token equivalents: 0-42K, 42K-84K, 84K-169K, 169K-282K, 282K-564K
    if tokens_est < 42000:  # ~56K words
        price_dollars = 0.50
        tier = "Short Novel"
    elif tokens_est < 84000:  # ~112K words
        price_dollars = 0.75
        tier = "Novel"
    elif tokens_est < 169000:  # ~225K words
        price_dollars = 1.00
        tier = "Long Novel"
    elif tokens_est < 282000:  # ~375K words
        price_dollars = 1.25
        tier = "Epic Novel"
    else:  # 282K-750K tokens (~375K-1M words, capped at 1M tokens)
        price_dollars = 1.50
        tier = "Epic Series"
    
    # Convert to cents
    final_price_cents = int(price_dollars * 100)
    
    # Apply minimum price (though tiers should always be above minimum)
    final_price = max(settings.min_price_cents, final_price_cents)
    
    # Calculate provider cost for logging
    provider_cost_dollars = float(calculate_provider_cost_cents(tokens_est, provider))
    
    logger.info(
        f"5-tier pricing: {tokens_est:,} tokens, {provider} -> "
        f"Tier: {tier} (${price_dollars:.2f}), "
        f"Provider cost: ${provider_cost_dollars:.3f}"
    )
    
    return final_price


def estimate_price_from_size(size_bytes: int, provider: str = "gemini") -> tuple[int, int]:
    """Estimate both tokens and price from file size.
    
    Returns:
        tuple: (tokens_estimated, price_cents)
    """
    tokens_est = estimate_tokens_from_size(size_bytes)
    price_cents = calculate_price_cents(tokens_est, provider)
    
    return tokens_est, price_cents


def validate_price_match(
    size_bytes: int, 
    expected_price_cents: int, 
    provider: str = "gemini",
    tolerance_cents: int = 10
) -> bool:
    """Validate that expected price matches server-side calculation.
    
    Used to prevent client-side price tampering.
    """
    _, calculated_price = estimate_price_from_size(size_bytes, provider)
    
    price_diff = abs(calculated_price - expected_price_cents)
    is_valid = price_diff <= tolerance_cents
    
    if not is_valid:
        logger.warning(
            f"Price validation failed: expected {expected_price_cents}, "
            f"calculated {calculated_price}, diff {price_diff}"
        )
    
    return is_valid


def calculate_provider_cost_cents(tokens_actual: int, provider: str) -> Decimal:
    """Calculate actual provider cost with sub-cent precision.
    
    Used for margin tracking and cost monitoring.
    Returns Decimal for precise cost calculations.
    """
    # Actual provider costs in dollars per 1M tokens
    # Translation workloads are typically ~20% input, ~80% output tokens
    cost_per_million_tokens = {
        "gemini": Decimal("0.34"),    # $0.34 per 1M tokens for Gemini 2.5 Flash-Lite (20% input $0.10 + 80% output $0.40)
        "groq": Decimal("0.074"),     # $0.074 per 1M tokens for Llama-3.1-8b Instant (20% input $0.05 + 80% output $0.08)
    }
    
    rate = cost_per_million_tokens.get(provider, Decimal("0.15"))
    
    # Calculate precise cost without rounding
    cost_decimal = Decimal(str(tokens_actual)) / Decimal("1000000") * rate
    
    logger.info(f"Provider cost: {tokens_actual} tokens via {provider} = ${cost_decimal:.6f}")
    
    return cost_decimal


def calculate_provider_cost_display(tokens_actual: int, provider: str) -> str:
    """Calculate provider cost with precise display formatting."""
    cost = calculate_provider_cost_cents(tokens_actual, provider)
    
    # Format for display with appropriate precision
    if cost >= Decimal("1.0"):
        return f"${cost:.2f}"
    elif cost >= Decimal("0.01"):
        return f"${cost:.3f}"
    else:
        return f"${cost:.6f}"


def get_optimal_payment_provider(amount_cents: int) -> str:
    """Determine optimal payment provider based on amount.
    
    PayPal micropayments: 5% + $0.05 fee structure
    Stripe standard: 2.9% + $0.30 fee structure
    
    Break-even point is around $8.00
    
    Args:
        amount_cents: Payment amount in cents
        
    Returns:
        str: "paypal" or "stripe"
    """
    # Calculate fees for both providers
    paypal_fee_cents = int(amount_cents * 0.05 + 5)  # 5% + 5 cents
    stripe_fee_cents = int(amount_cents * 0.029 + 30)  # 2.9% + 30 cents
    
    # Choose provider with lower fees
    if paypal_fee_cents < stripe_fee_cents:
        logger.info(
            f"PayPal optimal for ${amount_cents/100:.2f}: "
            f"PayPal fee ${paypal_fee_cents/100:.2f} vs Stripe ${stripe_fee_cents/100:.2f}"
        )
        return "paypal"
    else:
        logger.info(
            f"Stripe optimal for ${amount_cents/100:.2f}: "
            f"Stripe fee ${stripe_fee_cents/100:.2f} vs PayPal ${paypal_fee_cents/100:.2f}"
        )
        return "stripe"


def calculate_payment_fees(amount_cents: int, provider: str) -> int:
    """Calculate payment processing fees for given provider.
    
    Args:
        amount_cents: Payment amount in cents
        provider: "paypal" or "stripe"
        
    Returns:
        int: Fee amount in cents
    """
    if provider == "paypal":
        # PayPal micropayments: 5% + $0.05
        return int(amount_cents * 0.05 + 5)
    elif provider == "stripe":
        # Stripe standard: 2.9% + $0.30
        return int(amount_cents * 0.029 + 30)
    else:
        logger.warning(f"Unknown payment provider: {provider}")
        return 0