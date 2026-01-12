"""
Safety analysis and transient simulations
"""

try:
    from smrforge.safety.transients import (
        AirWaterIngressAnalysis,
        ATWSTransient,
        BWRSMRTransient,
        FeedwaterLineBreakTransient,
        IntegralSMRTransient,
        LOCATransientLWR,
        LOFCTransient,
        PointKineticsParameters,
        PointKineticsSolver,
        PressurizerTransient,
        PWRSMRTransient,
        ReactivityInsertionAccident,
        RecirculationPumpTripTransient,
        SteamGeneratorTubeRuptureTransient,
        SteamLineBreakTransient,
        SteamSeparatorIssueTransient,
        TransientConditions,
        TransientType,
        decay_heat_ans_standard,
    )

    _SAFETY_AVAILABLE = True
except ImportError as e:
    import warnings

    warnings.warn(f"Could not import safety transients: {e}", ImportWarning)
    _SAFETY_AVAILABLE = False

__all__ = []
if _SAFETY_AVAILABLE:
    __all__.extend(
        [
            "TransientType",
            "TransientConditions",
            "PointKineticsParameters",
            "PointKineticsSolver",
            "LOFCTransient",
            "ATWSTransient",
            "ReactivityInsertionAccident",
            "AirWaterIngressAnalysis",
            "decay_heat_ans_standard",
            # LWR SMR transient classes
            "PWRSMRTransient",
            "SteamLineBreakTransient",
            "FeedwaterLineBreakTransient",
            "PressurizerTransient",
            "LOCATransientLWR",
            "BWRSMRTransient",
            "RecirculationPumpTripTransient",
            "SteamSeparatorIssueTransient",
            "IntegralSMRTransient",
            "SteamGeneratorTubeRuptureTransient",
        ]
    )
