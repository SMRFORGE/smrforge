"""
Coupled safety margin report: nominal metrics, limits, margins, and optional UQ percentiles.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .constraints import ConstraintSet, DesignValidator, ValidationResult


@dataclass
class MarginEntry:
    """Single constraint margin."""

    name: str
    value: float
    limit: float
    unit: str
    margin: float  # value - limit (for max) or limit - value (for min); positive = within limit
    within_limit: bool
    percentile_5: Optional[float] = None
    percentile_95: Optional[float] = None


@dataclass
class SafetyMarginReport:
    """Coupled safety margin report."""

    passed: bool
    margins: List[MarginEntry] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
    violations: List[str] = field(default_factory=list)
    uq_available: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Export as JSON-serializable dict."""
        return {
            "passed": self.passed,
            "uq_available": self.uq_available,
            "metrics": self.metrics,
            "margins": [
                {
                    "name": m.name,
                    "value": m.value,
                    "limit": m.limit,
                    "unit": m.unit,
                    "margin": m.margin,
                    "within_limit": m.within_limit,
                    "percentile_5": m.percentile_5,
                    "percentile_95": m.percentile_95,
                }
                for m in self.margins
            ],
            "violations": self.violations,
        }


def margin_narrative(report: SafetyMarginReport) -> str:
    """
    Generate a short narrative summary of the safety margin report for reports/docs.

    Example: "All limits met. Minimum margin: shutdown margin at 0.015 (limit 0.005)."
    or "Validation failed. Violations: min_k_eff: 0.98 (limit 1.0)."
    """
    if report.passed:
        if not report.margins:
            return "All specified limits met. No margin details available."
        by_margin = sorted(report.margins, key=lambda m: m.margin)
        smallest = by_margin[0]
        unit = f" {smallest.unit}" if smallest.unit else ""
        return (
            f"All limits met. Minimum margin: {smallest.name} at {smallest.value}{unit} "
            f"(limit {smallest.limit}{unit}, margin {smallest.margin})."
        )
    if report.violations:
        return "Validation failed. Violations: " + "; ".join(report.violations)
    return "Validation failed. One or more constraints not satisfied."


def safety_margin_report(
    reactor: Any,
    constraint_set: Optional[ConstraintSet] = None,
    analysis_results: Optional[Dict[str, float]] = None,
    uq_results: Optional[Dict[str, Dict[str, float]]] = None,
) -> SafetyMarginReport:
    """
    Build a single safety margin report: nominal metrics vs limits, with optional UQ percentiles.

    Args:
        reactor: Reactor instance (used for solve() if analysis_results not provided).
        constraint_set: Constraint set (default: regulatory limits).
        analysis_results: Precomputed analysis dict (e.g. from get_design_point); if None, runs reactor.solve().
        uq_results: Optional dict mapping metric names to {"p5": float, "p95": float} for percentiles.

    Returns:
        SafetyMarginReport with margins and pass/fail.
    """
    if constraint_set is None:
        constraint_set = ConstraintSet.get_regulatory_limits()

    validator = DesignValidator(constraint_set)
    if analysis_results is None:
        try:
            analysis_results = reactor.solve()
        except Exception:  # pragma: no cover
            analysis_results = {}
    # Normalize to scalar metrics for constraint check
    metrics = validator.validate(reactor, analysis_results).metrics
    # Merge in any extra from analysis_results that validator might use
    if isinstance(analysis_results, dict):
        for k, v in analysis_results.items():
            if k not in metrics and isinstance(v, (int, float)):
                metrics[k] = float(v)
    if "power_thermal_mw" in analysis_results and "power_thermal_mw" not in metrics:
        metrics["power_thermal_mw"] = float(analysis_results["power_thermal_mw"])
    if "k_eff" in analysis_results:
        metrics["k_eff"] = float(analysis_results["k_eff"])

    validation = validator.validate(reactor, analysis_results)
    margins: List[MarginEntry] = []
    violations: List[str] = []

    for cname, cdef in constraint_set.constraints.items():
        limit = cdef["limit"]
        ctype = cdef.get("type", "max")
        unit = cdef.get("unit", "")
        value = metrics.get(cname)
        if value is None and cname == "min_k_eff":
            value = metrics.get("k_eff")
        if value is None or not isinstance(value, (int, float)):
            continue
        value = float(value)
        if ctype == "max":
            margin = limit - value
            within = value <= limit
        else:
            margin = value - limit
            within = value >= limit
        if not within:
            violations.append(f"{cname}: {value} {unit} (limit {limit} {unit})")
        p5 = p95 = None
        if uq_results and cname in uq_results:
            p5 = uq_results[cname].get("p5") or uq_results[cname].get("percentile_5")
            p95 = uq_results[cname].get("p95") or uq_results[cname].get("percentile_95")
        margins.append(
            MarginEntry(
                name=cname,
                value=value,
                limit=limit,
                unit=unit,
                margin=margin,
                within_limit=within,
                percentile_5=p5,
                percentile_95=p95,
            )
        )

    return SafetyMarginReport(
        passed=validation.passed,
        margins=margins,
        metrics=metrics,
        violations=violations,
        uq_available=uq_results is not None and len(uq_results) > 0,
    )
