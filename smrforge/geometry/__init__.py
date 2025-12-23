"""
Reactor geometry and spatial discretization
"""

try:
    from smrforge.geometry.core_geometry import (
        CoreType,
        GeometryExporter,
        LatticeType,
        PebbleBedCore,
        PrismaticCore,
        compute_distance_matrix,
    )

    _GEOMETRY_AVAILABLE = True
except ImportError as e:
    import warnings

    warnings.warn(f"Could not import geometry module: {e}", ImportWarning)
    _GEOMETRY_AVAILABLE = False

__all__ = []
if _GEOMETRY_AVAILABLE:
    __all__.extend(
        [
            "CoreType",
            "LatticeType",
            "PrismaticCore",
            "PebbleBedCore",
            "GeometryExporter",
            "compute_distance_matrix",
        ]
    )
