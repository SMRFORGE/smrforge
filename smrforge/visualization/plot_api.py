"""
Unified Plot API inspired by OpenMC.

Provides a flexible Plot class for creating various types of plots with
consistent interface, similar to OpenMC's Plot API.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np

from ..geometry.mesh_3d import Mesh3D
from ..utils.logging import get_logger

logger = get_logger("smrforge.visualization.plot_api")

try:
    import matplotlib.pyplot as plt

    _MATPLOTLIB_AVAILABLE = True
except ImportError:
    _MATPLOTLIB_AVAILABLE = False
    plt = None  # type: ignore

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


@dataclass
class Plot:
    """
    Unified plotting interface inspired by OpenMC.

    Provides a flexible API for creating various types of plots with
    consistent configuration options.

    Attributes:
        plot_type: Type of plot - 'slice', 'voxel', 'ray_trace', 'unstructured'
        origin: View origin point (x, y, z) [cm]
        width: View width in each direction (x, y, z) [cm]
        pixels: Resolution (width, height) in pixels
        basis: View basis ('xy', 'xz', 'yz', 'xyz' for 3D)
        color_by: Color scheme - 'material', 'cell', 'flux', 'power', 'temperature', 'density'
        colors: Custom color dictionary mapping IDs to colors
        background: Background color
        backend: Visualization backend - 'plotly', 'pyvista', 'matplotlib'
        output_file: Optional output file path
    """

    plot_type: str = "slice"  # 'slice', 'voxel', 'ray_trace', 'unstructured'
    origin: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    width: Tuple[float, float, float] = (200.0, 200.0, 400.0)
    pixels: Tuple[int, int] = (800, 600)
    basis: str = "xy"  # 'xy', 'xz', 'yz', 'xyz'
    color_by: str = (
        "material"  # 'material', 'cell', 'flux', 'power', 'temperature', 'density'
    )
    colors: Optional[Dict[Union[int, str], str]] = field(default=None)
    background: str = "white"
    backend: str = "plotly"  # 'plotly', 'pyvista', 'matplotlib'
    output_file: Optional[Union[str, Path]] = None

    def plot(
        self,
        geometry,
        data: Optional[np.ndarray] = None,
        field_name: Optional[str] = None,
    ):
        """
        Generate plot based on configuration.

        Args:
            geometry: Reactor geometry (PrismaticCore, PebbleBedCore, Mesh3D, etc.)
            data: Optional data array for coloring (flux, power, etc.)
            field_name: Name of the data field (for labels)

        Returns:
            Figure object (backend-dependent)

        Example:
            >>> from smrforge.visualization.plot_api import Plot
            >>> from smrforge.geometry import PrismaticCore
            >>>
            >>> # Create plot configuration
            >>> plot = Plot(
            ...     plot_type='slice',
            ...     origin=(0, 0, 200),
            ...     width=(300, 300, 400),
            ...     basis='xy',
            ...     color_by='material',
            ...     backend='plotly'
            ... )
            >>>
            >>> # Generate plot
            >>> core = PrismaticCore()
            >>> core.build_hexagonal_lattice(n_rings=3, pitch=40.0)
            >>> fig = plot.plot(core)
            >>> fig.show()
        """
        if self.plot_type == "slice":
            return self._plot_slice(geometry, data, field_name)
        elif self.plot_type == "voxel":
            return self._plot_voxel(geometry, data, field_name)
        elif self.plot_type == "ray_trace":
            return self._plot_ray_trace(geometry, data, field_name)
        elif self.plot_type == "unstructured":
            return self._plot_unstructured(geometry, data, field_name)
        else:
            raise ValueError(
                f"Unknown plot_type: {self.plot_type}. "
                "Choose 'slice', 'voxel', 'ray_trace', or 'unstructured'"
            )

    def _plot_slice(
        self, geometry, data: Optional[np.ndarray], field_name: Optional[str]
    ):
        """Generate 2D slice plot."""
        from .advanced import plot_slice

        # Determine slice axis and position from basis
        if self.basis == "xy":
            axis = "z"
            position = self.origin[2] + self.width[2] / 2
        elif self.basis == "xz":
            axis = "y"
            position = self.origin[1] + self.width[1] / 2
        elif self.basis == "yz":
            axis = "x"
            position = self.origin[0] + self.width[0] / 2
        else:
            raise ValueError(f"Invalid basis for slice plot: {self.basis}")

        fig = plot_slice(
            data if data is not None else np.array([]),
            geometry,
            axis=axis,
            position=position,
            field_name=field_name or "data",
            backend=self.backend,
        )

        if self.output_file:
            self._save_figure(fig, self.output_file)

        return fig

    def _plot_voxel(
        self, geometry, data: Optional[np.ndarray], field_name: Optional[str]
    ):
        """Generate 3D voxel plot."""
        try:
            from .voxel_plots import plot_voxel
        except ImportError:
            raise ImportError("voxel_plots module not available")

        fig = plot_voxel(
            geometry,
            origin=self.origin,
            width=self.width,
            pixels=self.pixels,
            color_by=self.color_by,
            data=data,
            field_name=field_name,
            colors=self.colors,
            background=self.background,
            backend=self.backend,
        )

        if self.output_file:
            self._save_figure(fig, self.output_file)

        return fig

    def _plot_ray_trace(
        self, geometry, data: Optional[np.ndarray], field_name: Optional[str]
    ):
        """Generate ray-traced plot."""
        from .advanced import plot_ray_traced_geometry

        fig = plot_ray_traced_geometry(
            geometry,
            origin=self.origin,
            width=self.width,
            pixels=self.pixels,
            basis=self.basis,
            color_by=self.color_by,
            backend=self.backend,
        )

        if self.output_file:
            self._save_figure(fig, self.output_file)

        return fig

    def _plot_unstructured(
        self, geometry, data: Optional[np.ndarray], field_name: Optional[str]
    ):
        """Generate unstructured mesh plot."""
        try:
            from .mesh_3d import plot_mesh3d_plotly, plot_mesh3d_pyvista
        except ImportError:
            raise ImportError("mesh_3d module not available")

        # Convert geometry to mesh if needed
        if isinstance(geometry, Mesh3D):
            mesh = geometry
        else:
            try:
                from ..geometry.mesh_extraction import extract_core_volume_mesh

                mesh = extract_core_volume_mesh(geometry)
            except ImportError:
                raise ImportError("mesh_extraction module not available")

        # Add data if provided
        if data is not None:
            if field_name:
                mesh.add_cell_data(field_name, data)
            else:
                mesh.add_cell_data("data", data)

        if self.backend == "plotly":
            fig = plot_mesh3d_plotly(
                mesh,
                color_by=field_name or self.color_by,
            )
        elif self.backend == "pyvista":
            fig = plot_mesh3d_pyvista(
                mesh,
                color_by=field_name or self.color_by,
            )
        else:
            raise ValueError(
                f"Unstructured plots only support 'plotly' or 'pyvista', not '{self.backend}'"
            )

        if self.output_file:
            self._save_figure(fig, self.output_file)

        return fig

    def _save_figure(self, fig, output_file: Union[str, Path]):
        """Save figure to file."""
        output_path = Path(output_file)

        if self.backend == "plotly":
            if output_path.suffix == ".html":
                fig.write_html(str(output_path))
            elif output_path.suffix in [".png", ".jpg", ".jpeg", ".webp"]:
                fig.write_image(str(output_path))
            elif output_path.suffix == ".pdf":
                fig.write_image(str(output_path))
            else:
                fig.write_html(str(output_path.with_suffix(".html")))

        elif self.backend == "pyvista":
            if isinstance(fig, pv.Plotter):
                fig.screenshot(str(output_path))
                fig.close()
            else:
                logger.warning(f"Cannot save pyvista figure to {output_path}")

        elif self.backend == "matplotlib":
            if isinstance(fig, tuple):
                fig_obj, ax = fig
                fig_obj.savefig(str(output_path))
            else:
                fig.savefig(str(output_path))

        logger.info(f"Saved plot to {output_path}")


def create_plot(
    plot_type: str = "slice",
    origin: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    width: Tuple[float, float, float] = (200.0, 200.0, 400.0),
    pixels: Tuple[int, int] = (800, 600),
    basis: str = "xy",
    color_by: str = "material",
    colors: Optional[Dict[Union[int, str], str]] = None,
    background: str = "white",
    backend: str = "plotly",
    output_file: Optional[Union[str, Path]] = None,
) -> Plot:
    """
    Create a Plot instance with specified configuration.

    Convenience function for creating Plot objects, similar to OpenMC's API.

    **Dual API Pattern:**
    SMRForge provides two visualization APIs for flexibility:

    1. **Class-based API (Recommended for reusable plots):**
       - Use `Plot` class or `create_plot()` function
       - Better for creating reusable plot configurations
       - Supports saving configuration for later use

    2. **Standalone function API (Recommended for quick plots):**
       - Use standalone functions like `plot_voxel()`, `plot_ray_traced_geometry()`
       - Better for one-off plots or quick visualization
       - More concise for simple use cases

    Both APIs support the same parameters and backends. Choose based on your use case.

    Args:
        plot_type: Type of plot - 'slice', 'voxel', 'ray_trace', 'unstructured'
        origin: View origin point (x, y, z) [cm]
        width: View width in each direction (x, y, z) [cm]
        pixels: Resolution (width, height) in pixels
        basis: View basis ('xy', 'xz', 'yz', 'xyz' for 3D)
        color_by: Color scheme - 'material', 'cell', 'flux', 'power', 'temperature', 'density'
        colors: Custom color dictionary mapping IDs to colors
        background: Background color
        backend: Visualization backend - 'plotly', 'pyvista', 'matplotlib'
        output_file: Optional output file path

    Returns:
        Plot instance

    Examples:
        # Class-based API (recommended for reusable configurations)
        >>> from smrforge.visualization.plot_api import create_plot
        >>>
        >>> plot = create_plot(
        ...     plot_type='slice',
        ...     origin=(0, 0, 200),
        ...     width=(300, 300, 400),
        ...     color_by='material',
        ...     backend='plotly'
        ... )
        >>> fig = plot.plot(geometry)

        # Alternative: Standalone function API (simpler for one-off plots)
        >>> from smrforge.visualization.voxel_plots import plot_voxel
        >>> fig = plot_voxel(geometry, origin=(0, 0, 0), width=(300, 300, 400),
        ...                  color_by='material', backend='plotly')
    """
    return Plot(
        plot_type=plot_type,
        origin=origin,
        width=width,
        pixels=pixels,
        basis=basis,
        color_by=color_by,
        colors=colors,
        background=background,
        backend=backend,
        output_file=output_file,
    )
