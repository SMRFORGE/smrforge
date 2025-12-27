# smrforge/core/materials_database.py
"""
Comprehensive material property database for HTGR applications.
Fast, temperature-dependent properties with modern implementation.

This module provides:
- MaterialProperty: Base class for temperature-dependent properties
- GraphiteMaterial: Nuclear graphite properties (IG-110, H-451, NBG-18, etc.)
- HeliumCoolant: Helium coolant properties
- TRISOFuel: TRISO particle fuel properties
- MaterialDatabase: Central database for querying material properties
"""

from dataclasses import dataclass
from functools import lru_cache
from typing import Callable, Dict, Optional, Tuple

import numpy as np
import polars as pl
from numba import njit


@dataclass
class MaterialProperty:
    """
    Base class for temperature-dependent material properties.
    
    Encapsulates a property correlation function with validity range and
    uncertainty information. Can be called directly with a temperature value
    or used for vectorized array evaluation.
    
    Attributes:
        name: Property name (e.g., "thermal_conductivity", "density").
        units: Physical units (e.g., "W/m-K", "kg/m³", "J/kg-K").
        T_min: Minimum valid temperature in Kelvin.
        T_max: Maximum valid temperature in Kelvin.
        correlation: Callable function f(T) that returns property value.
        uncertainty: Optional relative uncertainty (0.05 = 5% uncertainty).
    
    Example:
        >>> def k_corr(T):
        ...     return 100.0 * (T / 300.0) ** (-0.5)
        >>> k = MaterialProperty(
        ...     name="thermal_conductivity",
        ...     units="W/m-K",
        ...     T_min=300.0,
        ...     T_max=2000.0,
        ...     correlation=k_corr,
        ...     uncertainty=0.10
        ... )
        >>> k(600.0)  # Evaluate at 600 K
        70.710678...
        >>> T_array = np.array([400, 600, 800])
        >>> k_array = k.evaluate_array(T_array)
    """

    name: str
    units: str
    T_min: float  # K
    T_max: float  # K
    correlation: Callable[[float], float]
    uncertainty: Optional[float] = None  # Relative uncertainty (e.g., 0.05 = 5%)

    def __call__(self, T: float) -> float:
        """
        Evaluate property at temperature T.
        
        Args:
            T: Temperature in Kelvin.
        
        Returns:
            Property value at temperature T in the specified units.
        
        Raises:
            ValueError: If T is outside the valid range [T_min, T_max].
        
        Example:
            >>> prop = MaterialProperty(..., correlation=lambda T: 100.0 / T)
            >>> value = prop(500.0)  # Returns 0.2
        """
        if not (self.T_min <= T <= self.T_max):
            raise ValueError(
                f"{self.name} correlation valid for {self.T_min}-{self.T_max}K, "
                f"got {T}K"
            )
        return self.correlation(T)

    def evaluate_array(self, T: np.ndarray) -> np.ndarray:
        """
        Vectorized evaluation of property over an array of temperatures.
        
        Args:
            T: 1D NumPy array of temperatures in Kelvin.
        
        Returns:
            1D NumPy array of property values. Values outside [T_min, T_max]
            will raise ValueError (no automatic extrapolation).
        
        Example:
            >>> T = np.linspace(300, 1000, 100)
            >>> values = prop.evaluate_array(T)  # Returns array of length 100
        """
        return np.vectorize(self.correlation)(T)


