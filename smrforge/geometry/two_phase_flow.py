"""
Two-phase flow support for BWR SMRs.

Provides advanced two-phase flow calculations including:
- Void fraction calculations
- Quality (steam mass fraction) calculations
- Two-phase pressure drop
- Flow regime determination
- Heat transfer correlations
"""

from dataclasses import dataclass, field
from typing import Dict, Optional

import numpy as np

from ..utils.logging import get_logger
from .core_geometry import Point3D

logger = get_logger("smrforge.geometry.two_phase_flow")


@dataclass
class TwoPhaseFlowRegion:
    """
    Two-phase flow region for BWR SMRs.
    
    Represents a region with two-phase (liquid + vapor) flow,
    as occurs in BWR cores where water boils as it flows upward.
    
    Attributes:
        id: Unique identifier
        position: Center position
        flow_area: Flow area [cm²]
        height: Region height [cm]
        pressure: Pressure [Pa]
        inlet_temperature: Inlet temperature [K]
        outlet_temperature: Outlet temperature [K]
        mass_flow_rate: Mass flow rate [kg/s]
        void_fraction: Void fraction (vapor volume fraction, 0-1)
        quality: Steam mass fraction (0-1)
        flow_regime: Flow regime ("bubbly", "slug", "churn", "annular", "mist")
        _saturation_cache: Internal cache for saturation properties
    """
    
    id: int
    position: Point3D
    flow_area: float  # cm²
    height: float  # cm
    pressure: float = 7.0e6  # Pa (7 MPa typical BWR)
    inlet_temperature: float = 558.15  # K (285°C, subcooled)
    outlet_temperature: float = 558.15  # K (saturated)
    mass_flow_rate: float = 0.0  # kg/s
    void_fraction: float = 0.0  # 0-1
    quality: float = 0.0  # 0-1 (steam mass fraction)
    flow_regime: str = "bubbly"  # "bubbly", "slug", "churn", "annular", "mist"
    _saturation_cache: Optional[Dict[float, tuple[float, float]]] = field(default=None, init=False, repr=False)
    
    def calculate_void_fraction_from_quality(self) -> float:
        """
        Calculate void fraction from quality using Zivi correlation.
        
        Zivi correlation: α = 1 / (1 + (1-x)/x * (ρ_v/ρ_l)^(1/3))
        
        Returns:
            Void fraction (0-1)
        """
        if self.quality <= 0.0:
            return 0.0
        if self.quality >= 1.0:
            return 1.0
        
        # Get saturation properties at pressure
        rho_l, rho_v = self._get_saturation_densities()
        
        if rho_l <= 0 or rho_v <= 0:
            return 0.0
        
        # Zivi correlation
        x = self.quality
        density_ratio = rho_v / rho_l
        void_fraction = 1.0 / (1.0 + (1.0 - x) / x * (density_ratio ** (1.0 / 3.0)))
        
        return np.clip(void_fraction, 0.0, 1.0)
    
    def calculate_quality_from_void_fraction(self) -> float:
        """
        Calculate quality from void fraction (inverse of Zivi).
        
        Returns:
            Quality (steam mass fraction, 0-1)
        """
        if self.void_fraction <= 0.0:
            return 0.0
        if self.void_fraction >= 1.0:
            return 1.0
        
        # Get saturation properties
        rho_l, rho_v = self._get_saturation_densities()
        
        if rho_l <= 0 or rho_v <= 0:
            return 0.0
        
        # Inverse Zivi correlation
        alpha = self.void_fraction
        density_ratio = rho_v / rho_l
        
        # Solve: α = 1 / (1 + (1-x)/x * (ρ_v/ρ_l)^(1/3))
        # Rearranging: x = 1 / (1 + (1-α)/α * (ρ_l/ρ_v)^(1/3))
        quality = 1.0 / (1.0 + (1.0 - alpha) / alpha * ((rho_l / rho_v) ** (1.0 / 3.0)))
        
        return np.clip(quality, 0.0, 1.0)
    
    def determine_flow_regime(self) -> str:
        """
        Determine two-phase flow regime based on void fraction and flow conditions.
        
        Flow regimes:
        - Bubbly: α < 0.3, discrete bubbles
        - Slug: 0.3 < α < 0.5, large bubbles
        - Churn: 0.5 < α < 0.7, chaotic flow
        - Annular: 0.7 < α < 0.95, liquid film on wall
        - Mist: α > 0.95, liquid droplets in vapor
        
        Returns:
            Flow regime string
        """
        alpha = self.void_fraction
        
        if alpha < 0.3:
            return "bubbly"
        elif alpha < 0.5:
            return "slug"
        elif alpha < 0.7:
            return "churn"
        elif alpha < 0.95:
            return "annular"
        else:
            return "mist"
    
    def calculate_pressure_drop(
        self,
        friction_factor: float = 0.02,
        acceleration_loss: bool = True,
    ) -> float:
        """
        Calculate two-phase pressure drop.
        
        Includes:
        - Frictional pressure drop
        - Acceleration pressure drop (due to phase change)
        - Gravitational pressure drop (negligible for horizontal flow)
        
        Args:
            friction_factor: Friction factor (default: 0.02)
            acceleration_loss: Include acceleration pressure drop
        
        Returns:
            Pressure drop [Pa]
        """
        # Mass flux [kg/(m²·s)]
        mass_flux = self.mass_flow_rate / (self.flow_area / 1e4)  # Convert cm² to m²
        
        # Frictional pressure drop (simplified)
        # ΔP_f = f * (L/D) * (G²/(2*ρ))
        # Using average density
        rho_l, rho_v = self._get_saturation_densities()
        rho_avg = self.void_fraction * rho_v + (1.0 - self.void_fraction) * rho_l
        
        # Hydraulic diameter [m]
        D_h = 2.0 * np.sqrt(self.flow_area / np.pi / 1e4)  # Convert to m
        
        # Frictional pressure drop
        L = self.height / 100.0  # Convert to m
        dp_friction = friction_factor * (L / D_h) * (mass_flux ** 2) / (2.0 * rho_avg)
        
        # Acceleration pressure drop (due to phase change)
        dp_accel = 0.0
        if acceleration_loss and self.quality > 0:
            # Simplified: ΔP_accel = G² * (1/ρ_out - 1/ρ_in)
            # Using quality change
            rho_in = rho_l  # Subcooled inlet
            rho_out = 1.0 / (self.quality / rho_v + (1.0 - self.quality) / rho_l)
            dp_accel = mass_flux ** 2 * (1.0 / rho_out - 1.0 / rho_in)
        
        total_dp = dp_friction + dp_accel
        
        return total_dp
    
    def _get_saturation_densities(self) -> tuple[float, float]:
        """
        Get saturation liquid and vapor densities at pressure.
        
        Uses internal cache for performance when called multiple times
        with the same pressure.
        
        Returns:
            Tuple of (rho_liquid [kg/m³], rho_vapor [kg/m³])
        """
        # Initialize cache if needed
        if self._saturation_cache is None:
            self._saturation_cache = {}
        
        # Check cache
        if self.pressure in self._saturation_cache:
            return self._saturation_cache[self.pressure]
        
        # Simplified saturation properties (would use steam tables in production)
        # At 7 MPa: T_sat ≈ 285°C, rho_l ≈ 740 kg/m³, rho_v ≈ 36 kg/m³
        # Linear approximation for different pressures
        
        P_MPa = self.pressure / 1e6  # Convert to MPa
        
        # Saturation temperature [K] (simplified)
        T_sat = 273.15 + 179.9 * (P_MPa ** 0.25)  # Approximate
        
        # Liquid density [kg/m³] (simplified)
        rho_l = 1000.0 - 50.0 * (P_MPa - 0.1)  # Approximate
        
        # Vapor density [kg/m³] (simplified)
        rho_v = 0.6 * P_MPa  # Approximate
        
        result = (rho_l, rho_v)
        
        # Cache result (limit cache size to prevent memory issues)
        if len(self._saturation_cache) < 128:
            self._saturation_cache[self.pressure] = result
        
        return result
    
    def update_from_heat_addition(
        self,
        heat_added: float,  # W
        inlet_quality: float = 0.0,
    ) -> Dict[str, float]:
        """
        Update two-phase properties based on heat addition.
        
        Args:
            heat_added: Heat added to flow [W]
            inlet_quality: Inlet quality (0 for subcooled)
        
        Returns:
            Dictionary with updated properties:
            - 'quality': Outlet quality
            - 'void_fraction': Outlet void fraction
            - 'flow_regime': Flow regime
        """
        # Latent heat of vaporization [J/kg]
        h_fg = 2.26e6  # J/kg (at 7 MPa, simplified)
        
        # Quality increase from heat addition
        delta_quality = heat_added / (self.mass_flow_rate * h_fg) if self.mass_flow_rate > 0 else 0.0
        
        # Update quality
        self.quality = np.clip(inlet_quality + delta_quality, 0.0, 1.0)
        
        # Update void fraction
        self.void_fraction = self.calculate_void_fraction_from_quality()
        
        # Update flow regime
        self.flow_regime = self.determine_flow_regime()
        
        return {
            "quality": self.quality,
            "void_fraction": self.void_fraction,
            "flow_regime": self.flow_regime,
        }


