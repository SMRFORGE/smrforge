"""
Burnup solver for fuel depletion calculations.

This module provides:
- BurnupSolver: Main burnup/depletion solver class
- NuclideInventory: Tracks nuclide concentrations over time
- BurnupOptions: Configuration for burnup calculations
- LWR SMR-specific burnup features (gadolinium depletion, assembly/rod-wise tracking)
- Enhanced visualization tools (batch comparison, refueling cycles, control rod effects)
"""

from .solver import BurnupSolver, BurnupOptions, NuclideInventory

try:
    from .lwr_burnup import (
        AssemblyBurnup,
        AssemblyWiseBurnupTracker,
        GadoliniumDepletion,
        GadoliniumPoison,
        RodBurnup,
        RodWiseBurnupTracker,
    )
    _LWR_BURNUP_AVAILABLE = True
except ImportError:
    _LWR_BURNUP_AVAILABLE = False

try:
    from .fuel_management_integration import BurnupFuelManagerIntegration
    _FUEL_MANAGEMENT_INTEGRATION_AVAILABLE = True
except ImportError:
    _FUEL_MANAGEMENT_INTEGRATION_AVAILABLE = False

try:
    from .visualization import (
        plot_batch_comparison,
        plot_refueling_cycles,
        plot_control_rod_effects,
        plot_burnup_dashboard_enhanced,
    )
    _VISUALIZATION_AVAILABLE = True
except ImportError:
    _VISUALIZATION_AVAILABLE = False

__all__ = ["BurnupSolver", "BurnupOptions", "NuclideInventory"]

if _LWR_BURNUP_AVAILABLE:
    __all__.extend(
        [
            "GadoliniumDepletion",
            "GadoliniumPoison",
            "AssemblyBurnup",
            "AssemblyWiseBurnupTracker",
            "RodBurnup",
            "RodWiseBurnupTracker",
        ]
    )

if _FUEL_MANAGEMENT_INTEGRATION_AVAILABLE:
    __all__.append("BurnupFuelManagerIntegration")

if _VISUALIZATION_AVAILABLE:
    __all__.extend(
        [
            "plot_batch_comparison",
            "plot_refueling_cycles",
            "plot_control_rod_effects",
            "plot_burnup_dashboard_enhanced",
        ]
    )
