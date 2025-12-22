"""
Core reactor components and materials database
"""

from smrforge.core import constants, materials_database

# Try to import reactor_core if available
try:
    from smrforge.core.reactor_core import (
        NuclearDataCache,
        CrossSectionTable,
        DecayData,
        Nuclide,
        Library,
    )
    _CORE_DATA_AVAILABLE = True
except ImportError:
    _CORE_DATA_AVAILABLE = False

try:
    from smrforge.core.resonance_selfshield import (
        ResonanceSelfShielding,
        BondarenkoMethod,
        SubgroupMethod,
        EquivalenceTheory,
    )
    _RESONANCE_AVAILABLE = True
except ImportError:
    _RESONANCE_AVAILABLE = False

try:
    from smrforge.core.endf_parser import (
        ENDFEvaluation,
        ENDFCompatibility,
        ReactionData,
    )
    _ENDF_PARSER_AVAILABLE = True
except ImportError:
    _ENDF_PARSER_AVAILABLE = False

__all__ = ['constants', 'materials_database']

if _CORE_DATA_AVAILABLE:
    __all__.extend([
        'NuclearDataCache',
        'CrossSectionTable',
        'DecayData',
        'Nuclide',
        'Library',
    ])

if _RESONANCE_AVAILABLE:
    __all__.extend([
        'ResonanceSelfShielding',
        'BondarenkoMethod',
        'SubgroupMethod',
        'EquivalenceTheory',
    ])

if _ENDF_PARSER_AVAILABLE:
    __all__.extend([
        'ENDFEvaluation',
        'ENDFCompatibility',
        'ReactionData',
    ])
