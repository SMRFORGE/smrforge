"""
OpenMC statepoint HDF5 parsing and tally visualization.

Pro tier — 1D/2D Plotly visualization with ±1σ error bands.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np

from smrforge.utils.logging import get_logger

logger = get_logger("smrforge_pro.visualization.tally")


def load_tally_results(
    statepoint_path: Union[str, Path],
    tally_ids: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """
    Load tally results from OpenMC statepoint HDF5.

    Args:
        statepoint_path: Path to statepoint.N.h5
        tally_ids: Optional list of tally IDs to load (default: all)

    Returns:
        Dict with 'k_eff', 'k_eff_std', 'batches', 'tallies' (dict of tally_id -> mean/std_dev),
        and optional 'mesh' info for mesh tallies.
    """
    statepoint_path = Path(statepoint_path)
    if not statepoint_path.exists():
        raise FileNotFoundError(f"Statepoint not found: {statepoint_path}")

    try:
        import h5py
    except ImportError as e:
        raise ImportError("h5py required for tally loading. pip install h5py") from e

    result: Dict[str, Any] = {"tallies": {}}

    with h5py.File(statepoint_path, "r") as f:
        if "k_combined" in f:
            k = f["k_combined"][()]
            if hasattr(k, "__len__") and len(k) >= 2:
                result["k_eff"] = float(k[0])
                result["k_eff_std"] = float(k[1])
            else:
                result["k_eff"] = float(k)
                result["k_eff_std"] = 0.0

        if "k_generation" in f:
            kg = f["k_generation"][()]
            result["batches"] = int(kg.shape[0]) if hasattr(kg, "shape") else 0

        if "tallies" not in f:
            return result

        ids_attr = f["tallies"].attrs.get("ids", None)
        tally_id_list = ids_attr[:] if ids_attr is not None else list(f["tallies"].keys())

        for key in f["tallies"].keys():
            if key in ("ids", "meshes", "filters", "derivatives"):
                continue
            try:
                tid = int(key)
            except ValueError:
                continue
            if tally_ids is not None and tid not in tally_ids:
                continue

            t = f["tallies"][key]
            mean_arr = t.get("mean")
            std_arr = t.get("std_dev")
            results_arr = t.get("results")

            if mean_arr is not None:
                mean_raw = np.asarray(mean_arr[()])
                std_raw = np.asarray(std_arr[()]) if std_arr is not None else np.zeros_like(mean_raw)
            elif results_arr is not None:
                r = np.asarray(results_arr[()])
                if r.ndim >= 1 and r.shape[-1] >= 2:
                    n_real = int(t.attrs.get("n_realizations", 1)) or 1
                    sum_vals = r[..., 0]
                    sum_sq_vals = r[..., 1]
                    mean_raw = sum_vals / n_real
                    var = np.maximum(sum_sq_vals / n_real - mean_raw**2, 0)
                    std_raw = np.sqrt(var / max(n_real - 1, 1))
                else:
                    mean_raw = r.flatten()
                    std_raw = np.zeros_like(mean_raw)
            else:
                continue

            mean_flat = np.atleast_1d(mean_raw).flatten()
            std_flat = np.atleast_1d(std_raw).flatten()
            if len(std_flat) < len(mean_flat):
                std_flat = np.resize(std_flat, len(mean_flat))

            result["tallies"][tid] = {
                "mean": mean_flat.tolist(),
                "std_dev": std_flat.tolist(),
                "shape": list(np.atleast_1d(mean_raw).shape),
            }

    return result


def visualize_tally(
    results: Dict[str, Any],
    tally_id: int,
    output_path: Optional[Union[str, Path]] = None,
    title: Optional[str] = None,
    backend: str = "plotly",
) -> Any:
    """
    Create 1D or 2D Plotly visualization of tally with ±1σ error band.

    Args:
        results: Dict from load_tally_results()
        tally_id: Tally ID to visualize
        output_path: Optional path to save HTML/PNG
        title: Optional plot title
        backend: "plotly" (default) or "matplotlib"

    Returns:
        Plotly Figure or Matplotlib figure object.
    """
    tallies = results.get("tallies", {})
    if tally_id not in tallies:
        raise KeyError(f"Tally {tally_id} not in results. Available: {list(tallies.keys())}")

    t = tallies[tally_id]
    mean = np.array(t["mean"])
    std = np.array(t["std_dev"])
    shape = t.get("shape", mean.shape)

    plot_title = title or f"Tally {tally_id}"

    if backend == "plotly":
        try:
            import plotly.graph_objects as go
        except ImportError as e:
            raise ImportError("plotly required. pip install plotly") from e

        if len(mean) == 1:
            fig = go.Figure()
            fig.add_trace(
                go.Bar(
                    x=["value"],
                    y=[float(mean[0])],
                    error_y=dict(type="data", array=[float(std[0]) if len(std) else 0], visible=True),
                    name="Tally",
                )
            )
            fig.update_layout(title=plot_title, xaxis_title="", yaxis_title="Tally value")
        elif len(shape) == 1 or (len(mean) > 1 and len(shape) < 2):
            x = np.arange(len(mean))
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=x.tolist(),
                    y=mean.tolist(),
                    mode="lines+markers",
                    name="Mean",
                    line=dict(color="rgb(31, 119, 180)"),
                )
            )
            upper = mean + std
            lower = mean - std
            fig.add_trace(
                go.Scatter(
                    x=np.concatenate([x, x[::-1]]).tolist(),
                    y=np.concatenate([upper, lower[::-1]]).tolist(),
                    fill="toself",
                    fillcolor="rgba(31, 119, 180, 0.2)",
                    line=dict(color="rgba(255,255,255,0)"),
                    name="±1σ",
                )
            )
            fig.update_layout(title=plot_title, xaxis_title="Bin", yaxis_title="Tally value")
        else:
            mean_2d = mean.reshape(shape) if len(shape) >= 2 else mean.reshape(int(np.sqrt(len(mean))), -1)
            std_2d = std.reshape(mean_2d.shape) if std.size == mean.size else np.zeros_like(mean_2d)

            fig = go.Figure()
            fig.add_trace(
                go.Heatmap(
                    z=mean_2d.tolist(),
                    colorscale="Viridis",
                    name="Mean",
                )
            )
            fig.update_layout(title=plot_title, xaxis_title="Bin X", yaxis_title="Bin Y")
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            ext = Path(output_path).suffix.lower()
            if ext == ".html":
                fig.write_html(str(output_path))
            else:
                fig.write_image(str(output_path))
        return fig

    else:
        import matplotlib.pyplot as plt

        if len(mean) == 1 or (len(mean) > 1 and len(shape) < 2):
            fig, ax = plt.subplots()
            x = np.arange(len(mean))
            ax.plot(x, mean, "b-", label="Mean")
            ax.fill_between(x, mean - std, mean + std, alpha=0.3)
            ax.set_title(plot_title)
        else:
            mean_2d = mean.reshape(shape) if len(shape) >= 2 else mean.reshape(int(np.sqrt(len(mean))), -1)
            fig, ax = plt.subplots()
            im = ax.imshow(mean_2d, aspect="auto", cmap="viridis")
            plt.colorbar(im, ax=ax)
            ax.set_title(plot_title)
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(output_path)
        return fig
