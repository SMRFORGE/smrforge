#!/usr/bin/env python3
"""
Generate validation results report from test execution.

This script generates validation reports from validation test results,
comparing with benchmarks and documenting accuracy metrics.

Usage:
    python scripts/generate_validation_report.py --results results.json --benchmarks benchmarks.json --output report.md
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from tests.validation_benchmark_data import BenchmarkDatabase, compare_with_benchmark
    BENCHMARK_AVAILABLE = True
except ImportError:
    BENCHMARK_AVAILABLE = False


def load_validation_results(results_file: Path) -> Dict[str, Any]:
    """Load validation test results from JSON file."""
    return json.loads(results_file.read_text())


def calculate_accuracy_metrics(test_results: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Calculate accuracy metrics from validation results with comparison data.
    
    Args:
        test_results: List of validation test result dictionaries
        
    Returns:
        Dictionary of accuracy metrics by test category
    """
    metrics = {}
    
    for result in test_results:
        comparison_data = result.get("comparison_data")
        if not comparison_data:
            continue
        
        test_name = result.get("test_name", "").lower()
        
        # Extract comparison results
        comparisons = comparison_data.get("comparisons", [])
        if isinstance(comparisons, list) and len(comparisons) > 0:
            # Extract relative errors
            relative_errors = []
            within_tolerance_count = 0
            within_uncertainty_count = 0
            
            for comp in comparisons:
                if isinstance(comp, dict):
                    rel_error_pct = comp.get("relative_error_percent", 0)
                    if rel_error_pct is not None:
                        relative_errors.append(rel_error_pct)
                    if comp.get("within_tolerance", False):
                        within_tolerance_count += 1
                    if comp.get("within_uncertainty") is True:
                        within_uncertainty_count += 1
            
            if relative_errors:
                # Determine category
                category = None
                if "decay heat" in test_name or "ans" in test_name:
                    category = "decay_heat"
                elif "gamma" in test_name or "mcnp" in test_name:
                    category = "gamma_transport"
                elif "burnup" in test_name or "k-eff" in test_name:
                    category = "burnup"
                
                if category:
                    if category not in metrics:
                        metrics[category] = {
                            "relative_errors": [],
                            "within_tolerance_count": 0,
                            "within_uncertainty_count": 0,
                            "total_comparisons": 0,
                        }
                    
                    metrics[category]["relative_errors"].extend(relative_errors)
                    metrics[category]["within_tolerance_count"] += within_tolerance_count
                    metrics[category]["within_uncertainty_count"] += within_uncertainty_count
                    metrics[category]["total_comparisons"] += len(comparisons)
    
    # Calculate summary statistics
    for category in metrics:
        errors = metrics[category]["relative_errors"]
        if errors:
            metrics[category]["avg_relative_error_percent"] = sum(errors) / len(errors)
            metrics[category]["max_relative_error_percent"] = max(errors)
        else:
            metrics[category]["avg_relative_error_percent"] = 0.0
            metrics[category]["max_relative_error_percent"] = 0.0
    
    return metrics


