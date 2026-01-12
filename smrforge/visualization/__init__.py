"""
Visualization and plotting tools for reactor analysis.

This module provides visualization capabilities for:
- Geometry visualization (2D and 3D)
- Flux and power distribution plots
- Temperature distribution visualization
- 3D mesh visualization (plotly and pyvista)
- Animation of transient data
- Comparison views for multiple designs
- Advanced visualization (ray-traced geometry, dashboards, interactive viewers)
- Unified Plot API (OpenMC-inspired)
- Voxel plots with HDF5 export
- Mesh tally visualization
- Geometry verification visualization
- Material composition visualization
- Tally data visualization (energy spectra, spatial distributions)
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

try:
    from smrforge.visualization.animations import (
        animate_3d_transient_plotly,
        animate_transient_matplotlib,
        create_comparison_animation,
    )

    _ANIMATIONS_AVAILABLE = True
except ImportError:
    _ANIMATIONS_AVAILABLE = False

try:
    from smrforge.visualization.comparison import (
        compare_designs_matplotlib,
        compare_designs_plotly,
        compare_metrics_matplotlib,
        overlay_comparison_matplotlib,
    )

    _COMPARISON_AVAILABLE = True
except ImportError:
    _COMPARISON_AVAILABLE = False

try:
    from smrforge.visualization.advanced import (
        create_dashboard,
        create_interactive_viewer,
        export_visualization,
        plot_isosurface,
        plot_material_boundaries,
        plot_ray_traced_geometry,
        plot_slice,
        plot_vector_field,
    )

    _ADVANCED_VIS_AVAILABLE = True
except ImportError:
    _ADVANCED_VIS_AVAILABLE = False

try:
    from smrforge.visualization.plot_api import Plot, create_plot

    _PLOT_API_AVAILABLE = True
except ImportError:
    _PLOT_API_AVAILABLE = False

try:
    from smrforge.visualization.voxel_plots import (
        convert_voxel_hdf5_to_vtk,
        export_voxel_to_hdf5,
        plot_voxel,
    )

    _VOXEL_PLOTS_AVAILABLE = True
except ImportError:
    _VOXEL_PLOTS_AVAILABLE = False

try:
    from smrforge.visualization.mesh_tally import (
        MeshTally,
        plot_mesh_tally,
        plot_multi_group_mesh_tally,
    )

    _MESH_TALLY_AVAILABLE = True
except ImportError:
    _MESH_TALLY_AVAILABLE = False

try:
    from smrforge.visualization.geometry_verification import (
        plot_geometry_consistency,
        plot_material_assignment,
        plot_overlap_detection,
    )

    _GEOMETRY_VERIFICATION_AVAILABLE = True
except ImportError:
    _GEOMETRY_VERIFICATION_AVAILABLE = False

try:
    from smrforge.visualization.material_composition import (
        plot_burnup_composition,
        plot_material_property,
        plot_nuclide_concentration,
    )

    _MATERIAL_COMPOSITION_AVAILABLE = True
except ImportError:
    _MATERIAL_COMPOSITION_AVAILABLE = False

try:
    from smrforge.visualization.tally_data import (
        plot_energy_spectrum,
        plot_spatial_distribution,
        plot_time_dependent_tally,
        plot_uncertainty,
    )

    _TALLY_DATA_AVAILABLE = True
except ImportError:
    _TALLY_DATA_AVAILABLE = False

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

if _ANIMATIONS_AVAILABLE:
    __all__.extend(
        [
            "animate_transient_matplotlib",
            "animate_3d_transient_plotly",
            "create_comparison_animation",
        ]
    )

if _COMPARISON_AVAILABLE:
    __all__.extend(
        [
            "compare_designs_matplotlib",
            "compare_designs_plotly",
            "compare_metrics_matplotlib",
            "overlay_comparison_matplotlib",
        ]
    )

if _ADVANCED_VIS_AVAILABLE:
    __all__.extend(
        [
            "plot_ray_traced_geometry",
            "plot_slice",
            "plot_isosurface",
            "plot_vector_field",
            "plot_material_boundaries",
            "create_dashboard",
            "create_interactive_viewer",
            "export_visualization",
        ]
    )

if _PLOT_API_AVAILABLE:
    __all__.extend(
        [
            "Plot",
            "create_plot",
        ]
    )

if _VOXEL_PLOTS_AVAILABLE:
    __all__.extend(
        [
            "plot_voxel",
            "export_voxel_to_hdf5",
            "convert_voxel_hdf5_to_vtk",
        ]
    )

if _MESH_TALLY_AVAILABLE:
    __all__.extend(
        [
            "MeshTally",
            "plot_mesh_tally",
            "plot_multi_group_mesh_tally",
        ]
    )

if _GEOMETRY_VERIFICATION_AVAILABLE:
    __all__.extend(
        [
            "plot_overlap_detection",
            "plot_geometry_consistency",
            "plot_material_assignment",
        ]
    )

if _MATERIAL_COMPOSITION_AVAILABLE:
    __all__.extend(
        [
            "plot_nuclide_concentration",
            "plot_material_property",
            "plot_burnup_composition",
        ]
    )

if _TALLY_DATA_AVAILABLE:
    __all__.extend(
        [
            "plot_energy_spectrum",
            "plot_spatial_distribution",
            "plot_time_dependent_tally",
            "plot_uncertainty",
        ]
    )
