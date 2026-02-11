"""
Material aging and degradation models.

This module provides models for material property degradation over time,
including:
- Irradiation damage (neutron fluence effects)
- Thermal aging (temperature and time effects)
- Creep and fatigue
- Corrosion and oxidation
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, Optional

import numpy as np

from ..utils.logging import get_logger

logger = get_logger("smrforge.fuel_cycle.material_aging")


@dataclass
class MaterialAging:
    """
    Material aging and degradation models.

    Models material property degradation due to:
    - Neutron irradiation (fluence effects)
    - Thermal aging (temperature and time)
    - Creep and fatigue
    - Corrosion/oxidation

    Attributes:
        material_type: Material type ('graphite', 'zircaloy', 'steel', 'fuel')
        initial_properties: Initial material properties dictionary
        aging_models: Dictionary of aging models for different properties
    """

    material_type: str
    initial_properties: Dict[str, float]
    aging_models: Dict[str, Callable] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize aging models based on material type."""
        if not self.aging_models:
            self.aging_models = self._get_default_aging_models()

    def _get_default_aging_models(self) -> Dict[str, Callable]:
        """Get default aging models for material type."""
        if self.material_type == "graphite":
            return {
                "thermal_conductivity": self._graphite_conductivity_aging,
                "youngs_modulus": self._graphite_modulus_aging,
                "density": self._graphite_density_aging,
            }
        elif self.material_type == "zircaloy":
            return {
                "thermal_conductivity": self._zircaloy_conductivity_aging,
                "yield_strength": self._zircaloy_strength_aging,
                "corrosion": self._zircaloy_corrosion_aging,
            }
        elif self.material_type == "fuel":
            return {
                "thermal_conductivity": self._fuel_conductivity_aging,
                "density": self._fuel_density_aging,
                "swelling": self._fuel_swelling_aging,
            }
        else:
            # Generic aging model
            return {
                "thermal_conductivity": self._generic_aging,
            }

    def calculate_aged_properties(
        self,
        time: float,  # days
        temperature: float,  # K
        fluence: Optional[float] = None,  # n/cm²
        stress: Optional[float] = None,  # Pa
    ) -> Dict[str, float]:
        """
        Calculate material properties after aging.

        Args:
            time: Exposure time [days]
            temperature: Temperature [K]
            fluence: Neutron fluence [n/cm²] (optional)
            stress: Applied stress [Pa] (optional)

        Returns:
            Dictionary with aged material properties
        """
        aged_properties = self.initial_properties.copy()

        for property_name, aging_model in self.aging_models.items():
            if property_name in self.initial_properties:
                initial_value = self.initial_properties[property_name]
                aged_value = aging_model(
                    initial_value, time, temperature, fluence, stress
                )
                aged_properties[property_name] = aged_value

        return aged_properties

    # Graphite aging models
    def _graphite_conductivity_aging(
        self,
        initial: float,
        time: float,
        temperature: float,
        fluence: Optional[float],
        stress: Optional[float],
    ) -> float:
        """Graphite thermal conductivity degradation."""
        # Irradiation damage reduces conductivity
        if fluence is not None:
            # Typical: 20-30% reduction at high fluence
            fluence_factor = 1.0 - 0.25 * (fluence / 1e22) ** 0.5
            fluence_factor = max(0.5, fluence_factor)  # Minimum 50%
        else:
            fluence_factor = 1.0

        # Thermal aging (oxidation)
        time_years = time / 365.25
        oxidation_factor = 1.0 - 0.01 * time_years  # 1% per year
        oxidation_factor = max(0.8, oxidation_factor)  # Minimum 80%

        aged = initial * fluence_factor * oxidation_factor
        return aged

    def _graphite_modulus_aging(
        self,
        initial: float,
        time: float,
        temperature: float,
        fluence: Optional[float],
        stress: Optional[float],
    ) -> float:
        """Graphite Young's modulus degradation."""
        # Irradiation increases modulus initially, then decreases
        if fluence is not None:
            # Simplified: net decrease at high fluence
            fluence_factor = 1.0 - 0.15 * (fluence / 1e22) ** 0.3
            fluence_factor = max(0.7, fluence_factor)
        else:
            fluence_factor = 1.0

        aged = initial * fluence_factor
        return aged

    def _graphite_density_aging(
        self,
        initial: float,
        time: float,
        temperature: float,
        fluence: Optional[float],
        stress: Optional[float],
    ) -> float:
        """Graphite density change (swelling/shrinkage)."""
        # Graphite can shrink or swell depending on conditions
        if fluence is not None:
            # Typical: shrinkage at low fluence, swelling at high fluence
            density_change = -0.02 * (fluence / 1e22) ** 0.5
        else:
            density_change = 0.0

        aged = initial * (1.0 + density_change)
        return aged

    # Zircaloy aging models
    def _zircaloy_conductivity_aging(
        self,
        initial: float,
        time: float,
        temperature: float,
        fluence: Optional[float],
        stress: Optional[float],
    ) -> float:
        """Zircaloy thermal conductivity degradation."""
        # Irradiation damage reduces conductivity slightly
        if fluence is not None:
            fluence_factor = 1.0 - 0.05 * (fluence / 1e22) ** 0.3
            fluence_factor = max(0.9, fluence_factor)
        else:
            fluence_factor = 1.0

        aged = initial * fluence_factor
        return aged

    def _zircaloy_strength_aging(
        self,
        initial: float,
        time: float,
        temperature: float,
        fluence: Optional[float],
        stress: Optional[float],
    ) -> float:
        """Zircaloy yield strength change."""
        # Irradiation hardening increases strength initially
        if fluence is not None:
            # Hardening then softening
            if fluence < 1e21:
                strength_factor = 1.0 + 0.2 * (fluence / 1e21)
            else:
                strength_factor = 1.2 - 0.1 * ((fluence - 1e21) / 1e22)
            strength_factor = max(0.8, min(1.3, strength_factor))
        else:
            strength_factor = 1.0

        aged = initial * strength_factor
        return aged

    def _zircaloy_corrosion_aging(
        self,
        initial: float,
        time: float,
        temperature: float,
        fluence: Optional[float],
        stress: Optional[float],
    ) -> float:
        """Zircaloy corrosion/oxidation."""
        # Corrosion layer thickness (simplified)
        time_years = time / 365.25
        # Typical: ~1-2 microns per year
        corrosion_rate = 1.5e-6  # m/year
        corrosion_thickness = corrosion_rate * time_years

        return corrosion_thickness

    # Fuel aging models
    def _fuel_conductivity_aging(
        self,
        initial: float,
        time: float,
        temperature: float,
        fluence: Optional[float],
        stress: Optional[float],
    ) -> float:
        """Fuel thermal conductivity degradation."""
        # Fission products reduce conductivity
        # Simplified: burnup-dependent
        time_years = time / 365.25
        burnup_approx = time_years * 10.0  # Approximate burnup [MWd/kg]

        # Typical: 10-20% reduction at high burnup
        burnup_factor = 1.0 - 0.15 * (burnup_approx / 50.0) ** 0.5
        burnup_factor = max(0.7, burnup_factor)

        aged = initial * burnup_factor
        return aged

    def _fuel_density_aging(
        self,
        initial: float,
        time: float,
        temperature: float,
        fluence: Optional[float],
        stress: Optional[float],
    ) -> float:
        """Fuel density change (swelling)."""
        # Fuel swelling increases with burnup
        time_years = time / 365.25
        burnup_approx = time_years * 10.0  # Approximate burnup [MWd/kg]

        # Typical: 1-2% swelling per 10 MWd/kg
        swelling = 0.01 * (burnup_approx / 10.0)

        aged = initial * (1.0 + swelling)
        return aged

    def _fuel_swelling_aging(
        self,
        initial: float,
        time: float,
        temperature: float,
        fluence: Optional[float],
        stress: Optional[float],
    ) -> float:
        """Fuel swelling (volumetric)."""
        # Same as density aging but returns swelling fraction
        time_years = time / 365.25
        burnup_approx = time_years * 10.0

        swelling = 0.01 * (burnup_approx / 10.0)
        return swelling

    # Generic aging model
    def _generic_aging(
        self,
        initial: float,
        time: float,
        temperature: float,
        fluence: Optional[float],
        stress: Optional[float],
    ) -> float:
        """Generic aging model (exponential decay)."""
        # Simple exponential decay
        time_years = time / 365.25
        decay_rate = 0.01  # 1% per year
        aged = initial * np.exp(-decay_rate * time_years)
        return aged

    def get_aging_rate(
        self,
        property_name: str,
        time: float,
        temperature: float,
        fluence: Optional[float] = None,
    ) -> float:
        """
        Get aging rate for a property.

        Args:
            property_name: Property name
            time: Current time [days]
            temperature: Temperature [K]
            fluence: Neutron fluence [n/cm²]

        Returns:
            Aging rate (fraction per year)
        """
        if property_name not in self.aging_models:
            return 0.0

        # Calculate property at two time points
        dt = 1.0  # 1 day
        prop_t1 = self.calculate_aged_properties(time, temperature, fluence).get(
            property_name, 0.0
        )
        prop_t2 = self.calculate_aged_properties(time + dt, temperature, fluence).get(
            property_name, 0.0
        )

        if prop_t1 == 0.0:
            return 0.0

        # Rate per year
        rate = (prop_t2 - prop_t1) / prop_t1 * 365.25
        return rate
