import math
import zipfile
import xml.etree.ElementTree as ET
from typing import Optional
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import re

from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)


def extract_text_from_epub(file_path: str) -> str:
    """Extract text content from EPUB file, ignoring images and metadata."""
    try:
        with zipfile.ZipFile(file_path, 'r') as epub:
            text_content = []
            
            # Find all HTML/XHTML files in the EPUB
            for file_info in epub.filelist:
                if file_info.filename.endswith(('.html', '.xhtml', '.htm')):
                    try:
                        content = epub.read(file_info.filename).decode('utf-8', errors='ignore')
                        # Parse HTML and extract text
                        # Remove HTML tags but keep text content
                        text = re.sub(r'<[^>]+>', ' ', content)
                        # Clean up whitespace
                        text = re.sub(r'\s+', ' ', text).strip()
                        if text:
                            text_content.append(text)
                    except Exception as e:
                        logger.debug(f"Could not extract text from {file_info.filename}: {e}")
                        continue
            
            full_text = ' '.join(text_content)
            logger.info(f"Extracted {len(full_text)} characters of text from EPUB")
            return full_text
            
    except Exception as e:
        logger.warning(f"Could not extract text from EPUB: {e}")
        return ""


def estimate_tokens_from_size(size_bytes: int) -> int:
    """Estimate token count from file size.
    
    Rough heuristic: 1 token ≈ 4 characters ≈ 4 bytes for most languages.
    This is a fallback for non-EPUB files.
    """
    tokens_est = size_bytes // 4
    logger.info(f"Estimated {tokens_est} tokens from {size_bytes} bytes (fallback method)")
    return tokens_est


def estimate_tokens_from_epub(file_path: str) -> int:
    """Estimate token count from EPUB file by extracting text content only."""
    text_content = extract_text_from_epub(file_path)
    if not text_content:
        logger.warning("No text extracted from EPUB, using fallback estimation")
        return estimate_tokens_from_size(Path(file_path).stat().st_size)
    
    # Estimate tokens: ~4 characters per token for most languages
    char_count = len(text_content)
    tokens_est = char_count // 4
    
    logger.info(f"EPUB text analysis: {char_count:,} chars → {tokens_est:,} tokens")
    return tokens_est


def calculate_price_cents(tokens_est: int, provider: str = "gemini") -> int:
    """Calculate price using 5-tier pricing model with optimized margins.

    Tiers (aligned with word ranges, using 1 token = 0.75 words):
    - Short Book (0-53K tokens / 0-40K words): $0.99
    - Standard Novel (53K-160K tokens / 40K-120K words): $1.49
    - Long Novel (160K-267K tokens / 120K-200K words): $2.49
    - Epic Novel (267K-467K tokens / 200K-350K words): $2.99
    - Grand Epic (467K-1M tokens / 350K-750K words): $3.99
    - Files over 1M tokens (~750K+ words): Rejected (too large for profitable processing)

    Ensures 80-90% margins even with AI and PayPal costs.
    """
    # Check maximum token limit first
    if tokens_est > settings.max_file_tokens:
        logger.warning(f"File rejected: {tokens_est:,} tokens exceeds {settings.max_file_tokens:,} token limit")
        words_est = tokens_est * 0.75  # ~0.75 words per token
        max_words = settings.max_file_tokens * 0.75
        raise ValueError(f"📚 Book too large: Your file has approximately {words_est:,.0f} words, but our maximum is {max_words:,.0f} words (~750 pages). Please try a shorter book or split this into multiple files.")

    # 5-tier pricing structure aligned with word ranges
    # Word ranges: 0-40K, 40-120K, 120-200K, 200-350K, 350-750K
    # Token equivalents: 0-53K, 53-160K, 160-267K, 267-467K, 467-1M
    if tokens_est < 53333:  # ~40K words
        price_dollars = 0.99
        tier = "Short Book"
    elif tokens_est < 160000:  # ~120K words
        price_dollars = 1.49
        tier = "Standard Novel"
    elif tokens_est < 266667:  # ~200K words
        price_dollars = 2.19
        tier = "Long Novel"
    elif tokens_est < 466667:  # ~350K words
        price_dollars = 2.99
        tier = "Epic Novel"
    else:  # 467K-1M tokens (~350K-750K words, capped at 1M tokens)
        price_dollars = 3.99
        tier = "Grand Epic"

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


def estimate_price_from_file(file_path: str, provider: str = "gemini") -> tuple[int, int]:
    """Estimate both tokens and price from actual file, with EPUB text extraction.
    
    Returns:
        tuple: (tokens_estimated, price_cents)
    """
    if file_path.lower().endswith('.epub'):
        tokens_est = estimate_tokens_from_epub(file_path)
    else:
        file_size = Path(file_path).stat().st_size
        tokens_est = estimate_tokens_from_size(file_size)
    
    price_cents = calculate_price_cents(tokens_est, provider)
    
    return tokens_est, price_cents


