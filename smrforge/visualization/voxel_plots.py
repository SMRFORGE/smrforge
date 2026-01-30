"""
Voxel plot generation for 3D visualization.

Provides voxel plot functionality similar to OpenMC, with HDF5 export
and VTK conversion capabilities.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np

try:
    import h5py
    _H5PY_AVAILABLE = True
except ImportError:
    _H5PY_AVAILABLE = False
    h5py = None  # type: ignore

try:
    import plotly.graph_objects as go
    _PLOTLY_AVAILABLE = True
except ImportError:
    _PLOTLY_AVAILABLE = False
    go = None  # type: ignore

try:
    import pyvista as pv
    _PYVISTA_AVAILABLE = True
except ImportError:
    _PYVISTA_AVAILABLE = False
    pv = None  # type: ignore

from ..utils.logging import get_logger

logger = get_logger("smrforge.visualization.voxel_plots")


def plot_voxel(
    geometry,
    origin: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    width: Tuple[float, float, float] = (200.0, 200.0, 400.0),
    pixels: Tuple[int, int] = (800, 600),
    color_by: str = "material",
    data: Optional[np.ndarray] = None,
    field_name: Optional[str] = None,
    colors: Optional[Dict[Union[int, str], str]] = None,
    background: str = "white",
    backend: str = "plotly",
    **kwargs,
):
    """
    Generate 3D voxel plot of reactor geometry.
    
    Creates a voxelized representation of the geometry, similar to OpenMC's
    voxel plots. Can export to HDF5 format for conversion to VTK.
    
    **Dual API Pattern:**
    This function is part of the standalone function API for quick one-off plots.
    For reusable plot configurations, consider using the class-based `Plot` API
    from `smrforge.visualization.plot_api` instead.
    
    Args:
        geometry: Reactor geometry (PrismaticCore, PebbleBedCore, Mesh3D, etc.)
        origin: View origin point (x, y, z) [cm]
        width: View width in each direction (x, y, z) [cm]
        pixels: Resolution (width, height) in pixels (for 2D projection)
        color_by: Color scheme - 'material', 'cell', 'flux', 'power', 'temperature'
        data: Optional data array for coloring
        field_name: Name of the data field
        colors: Custom color dictionary
        background: Background color
        backend: Visualization backend - 'plotly', 'pyvista'
        **kwargs: Additional arguments
    
    Returns:
        Figure object (backend-dependent)
    
    Examples:
        # Standalone function API (simpler for quick plots)
        >>> from smrforge.visualization.voxel_plots import plot_voxel
        >>> 
        >>> fig = plot_voxel(
        ...     core,
        ...     origin=(0, 0, 0),
        ...     width=(300, 300, 400),
        ...     color_by='material',
        ...     backend='plotly'
        ... )
        
        # Alternative: Class-based API (better for reusable configurations)
        >>> from smrforge.visualization.plot_api import create_plot
        >>> plot = create_plot(plot_type='voxel', origin=(0, 0, 0),
        ...                    width=(300, 300, 400), color_by='material')
        >>> fig = plot.plot(core)
    """
    # Create voxel grid
    voxel_grid = _create_voxel_grid(geometry, origin, width, **kwargs)
    
    if backend == "plotly":
        return _plot_voxel_plotly(voxel_grid, color_by, data, field_name, colors, background)
    elif backend == "pyvista":
        return _plot_voxel_pyvista(voxel_grid, color_by, data, field_name, colors, background)
    else:
        raise ValueError(f"Unknown backend: {backend}. Choose 'plotly' or 'pyvista'")


def _create_voxel_grid(geometry, origin, width, resolution: Tuple[int, int, int] = (50, 50, 100)):
    """
    Create voxel grid from geometry.
    
    Args:
        geometry: Reactor geometry
        origin: Origin point
        width: Width in each direction
        resolution: Voxel resolution (nx, ny, nz)
    
    Returns:
        Dictionary with voxel data
    """
    nx, ny, nz = resolution

    # Use voxel centers (not edges) for coordinates.
    dx = width[0] / nx
    dy = width[1] / ny
    dz = width[2] / nz
    x = origin[0] + (np.arange(nx) + 0.5) * dx
    y = origin[1] + (np.arange(ny) + 0.5) * dy
    z = origin[2] + (np.arange(nz) + 0.5) * dz

    # Initialize voxel arrays
    material_ids = np.zeros((nx, ny, nz), dtype=int)
    cell_ids = np.zeros((nx, ny, nz), dtype=int)
    
    # Voxelize geometry (fast approximate).
    #
    # This implementation focuses on `PrismaticCore`-style geometries with hex
    # graphite blocks. It assigns:
    # - material_ids: coarse material categories (fuel/reflector/control)
    # - cell_ids: block.id (0 if empty)
    #
    # For other geometry types, the arrays remain zero-filled.
    if hasattr(geometry, "blocks"):
        # Material ID mapping for block types.
        mat_map = {"fuel": 1, "reflector": 2, "control": 3}

        # Helpers for index range clipping.
        def _idx_range_1d(arr: np.ndarray, lo: float, hi: float) -> Tuple[int, int]:
            i0 = int(np.searchsorted(arr, lo, side="left"))
            i1 = int(np.searchsorted(arr, hi, side="right"))
            return max(0, i0), min(arr.size, i1)

        sqrt3 = float(np.sqrt(3.0))

        for block in getattr(geometry, "blocks", []):
            # Expect GraphiteBlock-like API.
            if not (hasattr(block, "position") and hasattr(block, "flat_to_flat") and hasattr(block, "height")):
                continue

            cx = float(block.position.x)
            cy = float(block.position.y)
            cz = float(block.position.z)
            h = float(block.height)

            # Regular hex circumradius for the vertices() convention used in core_geometry.py.
            R = float(block.flat_to_flat) / sqrt3
            if R <= 0 or h <= 0:
                continue

            # Tight bounding box in xy, and z slab.
            # For a pointy-top hex (vertex at +x), y extent is +/- (sqrt(3)/2) * R.
            y_extent = (sqrt3 / 2.0) * R
            x0, x1 = _idx_range_1d(x, cx - R, cx + R)
            y0, y1 = _idx_range_1d(y, cy - y_extent, cy + y_extent)
            z0, z1 = _idx_range_1d(z, cz - 0.5 * h, cz + 0.5 * h)
            if x0 >= x1 or y0 >= y1 or z0 >= z1:
                continue

            xs = x[x0:x1] - cx  # [nx_sub]
            ys = y[y0:y1] - cy  # [ny_sub]

            # Point-in-regular-hex test (pointy-top orientation).
            # Let q=|x|, r=|y|. Inside iff:
            #   q <= R and r <= sqrt(3) * min(R - q, R/2)
            q = np.abs(xs)[:, None]        # [nx_sub, 1]
            r = np.abs(ys)[None, :]        # [1, ny_sub]
            inside_xy = (q <= R) & (r <= sqrt3 * np.minimum(R - q, 0.5 * R))

            # Assign into 3D slab.
            mat_id = int(mat_map.get(getattr(block, "block_type", "fuel"), 0))
            blk_id = int(getattr(block, "id", 0))
            sub_m = material_ids[x0:x1, y0:y1, z0:z1]
            sub_c = cell_ids[x0:x1, y0:y1, z0:z1]
            mask3 = np.broadcast_to(inside_xy[:, :, None], sub_m.shape)
            sub_m[mask3] = mat_id
            sub_c[mask3] = blk_id
    
    return {
        "x": x,
        "y": y,
        "z": z,
        "material_ids": material_ids,
        "cell_ids": cell_ids,
        "origin": origin,
        "width": width,
        "resolution": resolution,
    }


def _plot_voxel_plotly(voxel_grid, color_by, data, field_name, colors, background):
    """Plot voxel grid using plotly."""
    if not _PLOTLY_AVAILABLE:
        raise ImportError("plotly is required for voxel plots")
    
    x, y, z = np.meshgrid(
        voxel_grid["x"],
        voxel_grid["y"],
        voxel_grid["z"],
        indexing="ij",
    )
    
    material_ids = voxel_grid["material_ids"]
    
    # Create colors based on color_by
    if color_by == "material":
        if colors:
            color_map = colors
        else:
            # Default material colors
            unique_materials = np.unique(material_ids)
            # Convert numpy scalars to Python ints for dictionary keys
            color_map = {int(mat): f"hsl({i*360/len(unique_materials)}, 70%, 50%)" 
                        for i, mat in enumerate(unique_materials)}
        
        # Convert material_ids to integers and create color array
        # Use numpy operations to avoid list comprehension with numpy arrays
        material_ids_int = material_ids.astype(int)
        colors_array = np.empty_like(material_ids, dtype=object)
        
        # Fill color array using vectorized operations where possible
        for mat_id in np.unique(material_ids_int):
            mask = material_ids_int == mat_id
            colors_array[mask] = color_map.get(int(mat_id), "gray")
    else:
        colors_array = material_ids  # Use material IDs as colors
    
    fig = go.Figure(data=go.Volume(
        x=x.flatten(),
        y=y.flatten(),
        z=z.flatten(),
        value=material_ids.flatten(),
        isomin=material_ids.min(),
        isomax=material_ids.max(),
        opacity=0.3,
        surface_count=10,
    ))
    
    fig.update_layout(
        scene=dict(
            xaxis_title="X (cm)",
            yaxis_title="Y (cm)",
            zaxis_title="Z (cm)",
        ),
        title="Voxel Plot",
    )
    
    return fig


def _plot_voxel_pyvista(voxel_grid, color_by, data, field_name, colors, background):
    """Plot voxel grid using pyvista."""
    if not _PYVISTA_AVAILABLE:
        raise ImportError("pyvista is required for voxel plots")
    
    # Create structured grid
    x, y, z = np.meshgrid(
        voxel_grid["x"],
        voxel_grid["y"],
        voxel_grid["z"],
        indexing="ij",
    )
    
    grid = pv.StructuredGrid(x, y, z)
    grid["material_ids"] = voxel_grid["material_ids"].flatten(order="F")
    
    if data is not None:
        grid[field_name or "data"] = data.flatten(order="F")
    
    plotter = pv.Plotter()
    plotter.add_mesh(grid, scalars=color_by if data is None else (field_name or "data"))
    plotter.show_axes()
    plotter.set_background(background)
    
    return plotter


def export_voxel_to_hdf5(
    voxel_grid: Dict,
    output_file: Union[str, Path],
    **kwargs,
):
    """
    Export voxel grid to HDF5 format (OpenMC-compatible).
    
    Args:
        voxel_grid: Voxel grid dictionary from _create_voxel_grid
        output_file: Output HDF5 file path
        **kwargs: Additional metadata to store
    
    Example:
        >>> voxel_grid = _create_voxel_grid(core, origin, width)
        >>> export_voxel_to_hdf5(voxel_grid, "voxel_plot.h5")
    """
    if not _H5PY_AVAILABLE:
        raise ImportError("h5py is required for HDF5 export")
    
    output_path = Path(output_file)
    
    with h5py.File(output_path, "w") as f:
        # Store voxel data
        f.create_dataset("material_ids", data=voxel_grid["material_ids"])
        f.create_dataset("cell_ids", data=voxel_grid["cell_ids"])
        
        # Store grid information
        f.create_dataset("x", data=voxel_grid["x"])
        f.create_dataset("y", data=voxel_grid["y"])
        f.create_dataset("z", data=voxel_grid["z"])
        
        # Store metadata
        f.attrs["origin"] = voxel_grid["origin"]
        f.attrs["width"] = voxel_grid["width"]
        f.attrs["resolution"] = voxel_grid["resolution"]
        
        # Store additional metadata
        for key, value in kwargs.items():
            if isinstance(value, (int, float, str)):
                f.attrs[key] = value
    
    logger.info(f"Exported voxel grid to {output_path}")


def convert_voxel_hdf5_to_vtk(
    hdf5_file: Union[str, Path],
    vtk_file: Union[str, Path],
):
    """
    Convert voxel HDF5 file to VTK format for ParaView/VisIt.
    
    Args:
        hdf5_file: Input HDF5 file path
        vtk_file: Output VTK file path
    
    Example:
        >>> convert_voxel_hdf5_to_vtk("voxel_plot.h5", "voxel_plot.vtk")
    """
    if not _H5PY_AVAILABLE:
        raise ImportError("h5py is required for HDF5 import")
    
    if not _PYVISTA_AVAILABLE:
        raise ImportError("pyvista is required for VTK export")
    
    hdf5_path = Path(hdf5_file)
    vtk_path = Path(vtk_file)
    
    # Read HDF5 file
    with h5py.File(hdf5_path, "r") as f:
        material_ids = f["material_ids"][:]
        x = f["x"][:]
        y = f["y"][:]
        z = f["z"][:]
        origin = tuple(f.attrs["origin"])
        width = tuple(f.attrs["width"])
    
    # Create structured grid
    x_grid, y_grid, z_grid = np.meshgrid(x, y, z, indexing="ij")
    grid = pv.StructuredGrid(x_grid, y_grid, z_grid)
    grid["material_ids"] = material_ids.flatten(order="F")
    
    # Save to VTK
    grid.save(str(vtk_path))
    
    logger.info(f"Converted {hdf5_path} to {vtk_path}")
