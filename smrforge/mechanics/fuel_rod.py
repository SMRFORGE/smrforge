"""
Fuel rod mechanics and structural analysis.

This module provides comprehensive fuel rod mechanics capabilities including:
- Thermal expansion calculations
- Stress and strain analysis
- Pellet-cladding interaction (PCI)
- Fuel swelling models
- Creep models (primary, secondary, tertiary creep)
- Material degradation for long-term analysis
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, Optional, Tuple

import numpy as np

from ..utils.logging import get_logger

logger = get_logger("smrforge.mechanics.fuel_rod")


@dataclass
class ThermalExpansion:
    """
    Thermal expansion calculations for fuel rods.

    Calculates dimensional changes due to temperature variations in fuel
    pellets and cladding materials.

    Attributes:
        fuel_coefficient: Linear thermal expansion coefficient for fuel [1/K]
        cladding_coefficient: Linear thermal expansion coefficient for cladding [1/K]
        reference_temperature: Reference temperature for expansion [K]
    """

    fuel_coefficient: float = 1.0e-5  # 1/K (typical UO2)
    cladding_coefficient: float = 1.7e-5  # 1/K (typical Zircaloy)
    reference_temperature: float = 300.0  # K

    def fuel_expansion(
        self,
        temperature: float,
        initial_length: float,
        initial_radius: float,
    ) -> Tuple[float, float]:
        """
        Calculate fuel thermal expansion.

        Args:
            temperature: Current fuel temperature [K]
            initial_length: Initial fuel length [cm]
            initial_radius: Initial fuel radius [cm]

        Returns:
            Tuple of (expanded_length, expanded_radius) [cm]
        """
        delta_T = temperature - self.reference_temperature
        expansion_factor = 1.0 + self.fuel_coefficient * delta_T

        expanded_length = initial_length * expansion_factor
        expanded_radius = initial_radius * expansion_factor

        return expanded_length, expanded_radius

    def cladding_expansion(
        self,
        temperature: float,
        initial_length: float,
        initial_radius: float,
    ) -> Tuple[float, float]:
        """
        Calculate cladding thermal expansion.

        Args:
            temperature: Current cladding temperature [K]
            initial_length: Initial cladding length [cm]
            initial_radius: Initial cladding radius [cm]

        Returns:
            Tuple of (expanded_length, expanded_radius) [cm]
        """
        delta_T = temperature - self.reference_temperature
        expansion_factor = 1.0 + self.cladding_coefficient * delta_T

        expanded_length = initial_length * expansion_factor
        expanded_radius = initial_radius * expansion_factor

        return expanded_length, expanded_radius

    def gap_change(
        self,
        fuel_temperature: float,
        cladding_temperature: float,
        initial_gap: float,
        initial_fuel_radius: float,
        initial_cladding_inner_radius: float,
    ) -> float:
        """
        Calculate change in fuel-cladding gap due to thermal expansion.

        Args:
            fuel_temperature: Fuel temperature [K]
            cladding_temperature: Cladding temperature [K]
            initial_gap: Initial gap thickness [cm]
            initial_fuel_radius: Initial fuel radius [cm]
            initial_cladding_inner_radius: Initial cladding inner radius [cm]

        Returns:
            New gap thickness [cm]
        """
        _, fuel_radius = self.fuel_expansion(fuel_temperature, 1.0, initial_fuel_radius)
        _, cladding_inner_radius = self.cladding_expansion(
            cladding_temperature, 1.0, initial_cladding_inner_radius
        )

        new_gap = cladding_inner_radius - fuel_radius
        return max(0.0, new_gap)  # Gap cannot be negative


@dataclass
class StressStrain:
    """
    Stress and strain analysis for fuel rods.

    Calculates mechanical stress and strain in fuel pellets and cladding
    under thermal and mechanical loads.

    Attributes:
        fuel_youngs_modulus: Young's modulus for fuel [Pa]
        cladding_youngs_modulus: Young's modulus for cladding [Pa]
        fuel_poisson: Poisson's ratio for fuel
        cladding_poisson: Poisson's ratio for cladding
        fuel_yield_strength: Yield strength for fuel [Pa]
        cladding_yield_strength: Yield strength for cladding [Pa]
    """

    fuel_youngs_modulus: float = 2.0e11  # Pa (UO2)
    cladding_youngs_modulus: float = 9.0e10  # Pa (Zircaloy)
    fuel_poisson: float = 0.31  # UO2
    cladding_poisson: float = 0.33  # Zircaloy
    fuel_yield_strength: float = 1.0e8  # Pa
    cladding_yield_strength: float = 4.0e8  # Pa

    def hoop_stress(
        self,
        internal_pressure: float,
        external_pressure: float,
        inner_radius: float,
        outer_radius: float,
    ) -> Tuple[float, float]:
        """
        Calculate hoop stress in a thick-walled cylinder.

        Uses Lame's equations for thick-walled pressure vessel.

        Args:
            internal_pressure: Internal pressure [Pa]
            external_pressure: External pressure [Pa]
            inner_radius: Inner radius [m]
            outer_radius: Outer radius [m]

        Returns:
            Tuple of (inner_hoop_stress, outer_hoop_stress) [Pa]
        """
        if outer_radius <= inner_radius:
            return 0.0, 0.0

        r_i = inner_radius
        r_o = outer_radius
        p_i = internal_pressure
        p_o = external_pressure

        # Lame's equations for thick-walled cylinder
        inner_hoop = (p_i * r_i**2 - p_o * r_o**2) / (r_o**2 - r_i**2) + (
            p_i - p_o
        ) * r_i**2 * r_o**2 / (r_o**2 - r_i**2) / r_i**2

        outer_hoop = (p_i * r_i**2 - p_o * r_o**2) / (r_o**2 - r_i**2) + (
            p_i - p_o
        ) * r_i**2 * r_o**2 / (r_o**2 - r_i**2) / r_o**2

        return inner_hoop, outer_hoop

    def radial_stress(
        self,
        internal_pressure: float,
        external_pressure: float,
        inner_radius: float,
        outer_radius: float,
        radius: float,
    ) -> float:
        """
        Calculate radial stress at a given radius.

        Args:
            internal_pressure: Internal pressure [Pa]
            external_pressure: External pressure [Pa]
            inner_radius: Inner radius [m]
            outer_radius: Outer radius [m]
            radius: Radius at which to calculate stress [m]

        Returns:
            Radial stress [Pa]
        """
        if (
            outer_radius <= inner_radius
            or radius < inner_radius
            or radius > outer_radius
        ):
            return 0.0

        r_i = inner_radius
        r_o = outer_radius
        r = radius
        p_i = internal_pressure
        p_o = external_pressure

        # Lame's equation for radial stress
        radial = (p_i * r_i**2 - p_o * r_o**2) / (r_o**2 - r_i**2) - (
            p_i - p_o
        ) * r_i**2 * r_o**2 / (r_o**2 - r_i**2) / r**2

        return radial

    def von_mises_stress(
        self,
        hoop_stress: float,
        radial_stress: float,
        axial_stress: float,
    ) -> float:
        """
        Calculate von Mises equivalent stress.

        Args:
            hoop_stress: Hoop stress [Pa]
            radial_stress: Radial stress [Pa]
            axial_stress: Axial stress [Pa]

        Returns:
            Von Mises equivalent stress [Pa]
        """
        vm = np.sqrt(
            0.5
            * (
                (hoop_stress - radial_stress) ** 2
                + (radial_stress - axial_stress) ** 2
                + (axial_stress - hoop_stress) ** 2
            )
        )
        return vm

    def strain_from_stress(
        self,
        hoop_stress: float,
        radial_stress: float,
        axial_stress: float,
        youngs_modulus: float,
        poisson: float,
    ) -> Tuple[float, float, float]:
        """
        Calculate strains from stresses using Hooke's law.

        Args:
            hoop_stress: Hoop stress [Pa]
            radial_stress: Radial stress [Pa]
            axial_stress: Axial stress [Pa]
            youngs_modulus: Young's modulus [Pa]
            poisson: Poisson's ratio

        Returns:
            Tuple of (hoop_strain, radial_strain, axial_strain)

        Raises:
            ValueError: If Young's modulus <= 0 or Poisson's ratio is invalid.
        """
        hoop_strain = (
            hoop_stress - poisson * (radial_stress + axial_stress)
        ) / youngs_modulus

        radial_strain = (
            radial_stress - poisson * (hoop_stress + axial_stress)
        ) / youngs_modulus

        axial_strain = (
            axial_stress - poisson * (hoop_stress + radial_stress)
        ) / youngs_modulus

        return hoop_strain, radial_strain, axial_strain


@dataclass
class PelletCladdingInteraction:
    """
    Pellet-cladding interaction (PCI) modeling.

    Models the mechanical interaction between fuel pellets and cladding,
    including contact pressure, friction, and potential failure modes.

    Attributes:
        friction_coefficient: Friction coefficient between fuel and cladding
        contact_pressure: Contact pressure at fuel-cladding interface [Pa]
        gap_closed: Whether the fuel-cladding gap is closed
    """

    friction_coefficient: float = 0.3  # Typical for UO2-Zircaloy
    contact_pressure: float = 0.0  # Pa
    gap_closed: bool = False

    def check_gap_closure(
        self,
        fuel_radius: float,
        cladding_inner_radius: float,
        tolerance: float = 1e-6,
    ) -> bool:
        """
        Check if fuel-cladding gap is closed.

        Args:
            fuel_radius: Current fuel radius [cm]
            cladding_inner_radius: Current cladding inner radius [cm]
            tolerance: Tolerance for gap closure [cm]

        Returns:
            True if gap is closed
        """
        gap = cladding_inner_radius - fuel_radius
        self.gap_closed = gap <= tolerance
        return self.gap_closed

    def calculate_contact_pressure(
        self,
        fuel_radius: float,
        cladding_inner_radius: float,
        fuel_youngs_modulus: float,
        cladding_youngs_modulus: float,
        fuel_poisson: float,
        cladding_poisson: float,
    ) -> float:
        """
        Calculate contact pressure when gap is closed.

        Uses elastic contact mechanics for interference fit.

        Args:
            fuel_radius: Current fuel radius [cm]
            cladding_inner_radius: Current cladding inner radius [cm]
            fuel_youngs_modulus: Fuel Young's modulus [Pa]
            cladding_youngs_modulus: Cladding Young's modulus [Pa]
            fuel_poisson: Fuel Poisson's ratio
            cladding_poisson: Cladding Poisson's ratio

        Returns:
            Contact pressure [Pa]
        """
        if not self.gap_closed:
            self.contact_pressure = 0.0
            return 0.0

        # Interference (overlap)
        interference = fuel_radius - cladding_inner_radius

        if interference <= 0:
            self.contact_pressure = 0.0
            return 0.0

        # Convert to meters
        r_fuel = fuel_radius * 1e-2  # cm to m
        r_clad = cladding_inner_radius * 1e-2  # cm to m
        delta = interference * 1e-2  # cm to m

        # Contact pressure from interference fit
        # Simplified model: assumes both materials are elastic
        E_eff = 1.0 / (
            (1.0 - fuel_poisson**2) / fuel_youngs_modulus
            + (1.0 - cladding_poisson**2) / cladding_youngs_modulus
        )

        # For thin cladding approximation
        contact_p = E_eff * delta / r_clad

        self.contact_pressure = contact_p
        return contact_p

    def pci_stress_enhancement(
        self,
        base_stress: float,
        contact_pressure: float,
        stress_concentration_factor: float = 1.5,
    ) -> float:
        """
        Calculate stress enhancement due to PCI.

        PCI can cause stress concentrations at pellet interfaces.

        Args:
            base_stress: Base stress without PCI [Pa]
            contact_pressure: Contact pressure [Pa]
            stress_concentration_factor: Stress concentration factor

        Returns:
            Enhanced stress [Pa]
        """
        if not self.gap_closed:
            return base_stress

        # Stress enhancement from contact pressure
        enhanced = base_stress + stress_concentration_factor * contact_pressure
        return enhanced


@dataclass
class FuelSwelling:
    """
    Fuel swelling models.

    Models dimensional changes in fuel due to:
    - Solid fission products
    - Gas bubble formation
    - Irradiation-induced swelling

    Attributes:
        solid_swelling_rate: Solid fission product swelling rate [cm³/(MWd/kg)]
        gas_swelling_rate: Gas bubble swelling rate [cm³/(MWd/kg)]
        saturation_burnup: Burnup at which swelling saturates [MWd/kg]
    """

    solid_swelling_rate: float = 0.01  # cm³/(MWd/kg)
    gas_swelling_rate: float = 0.005  # cm³/(MWd/kg)
    saturation_burnup: float = 50.0  # MWd/kg

    def total_swelling(
        self,
        burnup: float,
        temperature: float,
        power_density: float,
    ) -> float:
        """
        Calculate total fuel swelling.

        Args:
            burnup: Current burnup [MWd/kg]
            temperature: Fuel temperature [K]
            power_density: Power density [W/cm³]

        Returns:
            Volumetric swelling fraction
        """
        # Solid fission product swelling (linear with burnup)
        solid_swelling = self.solid_swelling_rate * min(burnup, self.saturation_burnup)

        # Gas bubble swelling (temperature and power dependent)
        # Higher temperature and power density increase gas release
        temp_factor = 1.0 + 0.001 * (temperature - 1000.0) / 100.0
        power_factor = 1.0 + 0.0001 * power_density / 100.0

        gas_swelling = (
            self.gas_swelling_rate
            * min(burnup, self.saturation_burnup)
            * temp_factor
            * power_factor
        )

        total_swelling = solid_swelling + gas_swelling
        return total_swelling

    def radius_increase(
        self,
        burnup: float,
        temperature: float,
        power_density: float,
        initial_radius: float,
    ) -> float:
        """
        Calculate fuel radius increase due to swelling.

        Args:
            burnup: Current burnup [MWd/kg]
            temperature: Fuel temperature [K]
            power_density: Power density [W/cm³]
            initial_radius: Initial fuel radius [cm]

        Returns:
            Radius increase [cm]
        """
        volumetric_swelling = self.total_swelling(burnup, temperature, power_density)

        # For isotropic swelling: delta_V/V = 3 * delta_r/r
        # Therefore: delta_r = r * (delta_V/V) / 3
        radius_increase = initial_radius * volumetric_swelling / 3.0

        return radius_increase


@dataclass
class FuelRodMechanics:
    """
    Comprehensive fuel rod mechanics analysis.

    Integrates thermal expansion, stress/strain, PCI, fuel swelling, creep,
    and material degradation to provide complete structural analysis of fuel rods.

    Attributes:
        fuel_radius: Initial fuel radius [cm]
        cladding_inner_radius: Initial cladding inner radius [cm]
        cladding_outer_radius: Initial cladding outer radius [cm]
        fuel_length: Fuel length [cm]
        thermal_expansion: Thermal expansion calculator
        stress_strain: Stress/strain calculator
        pci: Pellet-cladding interaction model
        fuel_swelling: Fuel swelling model
        cladding_creep: Optional creep model for cladding
        fuel_creep: Optional creep model for fuel
        cladding_degradation: Optional material degradation model for cladding
        fuel_degradation: Optional material degradation model for fuel
    """

    fuel_radius: float  # cm
    cladding_inner_radius: float  # cm
    cladding_outer_radius: float  # cm
    fuel_length: float  # cm
    thermal_expansion: ThermalExpansion = field(default_factory=ThermalExpansion)
    stress_strain: StressStrain = field(default_factory=StressStrain)
    pci: PelletCladdingInteraction = field(default_factory=PelletCladdingInteraction)
    fuel_swelling: FuelSwelling = field(default_factory=FuelSwelling)
    cladding_creep: Optional[CreepModel] = None
    fuel_creep: Optional[CreepModel] = None
    cladding_degradation: Optional[MaterialDegradation] = None
    fuel_degradation: Optional[MaterialDegradation] = None

    def analyze(
        self,
        fuel_temperature: float,
        cladding_temperature: float,
        burnup: float,
        power_density: float,
        internal_pressure: float = 0.0,  # Pa
        external_pressure: float = 15.5e6,  # Pa (typical PWR)
        time: float = 0.0,  # days (for creep and degradation)
        fluence: Optional[float] = None,  # n/cm² (for irradiation effects)
        include_creep: bool = False,  # Whether to include creep analysis
        include_degradation: bool = False,  # Whether to include material degradation
    ) -> Dict:
        """
        Perform comprehensive fuel rod mechanics analysis.

        Args:
            fuel_temperature: Fuel temperature [K]
            cladding_temperature: Cladding temperature [K]
            burnup: Current burnup [MWd/kg]
            power_density: Power density [W/cm³]
            internal_pressure: Internal pressure (fission gas) [Pa]
            external_pressure: External pressure (coolant) [Pa]
            time: Exposure time [days] (for creep and degradation)
            fluence: Optional neutron fluence [n/cm²] (for irradiation effects)
            include_creep: Whether to include creep analysis
            include_degradation: Whether to include material degradation

        Returns:
            Dictionary with analysis results including creep and degradation if enabled
        """
        # 1. Thermal expansion
        fuel_length_exp, fuel_radius_exp = self.thermal_expansion.fuel_expansion(
            fuel_temperature, self.fuel_length, self.fuel_radius
        )
        clad_length_exp, clad_inner_radius_exp = (
            self.thermal_expansion.cladding_expansion(
                cladding_temperature, self.fuel_length, self.cladding_inner_radius
            )
        )

        # 2. Fuel swelling
        radius_swelling = self.fuel_swelling.radius_increase(
            burnup, fuel_temperature, power_density, self.fuel_radius
        )
        fuel_radius_total = fuel_radius_exp + radius_swelling

        # 3. Gap calculation
        gap = clad_inner_radius_exp - fuel_radius_total

        # 4. PCI check
        gap_closed = self.pci.check_gap_closure(
            fuel_radius_total, clad_inner_radius_exp
        )

        # 5. Contact pressure (if gap closed)
        contact_pressure = 0.0
        if gap_closed:
            contact_pressure = self.pci.calculate_contact_pressure(
                fuel_radius_total,
                clad_inner_radius_exp,
                self.stress_strain.fuel_youngs_modulus,
                self.stress_strain.cladding_youngs_modulus,
                self.stress_strain.fuel_poisson,
                self.stress_strain.cladding_poisson,
            )

        # 6. Stress analysis (cladding)
        # Convert radii to meters for stress calculations
        r_clad_inner = clad_inner_radius_exp * 1e-2  # cm to m
        r_clad_outer = self.cladding_outer_radius * 1e-2  # cm to m

        # Total internal pressure includes contact pressure
        total_internal_p = internal_pressure + contact_pressure

        cladding_hoop_inner, cladding_hoop_outer = self.stress_strain.hoop_stress(
            total_internal_p, external_pressure, r_clad_inner, r_clad_outer
        )

        cladding_radial_inner = self.stress_strain.radial_stress(
            total_internal_p,
            external_pressure,
            r_clad_inner,
            r_clad_outer,
            r_clad_inner,
        )

        # Von Mises stress
        cladding_vm = self.stress_strain.von_mises_stress(
            cladding_hoop_inner, cladding_radial_inner, 0.0
        )

        # 7. PCI stress enhancement
        cladding_vm_enhanced = self.pci.pci_stress_enhancement(
            cladding_vm, contact_pressure
        )

        # 8. Safety margin (using original yield strength)
        yield_strength = self.stress_strain.cladding_yield_strength

        # 9. Material degradation (if enabled)
        degraded_cladding_props = {}
        degraded_fuel_props = {}
        if include_degradation:
            if self.cladding_degradation:
                degraded_cladding_props = (
                    self.cladding_degradation.calculate_degraded_properties(
                        time, cladding_temperature, cladding_vm_enhanced, fluence
                    )
                )
                # Update yield strength if degraded
                if "yield_strength" in degraded_cladding_props:
                    yield_strength = degraded_cladding_props["yield_strength"]

            if self.fuel_degradation:
                fuel_stress = cladding_vm_enhanced * 0.5  # Approximate fuel stress
                degraded_fuel_props = (
                    self.fuel_degradation.calculate_degraded_properties(
                        time, fuel_temperature, fuel_stress, fluence
                    )
                )

        # 10. Creep analysis (if enabled)
        cladding_creep_results = {}
        fuel_creep_results = {}
        if include_creep:
            if self.cladding_creep:
                time_seconds = time * 86400.0  # Convert days to seconds
                cladding_creep_results = self.cladding_creep.calculate_creep_strain(
                    cladding_vm_enhanced, cladding_temperature, time_seconds, fluence
                )
                # Creep strain affects dimensions
                creep_radius_increase = (
                    clad_inner_radius_exp * cladding_creep_results["total_creep_strain"]
                )
                clad_inner_radius_exp += creep_radius_increase

            if self.fuel_creep:
                time_seconds = time * 86400.0
                fuel_stress = cladding_vm_enhanced * 0.5  # Approximate
                fuel_creep_results = self.fuel_creep.calculate_creep_strain(
                    fuel_stress, fuel_temperature, time_seconds, fluence
                )
                # Fuel creep affects radius
                creep_radius_increase = (
                    fuel_radius_total * fuel_creep_results["total_creep_strain"]
                )
                fuel_radius_total += creep_radius_increase

        # Recalculate safety margin with degraded properties
        safety_margin = (yield_strength - cladding_vm_enhanced) / yield_strength

        result = {
            "fuel_radius": fuel_radius_total,
            "cladding_inner_radius": clad_inner_radius_exp,
            "gap": gap,
            "gap_closed": gap_closed,
            "contact_pressure": contact_pressure,
            "cladding_hoop_stress_inner": cladding_hoop_inner,
            "cladding_hoop_stress_outer": cladding_hoop_outer,
            "cladding_radial_stress_inner": cladding_radial_inner,
            "cladding_von_mises_stress": cladding_vm,
            "cladding_von_mises_stress_enhanced": cladding_vm_enhanced,
            "safety_margin": safety_margin,
            "fuel_swelling_radius_increase": radius_swelling,
        }

        # Add creep results if available
        if cladding_creep_results:
            result["cladding_creep_strain"] = cladding_creep_results[
                "total_creep_strain"
            ]
            result["cladding_creep_strain_rate"] = cladding_creep_results[
                "creep_strain_rate"
            ]
            result["cladding_creep_life"] = self.cladding_creep.calculate_creep_life(
                cladding_vm_enhanced, cladding_temperature, fluence=fluence
            )

        if fuel_creep_results:
            result["fuel_creep_strain"] = fuel_creep_results["total_creep_strain"]
            result["fuel_creep_strain_rate"] = fuel_creep_results["creep_strain_rate"]

        # Add degradation results if available
        if degraded_cladding_props:
            result["cladding_degraded_properties"] = degraded_cladding_props

        if degraded_fuel_props:
            result["fuel_degraded_properties"] = degraded_fuel_props

        return result


@dataclass
class CreepModel:
    """
    Creep models for fuel rod materials.

    Creep is time-dependent deformation under constant stress and temperature.
    Important for long-term fuel rod performance analysis.

    Models implemented:
    - Primary creep: Initial transient creep
    - Secondary creep: Steady-state creep (Norton's law, power law)
    - Tertiary creep: Accelerating creep before failure
    - Irradiation creep: Neutron fluence-enhanced creep

    Attributes:
        material_type: Material type ('fuel', 'zircaloy', 'graphite')
        creep_model_type: Creep model type ('norton', 'power_law', 'garofalo', 'irradiation_enhanced')
        activation_energy: Creep activation energy [J/mol]
        stress_exponent: Stress exponent (n in Norton's law)
        pre_exponential: Pre-exponential factor [1/s]
    """

    material_type: str  # 'fuel', 'zircaloy', 'graphite'
    creep_model_type: str = (
        "norton"  # 'norton', 'power_law', 'garofalo', 'irradiation_enhanced'
    )
    activation_energy: Optional[float] = None  # J/mol
    stress_exponent: Optional[float] = None  # n
    pre_exponential: Optional[float] = None  # A [1/s]

    def __post_init__(self):
        """Initialize default creep parameters based on material type."""
        if self.material_type == "zircaloy":
            # Zircaloy-4 typical values
            self.activation_energy = self.activation_energy or 2.4e5  # J/mol
            self.stress_exponent = self.stress_exponent or 4.5
            self.pre_exponential = self.pre_exponential or 1.0e-15  # 1/s
        elif self.material_type == "fuel":
            # UO2 fuel typical values
            self.activation_energy = self.activation_energy or 3.0e5  # J/mol
            self.stress_exponent = self.stress_exponent or 5.0
            self.pre_exponential = self.pre_exponential or 1.0e-20  # 1/s
        elif self.material_type == "graphite":
            # Graphite typical values
            self.activation_energy = self.activation_energy or 2.0e5  # J/mol
            self.stress_exponent = self.stress_exponent or 3.0
            self.pre_exponential = self.pre_exponential or 1.0e-12  # 1/s
        else:
            # Default values
            self.activation_energy = self.activation_energy or 2.5e5
            self.stress_exponent = self.stress_exponent or 4.0
            self.pre_exponential = self.pre_exponential or 1.0e-15

    def calculate_creep_strain_rate(
        self,
        stress: float,  # Pa
        temperature: float,  # K
        fluence: Optional[float] = None,  # n/cm²
    ) -> float:
        """
        Calculate creep strain rate.

        Args:
            stress: Applied stress [Pa]
            temperature: Temperature [K]
            fluence: Optional neutron fluence [n/cm²] for irradiation creep

        Returns:
            Creep strain rate [1/s]
        """
        R = 8.314  # J/(mol·K) - gas constant

        if self.creep_model_type == "norton":
            # Norton's law: ε_dot = A * σ^n * exp(-Q/RT)
            creep_rate = (
                self.pre_exponential
                * (stress**self.stress_exponent)
                * np.exp(-self.activation_energy / (R * temperature))
            )

        elif self.creep_model_type == "power_law":
            # Power law creep (simplified)
            creep_rate = (
                self.pre_exponential
                * (stress / 1e6) ** self.stress_exponent  # Normalize stress to MPa
                * np.exp(-self.activation_energy / (R * temperature))
            )

        elif self.creep_model_type == "garofalo":
            # Garofalo (sinh) model: ε_dot = A * [sinh(α*σ)]^n * exp(-Q/RT)
            alpha = 1.0e-8  # Pa^-1 (typical value)
            sinh_term = np.sinh(alpha * stress)
            creep_rate = (
                self.pre_exponential
                * (sinh_term**self.stress_exponent)
                * np.exp(-self.activation_energy / (R * temperature))
            )

        elif self.creep_model_type == "irradiation_enhanced":
            # Irradiation-enhanced creep
            base_creep = (
                self.pre_exponential
                * (stress**self.stress_exponent)
                * np.exp(-self.activation_energy / (R * temperature))
            )

            # Irradiation enhancement factor
            if fluence is not None:
                # Typical: 2-5x enhancement at high fluence
                fluence_factor = 1.0 + 0.1 * (
                    fluence / 1e21
                )  # Enhancement per 10^21 n/cm²
                fluence_factor = min(5.0, fluence_factor)  # Cap at 5x
                creep_rate = base_creep * fluence_factor
            else:
                creep_rate = base_creep

        else:
            # Default to Norton's law
            creep_rate = (
                self.pre_exponential
                * (stress**self.stress_exponent)
                * np.exp(-self.activation_energy / (R * temperature))
            )

        return max(0.0, creep_rate)  # Ensure non-negative

    def calculate_creep_strain(
        self,
        stress: float,  # Pa
        temperature: float,  # K
        time: float,  # s
        fluence: Optional[float] = None,  # n/cm²
        include_primary: bool = True,
    ) -> Dict[str, float]:
        """
        Calculate total creep strain including primary, secondary, and tertiary.

        Args:
            stress: Applied stress [Pa]
            temperature: Temperature [K]
            time: Exposure time [s]
            fluence: Optional neutron fluence [n/cm²]
            include_primary: Whether to include primary creep

        Returns:
            Dictionary with:
                - total_creep_strain: Total creep strain [-]
                - primary_creep_strain: Primary creep strain [-]
                - secondary_creep_strain: Secondary creep strain [-]
                - tertiary_creep_strain: Tertiary creep strain [-]
                - creep_strain_rate: Current creep strain rate [1/s]
        """
        # Secondary creep (steady-state)
        secondary_rate = self.calculate_creep_strain_rate(stress, temperature, fluence)
        secondary_strain = secondary_rate * time

        # Primary creep (transient, decaying)
        primary_strain = 0.0
        if include_primary:
            # Primary creep: ε_p = ε_p0 * (1 - exp(-t/τ))
            # Typical: primary strain is 10-30% of secondary
            primary_strain_0 = 0.2 * secondary_strain  # 20% of secondary
            tau = 1e6  # s (typical relaxation time)
            primary_strain = primary_strain_0 * (1.0 - np.exp(-time / tau))

        # Tertiary creep (accelerating, before failure)
        # Typically starts after significant secondary creep
        tertiary_strain = 0.0
        if time > 1e7:  # After ~1 year at high stress
            # Tertiary creep accelerates as material approaches failure
            # Simplified: exponential acceleration
            tertiary_factor = 1.0 + 0.01 * (time / 1e7) ** 2
            tertiary_strain = secondary_strain * (tertiary_factor - 1.0)

        total_creep_strain = primary_strain + secondary_strain + tertiary_strain

        return {
            "total_creep_strain": total_creep_strain,
            "primary_creep_strain": primary_strain,
            "secondary_creep_strain": secondary_strain,
            "tertiary_creep_strain": tertiary_strain,
            "creep_strain_rate": secondary_rate,
        }

    def calculate_creep_life(
        self,
        stress: float,  # Pa
        temperature: float,  # K
        failure_strain: float = 0.1,  # Typical failure strain (10%)
        fluence: Optional[float] = None,  # n/cm²
    ) -> float:
        """
        Calculate time to creep failure (rupture time).

        Args:
            stress: Applied stress [Pa]
            temperature: Temperature [K]
            failure_strain: Failure strain criterion [-]
            fluence: Optional neutron fluence [n/cm²]

        Returns:
            Time to failure [s]
        """
        # Calculate steady-state creep rate
        creep_rate = self.calculate_creep_strain_rate(stress, temperature, fluence)

        if creep_rate <= 0:
            return float("inf")  # No creep at these conditions

        # Simplified: assume failure when total strain reaches failure_strain
        # More accurate models would account for tertiary creep acceleration
        time_to_failure = failure_strain / creep_rate

        return time_to_failure


@dataclass
class MaterialDegradation:
    """
    Material degradation models for long-term fuel rod analysis.

    Provides comprehensive material property degradation including:
    - Irradiation damage (neutron fluence effects)
    - Thermal aging (temperature and time effects)
    - Creep-induced property changes
    - Fatigue damage accumulation

    Attributes:
        material_type: Material type ('fuel', 'zircaloy', 'graphite')
        initial_properties: Initial material properties dictionary
        creep_model: Optional creep model for creep-induced degradation
    """

    material_type: str
    initial_properties: Dict[str, float]
    creep_model: Optional["CreepModel"] = None

    def __post_init__(self):
        """Initialize creep model if not provided."""
        if self.creep_model is None:
            self.creep_model = CreepModel(material_type=self.material_type)

    def calculate_degraded_properties(
        self,
        time: float,  # days
        temperature: float,  # K
        stress: float,  # Pa
        fluence: Optional[float] = None,  # n/cm²
    ) -> Dict[str, float]:
        """
        Calculate material properties after degradation.

        Args:
            time: Exposure time [days]
            temperature: Temperature [K]
            stress: Applied stress [Pa]
            fluence: Optional neutron fluence [n/cm²]

        Returns:
            Dictionary with degraded material properties
        """
        time_seconds = time * 86400.0  # Convert days to seconds

        degraded_properties = self.initial_properties.copy()

        # Calculate creep strain
        creep_results = self.creep_model.calculate_creep_strain(
            stress, temperature, time_seconds, fluence
        )

        # Degradation due to creep
        if self.material_type == "zircaloy":
            # Zircaloy degradation
            # Young's modulus decreases with creep damage
            creep_damage = min(1.0, creep_results["total_creep_strain"] / 0.1)
            degraded_properties["youngs_modulus"] = self.initial_properties.get(
                "youngs_modulus", 1e11
            ) * (
                1.0 - 0.2 * creep_damage
            )  # Up to 20% reduction

            # Yield strength decreases with irradiation and creep
            if fluence is not None:
                fluence_factor = 1.0 - 0.1 * (
                    fluence / 1e22
                )  # 10% reduction per 10^22 n/cm²
                fluence_factor = max(0.5, fluence_factor)  # Minimum 50% of original
            else:
                fluence_factor = 1.0

            degraded_properties["yield_strength"] = (
                self.initial_properties.get("yield_strength", 4e8)
                * fluence_factor
                * (1.0 - 0.15 * creep_damage)  # Additional 15% reduction from creep
            )

            # Thermal conductivity decreases with irradiation
            if fluence is not None:
                conductivity_factor = 1.0 - 0.05 * (fluence / 1e22)
                conductivity_factor = max(0.8, conductivity_factor)
            else:
                conductivity_factor = 1.0

            degraded_properties["thermal_conductivity"] = (
                self.initial_properties.get("thermal_conductivity", 20.0)
                * conductivity_factor
            )

        elif self.material_type == "fuel":
            # Fuel degradation
            # Thermal conductivity decreases with burnup (via time approximation)
            burnup_approx = time * 0.01  # Approximate burnup [MWd/kg] from time
            conductivity_factor = 1.0 - 0.15 * (burnup_approx / 50.0) ** 0.5
            conductivity_factor = max(0.7, conductivity_factor)

            degraded_properties["thermal_conductivity"] = (
                self.initial_properties.get("thermal_conductivity", 3.0)
                * conductivity_factor
            )

            # Young's modulus decreases with creep
            creep_damage = min(1.0, creep_results["total_creep_strain"] / 0.15)
            degraded_properties["youngs_modulus"] = self.initial_properties.get(
                "youngs_modulus", 2e11
            ) * (
                1.0 - 0.25 * creep_damage
            )  # Up to 25% reduction

        elif self.material_type == "graphite":
            # Graphite degradation
            # Young's modulus decreases with irradiation
            if fluence is not None:
                modulus_factor = 1.0 - 0.3 * (fluence / 1e22)
                modulus_factor = max(0.4, modulus_factor)  # Minimum 40% of original
            else:
                modulus_factor = 1.0

            degraded_properties["youngs_modulus"] = (
                self.initial_properties.get("youngs_modulus", 1e10) * modulus_factor
            )

            # Thermal conductivity decreases significantly with irradiation
            if fluence is not None:
                conductivity_factor = 1.0 - 0.4 * (fluence / 1e22)
                conductivity_factor = max(0.3, conductivity_factor)
            else:
                conductivity_factor = 1.0

            degraded_properties["thermal_conductivity"] = (
                self.initial_properties.get("thermal_conductivity", 100.0)
                * conductivity_factor
            )

        # Add creep information
        degraded_properties["creep_strain"] = creep_results["total_creep_strain"]
        degraded_properties["creep_strain_rate"] = creep_results["creep_strain_rate"]
        degraded_properties["creep_life"] = self.creep_model.calculate_creep_life(
            stress, temperature, fluence=fluence
        )

        return degraded_properties
