"""
Fuel performance modeling.

This module provides fuel performance analysis including:
- Fuel temperature calculations
- Fuel swelling models
- Fission gas release
- Cladding performance
"""

from dataclasses import dataclass
from typing import Dict, Optional

import numpy as np

from ..utils.logging import get_logger

logger = get_logger("smrforge.fuel.performance")


@dataclass
class FuelProperties:
    """
    Fuel pellet properties.

    Attributes:
        diameter: Fuel pellet diameter [cm]
        height: Fuel pellet height [cm]
        density: Fuel density [g/cm³]
        enrichment: U-235 enrichment [%]
        burnup: Current burnup [MWd/kgU]
    """

    diameter: float  # cm
    height: float  # cm
    density: float  # g/cm³
    enrichment: float  # % U-235
    burnup: float = 0.0  # MWd/kgU


@dataclass
class CladProperties:
    """
    Cladding properties.

    Attributes:
        inner_diameter: Cladding inner diameter [cm]
        outer_diameter: Cladding outer diameter [cm]
        material: Cladding material name
    """

    inner_diameter: float  # cm
    outer_diameter: float  # cm
    material: str = "Zircaloy-4"


class FuelPerformance:
    """
    Fuel performance analysis.

    Provides models for fuel temperature, swelling, and fission gas release.
    Integrates with structural mechanics module for comprehensive analysis.

    Attributes:
        fuel: Fuel properties
        clad: Cladding properties
    """

    def __init__(self, fuel: FuelProperties, clad: CladProperties):
        """
        Initialize fuel performance analyzer.

        Args:
            fuel: Fuel properties
            clad: Cladding properties
        """
        self.fuel = fuel
        self.clad = clad

    def fuel_centerline_temperature(
        self, linear_power: float, coolant_temp: float
    ) -> float:
        """
        Calculate fuel centerline temperature.

        Uses simplified heat conduction model with gap and cladding resistance.

        Args:
            linear_power: Linear power density [kW/m]
            coolant_temp: Coolant temperature [K]

        Returns:
            Fuel centerline temperature [K]
        """
        q_prime = linear_power * 1000.0  # Convert to W/m
        k_fuel = 3.0  # W/(m·K) - simplified UO2 thermal conductivity
        r_fuel = (self.fuel.diameter / 2.0) / 100.0  # Convert cm to m

        # Temperature rise in fuel (cylindrical heat conduction)
        # For uniform heat generation: T_center = T_surface + q_dot * r² / (4*k)
        delta_T_fuel = q_prime * r_fuel**2 / (4.0 * np.pi * k_fuel)

        # Add gap and cladding resistance (simplified)
        # Gap thermal resistance
        gap_thickness = (
            (self.clad.inner_diameter - self.fuel.diameter) / 2.0 / 100.0
        )  # m
        k_gap = 0.1  # W/(m·K) - simplified gap conductivity (gas)
        delta_T_gap = q_prime * gap_thickness / (2.0 * np.pi * r_fuel * k_gap)

        # Cladding thermal resistance
        r_clad_inner = self.clad.inner_diameter / 2.0 / 100.0  # m
        r_clad_outer = self.clad.outer_diameter / 2.0 / 100.0  # m
        k_clad = 20.0  # W/(m·K) - Zircaloy thermal conductivity
        delta_T_clad = (
            q_prime * np.log(r_clad_outer / r_clad_inner) / (2.0 * np.pi * k_clad)
        )

        T_centerline = coolant_temp + delta_T_fuel + delta_T_gap + delta_T_clad

        return T_centerline

    def fission_gas_release(self, temperature: float, burnup: float) -> float:
        """
        Calculate fission gas release fraction.

        Uses simplified Forsberg-Massih model for fission gas release.

        Args:
            temperature: Fuel temperature [K]
            burnup: Current burnup [MWd/kgU]

        Returns:
            Fission gas release fraction (0-1)
        """
        # Simplified Forsberg-Massih model
        if temperature < 1273.0:  # Below threshold
            # Low temperature: linear with burnup
            fgr = 0.01 * burnup / 50000.0
        else:
            # High temperature: temperature-dependent release
            fgr = 0.01 * (temperature - 1273.0) / 500.0 * burnup / 30000.0

        # Cap at reasonable maximum (15%)
        fgr = min(fgr, 0.15)

        return max(0.0, fgr)  # Ensure non-negative

    def fuel_swelling(self, burnup: float, temperature: float) -> float:
        """
        Calculate fuel swelling.

        Simplified model for volumetric fuel swelling due to:
        - Solid fission products
        - Gas bubble formation

        Args:
            burnup: Current burnup [MWd/kgU]
            temperature: Fuel temperature [K]

        Returns:
            Volumetric swelling [%]
        """
        # Base swelling: increases with burnup
        # Typical: ~0.5% per 10 GWd/tU (10000 MWd/kgU)
        swelling = 0.5 * burnup / 10000.0

        # Temperature enhancement (higher temp = more swelling)
        if temperature > 1500.0:
            swelling *= 1.2

        return max(0.0, swelling)  # Ensure non-negative

    def analyze(
        self,
        linear_power: float,
        coolant_temp: float,
        burnup: Optional[float] = None,
    ) -> Dict:
        """
        Perform comprehensive fuel performance analysis.

        Args:
            linear_power: Linear power density [kW/m]
            coolant_temp: Coolant temperature [K]
            burnup: Current burnup [MWd/kgU] (uses fuel.burnup if None)

        Returns:
            Dictionary with analysis results:
                - centerline_temperature: Fuel centerline temperature [K]
                - surface_temperature: Fuel surface temperature [K]
                - fission_gas_release: FGR fraction (0-1)
                - fuel_swelling: Volumetric swelling [%]
        """
        if burnup is None:
            burnup = self.fuel.burnup

        # Calculate temperatures
        T_centerline = self.fuel_centerline_temperature(linear_power, coolant_temp)

        # Estimate surface temperature (simplified)
        q_prime = linear_power * 1000.0  # W/m
        k_fuel = 3.0  # W/(m·K)
        r_fuel = (self.fuel.diameter / 2.0) / 100.0  # m
        delta_T_radial = q_prime * r_fuel**2 / (4.0 * np.pi * k_fuel)
        T_surface = T_centerline - delta_T_radial

        # Calculate fission gas release
        fgr = self.fission_gas_release(T_centerline, burnup)

        # Calculate fuel swelling
        swelling = self.fuel_swelling(burnup, T_centerline)

        return {
            "centerline_temperature": T_centerline,
            "surface_temperature": T_surface,
            "fission_gas_release": fgr,
            "fuel_swelling": swelling,
            "burnup": burnup,
        }
