"""
Visualization and plotting tools for reactor analysis.

This module provides visualization capabilities for:
- Geometry visualization (2D and 3D)
- Flux and power distribution plots
- Temperature distribution visualization
"""

try:
    from smrforge.visualization.geometry import (
        plot_core_layout,
        plot_flux_on_geometry,
        plot_power_distribution,
        plot_temperature_distribution,
    )

    _VISUALIZATION_AVAILABLE = True
except ImportError as e:
    import warnings

    warnings.warn(f"Could not import visualization module: {e}", ImportWarning)
    _VISUALIZATION_AVAILABLE = False

__all__ = []
if _VISUALIZATION_AVAILABLE:
    __all__.extend(
        [
            "plot_core_layout",
            "plot_flux_on_geometry",
            "plot_power_distribution",
            "plot_temperature_distribution",
        ]
    )
