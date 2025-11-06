"""Centralized model configuration for all LLM providers.

This module is the single source of truth for:
- Available models per provider
- Default models for each provider
- Pricing information for cost tracking
- Model capabilities and limitations

All parts of the application should import model information from here.
"""

from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class ModelPricing:
    """Pricing information for a model."""
    input_cost_per_1m: float  # Cost per 1M input tokens in USD
    output_cost_per_1m: float  # Cost per 1M output tokens in USD


@dataclass
class ModelConfig:
    """Configuration for a specific model."""
    name: str
    display_name: str
    pricing: ModelPricing
    max_tokens: Optional[int] = None  # Maximum output tokens
    context_window: Optional[int] = None  # Maximum context window


# =============================================================================
# GROQ MODELS
# =============================================================================

GROQ_MODELS = {
    "llama-3.1-8b-instant": ModelConfig(
        name="llama-3.1-8b-instant",
        display_name="Llama 3.1 8B Instant",
        pricing=ModelPricing(
            input_cost_per_1m=0.05,   # $0.05 per 1M input tokens
            output_cost_per_1m=0.08,  # $0.08 per 1M output tokens
        ),
        max_tokens=8192,
        context_window=131072,  # 128K context
    ),
    "llama-3.1-70b-versatile": ModelConfig(
        name="llama-3.1-70b-versatile",
        display_name="Llama 3.1 70B Versatile",
        pricing=ModelPricing(
            input_cost_per_1m=0.59,   # $0.59 per 1M input tokens
            output_cost_per_1m=0.79,  # $0.79 per 1M output tokens
        ),
        max_tokens=8192,
        context_window=131072,  # 128K context
    ),
}

# Default Groq model for production use
DEFAULT_GROQ_MODEL = "llama-3.1-8b-instant"


# =============================================================================
# GEMINI MODELS
# =============================================================================

GEMINI_MODELS = {
    "gemini-2.0-flash-exp": ModelConfig(
        name="gemini-2.0-flash-exp",
        display_name="Gemini 2.0 Flash (Experimental)",
        pricing=ModelPricing(
            input_cost_per_1m=0.00,   # FREE during preview
            output_cost_per_1m=0.00,  # FREE during preview
        ),
        max_tokens=8192,
        context_window=1000000,  # 1M context
    ),
    "gemini-2.5-flash-lite": ModelConfig(
        name="gemini-2.5-flash-lite",
        display_name="Gemini 2.5 Flash Lite",
        pricing=ModelPricing(
            input_cost_per_1m=0.00,   # FREE tier available
            output_cost_per_1m=0.00,  # FREE tier available
        ),
        max_tokens=8192,
        context_window=1000000,  # 1M context
    ),
    "gemini-1.5-flash": ModelConfig(
        name="gemini-1.5-flash",
        display_name="Gemini 1.5 Flash",
        pricing=ModelPricing(
            input_cost_per_1m=0.075,  # $0.075 per 1M input tokens
            output_cost_per_1m=0.30,  # $0.30 per 1M output tokens
        ),
        max_tokens=8192,
        context_window=1000000,  # 1M context
    ),
    "gemini-1.5-pro": ModelConfig(
        name="gemini-1.5-pro",
        display_name="Gemini 1.5 Pro",
        pricing=ModelPricing(
            input_cost_per_1m=1.25,   # $1.25 per 1M input tokens
            output_cost_per_1m=5.00,  # $5.00 per 1M output tokens
        ),
        max_tokens=8192,
        context_window=2000000,  # 2M context
    ),
}

# Default Gemini model for production use
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash-lite"


# =============================================================================
# PROVIDER CONFIGURATION
# =============================================================================

ALL_MODELS = {
    "groq": GROQ_MODELS,
    "gemini": GEMINI_MODELS,
}

DEFAULT_MODELS = {
    "groq": DEFAULT_GROQ_MODEL,
    "gemini": DEFAULT_GEMINI_MODEL,
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_model_config(provider: str, model_name: str) -> Optional[ModelConfig]:
    """Get configuration for a specific model.

    Args:
        provider: Provider name ('groq' or 'gemini')
        model_name: Model name

    Returns:
        ModelConfig if found, None otherwise
    """
    provider_models = ALL_MODELS.get(provider.lower(), {})
    return provider_models.get(model_name)


def get_default_model(provider: str) -> str:
    """Get the default model name for a provider.

    Args:
        provider: Provider name ('groq' or 'gemini')

    Returns:
        Default model name for the provider
    """
    return DEFAULT_MODELS.get(provider.lower(), DEFAULT_GEMINI_MODEL)


def get_model_pricing(provider: str, model_name: str) -> Optional[ModelPricing]:
    """Get pricing information for a specific model.

    Args:
        provider: Provider name ('groq' or 'gemini')
        model_name: Model name

    Returns:
        ModelPricing if found, None otherwise
    """
    config = get_model_config(provider, model_name)
    return config.pricing if config else None


def estimate_cost(
    provider: str,
    model_name: str,
    input_tokens: int,
    output_tokens: int
) -> float:
    """Estimate cost for a model with given token counts.

    Args:
        provider: Provider name
        model_name: Model name
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens

    Returns:
        Estimated cost in USD
    """
    pricing = get_model_pricing(provider, model_name)

    if not pricing:
        return 0.0

    input_cost = (input_tokens / 1_000_000) * pricing.input_cost_per_1m
    output_cost = (output_tokens / 1_000_000) * pricing.output_cost_per_1m

    return input_cost + output_cost