def generate_markdown_report(
    results: Dict[str, Any],
    benchmarks: BenchmarkDatabase = None,
    output_file: Path = None
) -> str:
    """Generate markdown validation report."""
    lines = []
    
    # Header
    lines.extend([
        "# Validation Results Report",
        "",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d')}",
        "**SMRForge Version:** [Version]",
        "**ENDF Library:** ENDF-B-VIII.1",
        "**Validation Test Suite:** Comprehensive Validation Framework",
        "",
        "---",
        ""
    ])
    
    # Executive Summary
    test_results = results.get("results", [])
    total_tests = len(test_results)
    passed_tests = sum(1 for r in test_results if r.get("passed", False))
    failed_tests = total_tests - passed_tests
    
    lines.extend([
        "## Executive Summary",
        "",
        f"**Overall Status:** {'PASS' if failed_tests == 0 else 'PARTIAL' if passed_tests > 0 else 'FAIL'}",
        "",
        f"- **Total Tests Run:** {total_tests}",
        f"- **Tests Passed:** {passed_tests}",
        f"- **Tests Failed:** {failed_tests}",
        "",
        "**Key Findings:**",
        "- [Summary of key validation results]",
        "- [Any issues or discrepancies found]",
        "- [Overall assessment of calculation accuracy]",
        "",
        "---",
        ""
    ])
    
    # Test Results
    lines.append("## Test Results")
    lines.append("")
    
    for result in test_results:
        status = "PASS" if result.get("passed", False) else "FAIL"
        test_name = result.get("test_name", "Unknown")
        message = result.get("message", "")
        
        lines.extend([
            f"### {test_name}",
            "",
            f"**Status:** {status}",
            f"**Message:** {message}",
            ""
        ])
        
        # Metrics
        metrics = result.get("metrics", {})
        if metrics:
            lines.append("**Metrics:**")
            for key, value in metrics.items():
                lines.append(f"- {key}: {value}")
            lines.append("")
        
        # Timing
        timing = result.get("timing")
        if timing and timing.get("elapsed_time"):
            lines.append(f"**Execution Time:** {timing['elapsed_time']:.4f} s")
            lines.append("")
        
        # Comparison with benchmarks (if available)
        if benchmarks and BENCHMARK_AVAILABLE:
            comparison_data = result.get("comparison_data")
            if comparison_data:
                lines.append("**Comparison:**")
                for key, value in comparison_data.items():
                    lines.append(f"- {key}: {value}")
                lines.append("")
        
        lines.append("---")
        lines.append("")
    
    # Performance Summary
    timings = [r.get("timing") for r in test_results if r.get("timing")]
    if timings:
        total_time = sum(t.get("elapsed_time", 0) for t in timings if t)
        lines.extend([
            "## Performance Summary",
            "",
            f"**Total Validation Time:** {total_time:.4f} seconds",
            "",
            "| Test | Time (s) |",
            "|------|----------|"
        ])
        
        for result in test_results:
            timing = result.get("timing")
            if timing and timing.get("elapsed_time"):
                test_name = result.get("test_name", "Unknown")
                elapsed = timing["elapsed_time"]
                lines.append(f"| {test_name} | {elapsed:.4f} |")
        
        lines.append("")
    
    # Accuracy Metrics (if benchmarks available)
    if benchmarks and BENCHMARK_AVAILABLE:
        # Calculate accuracy metrics from comparison data
        accuracy_metrics = calculate_accuracy_metrics(test_results)
        
        if accuracy_metrics:
            lines.extend([
                "## Accuracy Metrics",
                ""
            ])
            
            # Decay heat accuracy
            if "decay_heat" in accuracy_metrics:
                dh_metrics = accuracy_metrics["decay_heat"]
                lines.extend([
                    "### Decay Heat (ANSI/ANS-5.1)",
                    "",
                    f"- **Average Relative Error:** {dh_metrics.get('avg_relative_error_percent', 0):.3f}%",
                    f"- **Maximum Relative Error:** {dh_metrics.get('max_relative_error_percent', 0):.3f}%",
                    f"- **Tests Within Tolerance:** {dh_metrics.get('within_tolerance_count', 0)}/{dh_metrics.get('total_comparisons', 0)}",
                    f"- **Tests Within Uncertainty:** {dh_metrics.get('within_uncertainty_count', 0)}/{dh_metrics.get('total_comparisons', 0)}",
                    ""
                ])
            
            # Gamma transport accuracy
            if "gamma_transport" in accuracy_metrics:
                gt_metrics = accuracy_metrics["gamma_transport"]
                lines.extend([
                    "### Gamma Transport (MCNP Comparison)",
                    "",
                    f"- **Average Relative Error:** {gt_metrics.get('avg_relative_error_percent', 0):.3f}%",
                    f"- **Maximum Relative Error:** {gt_metrics.get('max_relative_error_percent', 0):.3f}%",
                    f"- **Tests Within Tolerance:** {gt_metrics.get('within_tolerance_count', 0)}/{gt_metrics.get('total_comparisons', 0)}",
                    ""
                ])
            
            # Burnup accuracy
            if "burnup" in accuracy_metrics:
                bu_metrics = accuracy_metrics["burnup"]
                lines.extend([
                    "### Burnup (IAEA Benchmark)",
                    "",
                    f"- **Average Relative Error (k-eff):** {bu_metrics.get('avg_relative_error_percent', 0):.3f}%",
                    f"- **Maximum Relative Error (k-eff):** {bu_metrics.get('max_relative_error_percent', 0):.3f}%",
                    f"- **Tests Within Tolerance:** {bu_metrics.get('within_tolerance_count', 0)}/{bu_metrics.get('total_comparisons', 0)}",
                    ""
                ])
        else:
            lines.extend([
                "## Accuracy Metrics",
                "",
                "**Note:** Accuracy metrics require benchmark values to be added to the benchmark database.",
                "See `docs/validation/validation-execution-guide.md` for instructions on adding benchmarks.",
                ""
            ])
    
    # Conclusions
    lines.extend([
        "## Conclusions",
        "",
        "[Summary of validation results and conclusions]",
        "",
        "### Overall Assessment",
        "[Overall assessment of calculation accuracy and reliability]",
        "",
        "### Recommendations",
        "- [Recommendations for improvements]",
        "- [Recommendations for additional validation]",
        "",
        "---",
        "",
        "*This report was generated by the SMRForge validation framework.*"
    ])
    
    report_text = "\n".join(lines)
    
    if output_file:
        output_file.write_text(report_text)
        print(f"Report generated: {output_file}")
    
    return report_text


