"""
Reactor geometry and spatial discretization.

This module provides:
- Core geometry classes (PrismaticCore, PebbleBedCore)
- Geometry import/export
- Mesh generation
- 3D mesh support
- Enhanced geometry validation
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
        BankPriority,
        ControlRod,
        ControlRodBank,
        ControlRodSequence,
        ControlRodSystem,
        ControlRodType,
        ScramEvent,
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

# Import advanced geometry importers if available
try:
    from smrforge.geometry.advanced_import import (
        AdvancedGeometryImporter,
        CSGCell,
        CSGSurface,
        GeometryConverter,
        Lattice,
    )

    _ADVANCED_IMPORTERS_AVAILABLE = True
except ImportError:
    _ADVANCED_IMPORTERS_AVAILABLE = False

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

# Import advanced 3D mesh generation if available
try:
    from smrforge.geometry.advanced_mesh import (
        AdvancedMeshGenerator3D,
        MeshConverter,
        StructuredMesh3D,
    )

    _ADVANCED_MESH_AVAILABLE = True
except ImportError:
    _ADVANCED_MESH_AVAILABLE = False

# Import 3D mesh support if available
try:
    from smrforge.geometry.mesh_3d import (
        Mesh3D,
        Surface,
        combine_meshes,
        extract_cylinder_mesh,
        extract_hexagonal_prism_mesh,
        extract_sphere_mesh,
    )
    from smrforge.geometry.mesh_extraction import (
        add_flux_to_mesh,
        add_power_to_mesh,
        extract_block_mesh,
        extract_coolant_channel_mesh,
        extract_core_surface_mesh,
        extract_core_volume_mesh,
        extract_fuel_channel_mesh,
        extract_material_boundaries,
        extract_pebble_bed_volume_mesh,
        extract_pebble_mesh,
    )

    _MESH_3D_AVAILABLE = True
except ImportError:
    _MESH_3D_AVAILABLE = False

# Import geometry validation if available
try:
    from smrforge.geometry.validation import (
        Gap,
        ValidationReport,
        check_distances_and_clearances,
        check_gaps_and_boundaries,
        comprehensive_validation,
        validate_assembly_placement,
        validate_control_rod_insertion,
        validate_fuel_loading_pattern,
        validate_geometry_completeness,
        validate_material_connectivity,
    )

    _VALIDATION_AVAILABLE = True
except ImportError:
    _VALIDATION_AVAILABLE = False

# Import LWR SMR geometry if available
try:
    from smrforge.geometry.lwr_smr import (
        AssemblyType,
        BWRSMRCore,
        ControlBlade,
        ControlRodCluster,
        FuelAssembly,
        FuelRod,
        InVesselSteamGenerator,
        IntegratedPrimarySystem,
        PWRSMRCore,
        SpacerGrid,
        SteamGeneratorTube,
        WaterChannel,
    )

    _LWR_SMR_AVAILABLE = True
except ImportError as e:
    import warnings

    warnings.warn(f"Could not import LWR SMR geometry: {e}", ImportWarning)
    _LWR_SMR_AVAILABLE = False

# Import Fast Reactor SMR geometry if available
try:
    from smrforge.geometry.fast_reactor_smr import (
        FastReactorAssembly,
        FastReactorFuelPin,
        FastReactorSMRCore,
        FastReactorType,
        LiquidMetalChannel,
        WireWrapSpacer,
    )

    _FAST_REACTOR_SMR_AVAILABLE = True
except ImportError as e:
    import warnings

    warnings.warn(f"Could not import Fast Reactor SMR geometry: {e}", ImportWarning)
    _FAST_REACTOR_SMR_AVAILABLE = False

# Import SMR mesh optimization if available
try:
    from smrforge.geometry.smr_mesh_optimization import (
        SMRMeshOptimizer,
        SMRMeshParams,
    )

    _SMR_MESH_OPTIMIZATION_AVAILABLE = True
except ImportError as e:
    import warnings

    warnings.warn(f"Could not import SMR mesh optimization: {e}", ImportWarning)
    _SMR_MESH_OPTIMIZATION_AVAILABLE = False

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
            "BankPriority",
            "ControlRodSequence",
            "ScramEvent",
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

if _ADVANCED_IMPORTERS_AVAILABLE:
    __all__.extend(
        [
            "AdvancedGeometryImporter",
            "GeometryConverter",
            "CSGSurface",
            "CSGCell",
            "Lattice",
        ]
    )

if _MESH_GENERATION_AVAILABLE:
    __all__.extend(
        [
            "AdvancedMeshGenerator",
            "MeshQuality",
            "MeshType",
            "compute_mesh_gradient",
        ]
    )

if _ADVANCED_MESH_AVAILABLE:
    __all__.extend(
        [
            "AdvancedMeshGenerator3D",
            "StructuredMesh3D",
            "MeshConverter",
        ]
    )

if _MESH_3D_AVAILABLE:
    __all__.extend(
        [
            "Mesh3D",
            "Surface",
            "combine_meshes",
            "extract_cylinder_mesh",
            "extract_hexagonal_prism_mesh",
            "extract_sphere_mesh",
            "extract_block_mesh",
            "extract_fuel_channel_mesh",
            "extract_coolant_channel_mesh",
            "extract_pebble_mesh",
            "extract_core_surface_mesh",
            "extract_core_volume_mesh",
            "extract_pebble_bed_volume_mesh",
            "extract_material_boundaries",
            "add_flux_to_mesh",
            "add_power_to_mesh",
        ]
    )

if _VALIDATION_AVAILABLE:
    __all__.extend(
        [
            "Gap",
            "ValidationReport",
            "validate_geometry_completeness",
            "check_gaps_and_boundaries",
            "validate_material_connectivity",
            "check_distances_and_clearances",
            "validate_assembly_placement",
            "validate_control_rod_insertion",
            "validate_fuel_loading_pattern",
            "comprehensive_validation",
        ]
    )

if _LWR_SMR_AVAILABLE:
    __all__.extend(
        [
            "PWRSMRCore",
            "BWRSMRCore",
            "FuelAssembly",
            "FuelRod",
            "SpacerGrid",
            "WaterChannel",
            "ControlRodCluster",
            "ControlBlade",
            "AssemblyType",
            "InVesselSteamGenerator",
            "SteamGeneratorTube",
            "IntegratedPrimarySystem",
        ]
    )

if _FAST_REACTOR_SMR_AVAILABLE:
    __all__.extend(
        [
            "FastReactorSMRCore",
            "FastReactorAssembly",
            "FastReactorFuelPin",
            "WireWrapSpacer",
            "LiquidMetalChannel",
            "FastReactorType",
        ]
    )

if _SMR_MESH_OPTIMIZATION_AVAILABLE:
    __all__.extend(
        [
            "SMRMeshOptimizer",
            "SMRMeshParams",
        ]
    )
