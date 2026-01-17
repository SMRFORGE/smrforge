"""
Structural mechanics and fuel rod performance analysis.

This module provides capabilities for:
- Fuel rod mechanics (stress, strain, deformation)
- Thermal expansion calculations
- Pellet-cladding interaction (PCI)
- Fuel swelling models
- Material property degradation

Classes:
    FuelRodMechanics: Main class for fuel rod structural analysis
    ThermalExpansion: Thermal expansion calculations
    StressStrain: Stress and strain analysis
    PelletCladdingInteraction: PCI modeling
    FuelSwelling: Fuel swelling models
"""

from smrforge.mechanics.fuel_rod import (
    FuelRodMechanics,
    FuelSwelling,
    PelletCladdingInteraction,
    StressStrain,
    ThermalExpansion,
)

__all__ = [
    "FuelRodMechanics",
    "ThermalExpansion",
    "StressStrain",
    "PelletCladdingInteraction",
    "FuelSwelling",
]
