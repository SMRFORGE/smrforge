"""
Surrogate validation report: compare surrogate predictions vs physics on holdout set.

Pro tier differentiator — regulatory-grade accuracy documentation for AI/surrogate use.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np

from smrforge.utils.logging import get_logger

logger = get_logger("smrforge_pro.workflows.surrogate_validation")


def generate_surrogate_validation_report(
    surrogate: Any,
    holdout_results: List[Dict[str, Any]],
    param_names: Optional[List[str]] = None,
    output_metric: str = "k_eff",
    output_path: Optional[Union[str, Path]] = None,
    format: str = "both",
    tolerance_relative: float = 0.01,
    tolerance_absolute: float = 0.001,
) -> Dict[str, Any]:
    """
    Generate validation report comparing surrogate predictions to physics (holdout) results.

    Produces metrics (MAE, RMSE, R², max error), point-by-point comparison, and
    pass/fail assessment against tolerances. Outputs JSON and/or Markdown.

    Args:
        surrogate: Fitted SurrogateModel with .predict(params) interface
        holdout_results: List of {parameters: {...}, k_eff: v, ...} from physics runs
        param_names: Parameter keys (default: from first result)
        output_metric: Metric to compare (e.g. k_eff)
        output_path: Optional path to save report (extension determines format)
        format: "json", "md", or "both"
        tolerance_relative: Relative tolerance for pass (e.g. 0.01 = 1%)
        tolerance_absolute: Absolute tolerance for pass (e.g. 0.001 for k_eff)

    Returns:
        Report dict with metrics, point_details, passed, summary
    """
    if not holdout_results:
        raise ValueError("holdout_results cannot be empty")

    first = holdout_results[0]
    params = first.get("parameters", first)
    param_names = param_names or (list(params.keys()) if isinstance(params, dict) else [])

    actual = []
    predicted = []
    point_details = []

    for r in holdout_results:
        p = r.get("parameters", r)
        if isinstance(p, dict):
            y_true = r.get(output_metric)
            if y_true is None:
                continue
            y_pred = surrogate.predict(p)
            actual.append(float(y_true))
            predicted.append(float(y_pred))
            err = abs(y_pred - y_true)
            rel_err = err / abs(y_true) if y_true != 0 else 0.0
            point_details.append({
                "parameters": p.copy(),
                "actual": y_true,
                "predicted": y_pred,
                "error_absolute": err,
                "error_relative": rel_err,
            })

    actual = np.array(actual)
    predicted = np.array(predicted)
    n = len(actual)

    errors = np.abs(predicted - actual)
    mae = float(np.mean(errors))
    rmse = float(np.sqrt(np.mean(errors ** 2)))
    max_err = float(np.max(errors))
    max_rel_err = float(np.max(np.abs((predicted - actual) / (np.where(actual != 0, actual, 1e-12)))))

    ss_res = np.sum((actual - predicted) ** 2)
    ss_tot = np.sum((actual - np.mean(actual)) ** 2)
    r2 = float(1 - ss_res / ss_tot) if ss_tot > 0 else 0.0

    passed = (
        mae <= tolerance_absolute or (tolerance_absolute == 0 and mae < 1e-6)
    ) and max_rel_err <= tolerance_relative

    report = {
        "summary": {
            "n_points": n,
            "output_metric": output_metric,
            "mae": mae,
            "rmse": rmse,
            "max_absolute_error": max_err,
            "max_relative_error": max_rel_err,
            "r_squared": r2,
            "passed": passed,
            "tolerance_relative": tolerance_relative,
            "tolerance_absolute": tolerance_absolute,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
        "point_details": point_details,
        "metrics": {
            "mae": mae,
            "rmse": rmse,
            "r2": r2,
            "max_error": max_err,
        },
    }

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        base = output_path.with_suffix("") if output_path.suffix else output_path

        if format in ("json", "both"):
            json_path = output_path if format == "json" and str(output_path).endswith(".json") else base.with_suffix(".json")
            json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
            logger.info("Validation report JSON saved to %s", json_path)

        if format in ("md", "markdown", "both"):
            md_path = output_path if format in ("md", "markdown") and str(output_path).endswith(".md") else base.with_suffix(".md")
            md_content = _format_markdown(report)
            md_path.write_text(md_content, encoding="utf-8")
            logger.info("Validation report Markdown saved to %s", md_path)

    return report


def _format_markdown(report: Dict[str, Any]) -> str:
    """Format report as Markdown."""
    s = report["summary"]
    lines = [
        "# Surrogate Validation Report",
        "",
        "## Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Points | {s['n_points']} |",
        f"| Output metric | {s['output_metric']} |",
        f"| MAE | {s['mae']:.6e} |",
        f"| RMSE | {s['rmse']:.6e} |",
        f"| Max absolute error | {s['max_absolute_error']:.6e} |",
        f"| Max relative error | {s['max_relative_error']:.2%} |",
        f"| R² | {s['r_squared']:.4f} |",
        f"| **Passed** | {'✅ Yes' if s['passed'] else '❌ No'} |",
        f"| Tolerances | rel={s['tolerance_relative']:.1%}, abs={s['tolerance_absolute']:.2e} |",
        "",
        "## Point-by-Point Comparison",
        "",
        "| Parameters | Actual | Predicted | Abs Error | Rel Error |",
        "|------------|--------|-----------|-----------|-----------|",
    ]
    for p in report["point_details"][:20]:
        params_str = ", ".join(f"{k}={v}" for k, v in list(p["parameters"].items())[:4])
        if len(params_str) > 40:
            params_str = params_str[:37] + "..."
        lines.append(
            f"| {params_str} | {p['actual']:.6e} | {p['predicted']:.6e} | {p['error_absolute']:.6e} | {p['error_relative']:.2%} |"
        )
    if len(report["point_details"]) > 20:
        lines.append(f"| ... ({len(report['point_details']) - 20} more) | | | | |")
    lines.append("")
    return "\n".join(lines)