class GraphiteMaterial:
    """
    Nuclear graphite properties for HTGR applications.
    
    Provides temperature-dependent properties for nuclear-grade graphite used
    as moderator and structural material in HTGRs. Supports multiple graphite
    grades with grade-specific thermal conductivity correlations. All other
    properties (specific heat, density, thermal expansion, etc.) use universal
    correlations valid for all nuclear graphite grades.
    
    Supported Grades:
        - IG-110: High-quality isotropic graphite (high thermal conductivity)
        - H-451: Near-isotropic graphite (used in Fort St. Vrain reactor)
        - NBG-18: Modern vibration-molded graphite (SGL Carbon)
    
    Properties:
        - Thermal conductivity (grade-specific)
        - Specific heat capacity (universal McEligot correlation)
        - Density (universal correlation)
        - Thermal expansion coefficient
        - Emissivity
        - Young's modulus
    
    References:
        IAEA TECDOC-1674: "Thermophysical Properties Database of Materials
        for Light Water Reactors and Heavy Water Reactors"
    
    Example:
        >>> graphite = GraphiteMaterial(grade="IG-110")
        >>> k = graphite.thermal_conductivity(800.0)  # W/m-K at 800 K
        >>> props = graphite.properties_at_temperature(1200.0)  # All properties
        >>> cp = graphite.specific_heat(600.0)  # J/kg-K
    """

    def __init__(self, grade: str = "IG-110"):
        """
        Initialize graphite material for specified grade.
        
        Args:
            grade: Graphite grade string. Must be one of: "IG-110", "H-451",
                or "NBG-18". Defaults to "IG-110".
        
        Raises:
            ValueError: If grade is not recognized.
        
        Example:
            >>> graphite = GraphiteMaterial("H-451")
            >>> print(graphite.grade)  # "H-451"
        """
        self.grade = grade
        self._initialize_properties()

    def _initialize_properties(self):
        """Initialize all property correlations."""

        # Thermal conductivity [W/m-K]
        # Reference: IAEA TECDOC-1674
        if self.grade == "IG-110":

            def k_corr(T):
                # High-quality isotropic graphite
                T_ref = 300.0
                k_ref = 116.0  # W/m-K at 300K
                # Temperature dependence: k ~ T^(-0.6)
                return k_ref * (T / T_ref) ** (-0.6)

            self.thermal_conductivity = MaterialProperty(
                name="thermal_conductivity",
                units="W/m-K",
                T_min=300.0,
                T_max=2500.0,
                correlation=k_corr,
                uncertainty=0.10,
            )

        elif self.grade == "H-451":

            def k_corr(T):
                # Near-isotropic graphite (Fort St. Vrain)
                if T < 600:
                    return 100.0 * (T / 300.0) ** (-0.5)
                else:
                    return 100.0 * (600 / 300.0) ** (-0.5) * (T / 600.0) ** (-0.7)

            self.thermal_conductivity = MaterialProperty(
                name="thermal_conductivity",
                units="W/m-K",
                T_min=300.0,
                T_max=2000.0,
                correlation=k_corr,
                uncertainty=0.15,
            )

        elif self.grade == "NBG-18":

            def k_corr(T):
                # Modern vibration-molded graphite
                return 85.0 * (T / 300.0) ** (-0.55)

            self.thermal_conductivity = MaterialProperty(
                name="thermal_conductivity",
                units="W/m-K",
                T_min=300.0,
                T_max=2200.0,
                correlation=k_corr,
                uncertainty=0.12,
            )

        # Specific heat capacity [J/kg-K]
        # Universal correlation for nuclear graphite
        def cp_corr(T):
            # McEligot correlation (valid for all grades)
            a = -3.02e2
            b = 3.19
            c = -1.83e-3
            d = 5.09e-7
            e = -5.29e-11
            return a + b * T + c * T**2 + d * T**3 + e * T**4

        self.specific_heat = MaterialProperty(
            name="specific_heat",
            units="J/kg-K",
            T_min=300.0,
            T_max=3000.0,
            correlation=cp_corr,
            uncertainty=0.05,
        )

        # Density [kg/m³]
        # Temperature-dependent due to thermal expansion
        def rho_corr(T):
            rho_0 = 1740.0  # kg/m³ at 300K
            alpha = self.thermal_expansion_coefficient(T)
            # Integrate CTE from 300K to T
            delta_L = self._integrate_cte(300.0, T)
            return rho_0 / (1 + delta_L) ** 3

        self.density = MaterialProperty(
            name="density",
            units="kg/m³",
            T_min=300.0,
            T_max=2500.0,
            correlation=rho_corr,
            uncertainty=0.02,
        )

        # Thermal expansion coefficient [1/K]
        def alpha_corr(T):
            # Polynomial fit to experimental data
            return 4.0e-6 + 1.5e-9 * (T - 300)

        self.thermal_expansion = MaterialProperty(
            name="thermal_expansion_coefficient",
            units="1/K",
            T_min=300.0,
            T_max=2500.0,
            correlation=alpha_corr,
            uncertainty=0.15,
        )

        # Emissivity (for radiation heat transfer)
        def emissivity_corr(T):
            # Graphite is nearly black body at high temps
            return 0.80 + 0.05 * (T / 1000.0)

        self.emissivity = MaterialProperty(
            name="emissivity",
            units="dimensionless",
            T_min=300.0,
            T_max=3000.0,
            correlation=emissivity_corr,
            uncertainty=0.10,
        )

        # Young's modulus [GPa]
        # Decreases with irradiation, this is unirradiated
        def E_corr(T):
            E_0 = 10.0  # GPa at 300K
            return E_0 * (1 - 1.5e-4 * (T - 300))

        self.youngs_modulus = MaterialProperty(
            name="youngs_modulus",
            units="GPa",
            T_min=300.0,
            T_max=2000.0,
            correlation=E_corr,
            uncertainty=0.20,
        )

    def _integrate_cte(self, T1: float, T2: float) -> float:
        """Integrate thermal expansion from T1 to T2."""
        from scipy.integrate import quad

        result, _ = quad(self.thermal_expansion_coefficient, T1, T2)
        return result

    def thermal_expansion_coefficient(self, T: float) -> float:
        """Helper to avoid circular reference."""
        return 4.0e-6 + 1.5e-9 * (T - 300)

    def properties_at_temperature(self, T: float) -> Dict[str, float]:
        """
        Get all material properties at a specified temperature.
        
        Args:
            T: Temperature in Kelvin.
        
        Returns:
            Dictionary mapping property names to values:
                - "thermal_conductivity": W/m-K
                - "specific_heat": J/kg-K
                - "density": kg/m³
                - "thermal_expansion": 1/K
                - "emissivity": dimensionless (0-1)
                - "youngs_modulus": Pa
        
        Example:
            >>> graphite = GraphiteMaterial("IG-110")
            >>> props = graphite.properties_at_temperature(1200.0)
            >>> print(f"k = {props['thermal_conductivity']:.2f} W/m-K")
        """
        return {
            "thermal_conductivity": self.thermal_conductivity(T),
            "specific_heat": self.specific_heat(T),
            "density": self.density(T),
            "thermal_expansion": self.thermal_expansion(T),
            "emissivity": self.emissivity(T),
            "youngs_modulus": self.youngs_modulus(T),
        }


