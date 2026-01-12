"""
Burnup solver for fuel depletion calculations.

This module provides:
- BurnupSolver: Main burnup/depletion solver class
- NuclideInventory: Tracks nuclide concentrations over time
- BurnupOptions: Configuration for burnup calculations
- LWR SMR-specific burnup features (gadolinium depletion, assembly/rod-wise tracking)
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
