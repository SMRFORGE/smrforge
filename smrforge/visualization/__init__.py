"""
Visualization and plotting tools for reactor analysis.

This module provides visualization capabilities for:
- Geometry visualization (2D and 3D)
- Flux and power distribution plots
- Temperature distribution visualization
- 3D mesh visualization (plotly and pyvista)
"""

try:
    from smrforge.visualization.geometry import (
        plot_core_layout,
        plot_flux_on_geometry,
        plot_power_distribution,
        plot_temperature_distribution,
    )

    _GEOMETRY_VIS_AVAILABLE = True
except ImportError as e:
    import warnings

    warnings.warn(f"Could not import geometry visualization: {e}", ImportWarning)
    _GEOMETRY_VIS_AVAILABLE = False

try:
    from smrforge.visualization.mesh_3d import (
        export_mesh_to_vtk,
        plot_mesh3d_plotly,
        plot_mesh3d_pyvista,
        plot_multiple_meshes_plotly,
        plot_surface_plotly,
        plot_surface_pyvista,
    )

    _MESH_3D_VIS_AVAILABLE = True
except ImportError:
    _MESH_3D_VIS_AVAILABLE = False

__all__ = []

if _GEOMETRY_VIS_AVAILABLE:
    __all__.extend(
        [
            "plot_core_layout",
            "plot_flux_on_geometry",
            "plot_power_distribution",
            "plot_temperature_distribution",
        ]
    )

if _MESH_3D_VIS_AVAILABLE:
    __all__.extend(
        [
            "plot_mesh3d_plotly",
            "plot_mesh3d_pyvista",
            "plot_surface_plotly",
            "plot_surface_pyvista",
            "plot_multiple_meshes_plotly",
            "export_mesh_to_vtk",
        ]
    )
