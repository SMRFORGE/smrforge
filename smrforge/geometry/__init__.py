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

# Import control rods if available
try:
    from smrforge.geometry.control_rods import (
        ControlRod,
        ControlRodBank,
        ControlRodSystem,
        ControlRodType,
    )

    _CONTROL_RODS_AVAILABLE = True
except ImportError:
    _CONTROL_RODS_AVAILABLE = False

# Import assembly management if available
try:
    from smrforge.geometry.assembly import (
        Assembly,
        AssemblyManager,
        FuelBatch,
        RefuelingEvent,
        RefuelingPattern,
    )

    _ASSEMBLY_AVAILABLE = True
except ImportError:
    _ASSEMBLY_AVAILABLE = False

# Import geometry importers if available
try:
    from smrforge.geometry.importers import GeometryImporter

    _IMPORTERS_AVAILABLE = True
except ImportError:
    _IMPORTERS_AVAILABLE = False

# Import mesh generation if available
try:
    from smrforge.geometry.mesh_generation import (
        AdvancedMeshGenerator,
        MeshQuality,
        MeshType,
        compute_mesh_gradient,
    )

    _MESH_GENERATION_AVAILABLE = True
except ImportError:
    _MESH_GENERATION_AVAILABLE = False

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

if _CONTROL_RODS_AVAILABLE:
    __all__.extend(
        [
            "ControlRod",
            "ControlRodBank",
            "ControlRodSystem",
            "ControlRodType",
        ]
    )

if _ASSEMBLY_AVAILABLE:
    __all__.extend(
        [
            "Assembly",
            "AssemblyManager",
            "FuelBatch",
            "RefuelingEvent",
            "RefuelingPattern",
        ]
    )

if _IMPORTERS_AVAILABLE:
    __all__.append("GeometryImporter")

if _MESH_GENERATION_AVAILABLE:
    __all__.extend(
        [
            "AdvancedMeshGenerator",
            "MeshQuality",
            "MeshType",
            "compute_mesh_gradient",
        ]
    )
