"""
Structural mechanics and fuel rod performance analysis.

This module provides capabilities for:
- Fuel rod mechanics (stress, strain, deformation)
- Thermal expansion calculations
- Pellet-cladding interaction (PCI)
- Fuel swelling models
- Creep models (primary, secondary, tertiary, irradiation-enhanced)
- Material property degradation for long-term analysis

Classes:
    FuelRodMechanics: Main class for fuel rod structural analysis
    ThermalExpansion: Thermal expansion calculations
    StressStrain: Stress and strain analysis
    PelletCladdingInteraction: PCI modeling
    FuelSwelling: Fuel swelling models
    CreepModel: Creep models for fuel rod materials
    MaterialDegradation: Material degradation models for long-term analysis
"""

from smrforge.mechanics.fuel_rod import (
    FuelRodMechanics,
    FuelSwelling,
    PelletCladdingInteraction,
    StressStrain,
    ThermalExpansion,
    CreepModel,
    MaterialDegradation,
)

__all__ = [
    "FuelRodMechanics",
    "ThermalExpansion",
    "StressStrain",
    "PelletCladdingInteraction",
    "FuelSwelling",
    "CreepModel",
    "MaterialDegradation",
]
