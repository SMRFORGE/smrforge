"""
Scenario-based design: run design-study (or validation) under multiple
constraint sets / missions and compare (e.g. baseload, load-follow, process heat).
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..utils.logging import get_logger
from ..validation.constraints import ConstraintSet
from ..validation.safety_report import safety_margin_report

logger = get_logger("smrforge.workflows.scenario_design")


@dataclass
class ScenarioResult:
    """Result of one scenario (one constraint set / mission)."""

    scenario_name: str
    passed: bool
    metrics: Dict[str, float] = field(default_factory=dict)
    violations: List[str] = field(default_factory=list)
    margins_summary: Dict[str, float] = field(default_factory=dict)


def run_scenario_design(
    reactor: Any,
    scenarios: Dict[str, Union[ConstraintSet, Path, str]],
    analysis_results: Optional[Dict[str, float]] = None,
) -> Dict[str, ScenarioResult]:
    """
    Run validation (safety margin report) for one reactor under multiple scenarios.

    Args:
        reactor: Reactor instance (used for solve() if analysis_results not provided).
        scenarios: Dict mapping scenario name -> ConstraintSet, or path to JSON, or preset name.
            If value is str, treated as preset name for ConstraintSet (e.g. "regulatory_limits").
        analysis_results: Optional precomputed design point; if None, reactor.solve() is called.

    Returns:
        Dict mapping scenario name -> ScenarioResult.
    """
    if analysis_results is None:
        try:
            analysis_results = reactor.solve()
        except Exception as e:  # pragma: no cover
            logger.warning("reactor.solve() failed: %s", e)
            analysis_results = {}
    results: Dict[str, ScenarioResult] = {}
    for name, spec in scenarios.items():
        if isinstance(spec, ConstraintSet):
            cs = spec
        elif isinstance(spec, (Path, str)):
            path = Path(spec)
            if path.exists():
                cs = ConstraintSet.load(path)
            else:
                if spec == "regulatory_limits":
                    cs = ConstraintSet.get_regulatory_limits()
                elif spec == "safety_margins":
                    cs = ConstraintSet.get_safety_margins()
                else:
                    logger.warning(
                        "Unknown scenario spec '%s', using regulatory_limits", spec
                    )
                    cs = ConstraintSet.get_regulatory_limits()
        else:
            cs = ConstraintSet.get_regulatory_limits()
        report = safety_margin_report(
            reactor, constraint_set=cs, analysis_results=analysis_results
        )
        margins_summary = {m.name: m.margin for m in report.margins}
        results[name] = ScenarioResult(
            scenario_name=name,
            passed=report.passed,
            metrics=report.metrics,
            violations=report.violations,
            margins_summary=margins_summary,
        )
    return results


def scenario_comparison_report(
    scenario_results: Dict[str, ScenarioResult],
    output_path: Optional[Path] = None,
) -> str:
    """
    Produce a short text/markdown comparison of scenario results.

    Returns:
        Markdown string. If output_path is set, also writes to file.
    """
    lines = ["# Scenario design comparison", ""]
    for name, sr in scenario_results.items():
        status = "PASS" if sr.passed else "FAIL"
        lines.append(f"## {name}: {status}")
        lines.append(f"- Metrics: {sr.metrics}")
        if sr.violations:
            lines.append("- Violations:")
            for v in sr.violations:
                lines.append(f"  - {v}")
        lines.append("")
    text = "\n".join(lines)
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
    return text
