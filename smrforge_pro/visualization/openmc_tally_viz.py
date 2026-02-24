"""
OpenMC tally visualization - load statepoint and plot mesh tallies.

Pro tier: Requires openmc package. Converts OpenMC mesh tally to SMRForge MeshTally
and uses smrforge.visualization.mesh_tally.plot_mesh_tally.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np


def visualize_openmc_tallies(
    statepoint_path: Union[str, Path],
    tally_id: Optional[int] = None,
    score: Optional[str] = None,
    output_path: Optional[Union[str, Path]] = None,
    backend: str = "plotly",
    show_uncertainty: bool = True,
    energy_group: Optional[int] = None,
) -> Any:
    """
    Load OpenMC statepoint and visualize mesh tally results.

    Args:
        statepoint_path: Path to statepoint.N.h5
        tally_id: Specific tally ID (default: first mesh tally found)
        score: Score type to plot (default: first score, e.g. 'flux', 'fission')
        output_path: Save figure to file (HTML for plotly, PNG for matplotlib)
        backend: 'plotly', 'matplotlib', or 'pyvista'
        show_uncertainty: Plot uncertainty heatmap
        energy_group: Energy group index (None = total)

    Returns:
        Figure object (plotly/matplotlib) or None

    Raises:
        ImportError: If openmc not installed (pip install openmc or smrforge-pro[openmc])
        FileNotFoundError: If statepoint not found
        ValueError: If no mesh tally found
    """
    try:
        import openmc
    except ImportError as e:
        raise ImportError(
            "OpenMC tally visualization requires the openmc package. "
            "pip install openmc or smrforge-pro[openmc]"
        ) from e

    from smrforge.visualization.mesh_tally import MeshTally, plot_mesh_tally

    statepoint_path = Path(statepoint_path)
    if not statepoint_path.exists():
        raise FileNotFoundError(f"Statepoint not found: {statepoint_path}")

    sp = openmc.StatePoint(statepoint_path, autolink=False)

    if not sp.tallies_present or not sp.tallies:
        raise ValueError("No tallies in statepoint")

    # Find mesh tally
    tally = None
    if tally_id is not None:
        tally = sp.tallies.get(tally_id)
        if tally is None:
            raise ValueError(f"Tally ID {tally_id} not found")
    else:
        for tid, t in sp.tallies.items():
            if any(isinstance(f, openmc.MeshFilter) for f in t.filters):
                tally = t
                tally_id = tid
                break
        if tally is None:
            raise ValueError(
                "No mesh tally found in statepoint. "
                "Define a mesh tally in tallies.xml (MeshFilter)."
            )

    # Get mesh filter and mesh
    mesh_filter = None
    for f in tally.filters:
        if isinstance(f, openmc.MeshFilter):
            mesh_filter = f
            break
    if mesh_filter is None:
        raise ValueError("Tally has no MeshFilter")

    mesh = getattr(mesh_filter, "mesh", None)
    if mesh is None and hasattr(mesh_filter, "mesh_id"):
        mesh = sp.meshes.get(getattr(mesh_filter, "mesh_id", None))
    if mesh is None and sp.meshes:
        mesh = next(iter(sp.meshes.values()))
    if mesh is None:
        raise ValueError("Could not resolve mesh from tally")

    # Extract mean and std_dev - shape (n_filter_bins, n_nuclides, n_scores) or similar
    mean_arr = np.asarray(tally.mean, dtype=float)
    std_arr = np.asarray(tally.std_dev, dtype=float)

    # Collapse to (n_bins,) - sum over nuclides, take first or selected score
    while mean_arr.ndim > 1:
        if mean_arr.ndim == 3:
            # (filter_bins, nuclides, scores) - sum nuclides, take first score
            if score and hasattr(tally, "scores"):
                scores_list = list(tally.scores) if tally.scores else ["flux"]
                for i, s in enumerate(scores_list):
                    sn = getattr(s, "name", str(s))
                    if str(score).lower() == str(sn).lower():
                        mean_arr = mean_arr[:, :, i]
                        std_arr = std_arr[:, :, i]
                        break
                else:
                    mean_arr = mean_arr[:, :, 0]
                    std_arr = std_arr[:, :, 0]
            else:
                mean_arr = mean_arr[:, :, 0]
                std_arr = std_arr[:, :, 0]
        if mean_arr.ndim == 2:
            mean_arr = np.sum(mean_arr, axis=1)
            std_arr = np.sqrt(np.sum(std_arr ** 2, axis=1))
        else:
            break

    mean_arr = np.asarray(mean_arr).flatten()
    std_arr = np.asarray(std_arr).flatten()

    # Build mesh coordinates from OpenMC mesh
    mesh_coords, geometry_type = _mesh_coords_from_openmc(mesh)
    dims_raw = tuple(len(c) - 1 for c in mesh_coords)
    n_cells = int(np.prod(dims_raw))

    if len(mean_arr) < n_cells:
        mean_arr = np.pad(mean_arr, (0, max(0, n_cells - len(mean_arr))), constant_values=np.nan)
        std_arr = np.pad(std_arr, (0, max(0, n_cells - len(std_arr))), constant_values=np.nan)
    mean_arr = mean_arr[:n_cells].reshape(dims_raw)
    std_arr = std_arr[:n_cells].reshape(dims_raw)

    # Cylindrical 3D (r, phi, z) -> average over phi to get 2D (r, z) for visualization
    if geometry_type == "cylindrical" and mean_arr.ndim == 3:
        mean_arr = np.mean(mean_arr, axis=1)
        std_arr = np.sqrt(np.mean(std_arr ** 2, axis=1))
        mesh_coords = (mesh_coords[0], mesh_coords[2])

    score_name = score or (getattr(tally, "scores", ["flux"]) or ["flux"])[0]
    if hasattr(score_name, "name"):
        score_name = score_name.name
    tally_type = str(score_name).lower().replace(" ", "_")

    mesh_tally = MeshTally(
        name=f"Tally {tally_id}",
        tally_type=tally_type,
        data=mean_arr,
        mesh_coords=mesh_coords,
        uncertainty=std_arr,
        geometry_type=geometry_type,
    )

    fig = plot_mesh_tally(
        mesh_tally,
        None,
        field=tally_type,
        energy_group=energy_group,
        backend=backend,
        show_uncertainty=show_uncertainty,
    )

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if hasattr(fig, "write_html"):
            fig.write_html(str(output_path))
        elif hasattr(fig, "savefig"):
            fig.savefig(str(output_path))
        else:
            from matplotlib.pyplot import savefig
            if hasattr(fig, "get_figure"):
                savefig(output_path)
            else:
                import matplotlib.pyplot as plt
                plt.savefig(output_path)
                plt.close()

    sp.close()
    return fig


def _mesh_coords_from_openmc(mesh) -> Tuple[Tuple[np.ndarray, ...], str]:
    """Convert OpenMC mesh to mesh_coords and geometry_type."""
    mesh_type = getattr(mesh, "type", "regular")
    if isinstance(mesh_type, bytes):
        mesh_type = mesh_type.decode("utf-8")

    if mesh_type in ("regular", "rectangular"):
        ll = np.asarray(mesh.lower_left)
        ur = np.asarray(mesh.upper_right)
        dim = np.asarray(mesh.dimension, dtype=int)
        width = (ur - ll) / dim
        x = np.linspace(ll[0], ur[0], dim[0] + 1)
        y = np.linspace(ll[1], ur[1], dim[1] + 1)
        z = np.linspace(ll[2], ur[2], dim[2] + 1)
        return (x, y, z), "cartesian"

    if mesh_type in ("cylindrical", "cylinder"):
        r = np.asarray(getattr(mesh, "r_grid", [0.0, 50.0]))
        phi = np.asarray(getattr(mesh, "phi_grid", [0, 2 * np.pi]))
        z = np.asarray(getattr(mesh, "z_grid", [0.0, 200.0]))
        if len(r) < 2:
            r = np.array([0.0, 50.0])
        if len(z) < 2:
            z = np.array([0.0, 200.0])
        return (r, phi, z) if len(phi) > 2 else (r, z), "cylindrical"

    # Fallback: regular from dimension
    dim = np.asarray(getattr(mesh, "dimension", [10, 10, 10]), dtype=int)
    if len(dim) < 3:
        dim = np.pad(dim, (0, 3 - len(dim)), constant_values=10)
    ll = np.asarray(getattr(mesh, "lower_left", [0, 0, 0]))
    ur = np.asarray(getattr(mesh, "upper_right", [100, 100, 200]))
    x = np.linspace(ll[0], ur[0], dim[0] + 1)
    y = np.linspace(ll[1], ur[1], dim[1] + 1)
    z = np.linspace(ll[2], ur[2], dim[2] + 1)
    return (x, y, z), "cartesian"