def main():
    parser = argparse.ArgumentParser(
        description="Generate validation results report"
    )
    parser.add_argument(
        "--results",
        type=Path,
        help="Validation results JSON file",
        default=Path("validation_results.json")
    )
    parser.add_argument(
        "--benchmarks",
        type=Path,
        help="Benchmark database JSON file (optional)",
        default=None
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output markdown report file",
        default=None
    )
    parser.add_argument(
        "--template",
        action="store_true",
        help="Generate template report file"
    )
    
    args = parser.parse_args()
    
    # Generate template
    if args.template:
        template_file = args.output or Path("docs/validation/validation-results-example.md")
        template_results = {
            "results": [
                {
                    "test_name": "Example Test",
                    "passed": True,
                    "message": "Example validation test result",
                    "metrics": {"example_metric": 123.45},
                    "timing": {"elapsed_time": 0.123}
                }
            ]
        }
        report = generate_markdown_report(template_results, output_file=template_file)
        print(f"Template report generated: {template_file}")
        return 0
    
    # Load results
    if not args.results.exists():
        print(f"Error: Results file not found: {args.results}")
        print("Hint: Run validation tests first or use --template to generate a template")
        return 1
    
    results = load_validation_results(args.results)
    
    # Load benchmarks (optional)
    benchmarks = None
    if args.benchmarks and args.benchmarks.exists() and BENCHMARK_AVAILABLE:
        benchmarks = BenchmarkDatabase(args.benchmarks)
        print(f"Loaded {len(benchmarks.decay_heat_benchmarks)} decay heat benchmarks")
        print(f"Loaded {len(benchmarks.gamma_transport_benchmarks)} gamma transport benchmarks")
        print(f"Loaded {len(benchmarks.burnup_benchmarks)} burnup benchmarks")
    
    # Generate report
    output_file = args.output or Path(f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
    report = generate_markdown_report(results, benchmarks, output_file)
    
    print(f"\nReport generated successfully!")
    print(f"Output: {output_file}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
