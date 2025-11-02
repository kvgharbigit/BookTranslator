"""
Cost analysis for AI provider usage and business metrics
"""

import sys
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any

# Add API to path
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir / "apps" / "api"))

from app.pricing import calculate_provider_cost_cents, calculate_price_cents

logger = logging.getLogger(__name__)


@dataclass
class CostAnalysis:
    """Comprehensive cost analysis data."""
    
    tokens_used: int
    provider_name: str
    provider_cost_cents: int
    provider_cost_usd: float
    user_price_cents: int
    user_price_usd: float
    profit_cents: int
    profit_usd: float
    profit_margin_pct: float
    cost_per_million_tokens: float


class CostAnalyzer:
    """Handles cost analysis and provider comparison metrics."""
    
    def __init__(self):
        pass
    
    def calculate_comprehensive_cost(
        self,
        tokens_used: int,
        provider: str
    ) -> CostAnalysis:
        """Calculate all cost metrics including margins and business data."""
        
        # Calculate provider cost
        provider_cost_cents = calculate_provider_cost_cents(tokens_used, provider)
        provider_cost_usd = provider_cost_cents / 100
        
        # Calculate what user pays
        user_price_cents = calculate_price_cents(tokens_used, provider)
        user_price_usd = user_price_cents / 100
        
        # Calculate profit metrics
        profit_cents = user_price_cents - provider_cost_cents
        profit_usd = profit_cents / 100
        
        # Calculate profit margin
        profit_margin_pct = (profit_usd / user_price_usd * 100) if user_price_usd > 0 else 0
        
        # Calculate cost per million tokens
        cost_per_million_tokens = (provider_cost_usd / tokens_used * 1_000_000) if tokens_used > 0 else 0
        
        return CostAnalysis(
            tokens_used=tokens_used,
            provider_name=provider,
            provider_cost_cents=provider_cost_cents,
            provider_cost_usd=provider_cost_usd,
            user_price_cents=user_price_cents,
            user_price_usd=user_price_usd,
            profit_cents=profit_cents,
            profit_usd=profit_usd,
            profit_margin_pct=profit_margin_pct,
            cost_per_million_tokens=cost_per_million_tokens
        )
    
    def format_cost_summary(self, analysis: CostAnalysis) -> str:
        """Format cost analysis as readable summary."""
        
        return f"""💰 Cost Analysis:
   Total tokens: {analysis.tokens_used:,}
   Provider cost: ${analysis.provider_cost_usd:.4f} USD ({analysis.provider_cost_cents} cents)
   User pays: ${analysis.user_price_usd:.2f} USD ({analysis.user_price_cents} cents)
   Profit: ${analysis.profit_usd:.4f} USD ({analysis.profit_cents} cents)
   Profit margin: {analysis.profit_margin_pct:.1f}%
   Provider rate: ${analysis.cost_per_million_tokens:.2f} per 1M tokens"""
    
    def compare_costs(
        self,
        analyses: Dict[str, CostAnalysis]
    ) -> Dict[str, Any]:
        """Compare costs between multiple providers."""
        
        comparison = {
            "summary": {},
            "differences": {},
            "best_value": None,
            "fastest": None
        }
        
        # Create summary table
        for provider, analysis in analyses.items():
            comparison["summary"][provider] = {
                "tokens": analysis.tokens_used,
                "provider_cost": f"${analysis.provider_cost_usd:.4f}",
                "user_pays": f"${analysis.user_price_usd:.2f}",
                "profit": f"${analysis.profit_usd:.4f}",
                "margin": f"{analysis.profit_margin_pct:.1f}%"
            }
        
        # Calculate differences if we have exactly 2 providers
        if len(analyses) == 2:
            providers = list(analyses.keys())
            analysis1, analysis2 = analyses[providers[0]], analyses[providers[1]]
            
            comparison["differences"] = {
                "tokens": analysis2.tokens_used - analysis1.tokens_used,
                "provider_cost": analysis2.provider_cost_usd - analysis1.provider_cost_usd,
                "user_pays": analysis2.user_price_usd - analysis1.user_price_usd,
                "profit": analysis2.profit_usd - analysis1.profit_usd,
                "margin": analysis2.profit_margin_pct - analysis1.profit_margin_pct
            }
        
        # Find best value (lowest user cost)
        if analyses:
            best_provider = min(analyses.keys(), 
                              key=lambda p: analyses[p].user_price_usd)
            comparison["best_value"] = best_provider
        
        return comparison
    
    def format_comparison_table(
        self,
        analyses: Dict[str, CostAnalysis],
        include_timing: bool = False,
        timing_data: Dict[str, float] = None
    ) -> str:
        """Format a comparison table for multiple providers."""
        
        if not analyses:
            return "No cost data available for comparison."
        
        # Header
        lines = [
            "💰 Cost Analysis & Business Metrics:",
            f"  {'Metric':<25} {'':>15} {'':>15} {'Difference':>15}",
            f"  {'-'*25} {'-'*15} {'-'*15} {'-'*15}"
        ]
        
        # Get provider names
        providers = list(analyses.keys())
        if len(providers) >= 2:
            provider1, provider2 = providers[0], providers[1]
            analysis1, analysis2 = analyses[provider1], analyses[provider2]
            
            # Calculate differences
            token_diff = analysis2.tokens_used - analysis1.tokens_used
            cost_diff = analysis2.provider_cost_usd - analysis1.provider_cost_usd
            price_diff = analysis2.user_price_usd - analysis1.user_price_usd
            profit_diff = analysis2.profit_usd - analysis1.profit_usd
            margin_diff = analysis2.profit_margin_pct - analysis1.profit_margin_pct
            
            # Format rows
            lines.extend([
                f"  {'Tokens Used':<25} {analysis1.tokens_used:>15,} {analysis2.tokens_used:>15,} {token_diff:>15,}",
                f"  {'Provider Cost':<25} ${analysis1.provider_cost_usd:>14.4f} ${analysis2.provider_cost_usd:>14.4f} ${cost_diff:>14.4f}",
                f"  {'User Pays':<25} ${analysis1.user_price_usd:>14.2f} ${analysis2.user_price_usd:>14.2f} ${price_diff:>14.2f}",
                f"  {'Profit':<25} ${analysis1.profit_usd:>14.4f} ${analysis2.profit_usd:>14.4f} ${profit_diff:>14.4f}",
                f"  {'Profit Margin':<25} {analysis1.profit_margin_pct:>14.1f}% {analysis2.profit_margin_pct:>14.1f}% {margin_diff:>14.1f}%"
            ])
            
            # Add timing if provided
            if include_timing and timing_data:
                time1 = timing_data.get(provider1, 0)
                time2 = timing_data.get(provider2, 0)
                time_diff = time2 - time1
                
                lines.extend([
                    "",
                    "⚡ Performance Comparison:",
                    f"  {provider1.title():>15}: {time1:.1f}s translation, timing not fully tracked",
                    f"  {provider2.title():>15}: {time2:.1f}s translation, timing not fully tracked"
                ])
        
        return "\n".join(lines)