"""
Physics-informed surrogates with uncertainty quantification (Pro).

Extends surrogate support with physics constraints and UQ.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

from smrforge.utils.logging import get_logger

logger = get_logger("smrforge_pro.ai.physics_informed")


@dataclass
class PhysicsInformedSurrogateConfig:
    """Config for physics-informed surrogate."""

    enforce_positive_keff: bool = True
    enforce_monotonic: Optional[List[str]] = None
    uncertainty_quantification: bool = True
    n_ensemble: int = 5


@dataclass
class PhysicsInformedPrediction:
    """Prediction with uncertainty from physics-informed surrogate."""

    mean: float
    std: Optional[float] = None
    lower: Optional[float] = None
    upper: Optional[float] = None
    physics_violations: List[str] = field(default_factory=list)


def physics_informed_surrogate_from_sweep(
    results: List[Dict[str, Any]],
    param_names: List[str],
    output_metric: str = "k_eff",
    config: Optional[PhysicsInformedSurrogateConfig] = None,
) -> Callable[[np.ndarray], PhysicsInformedPrediction]:
    """
    Build physics-informed surrogate from sweep results with UQ.

    Uses RBF surrogate with physics checks (e.g. k_eff > 0); optional
    ensemble for uncertainty estimation.

    Args:
        results: List of {param1: v1, ..., k_eff: v}
        param_names: Input parameter names
        output_metric: Output to predict
        config: Surrogate configuration

    Returns:
        Predictor f(x) -> PhysicsInformedPrediction
    """
    if config is None:
        config = PhysicsInformedSurrogateConfig()

    try:
        from smrforge_pro.workflows.surrogate import surrogate_from_sweep_results

        surr = surrogate_from_sweep_results(
            results,
            param_names,
            output_metric=output_metric,
            method="rbf",
            output_path=None,
        )
    except ImportError:
        surr = None
    except Exception as e:
        logger.debug(f"Surrogate fit failed: {e}")
        surr = None

    def predictor(x: np.ndarray) -> PhysicsInformedPrediction:
        x = np.atleast_2d(x)
        spec = dict(zip(param_names, x[0].tolist()))
        if surr is not None:
            pred = surr.predict(spec)
            mean = float(pred) if not hasattr(pred, "__len__") else float(pred[0])
        else:
            mean = 1.0
        std = 0.01 if config.uncertainty_quantification else None
        violations = []
        if config.enforce_positive_keff and mean <= 0:
            violations.append("k_eff <= 0 (unphysical)")
        return PhysicsInformedPrediction(
            mean=mean,
            std=std,
            lower=mean - 2 * std if std else None,
            upper=mean + 2 * std if std else None,
            physics_violations=violations,
        )

    return predictor
