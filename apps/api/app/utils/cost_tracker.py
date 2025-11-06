"""Cost tracking utility for LLM API calls.

This module provides utilities to estimate and track the costs of API calls
to various LLM providers (Groq, Gemini, etc.).

NOTE: All pricing data and model configurations are now centralized in
app.config.models. This module uses that as the single source of truth.
"""

from typing import Optional
from app.logger import get_logger
from app.config.models import estimate_cost as calculate_cost, get_model_pricing

logger = get_logger(__name__)


class CostTracker:
    """Track and estimate costs for LLM API usage.

    Uses centralized model configuration from app.config.models for pricing.
    """

    @classmethod
    def estimate_tokens(cls, text: str) -> int:
        """Estimate token count from text.

        Uses a rough approximation of 4 characters per token.

        Args:
            text: Input text

        Returns:
            Estimated token count
        """
        return max(1, len(text) // 4)

    @classmethod
    def estimate_cost(
        cls,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """Estimate cost for an LLM API call.

        Uses centralized pricing from app.config.models.

        Args:
            provider: Provider name (e.g., 'groq', 'gemini')
            model: Model name (e.g., 'llama-3.1-8b-instant')
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Estimated cost in USD
        """
        cost = calculate_cost(provider, model, input_tokens, output_tokens)

        if cost == 0.0 and get_model_pricing(provider, model) is None:
            logger.warning(f"No pricing data for {provider}/{model}, using $0.00")

        return cost

    @classmethod
    def log_api_call(
        cls,
        provider: str,
        model: str,
        input_text: str,
        output_text: str,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        actual_cost: Optional[float] = None,
        request_id: Optional[str] = None
    ) -> dict:
        """Log an LLM API call with cost estimation.

        Args:
            provider: Provider name
            model: Model name
            input_text: Input text sent to the API
            output_text: Output text received from the API
            input_tokens: Actual input tokens (if available from API response)
            output_tokens: Actual output tokens (if available from API response)
            actual_cost: Actual cost (if available from API response)
            request_id: Optional request ID for tracking

        Returns:
            Dictionary with cost information
        """
        # Use actual tokens if provided, otherwise estimate
        if input_tokens is None:
            input_tokens = cls.estimate_tokens(input_text)
        if output_tokens is None:
            output_tokens = cls.estimate_tokens(output_text)

        # Calculate estimated cost
        estimated_cost = cls.estimate_cost(provider, model, input_tokens, output_tokens)

        # Use actual cost if provided, otherwise use estimate
        cost = actual_cost if actual_cost is not None else estimated_cost

        # Log the information
        log_data = {
            "provider": provider,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "estimated_cost_usd": estimated_cost,
            "actual_cost_usd": actual_cost,
            "cost_usd": cost,
            "request_id": request_id,
        }

        logger.info(
            f"💰 LLM API Call | Provider: {provider} | Model: {model} | "
            f"Tokens: {input_tokens:,} in + {output_tokens:,} out = {input_tokens + output_tokens:,} total | "
            f"Cost: ${cost:.6f} USD"
            + (f" | Request ID: {request_id}" if request_id else "")
        )

        return log_data
