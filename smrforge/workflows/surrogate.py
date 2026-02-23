"""
Surrogate models for fast evaluation of reactor outputs.

Pro tier only. Community delegates to smrforge_pro when installed.
"""

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


def fit_surrogate(*args, **kwargs):
    """Pro tier only. Use SMRForge Pro for surrogate fitting."""
    if _PRO_AVAILABLE:
        return _fit_surrogate(*args, **kwargs)
    raise ImportError(_MSG)


def surrogate_from_sweep_results(*args, **kwargs):
    """Pro tier only. Use SMRForge Pro for surrogate workflows."""
    if _PRO_AVAILABLE:
        return _surrogate_from_sweep_results(*args, **kwargs)
    raise ImportError(_MSG)


class SurrogateModel:
    """Pro tier only. Use SMRForge Pro for surrogate models."""

    def __new__(cls, *args, **kwargs):
        if _PRO_AVAILABLE:
            return _SurrogateModel(*args, **kwargs)
        raise ImportError(_MSG)