class HeliumCoolant:
    """
    Helium coolant properties for HTGR applications.
    
    Provides temperature and pressure-dependent properties for helium gas
    used as primary coolant in HTGRs. Uses NIST-calibrated correlations
    and ideal gas law for density. Properties include thermal conductivity,
    viscosity, specific heat, and derived quantities (Prandtl number,
    Reynolds number).
    
    Properties:
        - Density (pressure-dependent via ideal gas law)
        - Dynamic viscosity (Sutherland's formula)
        - Thermal conductivity (polynomial fit to NIST data)
        - Specific heat at constant pressure (nearly constant for helium)
    
    Default pressure: 7.0 MPa (typical HTGR operating pressure)
    
    Example:
        >>> helium = HeliumCoolant()
        >>> rho = helium.density(T=900.0, P=7.0e6)  # kg/m³
        >>> mu = helium.dynamic_viscosity(900.0)  # Pa-s
        >>> Pr = helium.prandtl_number(900.0)
        >>> Re = helium.reynolds_number(T=900.0, P=7.0e6, velocity=50.0, diameter=0.1)
    """

    def __init__(self):
        """
        Initialize helium coolant properties.
        
        Sets up property correlations and physical constants. Helium is
        treated as an ideal gas with constant specific heat and
        temperature-dependent viscosity and thermal conductivity.
        """
        self._initialize_properties()
        self.molar_mass = 4.002602  # g/mol
        self.R_specific = 2077.0  # J/kg-K

    def _initialize_properties(self):
        """Initialize helium property correlations."""

        # Density from ideal gas law [kg/m³]
        def rho_corr(T, P=7.0e6):
            # P in Pa, T in K
            # rho = P / (R_specific * T)
            return P / (2077.0 * T)

        self.density_func = rho_corr

        # Dynamic viscosity [Pa-s]
        # Sutherland's formula for helium
        def mu_corr(T):
            T_ref = 273.15
            mu_ref = 1.865e-5  # Pa-s at 273.15K
            C = 79.4  # Sutherland constant for He
            return mu_ref * (T / T_ref) ** 1.5 * (T_ref + C) / (T + C)

        self.dynamic_viscosity = MaterialProperty(
            name="dynamic_viscosity",
            units="Pa-s",
            T_min=250.0,
            T_max=2000.0,
            correlation=mu_corr,
            uncertainty=0.02,
        )

        # Thermal conductivity [W/m-K]
        def k_corr(T):
            # Polynomial fit to NIST data
            a = 2.682e-3
            b = 1.123e-4
            c = -9.8e-9
            return a + b * T + c * T**2

        self.thermal_conductivity = MaterialProperty(
            name="thermal_conductivity",
            units="W/m-K",
            T_min=250.0,
            T_max=2000.0,
            correlation=k_corr,
            uncertainty=0.03,
        )

        # Specific heat at constant pressure [J/kg-K]
        def cp_corr(T):
            # Helium cp is nearly constant (ideal gas)
            return 5195.0  # J/kg-K

        self.specific_heat = MaterialProperty(
            name="specific_heat",
            units="J/kg-K",
            T_min=250.0,
            T_max=2000.0,
            correlation=cp_corr,
            uncertainty=0.01,
        )

    def density(self, T: float, P: float = 7.0e6) -> float:
        """
        Calculate helium density using ideal gas law.
        
        Uses rho = P / (R_specific * T) where R_specific = 2077.0 J/kg-K
        for helium.
        
        Args:
            T: Temperature in Kelvin.
            P: Pressure in Pascal. Defaults to 7.0 MPa (typical HTGR
                operating pressure).
        
        Returns:
            Density in kg/m³.
        
        Example:
            >>> helium = HeliumCoolant()
            >>> rho = helium.density(T=900.0, P=7.0e6)
            >>> print(f"ρ = {rho:.2f} kg/m³")
        """
        return P / (self.R_specific * T)

    def prandtl_number(self, T: float) -> float:
        """
        Calculate Prandtl number at temperature T.
        
        Prandtl number characterizes the relative importance of momentum
        and thermal diffusivity: Pr = μ * cp / k
        
        Args:
            T: Temperature in Kelvin.
        
        Returns:
            Dimensionless Prandtl number.
        
        Note:
            For helium, Pr ≈ 0.67-0.7 (nearly constant due to constant cp
            and similar temperature dependencies of μ and k).
        """
        mu = self.dynamic_viscosity(T)
        cp = self.specific_heat(T)
        k = self.thermal_conductivity(T)
        return mu * cp / k

    def reynolds_number(
        self, T: float, P: float, velocity: float, diameter: float
    ) -> float:
        """
        Calculate Reynolds number for helium flow.
        
        Reynolds number characterizes flow regime (laminar vs. turbulent):
        Re = ρ * v * D / μ
        
        Args:
            T: Temperature in Kelvin.
            P: Pressure in Pascal.
            velocity: Flow velocity in m/s.
            diameter: Hydraulic diameter in meters (4 * area / wetted perimeter
                for non-circular channels).
        
        Returns:
            Dimensionless Reynolds number.
        
        Note:
            Transition from laminar to turbulent typically occurs at Re ≈ 2300
            for pipe flow. HTGR coolant channels often operate in turbulent
            regime (Re > 10,000) for effective heat transfer.
        """
        rho = self.density(T, P)
        mu = self.dynamic_viscosity(T)
        return rho * velocity * diameter / mu