def create_bwr_two_phase_region(
    id: int,
    position: Point3D,
    flow_area: float,
    height: float,
    mass_flow_rate: float,
    pressure: float = 7.0e6,
) -> TwoPhaseFlowRegion:
    """
    Create a typical BWR two-phase flow region.
    
    Args:
        id: Region identifier
        position: Center position
        flow_area: Flow area [cm²]
        height: Region height [cm]
        mass_flow_rate: Mass flow rate [kg/s]
        pressure: Pressure [Pa] (default: 7 MPa typical BWR)
    
    Returns:
        TwoPhaseFlowRegion instance

    Example:
        >>> from smrforge.geometry.core_geometry import Point3D
        >>> from smrforge.geometry.two_phase_flow import create_bwr_two_phase_region
        >>> region = create_bwr_two_phase_region(
        ...     id=1,
        ...     position=Point3D(0.0, 0.0, 100.0),
        ...     flow_area=50.0,
        ...     height=400.0,
        ...     mass_flow_rate=120.0,
        ... )
        >>> region.determine_flow_regime()
    """
    region = TwoPhaseFlowRegion(
        id=id,
        position=position,
        flow_area=flow_area,
        height=height,
        pressure=pressure,
        mass_flow_rate=mass_flow_rate,
        inlet_temperature=558.15,  # K (subcooled)
        outlet_temperature=558.15,  # K (saturated)
    )
    
    return region
