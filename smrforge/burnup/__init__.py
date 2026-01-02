"""
Burnup solver for fuel depletion calculations.

This module provides:
- BurnupSolver: Main burnup/depletion solver class
- NuclideInventory: Tracks nuclide concentrations over time
- BurnupOptions: Configuration for burnup calculations
"""

from .solver import BurnupSolver, BurnupOptions, NuclideInventory

__all__ = ["BurnupSolver", "BurnupOptions", "NuclideInventory"]

