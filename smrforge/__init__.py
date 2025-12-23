"""
SMRForge - Small Modular Reactor Design and Analysis Toolkit
============================================================
A comprehensive toolkit for nuclear reactor design, analysis, and optimization.

Main modules:
- core: Reactor components and materials (✅ Stable)
- neutronics: Reactor physics and neutron transport (✅ Stable)
- thermal: Thermal-hydraulics analysis (🟡 Experimental)
- safety: Safety analysis and transients (🟡 Experimental)
- uncertainty: Uncertainty quantification (🟡 Experimental)
- fuel: Fuel performance modeling (❌ Not implemented)
- optimization: Design optimization (❌ Not implemented)
- io: Input/output utilities (❌ Not implemented)
- visualization: Plotting tools (❌ Not implemented)
- control: Control systems (❌ Not implemented)
- economics: Cost modeling (❌ Not implemented)

⚠️ Feature Status: See FEATURE_STATUS.md for detailed status of each module.
"""

# Import version from dedicated module
from smrforge.__version__ import __version__, __version_info__, get_version

__author__ = "SMRForge Development Team"

# Core imports
from smrforge.core import constants

# Expose key classes at package level
try:
    from smrforge.neutronics.solver import NeutronicsSolver, MultiGroupDiffusion
    _NEUTRONICS_AVAILABLE = True
except ImportError as e:
    import warnings
    warnings.warn(f"Could not import neutronics solver: {e}", ImportWarning)
    _NEUTRONICS_AVAILABLE = False

try:
    from smrforge.thermal import (
        ChannelThermalHydraulics,
        ThermalHydraulics,  # Alias for ChannelThermalHydraulics
        ChannelGeometry,
        FluidProperties,
        FlowRegime,
    )
    _THERMAL_AVAILABLE = True
except ImportError as e:
    import warnings
    warnings.warn(f"Could not import thermal hydraulics: {e}", ImportWarning)
    _THERMAL_AVAILABLE = False

# Convenience functions and classes for easy usage
try:
    from smrforge.convenience import (
        # Factory functions
        create_reactor,
        list_presets,
        get_preset,
        quick_keff,
        analyze_preset,
        compare_designs,
        # High-level class
        SimpleReactor,
    )
    _CONVENIENCE_AVAILABLE = True
except ImportError as e:
    import warnings
    warnings.warn(f"Could not import convenience functions: {e}", ImportWarning)
    _CONVENIENCE_AVAILABLE = False

__all__ = [
    '__version__',
    '__version_info__',
    'get_version',
    '__author__',
    'constants',
]

# Add solver exports if available
if _NEUTRONICS_AVAILABLE:
    __all__.extend(['NeutronicsSolver', 'MultiGroupDiffusion'])

# Add thermal exports if available
if _THERMAL_AVAILABLE:
    __all__.extend([
        'ThermalHydraulics',
        'ChannelThermalHydraulics',
        'ChannelGeometry',
        'FluidProperties',
        'FlowRegime',
    ])

# Add convenience exports if available
if _CONVENIENCE_AVAILABLE:
    __all__.extend([
        'create_reactor',
        'list_presets',
        'get_preset',
        'quick_keff',
        'analyze_preset',
        'compare_designs',
        'SimpleReactor',
    ])
