"""
Safety analysis and transient simulations
"""

try:
    from smrforge.safety.transients import (
        TransientType,
        TransientConditions,
        PointKineticsParameters,
        PointKineticsSolver,
        LOFCTransient,
        ATWSTransient,
        ReactivityInsertionAccident,
        AirWaterIngressAnalysis,
        decay_heat_ans_standard,
    )
    _SAFETY_AVAILABLE = True
except ImportError as e:
    import warnings
    warnings.warn(f"Could not import safety transients: {e}", ImportWarning)
    _SAFETY_AVAILABLE = False

__all__ = []
if _SAFETY_AVAILABLE:
    __all__.extend([
        'TransientType',
        'TransientConditions',
        'PointKineticsParameters',
        'PointKineticsSolver',
        'LOFCTransient',
        'ATWSTransient',
        'ReactivityInsertionAccident',
        'AirWaterIngressAnalysis',
        'decay_heat_ans_standard',
    ])
