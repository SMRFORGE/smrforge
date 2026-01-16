"""
Thermal-hydraulics analysis
"""

try:
    from smrforge.thermal.hydraulics import (
        ChannelGeometry,
        ChannelThermalHydraulics,
        FlowRegime,
        FluidProperties,
    )

    # Alias for backward compatibility
    ThermalHydraulics = ChannelThermalHydraulics
    _THERMAL_AVAILABLE = True
except ImportError as e:
    import warnings

    warnings.warn(f"Could not import thermal hydraulics: {e}", ImportWarning)
    _THERMAL_AVAILABLE = False

# Try to import lumped-parameter thermal hydraulics (optional)
try:
    from smrforge.thermal.lumped import (
        LumpedThermalHydraulics,
        ThermalLump,
        ThermalResistance,
    )

    _LUMPED_THERMAL_AVAILABLE = True
except ImportError:
    _LUMPED_THERMAL_AVAILABLE = False

__all__ = []
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

if _LUMPED_THERMAL_AVAILABLE:
    __all__.extend(
        [
            "LumpedThermalHydraulics",
            "ThermalLump",
            "ThermalResistance",
        ]
    )
