"""
Fuel cycle optimization and refueling strategy optimization.

This module provides capabilities for:
- Fuel cycle optimization algorithms
- Refueling strategy optimization
- Enhanced thermal-hydraulics coupling for long transients
- Material aging and degradation models
- Advanced optimization algorithms (Genetic Algorithm, Particle Swarm Optimization)

Classes:
    FuelCycleOptimizer: Fuel cycle optimization algorithms
    RefuelingStrategyOptimizer: Refueling strategy optimization
    LongTermThermalCoupling: Enhanced thermal-hydraulics for long transients
    MaterialAging: Material aging and degradation models
    GeneticAlgorithm: Genetic algorithm optimizer
    ParticleSwarmOptimization: Particle swarm optimizer
"""

from smrforge.fuel_cycle.optimization import (
    FuelCycleOptimizer,
    RefuelingStrategyOptimizer,
)
from smrforge.fuel_cycle.long_term import LongTermThermalCoupling
from smrforge.fuel_cycle.material_aging import MaterialAging

# Try to import advanced optimization algorithms
try:
    from smrforge.fuel_cycle.advanced_optimization import (
        GeneticAlgorithm,
        ParticleSwarmOptimization,
        OptimizationResult,
    )
    _ADVANCED_OPT_AVAILABLE = True
except ImportError:
    _ADVANCED_OPT_AVAILABLE = False
    GeneticAlgorithm = None
    ParticleSwarmOptimization = None
    OptimizationResult = None

__all__ = [
    "FuelCycleOptimizer",
    "RefuelingStrategyOptimizer",
    "LongTermThermalCoupling",
    "MaterialAging",
]

if _ADVANCED_OPT_AVAILABLE:
    __all__.extend(
        [
            "GeneticAlgorithm",
            "ParticleSwarmOptimization",
            "OptimizationResult",
        ]
    )
