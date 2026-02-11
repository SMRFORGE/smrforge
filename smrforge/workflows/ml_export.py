"""
ML-friendly data export for SMRForge.

Export design points, parameters, and results in Parquet or HDF5
with clear schema for AI training pipelines and automated workflows.
Reference: NUCLEAR_INDUSTRY_ANALYSIS_AND_AI_FUTURE_PROOFING.md § 3.2
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd

from ..utils.logging import get_logger

logger = get_logger("smrforge.workflows.ml_export")

# Schema: flat table with param_* columns (inputs) and output_* columns (outputs)
SCHEMA_DESCRIPTION = """
ML export schema:
- param_<name>: Input parameter values (float or int)
- output_<metric>: Output metric (e.g., output_k_eff, output_power_thermal_mw)
- run_id: Optional run identifier
"""


def export_ml_dataset(
    results: List[Dict[str, Any]],
    output_path: Union[str, Path],
    param_names: Optional[List[str]] = None,
    output_metrics: Optional[List[str]] = None,
    format: Optional[str] = None,
) -> Path:
    """
    Export design points and results to Parquet or HDF5 for ML pipelines.

    Flattens nested results into a tabular format with param_* and output_*
    columns. Suitable for training surrogate models, UQ, or design optimization.

    Args:
        results: List of result dicts, each with "parameters" (or flat keys)
                and output metrics (e.g., "k_eff", "power_thermal_mw").
        output_path: Output file path (.parquet or .h5/.hdf5).
        param_names: Parameter names in order; auto-detected if None.
        output_metrics: Output metric keys; auto-detected if None.
        format: "parquet" or "hdf5"; inferred from suffix if None.

    Returns:
        Path to written file.

    Example:
        >>> results = [
        ...     {"parameters": {"x": 0.1, "y": 0.2}, "k_eff": 1.02, "power": 50.0},
        ...     {"parameters": {"x": 0.2, "y": 0.3}, "k_eff": 1.05, "power": 55.0},
        ... ]
        >>> export_ml_dataset(results, "design_points.parquet")
    """
    output_path = Path(output_path)
    if format is None:
        format = "parquet" if output_path.suffix == ".parquet" else "hdf5"

    rows: List[Dict[str, Any]] = []
    for r in results:
        params = r.get("parameters", r)
        row: Dict[str, Any] = {}
        for k, v in params.items():
            if isinstance(v, (int, float, np.integer, np.floating)):
                row[f"param_{k}"] = float(v)
            elif hasattr(v, "tolist"):
                row[f"param_{k}"] = v.tolist()
            else:
                row[f"param_{k}"] = v
        for k, v in r.items():
            if k == "parameters":
                continue
            if isinstance(v, (int, float, np.integer, np.floating)):
                row[f"output_{k}"] = float(v)
            elif hasattr(v, "tolist"):
                row[f"output_{k}"] = v.tolist()
            elif isinstance(v, (list, dict)) and k not in ("parameters",):
                row[f"output_{k}"] = v
        if row:
            rows.append(row)

    if not rows:
        raise ValueError("No valid rows to export")

    df = pd.DataFrame(rows)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if format == "parquet":
        df.to_parquet(output_path, index=False)
    elif format in ("hdf5", "h5"):
        try:
            import h5py
        except ImportError:
            raise ImportError(
                "h5py required for HDF5 export. Install: pip install h5py"
            )
        with h5py.File(output_path, "w") as f:
            f.attrs["schema"] = (
                "SMRForge ML export: param_* (inputs), output_* (outputs)"
            )
            f.attrs["columns"] = list(df.columns)
            for col in df.columns:
                arr = np.asarray(df[col].values)
                if np.issubdtype(arr.dtype, np.number):
                    f.create_dataset(col, data=arr)
                else:
                    str_arr = arr.astype(str)
                    dt = h5py.special_dtype(vlen=str)
                    f.create_dataset(col, data=str_arr, dtype=dt)
    else:
        raise ValueError(f"format must be 'parquet' or 'hdf5', got {format!r}")

    logger.info(
        "Exported ML dataset: %s (%d rows, %d cols)",
        output_path,
        len(df),
        len(df.columns),
    )
    return output_path
