"""
Surrogate validation report — Pro tier only.

Delegates to smrforge_pro when installed.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

_MSG = (
    "Surrogate validation report requires SMRForge Pro. "
    "Upgrade at https://smrforge.io or install smrforge-pro."
)

try:
    from smrforge_pro.workflows.surrogate_validation import (
        generate_surrogate_validation_report as _generate_surrogate_validation_report,
    )
    _PRO_AVAILABLE = True
except ImportError:
    _generate_surrogate_validation_report = None  # type: ignore
    _PRO_AVAILABLE = False


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
    """Pro tier only. Compare surrogate predictions to physics on holdout set."""
    if _PRO_AVAILABLE:
        return _generate_surrogate_validation_report(
            surrogate,
            holdout_results,
            param_names=param_names,
            output_metric=output_metric,
            output_path=output_path,
            format=format,
            tolerance_relative=tolerance_relative,
            tolerance_absolute=tolerance_absolute,
        )
    raise ImportError(_MSG)