def validate_price_match(
    size_bytes: int,
    expected_price_cents: int,
    provider: str = "gemini",
    tolerance_cents: int = 10,
    output_format: str = "translation"
) -> bool:
    """Validate that expected price matches server-side calculation.

    Used to prevent client-side price tampering.
    """
    tokens_est = estimate_tokens_from_size(size_bytes)
    calculated_price = calculate_price_with_format(tokens_est, output_format, provider)

    price_diff = abs(calculated_price - expected_price_cents)
    is_valid = price_diff <= tolerance_cents

    if not is_valid:
        logger.warning(
            f"Price validation failed: expected {expected_price_cents}, "
            f"calculated {calculated_price}, diff {price_diff}"
        )

    return is_valid


def validate_price_match_from_file(
    file_path: str,
    expected_price_cents: int,
    provider: str = "gemini",
    tolerance_cents: int = 10,
    output_format: str = "translation"
) -> bool:
    """Validate that expected price matches server-side calculation using file analysis.

    Used to prevent client-side price tampering for EPUB files.
    """
    if file_path.lower().endswith('.epub'):
        tokens_est = estimate_tokens_from_epub(file_path)
    else:
        file_size = Path(file_path).stat().st_size
        tokens_est = estimate_tokens_from_size(file_size)

    calculated_price = calculate_price_with_format(tokens_est, output_format, provider)

    price_diff = abs(calculated_price - expected_price_cents)
    is_valid = price_diff <= tolerance_cents

    if not is_valid:
        logger.warning(
            f"Price validation failed (file-based): expected {expected_price_cents}, "
            f"calculated {calculated_price}, diff {price_diff}"
        )

    return is_valid


def calculate_provider_cost_cents(tokens_actual: int, provider: str) -> int:
    """Calculate actual provider cost in cents for database storage.
    
    Used for margin tracking and cost monitoring.
    Returns integer cents to avoid SQLite Decimal issues.
    """
    # Actual provider costs in dollars per 1M tokens
    # Translation workloads are typically ~20% input, ~80% output tokens
    cost_per_million_tokens = {
        "gemini": Decimal("0.34"),    # $0.34 per 1M tokens for Gemini 2.5 Flash-Lite (20% input $0.10 + 80% output $0.40)
        "groq": Decimal("0.074"),     # $0.074 per 1M tokens for Llama-3.1-8b Instant (20% input $0.05 + 80% output $0.08)
    }
    
    rate = cost_per_million_tokens.get(provider, Decimal("0.15"))
    
    # Calculate precise cost in dollars
    cost_dollars = Decimal(str(tokens_actual)) / Decimal("1000000") * rate
    
    # Convert to cents for database storage (SQLite-compatible)
    cost_cents = int(cost_dollars * 100)
    
    logger.info(f"Provider cost: {tokens_actual} tokens via {provider} = ${cost_dollars:.6f} = {cost_cents} cents")
    
    return cost_cents


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
    """Return PayPal as the only payment provider.
    
    PayPal micropayments: 5% + $0.05 fee structure
    
    Args:
        amount_cents: Payment amount in cents
        
    Returns:
        str: Always "paypal"
    """
    # Calculate PayPal fee for logging
    paypal_fee_cents = int(amount_cents * 0.05 + 5)  # 5% + 5 cents
    
    logger.info(f"Using PayPal for ${amount_cents/100:.2f}: PayPal fee ${paypal_fee_cents/100:.2f}")
    
    return "paypal"


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


def calculate_price_with_format(
    tokens_est: int,
    output_format: str = "translation",
    provider: str = "gemini"
) -> int:
    """Calculate price including bilingual format surcharge.

    Output format pricing:
    - "translation": Base price only (standard translation)
    - "bilingual": Base price + $1.00 (bilingual reader only)
    - "both": Base price + $1.50 (both standard + bilingual)

    Args:
        tokens_est: Estimated token count
        output_format: One of "translation", "bilingual", "both"
        provider: AI provider name

    Returns:
        int: Total price in cents
    """
    # Calculate base translation price
    base_price_cents = calculate_price_cents(tokens_est, provider)

    # Add format surcharge
    if output_format == "bilingual":
        surcharge_cents = 100  # $1.00 for bilingual only
        logger.info(f"Applied bilingual surcharge: +$1.00")
    elif output_format == "both":
        surcharge_cents = 150  # $1.50 for both formats
        logger.info(f"Applied both formats surcharge: +$1.50")
    else:  # "translation" or unspecified
        surcharge_cents = 0

    total_price_cents = base_price_cents + surcharge_cents

    logger.info(
        f"Format pricing: base ${base_price_cents/100:.2f} + "
        f"format surcharge ${surcharge_cents/100:.2f} = "
        f"total ${total_price_cents/100:.2f}"
    )

    return total_price_cents