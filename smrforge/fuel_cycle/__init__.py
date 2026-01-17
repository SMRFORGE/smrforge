"""
Fuel cycle optimization and refueling strategy optimization.

This module provides capabilities for:
- Fuel cycle optimization algorithms
- Refueling strategy optimization
- Enhanced thermal-hydraulics coupling for long transients
- Material aging and degradation models

Classes:
    FuelCycleOptimizer: Fuel cycle optimization algorithms
    RefuelingStrategyOptimizer: Refueling strategy optimization
    LongTermThermalCoupling: Enhanced thermal-hydraulics for long transients
    MaterialAging: Material aging and degradation models
"""

from smrforge.fuel_cycle.optimization import (
    FuelCycleOptimizer,
    RefuelingStrategyOptimizer,
)
from smrforge.fuel_cycle.long_term import LongTermThermalCoupling
from smrforge.fuel_cycle.material_aging import MaterialAging

__all__ = [
    "FuelCycleOptimizer",
    "RefuelingStrategyOptimizer",
    "LongTermThermalCoupling",
    "MaterialAging",
]