class TRISOFuel:
    """
    TRISO (Tristructural-Isotropic) particle fuel properties.
    
    TRISO particles consist of a fuel kernel (UCO or UO2) surrounded by
    multiple coating layers: porous buffer, inner PyC, SiC, and outer PyC.
    This class provides thermal properties for each layer and calculates
    effective thermal conductivity through the particle using a spherical
    resistance model.
    
    Layer Structure (from inside to outside):
        1. Kernel: UCO or UO2 (fuel)
        2. Buffer: Porous PyC (accommodates fission products, 100 μm)
        3. IPyC: Inner dense PyC layer (40 μm)
        4. SiC: Silicon carbide barrier layer (35 μm, primary containment)
        5. OPyC: Outer dense PyC layer (40 μm)
    
    Standard Geometry (425 μm kernel diameter):
        - Kernel radius: 212.5 μm
        - Buffer thickness: 100 μm
        - IPyC thickness: 40 μm
        - SiC thickness: 35 μm
        - OPyC thickness: 40 μm
        - Total particle radius: ~427.5 μm
    
    Example:
        >>> triso_uco = TRISOFuel(kernel_type="UCO")
        >>> k_eff = triso_uco.effective_conductivity(T=1200.0)  # W/m-K
        >>> k_kernel = triso_uco.kernel_conductivity(1200.0)
        >>> P_fail = triso_uco.failure_probability(T_max=1600.0, burnup=15.0, fluence=2e25)
    """

    def __init__(self, kernel_type: str = "UCO"):
        """
        Initialize TRISO fuel particle properties.
        
        Args:
            kernel_type: Fuel kernel type, either "UCO" (uranium oxycarbide)
                or "UO2" (uranium dioxide). Defaults to "UCO".
        
        Note:
            UCO (UC0.5O1.5) has lower thermal conductivity than UO2 but better
            chemical stability at high temperatures. UO2 has well-characterized
            properties but may have compatibility issues at extreme conditions.
        """
        self.kernel_type = kernel_type  # "UCO" or "UO2"
        self._initialize_geometry()
        self._initialize_properties()

    def _initialize_geometry(self):
        """Standard TRISO geometry [cm]."""
        self.kernel_radius = 212.5e-4  # 425 μm diameter
        self.buffer_thickness = 100e-4  # Porous PyC buffer
        self.ipyc_thickness = 40e-4  # Inner PyC
        self.sic_thickness = 35e-4  # SiC
        self.opyc_thickness = 40e-4  # Outer PyC

        # Cumulative radii
        self.r_kernel = self.kernel_radius
        self.r_buffer = self.r_kernel + self.buffer_thickness
        self.r_ipyc = self.r_buffer + self.ipyc_thickness
        self.r_sic = self.r_ipyc + self.sic_thickness
        self.r_opyc = self.r_sic + self.opyc_thickness

        self.total_radius = self.r_opyc

    def _initialize_properties(self):
        """Initialize layer properties."""

        # Kernel thermal conductivity [W/m-K]
        if self.kernel_type == "UCO":

            def k_kernel(T):
                # UCO (UC0.5O1.5) correlation
                # Lower than UO2 due to carbon
                return 1.0 / (0.06 + 2.4e-4 * T)

        else:  # UO2

            def k_kernel(T):
                # Standard UO2 correlation (Fink-Petersen)
                k_0 = 100.0 / (6.548 + 23.533 * (T / 1000.0))
                # Porosity correction (assume 95% TD)
                P = 0.05
                return k_0 * (1 - P) / (1 + 0.5 * P)

        self.kernel_conductivity = MaterialProperty(
            name="kernel_thermal_conductivity",
            units="W/m-K",
            T_min=300.0,
            T_max=2500.0,
            correlation=k_kernel,
            uncertainty=0.15,
        )

        # Buffer layer (porous PyC) [W/m-K]
        def k_buffer(T):
            # Very low due to high porosity (50%)
            return 0.5 * (1.0 + 5.0e-4 * T)

        self.buffer_conductivity = MaterialProperty(
            name="buffer_thermal_conductivity",
            units="W/m-K",
            T_min=300.0,
            T_max=2500.0,
            correlation=k_buffer,
            uncertainty=0.30,
        )

        # IPyC and OPyC [W/m-K]
        def k_pyc(T):
            # Dense pyrolytic carbon
            return 4.0 * (1.0 + 1.0e-3 * T)

        self.pyc_conductivity = MaterialProperty(
            name="pyc_thermal_conductivity",
            units="W/m-K",
            T_min=300.0,
            T_max=2500.0,
            correlation=k_pyc,
            uncertainty=0.20,
        )

        # SiC layer [W/m-K]
        def k_sic(T):
            # SiC has excellent thermal conductivity
            # Decreases with temperature
            k_300 = 80.0
            return k_300 * (300.0 / T) ** 0.5

        self.sic_conductivity = MaterialProperty(
            name="sic_thermal_conductivity",
            units="W/m-K",
            T_min=300.0,
            T_max=2500.0,
            correlation=k_sic,
            uncertainty=0.10,
        )

    def effective_conductivity(self, T: float) -> float:
        """
        Compute effective thermal conductivity through all TRISO layers.
        
        Uses a 1D spherical resistance model treating each layer as a thermal
        resistance in series. Assumes steady-state radial heat conduction.
        
        Args:
            T: Temperature in Kelvin (assumes all layers at same temperature
                for simplicity; real particles have radial temperature gradient).
        
        Returns:
            Effective thermal conductivity in W/m-K through the entire
            particle (kernel + all coating layers).
        
        Note:
            This is a simplified model assuming uniform temperature across
            layers. Real TRISO particles have significant radial temperature
            gradients due to internal heat generation in the kernel.
        """
        # Thermal resistances in series
        k_kernel = self.kernel_conductivity(T)
        k_buffer = self.buffer_conductivity(T)
        k_ipyc = self.pyc_conductivity(T)
        k_sic = self.sic_conductivity(T)
        k_opyc = self.pyc_conductivity(T)

        # Spherical resistance: R = (1/r1 - 1/r2) / (4*pi*k)
        R_kernel = 0  # Reference
        R_buffer = (1 / self.r_kernel - 1 / self.r_buffer) / (4 * np.pi * k_buffer)
        R_ipyc = (1 / self.r_buffer - 1 / self.r_ipyc) / (4 * np.pi * k_ipyc)
        R_sic = (1 / self.r_ipyc - 1 / self.r_sic) / (4 * np.pi * k_sic)
        R_opyc = (1 / self.r_sic - 1 / self.r_opyc) / (4 * np.pi * k_opyc)

        R_total = R_buffer + R_ipyc + R_sic + R_opyc

        # Effective conductivity over total particle
        k_eff = (1 / self.r_kernel - 1 / self.r_opyc) / (4 * np.pi * R_total)
        return k_eff

    def failure_probability(self, T_max: float, burnup: float, fluence: float) -> float:
        """
        Estimate TRISO particle failure probability based on operating conditions.
        
        Uses simplified failure models considering temperature, burnup, and
        fast neutron fluence effects. Based on AGR-1 experiment data and
        typical failure mechanisms (SiC layer failure, kernel migration,
        pressure vessel failure).
        
        Args:
            T_max: Maximum temperature experienced during operation in Kelvin.
            burnup: Fuel burnup in % FIMA (Fissions per Initial Metal Atom).
                Typical values: 5-20% FIMA for HTGR fuel.
            fluence: Fast neutron fluence (>0.18 MeV) in n/cm². Typical values:
                1e25 - 5e25 n/cm² for HTGR fuel lifetime.
        
        Returns:
            Failure probability as a dimensionless value between 0 and 1.
            Typical values: 1e-6 to 1e-4 for well-designed TRISO particles.
        
        Note:
            This is a simplified empirical model. Real failure analysis
            requires detailed mechanistic modeling of stress states, fission
            product pressures, and irradiation damage.
        
        Example:
            >>> triso = TRISOFuel("UCO")
            >>> P_fail = triso.failure_probability(
            ...     T_max=1600.0,  # 1327°C
            ...     burnup=15.0,   # 15% FIMA
            ...     fluence=2e25   # 2×10²⁵ n/cm²
            ... )
            >>> print(f"Failure probability: {P_fail:.2e}")
        """
        # Simplified model - real version would be more complex
        # Based on AGR-1 experiment data

        # Temperature factor
        T_threshold = 1873.0  # 1600°C
        f_T = np.exp((T_max - T_threshold) / 100.0) if T_max > T_threshold else 0.0

        # Burnup factor
        burnup_threshold = 20.0  # % FIMA
        f_bu = (burnup / burnup_threshold) ** 2 if burnup > burnup_threshold else 0.0

        # Fluence factor (fast fluence > 0.18 MeV)
        fluence_threshold = 4.0e25  # n/cm²
        f_flu = (
            (fluence / fluence_threshold) ** 1.5 if fluence > fluence_threshold else 0.0
        )

        # Combined failure probability (simplified)
        P_fail = min(1.0e-5 * (1 + f_T + f_bu + f_flu), 1.0)

        return P_fail


