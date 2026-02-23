"""
ML-friendly data export for SMRForge.

Pro tier only. Delegates to smrforge_pro when installed.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

_MSG = (
    "ML export (export_ml_dataset) requires SMRForge Pro. "
    "Upgrade at https://smrforge.io or install smrforge-pro."
)

try:
    from smrforge_pro.workflows.ml_export import export_ml_dataset as _export_ml_dataset
    _PRO_AVAILABLE = True
except ImportError:
    _export_ml_dataset = None  # type: ignore
    _PRO_AVAILABLE = False


def export_ml_dataset(
    results: List[Dict[str, Any]],
    output_path: Union[str, Path],
    param_names: Optional[List[str]] = None,
    output_metrics: Optional[List[str]] = None,
    format: Optional[str] = None,
) -> Path:
    """Pro tier only. Use SMRForge Pro for ML dataset export."""
    if _PRO_AVAILABLE:
        return _export_ml_dataset(
            results,
            output_path,
            param_names=param_names,
            output_metrics=output_metrics,
            format=format,
        )
    raise ImportError(_MSG)
