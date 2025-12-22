"""
Thermal-hydraulics analysis
"""

try:
    from smrforge.thermal.hydraulics import (
        ChannelThermalHydraulics,
        ChannelGeometry,
        FluidProperties,
        FlowRegime,
    )
    # Alias for backward compatibility
    ThermalHydraulics = ChannelThermalHydraulics
    _THERMAL_AVAILABLE = True
except ImportError as e:
    import warnings
    warnings.warn(f"Could not import thermal hydraulics: {e}", ImportWarning)
    _THERMAL_AVAILABLE = False

__all__ = []
if _THERMAL_AVAILABLE:
    __all__.extend([
        'ThermalHydraulics',
        'ChannelThermalHydraulics',
        'ChannelGeometry',
        'FluidProperties',
        'FlowRegime',
    ])