class MaterialDatabase:
    """
    Central database for all HTGR materials.
    
    Provides a unified interface for accessing material properties across
    different material types (graphite, helium, TRISO fuel, structural
    materials). Uses Polars for fast querying and comparison operations.
    Supports filtering by material category and comparison of properties
    across multiple materials.
    
    Available Materials:
        - Graphite: IG-110, H-451, NBG-18
        - Coolant: Helium
        - Fuel: TRISO (UCO and UO2 kernels)
        - Structural: B4C (control rods), Alloy 800H (metallic internals)
    
    Example:
        >>> db = MaterialDatabase()
        >>> graphite = db.get("graphite_IG-110")
        >>> k = graphite.thermal_conductivity(1200.0)
        >>> materials = db.list_materials(category="moderator")
        >>> comparison = db.compare_properties(
        ...     material_names=["graphite_IG-110", "graphite_H-451"],
        ...     property_name="thermal_conductivity",
        ...     T_range=np.linspace(300, 2000, 100)
        ... )
    """

    def __init__(self):
        """
        Initialize material database.
        
        Loads all available materials and builds a searchable index.
        Materials are accessible by name using get() method.
        """
        self.materials: Dict[str, object] = {}
        self._load_materials()
        self._build_index()

    def _load_materials(self):
        """Load all material definitions."""
        # Graphite grades
        self.materials["graphite_IG-110"] = GraphiteMaterial("IG-110")
        self.materials["graphite_H-451"] = GraphiteMaterial("H-451")
        self.materials["graphite_NBG-18"] = GraphiteMaterial("NBG-18")

        # Coolant
        self.materials["helium"] = HeliumCoolant()

        # Fuel
        self.materials["triso_uco"] = TRISOFuel("UCO")
        self.materials["triso_uo2"] = TRISOFuel("UO2")

        # Structural materials
        self._add_structural_materials()

    def _add_structural_materials(self):
        """Add structural/control materials."""
        # Simplified - would expand these

        # Boron carbide (control rods)
        class B4C:
            def thermal_conductivity(self, T):
                return 20.0 + 0.01 * T  # W/m-K

            def density(self, T):
                return 2520.0  # kg/m³

        self.materials["b4c"] = B4C()

        # Alloy 800H (metallic internals)
        class Alloy800H:
            def thermal_conductivity(self, T):
                return 11.6 + 0.0075 * T  # W/m-K

            def density(self, T):
                return 8000.0  # kg/m³

        self.materials["alloy_800h"] = Alloy800H()

    def _build_index(self):
        """Build searchable index of materials."""
        records = []
        for name, mat in self.materials.items():
            mat_type = mat.__class__.__name__
            records.append(
                {"name": name, "type": mat_type, "category": self._categorize(mat_type)}
            )

        self.index = pl.DataFrame(records)

    @staticmethod
    def _categorize(mat_type: str) -> str:
        """Categorize material type."""
        if "Graphite" in mat_type:
            return "moderator"
        elif "Helium" in mat_type:
            return "coolant"
        elif "TRISO" in mat_type:
            return "fuel"
        else:
            return "structural"

    def get(self, name: str):
        """Get material by name."""
        if name not in self.materials:
            raise KeyError(
                f"Material '{name}' not found. Available: {list(self.materials.keys())}"
            )
        return self.materials[name]

    def list_materials(self, category: Optional[str] = None) -> pl.DataFrame:
        """
        List all materials in the database, optionally filtered by category.
        
        Args:
            category: Optional category filter. Categories include:
                - "moderator" (graphite materials)
                - "coolant" (helium)
                - "fuel" (TRISO particles)
                - "structural" (B4C, Alloy 800H, etc.)
                If None, returns all materials.
        
        Returns:
            Polars DataFrame with columns: name, type, category.
        
        Example:
            >>> db = MaterialDatabase()
            >>> all_materials = db.list_materials()
            >>> graphite_only = db.list_materials(category="moderator")
        """
        if category:
            return self.index.filter(pl.col("category") == category)
        return self.index

    def compare_properties(
        self, material_names: list, property_name: str, T_range: np.ndarray
    ) -> pl.DataFrame:
        """
        Compare a specific property across multiple materials over temperature range.
        
        Evaluates the specified property for each material at each temperature
        point and returns results in a Polars DataFrame suitable for plotting
        or analysis.
        
        Args:
            material_names: List of material name strings to compare.
            property_name: Property name string (e.g., "thermal_conductivity",
                "density", "specific_heat"). Must be a valid property on the
                material objects.
            T_range: 1D NumPy array of temperatures in Kelvin to evaluate.
        
        Returns:
            Polars DataFrame with columns:
                - material: Material name (str)
                - temperature: Temperature in K (float)
                - property: Property name (str)
                - value: Property value (float)
        
        Example:
            >>> db = MaterialDatabase()
            >>> T = np.linspace(400, 1600, 100)
            >>> comparison = db.compare_properties(
            ...     material_names=["graphite_IG-110", "graphite_H-451"],
            ...     property_name="thermal_conductivity",
            ...     T_range=T
            ... )
            >>> # Plot comparison
            >>> import matplotlib.pyplot as plt
            >>> for mat in comparison["material"].unique():
            ...     data = comparison.filter(pl.col("material") == mat)
            ...     plt.plot(data["temperature"], data["value"], label=mat)
        """
        records = []
        for name in material_names:
            mat = self.get(name)
            prop = getattr(mat, property_name, None)
            if prop is None:
                continue

            for T in T_range:
                if hasattr(prop, "__call__"):
                    if property_name == "density" and name == "helium":
                        value = prop(T, P=7.0e6)  # Default pressure
                    else:
                        value = prop(T)
                else:
                    value = prop

                records.append(
                    {
                        "material": name,
                        "temperature": T,
                        "property": property_name,
                        "value": value,
                    }
                )

        return pl.DataFrame(records)


