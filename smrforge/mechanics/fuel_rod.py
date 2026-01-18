"""
Fuel rod mechanics and structural analysis.

This module provides comprehensive fuel rod mechanics capabilities including:
- Thermal expansion calculations
- Stress and strain analysis
- Pellet-cladding interaction (PCI)
- Fuel swelling models
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional, Tuple

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
        _, fuel_radius = self.fuel_expansion(
            fuel_temperature, 1.0, initial_fuel_radius
        )
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
        inner_hoop = (
            (p_i * r_i**2 - p_o * r_o**2) / (r_o**2 - r_i**2)
            + (p_i - p_o) * r_i**2 * r_o**2 / (r_o**2 - r_i**2) / r_i**2
        )
        
        outer_hoop = (
            (p_i * r_i**2 - p_o * r_o**2) / (r_o**2 - r_i**2)
            + (p_i - p_o) * r_i**2 * r_o**2 / (r_o**2 - r_i**2) / r_o**2
        )
        
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
        if outer_radius <= inner_radius or radius < inner_radius or radius > outer_radius:
            return 0.0
        
        r_i = inner_radius
        r_o = outer_radius
        r = radius
        p_i = internal_pressure
        p_o = external_pressure
        
        # Lame's equation for radial stress
        radial = (
            (p_i * r_i**2 - p_o * r_o**2) / (r_o**2 - r_i**2)
            - (p_i - p_o) * r_i**2 * r_o**2 / (r_o**2 - r_i**2) / r**2
        )
        
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
    
    Integrates thermal expansion, stress/strain, PCI, and fuel swelling
    to provide complete structural analysis of fuel rods.
    
    Attributes:
        fuel_radius: Initial fuel radius [cm]
        cladding_inner_radius: Initial cladding inner radius [cm]
        cladding_outer_radius: Initial cladding outer radius [cm]
        fuel_length: Fuel length [cm]
        thermal_expansion: Thermal expansion calculator
        stress_strain: Stress/strain calculator
        pci: Pellet-cladding interaction model
        fuel_swelling: Fuel swelling model
    """
    
    fuel_radius: float  # cm
    cladding_inner_radius: float  # cm
    cladding_outer_radius: float  # cm
    fuel_length: float  # cm
    thermal_expansion: ThermalExpansion = field(default_factory=ThermalExpansion)
    stress_strain: StressStrain = field(default_factory=StressStrain)
    pci: PelletCladdingInteraction = field(default_factory=PelletCladdingInteraction)
    fuel_swelling: FuelSwelling = field(default_factory=FuelSwelling)
    
    def analyze(
        self,
        fuel_temperature: float,
        cladding_temperature: float,
        burnup: float,
        power_density: float,
        internal_pressure: float = 0.0,  # Pa
        external_pressure: float = 15.5e6,  # Pa (typical PWR)
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
            
        Returns:
            Dictionary with analysis results
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
        
        cladding_hoop_inner, cladding_hoop_outer = (
            self.stress_strain.hoop_stress(
                total_internal_p, external_pressure, r_clad_inner, r_clad_outer
            )
        )
        
        cladding_radial_inner = self.stress_strain.radial_stress(
            total_internal_p, external_pressure, r_clad_inner, r_clad_outer, r_clad_inner
        )
        
        # Von Mises stress
        cladding_vm = self.stress_strain.von_mises_stress(
            cladding_hoop_inner, cladding_radial_inner, 0.0
        )
        
        # 7. PCI stress enhancement
        cladding_vm_enhanced = self.pci.pci_stress_enhancement(
            cladding_vm, contact_pressure
        )
        
        # 8. Safety margin
        safety_margin = (
            self.stress_strain.cladding_yield_strength - cladding_vm_enhanced
        ) / self.stress_strain.cladding_yield_strength
        
        return {
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
