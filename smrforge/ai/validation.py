"""
Surrogate validation report generation.

Produces a validation report (dict/JSON) comparing surrogate predictions
against reference physics runs. Pro tier can extend to PDF export.

Offline-first, deterministic. All metrics recorded for audit.
"""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from ..utils.logging import get_logger

logger = get_logger("smrforge.ai.validation")


@dataclass
class ValidationMetric:
    """Single validation metric (e.g., MAE, max error)."""

    name: str
    value: float
    units: Optional[str] = None
    threshold: Optional[float] = None
    passed: Optional[bool] = None


@dataclass
class SurrogateValidationReport:
    """
    Validation report for a surrogate model.

    Compares surrogate predictions to reference physics runs.
    Pro tier can export to PDF.
    """

    surrogate_name: str
    surrogate_hash: Optional[str]
    n_reference: int
    n_params: int
    param_names: List[str]
    output_metric: str
    metrics: List[ValidationMetric]
    validity_envelope: Optional[Dict[str, Any]] = None
    reference_samples: Optional[List[Dict[str, Any]]] = None
    seed_used: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for JSON/audit."""
        return {
            "surrogate_name": self.surrogate_name,
            "surrogate_hash": self.surrogate_hash,
            "n_reference": self.n_reference,
            "n_params": self.n_params,
            "param_names": self.param_names,
            "output_metric": self.output_metric,
            "metrics": [asdict(m) for m in self.metrics],
            "validity_envelope": self.validity_envelope,
            "reference_samples": self.reference_samples,
            "seed_used": self.seed_used,
        }

    def save_json(self, path: Path) -> None:
        """Save report to JSON file."""
        import json

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)
        logger.info("Validation report saved to %s", path)


def generate_validation_report(
    surrogate_pred: List[float],
    reference_values: List[float],
    surrogate_name: str = "surrogate",
    surrogate_hash: Optional[str] = None,
    param_names: Optional[List[str]] = None,
    output_metric: str = "k_eff",
    reference_samples: Optional[List[Dict[str, Any]]] = None,
    seed_used: Optional[int] = None,
) -> SurrogateValidationReport:
    """
    Generate surrogate validation report from predictions vs reference.

    Args:
        surrogate_pred: Surrogate predictions for each reference point.
        reference_values: Reference (physics) values.
        surrogate_name: Name of surrogate.
        surrogate_hash: Model hash for audit.
        param_names: Parameter names.
        output_metric: Output metric name.
        reference_samples: Optional list of param dicts per sample.
        seed_used: RNG seed for reproducibility.

    Returns:
        SurrogateValidationReport.
    """
    pred = np.asarray(surrogate_pred, dtype=float).ravel()
    ref = np.asarray(reference_values, dtype=float).ravel()
    if len(pred) != len(ref):
        raise ValueError(
            "surrogate_pred and reference_values must have same length, "
            f"got {len(pred)} vs {len(ref)}"
        )

    errors = pred - ref
    mae = float(np.mean(np.abs(errors)))
    max_abs_err = float(np.max(np.abs(errors)))
    rmse = float(np.sqrt(np.mean(errors**2)))
    mean_bias = float(np.mean(errors))

    metrics = [
        ValidationMetric(name="MAE", value=mae, units=output_metric),
        ValidationMetric(name="max_abs_error", value=max_abs_err, units=output_metric),
        ValidationMetric(name="RMSE", value=rmse, units=output_metric),
        ValidationMetric(name="mean_bias", value=mean_bias, units=output_metric),
    ]

    # Validity envelope: param ranges of reference set
    validity = None
    if reference_samples and reference_samples:
        param_names = param_names or list(reference_samples[0].keys())
        validity = {}
        for p in param_names:
            vals = [s.get(p) for s in reference_samples if p in s and s.get(p) is not None]
            if vals:
                validity[p] = {"min": min(vals), "max": max(vals)}

    return SurrogateValidationReport(
        surrogate_name=surrogate_name,
        surrogate_hash=surrogate_hash,
        n_reference=len(ref),
        n_params=len(param_names) if param_names else 0,
        param_names=param_names or [],
        output_metric=output_metric,
        metrics=metrics,
        validity_envelope=validity,
        reference_samples=reference_samples,
        seed_used=seed_used,
    )