# Fast Numba-accelerated property evaluations for solver
@njit(cache=True)
def graphite_conductivity_fast(T: np.ndarray, grade: int = 0) -> np.ndarray:
    """
    Ultra-fast graphite conductivity evaluation.
    grade: 0=IG-110, 1=H-451, 2=NBG-18
    """
    k = np.zeros_like(T)

    if grade == 0:  # IG-110
        k_ref = 116.0
        for i in range(len(T)):
            k[i] = k_ref * (T[i] / 300.0) ** (-0.6)
    elif grade == 1:  # H-451
        for i in range(len(T)):
            if T[i] < 600:
                k[i] = 100.0 * (T[i] / 300.0) ** (-0.5)
            else:
                k[i] = 100.0 * (600 / 300.0) ** (-0.5) * (T[i] / 600.0) ** (-0.7)
    elif grade == 2:  # NBG-18
        for i in range(len(T)):
            k[i] = 85.0 * (T[i] / 300.0) ** (-0.55)

    return k


@njit(cache=True)
def helium_properties_fast(
    T: np.ndarray, P: float = 7.0e6
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Fast helium property evaluation.
    Returns: density [kg/m³], viscosity [Pa-s], conductivity [W/m-K]
    """
    n = len(T)
    rho = np.zeros(n)
    mu = np.zeros(n)
    k = np.zeros(n)

    R = 2077.0
    T_ref = 273.15
    mu_ref = 1.865e-5
    C = 79.4

    for i in range(n):
        # Density
        rho[i] = P / (R * T[i])

        # Viscosity (Sutherland)
        mu[i] = mu_ref * (T[i] / T_ref) ** 1.5 * (T_ref + C) / (T[i] + C)

        # Conductivity
        k[i] = 2.682e-3 + 1.123e-4 * T[i] - 9.8e-9 * T[i] ** 2

    return rho, mu, k


if __name__ == "__main__":
    # Demonstration
    db = MaterialDatabase()

    print("Available materials:")
    print(db.list_materials())
    print()

    # Compare graphite grades
    T_range = np.linspace(300, 2000, 20)
    comparison = db.compare_properties(
        ["graphite_IG-110", "graphite_H-451", "graphite_NBG-18"],
        "thermal_conductivity",
        T_range,
    )
    print("Graphite thermal conductivity comparison:")
    print(comparison.head(10))
    print()

    # TRISO particle analysis
    triso = db.get("triso_uco")
    print(f"TRISO geometry:")
    print(f"  Total radius: {triso.total_radius*1e4:.1f} μm")
    print(f"  Effective k at 1200K: {triso.effective_conductivity(1200.0):.2f} W/m-K")
    print()

    # Performance test
    import time

    T_array = np.linspace(300, 2000, 10000)

    start = time.time()
    k_graphite = graphite_conductivity_fast(T_array, grade=0)
    t1 = time.time() - start

    print(f"Fast evaluation of 10k points: {t1*1000:.2f} ms")
