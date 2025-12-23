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
    from smrforge.neutronics.solver import MultiGroupDiffusion, NeutronicsSolver

    _NEUTRONICS_AVAILABLE = True
except ImportError as e:
    import warnings

    warnings.warn(f"Could not import neutronics solver: {e}", ImportWarning)
    _NEUTRONICS_AVAILABLE = False

try:
    from smrforge.thermal import ThermalHydraulics  # Alias for ChannelThermalHydraulics
    from smrforge.thermal import (
        ChannelGeometry,
        ChannelThermalHydraulics,
        FlowRegime,
        FluidProperties,
    )

    _THERMAL_AVAILABLE = True
except ImportError as e:
    import warnings

    warnings.warn(f"Could not import thermal hydraulics: {e}", ImportWarning)
    _THERMAL_AVAILABLE = False

# Convenience functions and classes for easy usage
try:
    from smrforge.convenience import (  # Factory functions; High-level class
        SimpleReactor,
        analyze_preset,
        compare_designs,
        create_reactor,
        get_preset,
        list_presets,
        quick_keff,
    )

    _CONVENIENCE_AVAILABLE = True
except ImportError as e:
    import warnings

    warnings.warn(
        f"Could not import convenience functions: {e}\n"
        f"Some features may not be available. Please check your installation.",
        ImportWarning,
    )
    _CONVENIENCE_AVAILABLE = False

__all__ = [
    "__version__",
    "__version_info__",
    "get_version",
    "__author__",
    "constants",
]

# Add solver exports if available
if _NEUTRONICS_AVAILABLE:
    __all__.extend(["NeutronicsSolver", "MultiGroupDiffusion"])

# Add thermal exports if available
if _THERMAL_AVAILABLE:
    __all__.extend(
        [
            "ThermalHydraulics",
            "ChannelThermalHydraulics",
            "ChannelGeometry",
            "FluidProperties",
            "FlowRegime",
        ]
    )

# Add convenience exports if available
if _CONVENIENCE_AVAILABLE:
    __all__.extend(
        [
            "create_reactor",
            "list_presets",
            "get_preset",
            "quick_keff",
            "analyze_preset",
            "compare_designs",
            "SimpleReactor",
        ]
    )
