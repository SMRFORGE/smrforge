"""
ML dataset export for Pro tier.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd


def export_ml_dataset(
    results: List[Dict[str, Any]],
    output_path: Union[str, Path],
    param_names: Optional[List[str]] = None,
    output_metrics: Optional[List[str]] = None,
    format: Optional[str] = None,
) -> Path:
    """
    Export parameter sweep results to ML-friendly format (Parquet or HDF5).

    Args:
        results: List of {parameters: {...}, metric: value, ...}
        output_path: Output file path
        param_names: Parameter keys to include (default: from first result)
        output_metrics: Metric keys to include (default: k_eff, burnup, etc.)
        format: "parquet" or "hdf5" (default: from extension)

    Returns:
        Path to written file
    """
    output_path = Path(output_path)
    if not results:
        raise ValueError("No results to export")

    first = results[0]
    params = first.get("parameters", first)
    param_names = param_names or list(params.keys()) if isinstance(params, dict) else []
    output_metrics = output_metrics or _infer_metrics(results)

    rows = []
    for r in results:
        params = r.get("parameters", {})
        row = {k: params.get(k) for k in param_names}
        for m in output_metrics:
            if m in r:
                row[m] = r[m]
        rows.append(row)

    df = pd.DataFrame(rows)
    fmt = format or output_path.suffix.lower().lstrip(".")
    if fmt in ("parquet", ""):
        df.to_parquet(output_path, index=False)
    elif fmt in ("h5", "hdf5"):
        df.to_hdf(output_path, key="data", mode="w", index=False)
    else:
        df.to_parquet(output_path.with_suffix(".parquet"), index=False)

    return output_path


def _infer_metrics(results: List[Dict]) -> List[str]:
    """Infer metric keys from results."""
    seen = set()
    for r in results:
        for k in r:
            if k != "parameters" and not isinstance(r.get(k), dict):
                seen.add(k)
    return sorted(seen) if seen else ["k_eff"]
