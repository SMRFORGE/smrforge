"""
Core reactor components and materials database
"""

from smrforge.core import constants, materials_database

# Try to import reactor_core if available
try:
    from smrforge.core.reactor_core import (
        CrossSectionTable,
        DecayData,
        Library,
        NuclearDataCache,
        Nuclide,
        NuclideInventoryTracker,
        get_fission_yield_data,
        get_thermal_scattering_data,
        get_standard_endf_directory,
        organize_bulk_endf_downloads,
        scan_endf_directory,
    )

    _CORE_DATA_AVAILABLE = True
except ImportError:
    _CORE_DATA_AVAILABLE = False

try:
    from smrforge.core.endf_setup import (
        setup_endf_data_interactive,
        validate_endf_setup,
    )

    _ENDF_SETUP_AVAILABLE = True
except ImportError:
    _ENDF_SETUP_AVAILABLE = False

try:
    from smrforge.core.resonance_selfshield import (
        BondarenkoMethod,
        EquivalenceTheory,
        ResonanceSelfShielding,
        SubgroupMethod,
    )

    _RESONANCE_AVAILABLE = True
except ImportError:
    _RESONANCE_AVAILABLE = False

try:
    from smrforge.core.control_rod_worth import (
        ControlRodWorthCalculator,
        WorthProfile,
        calculate_rod_worth_from_neutronics,
        calculate_rod_worth_pcm,
        calculate_worth_profile_from_neutronics,
    )

    _CONTROL_ROD_WORTH_AVAILABLE = True
except ImportError:
    _CONTROL_ROD_WORTH_AVAILABLE = False

try:
    from smrforge.core.multigroup_advanced import (
        EquivalenceTheory,
        SPHFactors,
        SPHMethod,
        apply_sph_to_multigroup_table,
    )

    _MULTIGROUP_ADVANCED_AVAILABLE = True
except ImportError:
    _MULTIGROUP_ADVANCED_AVAILABLE = False

try:
    from smrforge.core.energy_angle_parser import (
        AngularDistribution,
        ENDFEnergyAngleParser,
        EnergyAngleData,
        get_energy_angle_data,
    )

    _ENERGY_ANGLE_PARSER_AVAILABLE = True
except ImportError:
    _ENERGY_ANGLE_PARSER_AVAILABLE = False

try:
    from smrforge.core.endf_parser import (
        ENDFCompatibility,
        ENDFEvaluation,
        ReactionData,
    )

    _ENDF_PARSER_AVAILABLE = True
except ImportError:
    _ENDF_PARSER_AVAILABLE = False

__all__ = ["constants", "materials_database"]

if _CORE_DATA_AVAILABLE:
    __all__.extend(
        [
            "NuclearDataCache",
            "CrossSectionTable",
            "DecayData",
            "Nuclide",
            "NuclideInventoryTracker",
            "Library",
            "get_fission_yield_data",
            "get_thermal_scattering_data",
            "get_standard_endf_directory",
            "organize_bulk_endf_downloads",
            "scan_endf_directory",
        ]
    )

if _ENDF_SETUP_AVAILABLE:
    __all__.extend(
        [
            "setup_endf_data_interactive",
            "validate_endf_setup",
        ]
    )

if _RESONANCE_AVAILABLE:
    __all__.extend(
        [
            "ResonanceSelfShielding",
            "BondarenkoMethod",
            "SubgroupMethod",
            "EquivalenceTheory",
        ]
    )

if _ENDF_PARSER_AVAILABLE:
    __all__.extend(
        [
            "ENDFEvaluation",
            "ENDFCompatibility",
            "ReactionData",
        ]
    )

if _CONTROL_ROD_WORTH_AVAILABLE:
    __all__.extend(
        [
            "ControlRodWorthCalculator",
            "WorthProfile",
            "calculate_rod_worth_from_neutronics",
            "calculate_rod_worth_pcm",
            "calculate_worth_profile_from_neutronics",
        ]
    )

if _MULTIGROUP_ADVANCED_AVAILABLE:
    __all__.extend(
        [
            "SPHMethod",
            "SPHFactors",
            "EquivalenceTheory",
            "apply_sph_to_multigroup_table",
        ]
    )

if _ENERGY_ANGLE_PARSER_AVAILABLE:
    __all__.extend(
        [
            "ENDFEnergyAngleParser",
            "EnergyAngleData",
            "AngularDistribution",
            "get_energy_angle_data",
        ]
    )
