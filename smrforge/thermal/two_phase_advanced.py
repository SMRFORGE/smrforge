"""
Advanced two-phase flow models for BWR SMRs and LOCA analysis.

This module provides:
- Advanced drift-flux models (Zuber-Findlay, Chexal-Lellouche, Ishii-Mishima)
- Two-fluid models for detailed analysis
- Advanced interfacial transfer models (mass, momentum, energy)
- Enhanced boiling heat transfer correlations
- Integration with thermal-hydraulics solver
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np

from ..utils.logging import get_logger

logger = get_logger("smrforge.thermal.two_phase_advanced")


@dataclass
class DriftFluxModel:
    """
    Advanced drift-flux models for two-phase flow.

    Drift-flux models relate void fraction to quality and flow conditions
    using a drift velocity and distribution parameter.

    Models implemented:
    - Zuber-Findlay (1965): Classic drift-flux model
    - Chexal-Lellouche (1990): Improved model for vertical flows
    - Ishii-Mishima (1984): For various flow regimes

    Attributes:
        model_type: Drift-flux model type ('zuber_findlay', 'chexal_lellouche', 'ishii_mishima')
        distribution_parameter: Distribution parameter C0 (default: calculated)
        drift_velocity: Drift velocity [m/s] (default: calculated)
    """

    model_type: str = (
        "chexal_lellouche"  # 'zuber_findlay', 'chexal_lellouche', 'ishii_mishima'
    )
    distribution_parameter: Optional[float] = None  # C0
    drift_velocity: Optional[float] = None  # Vgj [m/s]

    def calculate_void_fraction(
        self,
        quality: float,
        mass_flux: float,  # kg/(m²·s)
        pressure: float,  # Pa
        diameter: float,  # m
        flow_direction: str = "vertical",  # 'vertical', 'horizontal'
    ) -> float:
        """
        Calculate void fraction using drift-flux model.

        Void fraction equation: α = j_g / (C0 * j + Vgj)
        where j = j_l + j_g is total volumetric flux

        Args:
            quality: Steam mass fraction (0-1)
            mass_flux: Mass flux [kg/(m²·s)]
            pressure: Pressure [Pa]
            diameter: Channel diameter [m]
            flow_direction: Flow direction

        Returns:
            Void fraction (0-1)
        """
        if quality <= 0.0:
            return 0.0
        if quality >= 1.0:
            return 1.0

        # Get saturation properties
        rho_l, rho_v, h_fg = self._get_saturation_properties(pressure)

        if rho_l <= 0 or rho_v <= 0:
            return 0.0

        # Calculate distribution parameter and drift velocity
        C0 = self._calculate_distribution_parameter(
            quality, mass_flux, pressure, diameter, flow_direction
        )
        Vgj = self._calculate_drift_velocity(
            quality, mass_flux, pressure, diameter, flow_direction
        )

        # Volumetric fluxes
        j_l = mass_flux * (1.0 - quality) / rho_l  # Liquid flux [m/s]
        j_g = mass_flux * quality / rho_v  # Vapor flux [m/s]
        j = j_l + j_g  # Total volumetric flux [m/s]

        # Drift-flux void fraction
        if j > 0:
            void_fraction = j_g / (C0 * j + Vgj)
        else:
            void_fraction = 0.0

        return np.clip(void_fraction, 0.0, 1.0)

    def _calculate_distribution_parameter(
        self,
        quality: float,
        mass_flux: float,
        pressure: float,
        diameter: float,
        flow_direction: str,
    ) -> float:
        """
        Calculate distribution parameter C0.

        C0 accounts for non-uniform void distribution across channel.
        """
        if self.distribution_parameter is not None:
            return self.distribution_parameter

        if self.model_type == "zuber_findlay":
            # Zuber-Findlay: C0 = 1.13 for vertical flow
            return 1.13 if flow_direction == "vertical" else 1.0

        elif self.model_type == "chexal_lellouche":
            # Chexal-Lellouche: C0 depends on quality and flow conditions
            # Simplified: C0 = 1.0 + 0.2 * (1 - exp(-10*quality))
            C0 = 1.0 + 0.2 * (1.0 - np.exp(-10.0 * quality))
            return C0

        elif self.model_type == "ishii_mishima":
            # Ishii-Mishima: C0 depends on flow regime
            # Simplified: C0 = 1.2 - 0.2 * sqrt(rho_v/rho_l)
            rho_l, rho_v, _ = self._get_saturation_properties(pressure)
            C0 = 1.2 - 0.2 * np.sqrt(rho_v / rho_l)
            return C0

        else:
            return 1.0  # Default

    def _calculate_drift_velocity(
        self,
        quality: float,
        mass_flux: float,
        pressure: float,
        diameter: float,
        flow_direction: str,
    ) -> float:
        """
        Calculate drift velocity Vgj.

        Drift velocity is the relative velocity between vapor and liquid phases.
        """
        if self.drift_velocity is not None:
            return self.drift_velocity

        # Get saturation properties
        rho_l, rho_v, h_fg = self._get_saturation_properties(pressure)

        if flow_direction != "vertical":
            return 0.0  # No drift in horizontal flow

        # Calculate based on model
        if self.model_type == "zuber_findlay":
            # Zuber-Findlay: Vgj = 1.41 * (g * sigma * (rho_l - rho_v) / rho_l^2)^0.25
            g = 9.81  # m/s²
            sigma = 0.0589  # N/m (surface tension at 7 MPa, simplified)
            Vgj = 1.41 * (g * sigma * (rho_l - rho_v) / (rho_l**2)) ** 0.25
            return Vgj

        elif self.model_type == "chexal_lellouche":
            # Chexal-Lellouche: More complex, depends on quality and flow
            g = 9.81
            sigma = 0.0589
            base_velocity = 1.41 * (g * sigma * (rho_l - rho_v) / (rho_l**2)) ** 0.25

            # Quality-dependent correction
            quality_factor = 1.0 + 0.1 * quality
            return base_velocity * quality_factor

        elif self.model_type == "ishii_mishima":
            # Ishii-Mishima: Similar to Zuber-Findlay
            g = 9.81
            sigma = 0.0589
            Vgj = 1.41 * (g * sigma * (rho_l - rho_v) / (rho_l**2)) ** 0.25
            return Vgj

        else:
            return 0.0

    def _get_saturation_properties(self, pressure: float) -> Tuple[float, float, float]:
        """
        Get saturation properties at pressure.

        Returns:
            Tuple of (rho_liquid, rho_vapor, h_fg) [kg/m³, kg/m³, J/kg]
        """
        # Simplified saturation properties (would use steam tables in practice)
        # At 7 MPa (typical BWR):
        if abs(pressure - 7e6) < 1e5:
            rho_l = 740.0  # kg/m³
            rho_v = 36.5  # kg/m³
            h_fg = 1.5e6  # J/kg
        else:
            # Approximate scaling
            p_ref = 7e6
            rho_l = 740.0 * (pressure / p_ref) ** 0.1
            rho_v = 36.5 * (pressure / p_ref) ** 0.5
            h_fg = 1.5e6 * (p_ref / pressure) ** 0.2

        return rho_l, rho_v, h_fg


@dataclass
class TwoFluidModel:
    """
    Two-fluid model for detailed two-phase flow analysis.

    Two-fluid models solve separate conservation equations for liquid and vapor
    phases, providing more detailed analysis than drift-flux models.

    Conservation equations:
    - Mass conservation (liquid and vapor)
    - Momentum conservation (liquid and vapor)
    - Energy conservation (liquid and vapor)
    - Interfacial transfer (mass, momentum, energy)

    Attributes:
        pressure: Pressure [Pa]
        temperature: Temperature [K]
        mass_flux: Mass flux [kg/(m²·s)]
        quality: Steam mass fraction (0-1)
        diameter: Channel diameter [m]
        length: Channel length [m]
    """

    pressure: float  # Pa
    temperature: float  # K
    mass_flux: float  # kg/(m²·s)
    quality: float  # 0-1
    diameter: float  # m
    length: float  # m

    def solve_two_fluid(
        self,
        heat_flux: float,  # W/m²
        inlet_quality: float,
        outlet_quality: Optional[float] = None,
    ) -> Dict:
        """
        Solve two-fluid model equations.

        Args:
            heat_flux: Wall heat flux [W/m²]
            inlet_quality: Inlet quality (0-1)
            outlet_quality: Optional outlet quality (if None, calculated)

        Returns:
            Dictionary with solution:
                - void_fraction: Void fraction distribution
                - pressure_drop: Pressure drop [Pa]
                - liquid_velocity: Liquid velocity [m/s]
                - vapor_velocity: Vapor velocity [m/s]
                - temperature: Temperature distribution [K]
        """
        # Get saturation properties
        rho_l, rho_v, h_fg = self._get_saturation_properties(self.pressure)

        # Calculate outlet quality if not provided
        if outlet_quality is None:
            # Energy balance: q'' * A = m_dot * (h_out - h_in)
            # h_out - h_in = x_out * h_fg - x_in * h_fg = (x_out - x_in) * h_fg
            area = np.pi * (self.diameter / 2) ** 2  # m²
            m_dot = self.mass_flux * area  # kg/s
            delta_h = (heat_flux * np.pi * self.diameter * self.length) / m_dot  # J/kg
            outlet_quality = inlet_quality + delta_h / h_fg
            outlet_quality = np.clip(outlet_quality, 0.0, 1.0)

        # Calculate void fraction using drift-flux
        drift_flux = DriftFluxModel(model_type="chexal_lellouche")
        void_fraction = drift_flux.calculate_void_fraction(
            quality=(inlet_quality + outlet_quality) / 2.0,
            mass_flux=self.mass_flux,
            pressure=self.pressure,
            diameter=self.diameter,
        )

        # Calculate phase velocities
        j_l = self.mass_flux * (1.0 - outlet_quality) / rho_l  # m/s
        j_g = self.mass_flux * outlet_quality / rho_v  # m/s

        # Two-fluid velocities (accounting for void fraction)
        liquid_velocity = j_l / (1.0 - void_fraction) if void_fraction < 1.0 else 0.0
        vapor_velocity = j_g / void_fraction if void_fraction > 0.0 else 0.0

        # Calculate pressure drop
        pressure_drop = self._calculate_pressure_drop(
            void_fraction, liquid_velocity, vapor_velocity, rho_l, rho_v
        )

        # Temperature (assumed saturated)
        T_sat = self._get_saturation_temperature(self.pressure)

        # Calculate interfacial transfer using advanced models
        interfacial = InterfacialTransferModels(
            pressure=self.pressure,
            temperature_liquid=T_sat,
            temperature_vapor=T_sat,
            void_fraction=void_fraction,
            liquid_velocity=liquid_velocity,
            vapor_velocity=vapor_velocity,
            diameter=self.diameter,
            model_type="ishii_hibiki",
        )

        # Calculate interfacial transfer rates
        mass_transfer = interfacial.calculate_mass_transfer_rate(
            heat_flux_interface=heat_flux
            / 10.0,  # Assume 10% of wall heat flux at interface
            superheat=0.0,  # Saturated conditions
        )

        momentum_transfer = interfacial.calculate_momentum_transfer()

        energy_transfer = interfacial.calculate_energy_transfer(
            heat_flux_interface=heat_flux / 10.0,
        )

        return {
            "void_fraction": void_fraction,
            "pressure_drop": pressure_drop,
            "liquid_velocity": liquid_velocity,
            "vapor_velocity": vapor_velocity,
            "temperature": T_sat,
            "outlet_quality": outlet_quality,
            # Interfacial transfer results
            "mass_transfer_rate": mass_transfer["mass_transfer_rate"],
            "evaporation_rate": mass_transfer["evaporation_rate"],
            "condensation_rate": mass_transfer["condensation_rate"],
            "interfacial_area": mass_transfer["interfacial_area"],
            "drag_force": momentum_transfer["drag_force"],
            "drag_coefficient": momentum_transfer["drag_coefficient"],
            "virtual_mass_force": momentum_transfer["virtual_mass_force"],
            "turbulent_dispersion_force": momentum_transfer[
                "turbulent_dispersion_force"
            ],
            "interfacial_heat_transfer_rate": energy_transfer["heat_transfer_rate"],
            "interfacial_htc": energy_transfer["interfacial_htc"],
            "latent_heat_transfer": energy_transfer["latent_heat_transfer"],
        }

    def _calculate_pressure_drop(
        self,
        void_fraction: float,
        liquid_velocity: float,
        vapor_velocity: float,
        rho_l: float,
        rho_v: float,
    ) -> float:
        """
        Calculate two-phase pressure drop.

        Includes:
        - Frictional pressure drop
        - Gravitational pressure drop
        - Accelerational pressure drop
        """
        # Frictional pressure drop (simplified)
        f_l = 0.02  # Friction factor (simplified)
        f_v = 0.02

        # Two-phase multiplier (Lockhart-Martinelli)
        X = np.sqrt((1.0 - void_fraction) / void_fraction * rho_v / rho_l)
        phi_l_sq = 1.0 + 20.0 / X + 1.0 / (X**2)  # Simplified

        dp_friction = (
            phi_l_sq
            * f_l
            * (1.0 - void_fraction)
            * rho_l
            * liquid_velocity**2
            * self.length
            / (2.0 * self.diameter)
        )

        # Gravitational pressure drop
        rho_mixture = void_fraction * rho_v + (1.0 - void_fraction) * rho_l
        g = 9.81  # m/s²
        dp_gravity = rho_mixture * g * self.length

        # Accelerational pressure drop (simplified)
        dp_accel = 0.0  # Usually small

        total_dp = dp_friction + dp_gravity + dp_accel

        return total_dp

    def _get_saturation_properties(self, pressure: float) -> Tuple[float, float, float]:
        """Get saturation properties (same as DriftFluxModel)."""
        if abs(pressure - 7e6) < 1e5:
            rho_l = 740.0
            rho_v = 36.5
            h_fg = 1.5e6
        else:
            p_ref = 7e6
            rho_l = 740.0 * (pressure / p_ref) ** 0.1
            rho_v = 36.5 * (pressure / p_ref) ** 0.5
            h_fg = 1.5e6 * (p_ref / pressure) ** 0.2

        return rho_l, rho_v, h_fg

    def _get_saturation_temperature(self, pressure: float) -> float:
        """Get saturation temperature at pressure."""
        # Simplified: T_sat ≈ 273.15 + 180 * (P/1e6)^0.25
        T_sat = 273.15 + 180.0 * (pressure / 1e6) ** 0.25
        return T_sat


@dataclass
class InterfacialTransferModels:
    """
    Advanced interfacial transfer models for two-fluid two-phase flow.

    Provides detailed models for:
    - Mass transfer (evaporation/condensation at interface)
    - Momentum transfer (interfacial drag forces)
    - Energy transfer (interfacial heat transfer)

    These models are essential for accurate two-fluid modeling where separate
    conservation equations are solved for liquid and vapor phases.

    Attributes:
        pressure: Pressure [Pa]
        temperature_liquid: Liquid temperature [K]
        temperature_vapor: Vapor temperature [K]
        void_fraction: Void fraction (0-1)
        liquid_velocity: Liquid velocity [m/s]
        vapor_velocity: Vapor velocity [m/s]
        diameter: Channel diameter [m]
        model_type: Interfacial transfer model type
            - 'ishii_hibiki': Ishii-Hibiki (2006) comprehensive model
            - 'relap5': RELAP5-style models
            - 'trap': TRACE-style models
    """

    pressure: float  # Pa
    temperature_liquid: float  # K
    temperature_vapor: float  # K
    void_fraction: float  # 0-1
    liquid_velocity: float  # m/s
    vapor_velocity: float  # m/s
    diameter: float  # m
    model_type: str = "ishii_hibiki"  # 'ishii_hibiki', 'relap5', 'trap'

    def calculate_mass_transfer_rate(
        self,
        heat_flux_interface: Optional[float] = None,
        superheat: Optional[float] = None,
    ) -> Dict[str, float]:
        """
        Calculate interfacial mass transfer rate (evaporation/condensation).

        Mass transfer occurs due to:
        - Wall heat flux (evaporation)
        - Temperature difference between phases (condensation/evaporation)
        - Pressure changes

        Args:
            heat_flux_interface: Interfacial heat flux [W/m²] (if None, calculated)
            superheat: Liquid superheat [K] (if None, calculated from temperatures)

        Returns:
            Dictionary with:
                - mass_transfer_rate: Mass transfer rate [kg/(m²·s)] (positive = evaporation)
                - evaporation_rate: Evaporation rate [kg/(m²·s)]
                - condensation_rate: Condensation rate [kg/(m²·s)]
                - interfacial_area: Interfacial area per unit volume [m²/m³]
        """
        # Get saturation properties
        rho_l, rho_v, h_fg = self._get_saturation_properties(self.pressure)
        T_sat = self._get_saturation_temperature(self.pressure)

        # Calculate superheat if not provided
        if superheat is None:
            superheat = max(0.0, self.temperature_liquid - T_sat)

        # Calculate interfacial area density (area per unit volume)
        # Simplified: a_i = 6 * void_fraction * (1 - void_fraction) / d_bubble
        # For bubbly flow, use bubble diameter estimate
        d_bubble = 0.001  # m (1 mm typical bubble size, simplified)
        if self.void_fraction < 0.3:
            # Bubbly flow
            interfacial_area = (
                6.0 * self.void_fraction * (1.0 - self.void_fraction) / d_bubble
            )
        elif self.void_fraction < 0.7:
            # Slug/churn flow
            interfacial_area = (
                4.0 * self.void_fraction * (1.0 - self.void_fraction) / self.diameter
            )
        else:
            # Annular flow
            interfacial_area = 4.0 * (1.0 - self.void_fraction) / self.diameter

        # Mass transfer due to wall heat flux (if provided)
        if heat_flux_interface is not None:
            # Evaporation from wall: m_dot = q'' / h_fg
            evaporation_from_wall = heat_flux_interface / h_fg  # kg/(m²·s)
        else:
            evaporation_from_wall = 0.0

        # Mass transfer due to temperature difference (interfacial)
        # Ishii-Hibiki model: m_dot = h_i * (T_l - T_sat) / h_fg
        # where h_i is interfacial heat transfer coefficient
        h_i = self._calculate_interfacial_heat_transfer_coefficient()

        # Evaporation due to superheat
        evaporation_from_superheat = h_i * superheat / h_fg  # kg/(m²·s)

        # Condensation (if vapor is subcooled)
        subcool = max(0.0, T_sat - self.temperature_vapor)
        condensation_rate = h_i * subcool / h_fg  # kg/(m²·s)

        # Net mass transfer rate (positive = evaporation)
        total_evaporation = evaporation_from_wall + evaporation_from_superheat
        net_mass_transfer = total_evaporation - condensation_rate

        return {
            "mass_transfer_rate": net_mass_transfer,  # kg/(m²·s)
            "evaporation_rate": total_evaporation,  # kg/(m²·s)
            "condensation_rate": condensation_rate,  # kg/(m²·s)
            "interfacial_area": interfacial_area,  # m²/m³
        }

    def calculate_momentum_transfer(
        self,
        relative_velocity: Optional[float] = None,
    ) -> Dict[str, float]:
        """
        Calculate interfacial momentum transfer (drag forces).

        Momentum transfer occurs due to:
        - Interfacial drag (friction between phases)
        - Virtual mass effects
        - Turbulent dispersion

        Args:
            relative_velocity: Relative velocity between phases [m/s] (if None, calculated)

        Returns:
            Dictionary with:
                - drag_force: Interfacial drag force per unit volume [N/m³]
                - drag_coefficient: Interfacial drag coefficient
                - virtual_mass_force: Virtual mass force per unit volume [N/m³]
                - turbulent_dispersion_force: Turbulent dispersion force [N/m³]
        """
        # Calculate relative velocity if not provided
        if relative_velocity is None:
            relative_velocity = abs(self.vapor_velocity - self.liquid_velocity)

        # Get saturation properties
        rho_l, rho_v, _ = self._get_saturation_properties(self.pressure)

        # Calculate interfacial drag coefficient based on flow regime
        C_d = self._calculate_interfacial_drag_coefficient(relative_velocity)

        # Interfacial area density
        interfacial_area = self._calculate_interfacial_area_density()

        # Interfacial drag force (per unit volume)
        # F_drag = 0.5 * C_d * rho_mixture * |v_g - v_l|^2 * a_i
        rho_mixture = self.void_fraction * rho_v + (1.0 - self.void_fraction) * rho_l
        drag_force = (
            0.5 * C_d * rho_mixture * relative_velocity**2 * interfacial_area
        )  # N/m³

        # Virtual mass force (acceleration effects)
        # F_vm = C_vm * rho_l * alpha * (1 - alpha) * (dv_g/dt - dv_l/dt)
        # Simplified: assume acceleration is proportional to velocity difference
        C_vm = 0.5  # Virtual mass coefficient (typical value)
        virtual_mass_force = (
            C_vm
            * rho_l
            * self.void_fraction
            * (1.0 - self.void_fraction)
            * relative_velocity
            * 0.1
        )  # N/m³ (simplified)

        # Turbulent dispersion force (mixing effects)
        # F_td = C_td * rho_l * k * grad(alpha)
        # Simplified: use velocity difference as proxy
        C_td = 0.1  # Turbulent dispersion coefficient
        turbulent_dispersion_force = (
            C_td * rho_l * relative_velocity * 0.05
        )  # N/m³ (simplified)

        return {
            "drag_force": drag_force,  # N/m³
            "drag_coefficient": C_d,
            "virtual_mass_force": virtual_mass_force,  # N/m³
            "turbulent_dispersion_force": turbulent_dispersion_force,  # N/m³
        }

    def calculate_energy_transfer(
        self,
        heat_flux_interface: Optional[float] = None,
    ) -> Dict[str, float]:
        """
        Calculate interfacial energy transfer (heat transfer at interface).

        Energy transfer occurs due to:
        - Temperature difference between phases
        - Latent heat of phase change
        - Interfacial heat transfer coefficient

        Args:
            heat_flux_interface: Interfacial heat flux [W/m²] (if None, calculated)

        Returns:
            Dictionary with:
                - heat_transfer_rate: Interfacial heat transfer rate per unit volume [W/m³]
                - interfacial_htc: Interfacial heat transfer coefficient [W/(m²·K)]
                - latent_heat_transfer: Latent heat transfer rate [W/m³]
        """
        # Get saturation properties
        rho_l, rho_v, h_fg = self._get_saturation_properties(self.pressure)
        T_sat = self._get_saturation_temperature(self.pressure)

        # Calculate interfacial heat transfer coefficient
        h_i = self._calculate_interfacial_heat_transfer_coefficient()

        # Temperature difference
        delta_T = self.temperature_liquid - self.temperature_vapor

        # Interfacial area density
        interfacial_area = self._calculate_interfacial_area_density()

        # Sensible heat transfer (convection between phases)
        sensible_heat_transfer = h_i * delta_T * interfacial_area  # W/m³

        # Latent heat transfer (from mass transfer)
        mass_transfer = self.calculate_mass_transfer_rate()
        latent_heat_transfer = (
            mass_transfer["mass_transfer_rate"] * h_fg * interfacial_area
        )  # W/m³

        # Total heat transfer
        if heat_flux_interface is not None:
            total_heat_transfer = heat_flux_interface * interfacial_area  # W/m³
        else:
            total_heat_transfer = sensible_heat_transfer + latent_heat_transfer

        return {
            "heat_transfer_rate": total_heat_transfer,  # W/m³
            "interfacial_htc": h_i,  # W/(m²·K)
            "latent_heat_transfer": latent_heat_transfer,  # W/m³
            "sensible_heat_transfer": sensible_heat_transfer,  # W/m³
        }

    def _calculate_interfacial_drag_coefficient(
        self,
        relative_velocity: float,
    ) -> float:
        """
        Calculate interfacial drag coefficient based on flow regime.

        Uses Ishii-Hibiki (2006) correlations for different flow regimes.
        """
        # Get saturation properties
        rho_l, rho_v, _ = self._get_saturation_properties(self.pressure)

        # Reynolds number based on relative velocity
        mu_l = 1e-4  # Pa·s (liquid viscosity, simplified)
        Re = rho_l * relative_velocity * self.diameter / mu_l

        if self.model_type == "ishii_hibiki":
            # Ishii-Hibiki model
            if self.void_fraction < 0.3:
                # Bubbly flow
                C_d = 24.0 / Re * (1.0 + 0.1 * Re**0.75)  # Drag coefficient
            elif self.void_fraction < 0.7:
                # Slug/churn flow
                C_d = 0.5  # Simplified
            else:
                # Annular flow
                C_d = 0.01 * (1.0 - self.void_fraction) ** 2  # Wall friction dominated
        elif self.model_type == "relap5":
            # RELAP5-style model
            C_d = 0.44 * (1.0 + 0.1 * self.void_fraction)  # Simplified
        else:  # trap
            # TRACE-style model
            C_d = 0.3 * (1.0 - self.void_fraction) ** 0.5  # Simplified

        return max(0.01, min(1.0, C_d))  # Clamp to reasonable range

    def _calculate_interfacial_heat_transfer_coefficient(self) -> float:
        """
        Calculate interfacial heat transfer coefficient.

        Based on flow regime and phase properties.
        """
        # Get saturation properties
        rho_l, rho_v, _ = self._get_saturation_properties(self.pressure)

        # Thermal conductivity (simplified)
        k_l = 0.6  # W/(m·K) (liquid thermal conductivity)
        k_v = 0.03  # W/(m·K) (vapor thermal conductivity)

        # Relative velocity
        relative_velocity = abs(self.vapor_velocity - self.liquid_velocity)

        # Reynolds number
        mu_l = 1e-4  # Pa·s
        Re = rho_l * relative_velocity * self.diameter / mu_l

        # Prandtl number (simplified)
        Pr_l = 1.0  # Liquid Prandtl number

        # Nusselt number (Dittus-Boelter type)
        Nu = 0.023 * Re**0.8 * Pr_l**0.4

        # Heat transfer coefficient
        h_i = Nu * k_l / self.diameter  # W/(m²·K)

        # Flow regime corrections
        if self.void_fraction > 0.7:
            # Annular flow: higher heat transfer
            h_i *= 1.5
        elif self.void_fraction < 0.3:
            # Bubbly flow: lower heat transfer
            h_i *= 0.8

        return max(100.0, min(100000.0, h_i))  # Clamp to reasonable range

    def _calculate_interfacial_area_density(self) -> float:
        """Calculate interfacial area per unit volume [m²/m³]."""
        d_bubble = 0.001  # m (typical bubble size)

        if self.void_fraction < 0.3:
            # Bubbly flow
            return 6.0 * self.void_fraction * (1.0 - self.void_fraction) / d_bubble
        elif self.void_fraction < 0.7:
            # Slug/churn flow
            return 4.0 * self.void_fraction * (1.0 - self.void_fraction) / self.diameter
        else:
            # Annular flow
            return 4.0 * (1.0 - self.void_fraction) / self.diameter

    def _get_saturation_properties(self, pressure: float) -> Tuple[float, float, float]:
        """Get saturation properties (same as DriftFluxModel)."""
        if abs(pressure - 7e6) < 1e5:
            rho_l = 740.0
            rho_v = 36.5
            h_fg = 1.5e6
        else:
            p_ref = 7e6
            rho_l = 740.0 * (pressure / p_ref) ** 0.1
            rho_v = 36.5 * (pressure / p_ref) ** 0.5
            h_fg = 1.5e6 * (p_ref / pressure) ** 0.2

        return rho_l, rho_v, h_fg

    def _get_saturation_temperature(self, pressure: float) -> float:
        """Get saturation temperature at pressure."""
        T_sat = 273.15 + 180.0 * (pressure / 1e6) ** 0.25
        return T_sat


@dataclass
class BoilingHeatTransfer:
    """
    Enhanced boiling heat transfer correlations.

    Provides correlations for:
    - Nucleate boiling (Chen, Forster-Zuber)
    - Film boiling (Bromley)
    - Transition boiling
    - Critical heat flux (CHF) predictions

    Attributes:
        pressure: Pressure [Pa]
        mass_flux: Mass flux [kg/(m²·s)]
        quality: Steam mass fraction (0-1)
        diameter: Channel diameter [m]
    """

    pressure: float  # Pa
    mass_flux: float  # kg/(m²·s)
    quality: float  # 0-1
    diameter: float  # m

    def calculate_heat_transfer_coefficient(
        self,
        heat_flux: float,  # W/m²
        wall_temperature: float,  # K
        bulk_temperature: float,  # K
        correlation: str = "chen",  # 'chen', 'forster_zuber', 'gorenflo'
    ) -> float:
        """
        Calculate boiling heat transfer coefficient.

        Args:
            heat_flux: Wall heat flux [W/m²]
            wall_temperature: Wall temperature [K]
            bulk_temperature: Bulk fluid temperature [K]
            correlation: Heat transfer correlation name

        Returns:
            Heat transfer coefficient [W/(m²·K)]
        """
        delta_T = wall_temperature - bulk_temperature

        if delta_T <= 0:
            return 1000.0  # Default single-phase

        if correlation == "chen":
            return self._chen_correlation(heat_flux, delta_T)
        elif correlation == "forster_zuber":
            return self._forster_zuber_correlation(heat_flux, delta_T)
        elif correlation == "gorenflo":
            return self._gorenflo_correlation(heat_flux, delta_T)
        else:
            return self._chen_correlation(heat_flux, delta_T)

    def _chen_correlation(self, heat_flux: float, delta_T: float) -> float:
        """
        Chen correlation for nucleate boiling.

        Combines nucleate boiling and convective contributions.
        """
        # Get saturation properties
        rho_l, rho_v, h_fg = self._get_saturation_properties(self.pressure)
        T_sat = self._get_saturation_temperature(self.pressure)

        # Nucleate boiling component
        # Simplified Chen correlation
        S = 1.0 / (1.0 + 2.53e-6 * (self.mass_flux**1.17))  # Suppression factor
        h_nb = (
            0.00122
            * (
                (0.023**0.79)
                * (4.18**0.45)
                * (740.0**0.49)
                / ((0.0589**0.5) * (1.5e6**0.24) * (0.0003**0.29))
                * (delta_T**0.24)
                * ((self.pressure / 1e6) ** 0.75)
            )
            * S
        )

        # Convective component (Dittus-Boelter for liquid)
        Pr_l = 1.0  # Prandtl number (simplified)
        Re_l = (
            self.mass_flux * self.diameter / 0.0003
        )  # Reynolds (simplified viscosity)
        Nu_l = 0.023 * (Re_l**0.8) * (Pr_l**0.4)
        k_l = 0.6  # W/(m·K) liquid thermal conductivity
        h_conv = Nu_l * k_l / self.diameter

        # Two-phase multiplier
        X = np.sqrt((1.0 - self.quality) / self.quality * rho_v / rho_l)
        F = 1.0 + 0.5 / X  # Simplified

        h_total = h_nb + F * h_conv

        return h_total

    def _forster_zuber_correlation(self, heat_flux: float, delta_T: float) -> float:
        """
        Forster-Zuber correlation for nucleate boiling.
        """
        # Simplified Forster-Zuber
        rho_l, rho_v, h_fg = self._get_saturation_properties(self.pressure)

        h_nb = 0.00122 * (
            (0.023**0.79)
            * (4.18**0.45)
            * (rho_l**0.49)
            / ((0.0589**0.5) * (h_fg**0.24) * (0.0003**0.29))
            * (delta_T**0.24)
            * ((self.pressure / 1e6) ** 0.75)
        )

        return h_nb

    def _gorenflo_correlation(self, heat_flux: float, delta_T: float) -> float:
        """
        Gorenflo correlation (pressure-dependent).
        """
        # Simplified Gorenflo
        p_critical = 22.1e6  # Critical pressure for water [Pa]
        p_reduced = self.pressure / p_critical

        h_ref = 5600.0  # Reference HTC [W/(m²·K)] at 0.1 MPa
        q_ref = 20000.0  # Reference heat flux [W/m²]

        h_nb = h_ref * ((heat_flux / q_ref) ** 0.9) * ((0.1 / p_reduced) ** 0.27)

        return h_nb

    def calculate_critical_heat_flux(
        self,
        correlation: str = "bowring",  # 'bowring', 'biasi', 'groeneveld'
    ) -> float:
        """
        Calculate Critical Heat Flux (CHF).

        CHF is the maximum heat flux before film boiling occurs.

        Args:
            correlation: CHF correlation name

        Returns:
            Critical heat flux [W/m²]
        """
        if correlation == "bowring":
            return self._bowring_chf()
        elif correlation == "biasi":
            return self._biasi_chf()
        elif correlation == "groeneveld":
            return self._groeneveld_chf()
        else:
            return self._bowring_chf()

    def _bowring_chf(self) -> float:
        """Bowring correlation for CHF."""
        # Simplified Bowring correlation
        p_mpa = self.pressure / 1e6  # MPa

        # Parameters
        A = 0.532
        B = 0.1212 * (p_mpa - 1.0) * (1.0 - self.quality)
        C = 0.0022 * self.diameter * 100  # Convert m to cm

        CHF = (A - B) / (C + 0.5 * self.quality) * 1e6  # W/m²

        return max(CHF, 1e6)  # Minimum 1 MW/m²

    def _biasi_chf(self) -> float:
        """Biasi correlation for CHF."""
        # Simplified Biasi correlation
        p_mpa = self.pressure / 1e6

        CHF = (
            1.883e7
            * (p_mpa**0.4)
            * (1.0 - self.quality) ** 0.6
            * (self.mass_flux / 1000.0) ** 0.4
        )

        return CHF

    def _groeneveld_chf(self) -> float:
        """Groeneveld correlation for CHF."""
        # Simplified Groeneveld (lookup table method)
        # Use Bowring as approximation
        return self._bowring_chf()

    def _get_saturation_properties(self, pressure: float) -> Tuple[float, float, float]:
        """Get saturation properties."""
        if abs(pressure - 7e6) < 1e5:
            rho_l = 740.0
            rho_v = 36.5
            h_fg = 1.5e6
        else:
            p_ref = 7e6
            rho_l = 740.0 * (pressure / p_ref) ** 0.1
            rho_v = 36.5 * (pressure / p_ref) ** 0.5
            h_fg = 1.5e6 * (p_ref / pressure) ** 0.2

        return rho_l, rho_v, h_fg

    def _get_saturation_temperature(self, pressure: float) -> float:
        """Get saturation temperature."""
        T_sat = 273.15 + 180.0 * (pressure / 1e6) ** 0.25
        return T_sat


@dataclass
class TwoPhaseThermalHydraulics:
    """
    Integrated two-phase flow thermal-hydraulics solver.

    Combines drift-flux, two-fluid, and boiling heat transfer models
    for comprehensive two-phase flow analysis.

    Attributes:
        pressure: Pressure [Pa]
        mass_flux: Mass flux [kg/(m²·s)]
        diameter: Channel diameter [m]
        length: Channel length [m]
        heat_flux: Wall heat flux [W/m²]
    """

    pressure: float  # Pa
    mass_flux: float  # kg/(m²·s)
    diameter: float  # m
    length: float  # m
    heat_flux: float  # W/m²

    def solve(
        self,
        inlet_temperature: float,  # K
        inlet_quality: float = 0.0,
        model_type: str = "drift_flux",  # 'drift_flux', 'two_fluid'
    ) -> Dict:
        """
        Solve two-phase thermal-hydraulics problem.

        Args:
            inlet_temperature: Inlet temperature [K]
            inlet_quality: Inlet quality (0-1)
            model_type: Model type ('drift_flux' or 'two_fluid')

        Returns:
            Dictionary with solution:
                - void_fraction: Void fraction
                - outlet_quality: Outlet quality
                - pressure_drop: Pressure drop [Pa]
                - heat_transfer_coefficient: HTC [W/(m²·K)]
                - critical_heat_flux: CHF [W/m²]
                - flow_regime: Flow regime
        """
        # Calculate outlet quality from energy balance
        rho_l, rho_v, h_fg = self._get_saturation_properties(self.pressure)
        area = np.pi * (self.diameter / 2) ** 2  # m²
        m_dot = self.mass_flux * area  # kg/s

        delta_h = (self.heat_flux * np.pi * self.diameter * self.length) / m_dot
        outlet_quality = inlet_quality + delta_h / h_fg
        outlet_quality = np.clip(outlet_quality, 0.0, 1.0)

        avg_quality = (inlet_quality + outlet_quality) / 2.0

        # Calculate void fraction
        if model_type == "two_fluid":
            two_fluid = TwoFluidModel(
                pressure=self.pressure,
                temperature=self._get_saturation_temperature(self.pressure),
                mass_flux=self.mass_flux,
                quality=avg_quality,
                diameter=self.diameter,
                length=self.length,
            )
            result = two_fluid.solve_two_fluid(
                heat_flux=self.heat_flux, inlet_quality=inlet_quality
            )
            void_fraction = result["void_fraction"]
            pressure_drop = result["pressure_drop"]
        else:
            # Drift-flux model
            drift_flux = DriftFluxModel(model_type="chexal_lellouche")
            void_fraction = drift_flux.calculate_void_fraction(
                quality=avg_quality,
                mass_flux=self.mass_flux,
                pressure=self.pressure,
                diameter=self.diameter,
            )

            # Simplified pressure drop
            pressure_drop = self._calculate_simple_pressure_drop(
                void_fraction, avg_quality, rho_l, rho_v
            )

        # Calculate heat transfer coefficient
        T_sat = self._get_saturation_temperature(self.pressure)
        boiling = BoilingHeatTransfer(
            pressure=self.pressure,
            mass_flux=self.mass_flux,
            quality=avg_quality,
            diameter=self.diameter,
        )
        htc = boiling.calculate_heat_transfer_coefficient(
            heat_flux=self.heat_flux,
            wall_temperature=T_sat + 10.0,  # Assume 10K superheat
            bulk_temperature=T_sat,
        )

        # Calculate CHF
        chf = boiling.calculate_critical_heat_flux()

        # Determine flow regime
        flow_regime = self._determine_flow_regime(void_fraction, avg_quality)

        return {
            "void_fraction": void_fraction,
            "outlet_quality": outlet_quality,
            "pressure_drop": pressure_drop,
            "heat_transfer_coefficient": htc,
            "critical_heat_flux": chf,
            "flow_regime": flow_regime,
            "chf_margin": (chf - self.heat_flux) / chf if chf > 0 else 0.0,
        }

    def _calculate_simple_pressure_drop(
        self, void_fraction: float, quality: float, rho_l: float, rho_v: float
    ) -> float:
        """Calculate simplified pressure drop."""
        # Two-phase multiplier
        X = np.sqrt((1.0 - quality) / quality * rho_v / rho_l)
        phi_l_sq = 1.0 + 20.0 / X + 1.0 / (X**2)

        # Friction factor
        f = 0.02

        # Mixture density
        rho_mix = void_fraction * rho_v + (1.0 - void_fraction) * rho_l

        # Velocity
        velocity = self.mass_flux / rho_mix

        # Pressure drop
        dp = phi_l_sq * f * rho_mix * velocity**2 * self.length / (2.0 * self.diameter)

        # Add gravity
        g = 9.81
        dp += rho_mix * g * self.length

        return dp

    def _determine_flow_regime(self, void_fraction: float, quality: float) -> str:
        """Determine flow regime from void fraction and quality."""
        if void_fraction < 0.1:
            return "bubbly"
        elif void_fraction < 0.3:
            return "slug"
        elif void_fraction < 0.7:
            return "churn"
        elif void_fraction < 0.9:
            return "annular"
        else:
            return "mist"

    def _get_saturation_properties(self, pressure: float) -> Tuple[float, float, float]:
        """Get saturation properties."""
        if abs(pressure - 7e6) < 1e5:
            rho_l = 740.0
            rho_v = 36.5
            h_fg = 1.5e6
        else:
            p_ref = 7e6
            rho_l = 740.0 * (pressure / p_ref) ** 0.1
            rho_v = 36.5 * (pressure / p_ref) ** 0.5
            h_fg = 1.5e6 * (p_ref / pressure) ** 0.2

        return rho_l, rho_v, h_fg

    def _get_saturation_temperature(self, pressure: float) -> float:
        """Get saturation temperature."""
        T_sat = 273.15 + 180.0 * (pressure / 1e6) ** 0.25
        return T_sat
