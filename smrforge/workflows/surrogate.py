"""
Surrogate models for fast evaluation of reactor outputs.

Pro tier only. Community delegates to smrforge_pro when installed.
"""

from pathlib import Path
from typing import Any, List, Optional, Union

import numpy as np

_MSG = (
    "Surrogate models require SMRForge Pro. "
    "Upgrade at https://smrforge.io or install smrforge-pro."
)

try:
    from smrforge_pro.workflows.surrogate import (
        SurrogateModel as _SurrogateModel,
        fit_surrogate as _fit_surrogate,
        surrogate_from_sweep_results as _surrogate_from_sweep_results,
    )
    _PRO_AVAILABLE = True
except ImportError:
    _SurrogateModel = None  # type: ignore
    _fit_surrogate = None  # type: ignore
    _surrogate_from_sweep_results = None  # type: ignore
    _PRO_AVAILABLE = False


def fit_surrogate(
    X: Union[np.ndarray, List],
    y: Union[np.ndarray, List],
    method: str = "rbf",
    param_names: Optional[List[str]] = None,
    output_metric: str = "output",
    audit_trail: Optional[Any] = None,
    **kwargs: Any,
) -> Any:
    """Pro tier only. Use SMRForge Pro for surrogate fitting."""
    if _PRO_AVAILABLE:
        return _fit_surrogate(
            X, y,
            method=method,
            param_names=param_names,
            output_metric=output_metric,
            audit_trail=audit_trail,
            **kwargs,
        )
    raise ImportError(_MSG)


def surrogate_from_sweep_results(
    results: List[Any],
    param_names: List[str],
    output_metric: str = "k_eff",
    method: str = "rbf",
    output_path: Optional[Union[str, Path]] = None,
    **kwargs: Any,
) -> Any:
    """Pro tier only. Use SMRForge Pro for surrogate workflows."""
    if _PRO_AVAILABLE:
        return _surrogate_from_sweep_results(
            results,
            param_names,
            output_metric=output_metric,
            method=method,
            output_path=output_path,
            **kwargs,
        )
    raise ImportError(_MSG)


class SurrogateModel:
    """Pro tier only. Use SMRForge Pro for surrogate models."""

    def __new__(cls, *args, **kwargs):
        if _PRO_AVAILABLE:
            return _SurrogateModel(*args, **kwargs)
        raise ImportError(_MSG)
