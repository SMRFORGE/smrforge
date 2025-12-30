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
        get_standard_endf_directory,
        organize_bulk_endf_downloads,
        scan_endf_directory,
    )

    _CORE_DATA_AVAILABLE = True
except ImportError:
    _CORE_DATA_AVAILABLE = False

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
            "Library",
            "get_standard_endf_directory",
            "organize_bulk_endf_downloads",
            "scan_endf_directory",
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
