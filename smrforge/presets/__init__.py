"""
Reference reactor designs and presets
"""

try:
    from smrforge.presets.htgr import (
        BWRX300,
        GTMHR350,
        HTRPM200,
        CAREM32MWe,
        DesignLibrary,
        MicroHTGR,
        NuScalePWR77MWe,
        SMART100MWe,
        ValarAtomicsReactor,
    )

    try:
        from smrforge.presets.msr import LiquidFuelMSR
    except ImportError:
        LiquidFuelMSR = None  # type: ignore[misc, assignment]

    _PRESETS_AVAILABLE = True
except ImportError as e:
    import warnings

    warnings.warn(f"Could not import presets module: {e}", ImportWarning)
    _PRESETS_AVAILABLE = False

__all__ = []
if _PRESETS_AVAILABLE:
    __all__.extend(
        [
            "ValarAtomicsReactor",
            "GTMHR350",
            "HTRPM200",
            "MicroHTGR",
            "DesignLibrary",
            "NuScalePWR77MWe",
            "SMART100MWe",
            "CAREM32MWe",
            "BWRX300",
        ]
    )
    if LiquidFuelMSR is not None:
        __all__.append("LiquidFuelMSR")
