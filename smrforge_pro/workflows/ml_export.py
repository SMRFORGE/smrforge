"""
ML-friendly data export for SMRForge - Parquet and HDF5.

Pro tier: Full implementation of export_ml_dataset.
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
    Export sweep/ML dataset to Parquet or HDF5.

    Args:
        results: List of {"parameters": {p: v}, "k_eff": ..., ...}
        output_path: Output file path
        param_names: Parameter keys to include as columns (default: all from first)
        output_metrics: Output keys (default: infer from first result)
        format: "parquet" or "hdf5" (default: from path suffix)

    Returns:
        Path to written file
    """
    output_path = Path(output_path)
    if not results:
        raise ValueError("Results list is empty")

    # Infer param names and metrics
    first = results[0]
    params = first.get("parameters", first)
    if param_names is None:
        param_names = [k for k in params.keys() if isinstance(params[k], (int, float))]
    if output_metrics is None:
        output_metrics = [
            k for k in first.keys()
            if k != "parameters" and isinstance(first.get(k), (int, float, np.floating))
        ]

    # Build flat rows
    rows = []
    for r in results:
        if "error" in r:
            continue
        params = r.get("parameters", r)
        row = {p: float(params.get(p, np.nan)) for p in param_names}
        for m in output_metrics:
            val = r.get(m)
            if isinstance(val, (int, float, np.floating)):
                row[m] = float(val)
            else:
                row[m] = np.nan
        rows.append(row)

    df = pd.DataFrame(rows)

    fmt = format or output_path.suffix.lower().lstrip(".")
    if fmt in ("parquet", ""):
        fmt = "parquet"
    elif fmt in ("h5", "hdf5"):
        fmt = "hdf5"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if fmt == "parquet":
        if output_path.suffix.lower() != ".parquet":
            output_path = output_path.with_suffix(".parquet")
        try:
            df.to_parquet(output_path, index=False)
        except ImportError as e:
            raise ImportError(
                "Parquet export requires pyarrow or fastparquet. pip install pyarrow or smrforge-pro[ml]"
            ) from e
    elif fmt == "hdf5":
        if output_path.suffix.lower() not in (".h5", ".hdf5"):
            output_path = output_path.with_suffix(".h5")
        try:
            df.to_hdf(output_path, key="data", mode="w", format="table")
        except ImportError as e:
            raise ImportError(
                "HDF5 export requires pytables. pip install tables"
            ) from e
    else:
        raise ValueError(f"Unsupported format: {format}. Use parquet or hdf5.")

    return output_path
