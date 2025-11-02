"""
Provider comparison and performance analysis
"""

import time
import json
import logging
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional
from datetime import datetime

from .cost import CostAnalysis

logger = logging.getLogger(__name__)


@dataclass
class ProviderResult:
    """Complete provider test result data."""
    
    provider_name: str
    success: bool
    translation_time: float
    total_time: float
    tokens_used: int
    provider_used: str
    cost_analysis: CostAnalysis
    outputs_generated: Dict[str, bool]
    file_paths: Dict[str, Optional[str]]
    file_sizes: Dict[str, str]
    error_message: Optional[str] = None


@dataclass
class ComparisonReport:
    """Complete comparison report between providers."""
    
    test_info: Dict[str, Any]
    provider_results: Dict[str, ProviderResult]
    comparison_summary: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    output_status: Dict[str, Any]
    timestamp: str


class ProviderComparator:
    """Handles provider comparison and performance analysis."""
    
    def __init__(self):
        self.results: Dict[str, ProviderResult] = {}
    
    def add_result(self, result: ProviderResult):
        """Add a provider result to the comparison."""
        self.results[result.provider_name] = result
    
    def generate_comparison_summary(self) -> Dict[str, Any]:
        """Generate comprehensive comparison summary."""
        
        if not self.results:
            return {"error": "No results to compare"}
        
        summary = {
            "success_rate": {},
            "performance": {},
            "cost_comparison": {},
            "output_generation": {},
            "recommendations": {}
        }
        
        # Success rate analysis
        for provider, result in self.results.items():
            summary["success_rate"][provider] = "✅ Success" if result.success else "❌ Failed"
        
        # Performance comparison
        for provider, result in self.results.items():
            summary["performance"][provider] = {
                "translation_time": f"{result.translation_time:.1f}s",
                "total_time": f"{result.total_time:.1f}s",
                "tokens_used": result.tokens_used
            }
        
        # Find fastest provider
        if len(self.results) > 1:
            fastest = min(self.results.keys(), 
                         key=lambda p: self.results[p].translation_time)
            summary["performance"]["fastest_provider"] = fastest
        
        # Cost comparison
        for provider, result in self.results.items():
            if result.cost_analysis:
                summary["cost_comparison"][provider] = {
                    "user_cost": f"${result.cost_analysis.user_price_usd:.2f}",
                    "provider_cost": f"${result.cost_analysis.provider_cost_usd:.4f}",
                    "profit_margin": f"{result.cost_analysis.profit_margin_pct:.1f}%"
                }
        
        # Output generation status
        all_formats = ["epub", "pdf", "txt"]
        for format_type in all_formats:
            summary["output_generation"][format_type] = {}
            for provider, result in self.results.items():
                status = "✅" if result.outputs_generated.get(format_type, False) else "❌"
                summary["output_generation"][format_type][provider] = status
        
        # Generate recommendations
        summary["recommendations"] = self._generate_recommendations()
        
        return summary
    
    def _generate_recommendations(self) -> Dict[str, str]:
        """Generate usage recommendations based on results."""
        
        recommendations = {}
        
        if len(self.results) < 2:
            return {"note": "Need at least 2 providers for recommendations"}
        
        # Speed recommendation
        fastest = min(self.results.keys(), 
                     key=lambda p: self.results[p].translation_time)
        slowest = max(self.results.keys(), 
                     key=lambda p: self.results[p].translation_time)
        
        speed_ratio = (self.results[slowest].translation_time / 
                      self.results[fastest].translation_time)
        
        recommendations["speed"] = (
            f"{fastest.title()} is {speed_ratio:.1f}x faster than {slowest.title()}"
        )
        
        # Cost recommendation
        valid_cost_results = {k: v for k, v in self.results.items() if v.cost_analysis is not None}
        if valid_cost_results:
            cheapest = min(valid_cost_results.keys(), 
                          key=lambda p: valid_cost_results[p].cost_analysis.user_price_usd)
        else:
            cheapest = list(self.results.keys())[0] if self.results else "Unknown"
        
        recommendations["cost"] = f"{cheapest.title()} offers the lowest user cost"
        
        # Quality recommendation (based on success rate and output generation)
        quality_scores = {}
        for provider, result in self.results.items():
            score = 0
            if result.success:
                score += 50
            score += sum(result.outputs_generated.values()) * 16.67  # Each format worth ~16.67 points
            quality_scores[provider] = score
        
        best_quality = max(quality_scores.keys(), key=lambda p: quality_scores[p])
        recommendations["quality"] = f"{best_quality.title()} has the highest success rate"
        
        return recommendations
    
    def format_comparison_report(self) -> str:
        """Format a comprehensive comparison report."""
        
        if not self.results:
            return "No results available for comparison."
        
        lines = [
            "📊 PROVIDER COMPARISON SUMMARY",
            "=" * 80
        ]
        
        # Success Rate
        lines.append("Success Rate:")
        for provider, result in self.results.items():
            status = "✅ Success" if result.success else "❌ Failed"
            lines.append(f"  {provider.title():<10} {status}")
        
        lines.append("")
        
        # Performance Comparison
        lines.append("⚡ Performance Comparison:")
        for provider, result in self.results.items():
            lines.append(
                f"  {provider.title():<10} {result.translation_time:.1f}s translation, "
                f"{result.total_time:.1f}s total"
            )
        
        lines.append("")
        
        # Output Generation
        lines.append("📄 Output Generation:")
        formats = ["EPUB", "PDF", "TXT"]
        for format_name in formats:
            format_key = format_name.lower()
            statuses = []
            for provider, result in self.results.items():
                status = "✅" if result.outputs_generated.get(format_key, False) else "❌"
                statuses.append(f"{provider.title()} {status}")
            lines.append(f"  {format_name}: {' | '.join(statuses)}")
        
        lines.append("")
        
        # File paths
        lines.append("📁 Output Files:")
        for provider, result in self.results.items():
            if result.file_paths:
                output_dir = str(Path(list(result.file_paths.values())[0]).parent) if any(result.file_paths.values()) else "Not generated"
                lines.append(f"  {provider.title()}: {output_dir}")
        
        lines.extend(["", "=" * 80, ""])
        
        return "\n".join(lines)
    
    def save_results_json(
        self,
        output_path: str,
        test_metadata: Optional[Dict] = None
    ) -> str:
        """Save comprehensive results to JSON file."""
        
        # Create comprehensive report
        report = ComparisonReport(
            test_info=test_metadata or {},
            provider_results={name: result for name, result in self.results.items()},
            comparison_summary=self.generate_comparison_summary(),
            performance_metrics=self._extract_performance_metrics(),
            output_status=self._extract_output_status(),
            timestamp=datetime.now().isoformat()
        )
        
        # Convert to dict and handle non-serializable objects
        report_dict = asdict(report)
        
        # Save to file
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report_dict, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Results saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            return ""
    
    def _extract_performance_metrics(self) -> Dict[str, Any]:
        """Extract performance metrics for reporting."""
        
        metrics = {}
        
        for provider, result in self.results.items():
            metrics[provider] = {
                "translation_time_seconds": result.translation_time,
                "total_time_seconds": result.total_time,
                "tokens_processed": result.tokens_used,
                "tokens_per_second": result.tokens_used / result.translation_time if result.translation_time > 0 else 0,
                "success": result.success
            }
        
        return metrics
    
    def _extract_output_status(self) -> Dict[str, Any]:
        """Extract output generation status for reporting."""
        
        status = {
            "formats": ["epub", "pdf", "txt"],
            "provider_status": {}
        }
        
        for provider, result in self.results.items():
            status["provider_status"][provider] = {
                "outputs_generated": result.outputs_generated,
                "file_paths": result.file_paths,
                "file_sizes": result.file_sizes
            }
        
        return status