"""
Fuel performance modeling.

This module provides fuel performance analysis including:
- Fuel temperature calculations
- Fuel swelling models
- Fission gas release
- Cladding performance

Classes:
    FuelProperties: Fuel pellet properties
    CladProperties: Cladding properties
    FuelPerformance: Fuel performance analyzer
"""

from smrforge.fuel.performance import (
    CladProperties,
    FuelPerformance,
    FuelProperties,
)

__all__ = [
    "FuelProperties",
    "CladProperties",
    "FuelPerformance",
]
