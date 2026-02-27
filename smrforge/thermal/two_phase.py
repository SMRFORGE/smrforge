"""
Two-phase flow models for BWR SMR and integral LWR applications.

Implements Drift-Flux model for void fraction and slip ratio.
Needed for BWR SMR, NuScale-style integral design with steam.
"""

from dataclasses import dataclass
from typing import Optional

import numpy as np

from ..utils.logging import get_logger

logger = get_logger("smrforge.thermal.two_phase")


@dataclass
class TwoPhaseState:
    """State variables for two-phase flow."""

    pressure: float  # Pa
    quality: float  # mass fraction vapor (0=saturated liquid, 1=saturated vapor)
    mass_flux: float  # kg/m²-s
    void_fraction: float  # volume fraction vapor (alpha)
    liquid_density: float  # kg/m³
    vapor_density: float  # kg/m³
    slip_ratio: float  # vapor velocity / liquid velocity


def steam_saturation_temperature(pressure_pa: float) -> float:
    """Saturation temperature [K] for water at pressure [Pa]. IAPWS approximation."""
    p_mpa = pressure_pa / 1e6
    if p_mpa < 0.01 or p_mpa > 22:
        logger.warning(f"Pressure {p_mpa} MPa outside IAPWS range")
    # Simplified Wagner–Pruss: T_sat ≈ 647.096 * (p/22.064)^0.25 for rough estimate
    return 273.15 + 100 * (p_mpa / 0.101325) ** 0.25  # K, approximate


def zuber_findlay_void_fraction(
    quality: float,
    mass_flux: float,
    liquid_density: float,
    vapor_density: float,
    drift_flux_coeff: float = 1.13,
    distribution_coeff: float = 1.0,
) -> float:
    """
    Zuber-Findlay drift-flux void fraction: alpha = j_g / (C0*j + Vgj).

    Args:
        quality: vapor mass fraction
        mass_flux: G [kg/m²-s]
        liquid_density: rho_f [kg/m³]
        vapor_density: rho_g [kg/m³]
        drift_flux_coeff: C0 (distribution parameter)
        distribution_coeff: Vgj coefficient

    Returns:
        void_fraction: alpha [0, 1]
    """
    if quality <= 0:
        return 0.0
    if quality >= 1:
        return 1.0

    j_f = mass_flux * (1 - quality) / liquid_density
    j_g = mass_flux * quality / vapor_density
    j = j_f + j_g
    vgj = 0.24  # m/s approximate for bubbly flow
    alpha = j_g / (distribution_coeff * j + drift_flux_coeff * vgj)
    return float(np.clip(alpha, 0.0, 1.0))


def homogeneous_void_fraction(quality: float, liquid_density: float, vapor_density: float) -> float:
    """Homogeneous model: alpha = 1 / (1 + (1-x)/x * rho_g/rho_f)."""
    if quality <= 0:
        return 0.0
    if quality >= 1:
        return 1.0
    r = (1 - quality) / quality * vapor_density / liquid_density
    return 1.0 / (1.0 + r)


class DriftFluxModel:
    """
    Drift-flux two-phase flow model for 1D channels.

    Used for BWR SMR subcooled boiling, bulk boiling, and annular flow.
    """

    def __init__(
        self,
        pressure: float,
        liquid_density: float = 800.0,
        vapor_density: float = 5.0,
        c0: float = 1.13,
        vgj: float = 0.24,
    ):
        self.pressure = pressure
        self.liquid_density = liquid_density
        self.vapor_density = vapor_density
        self.c0 = c0
        self.vgj = vgj

    def void_fraction(self, quality: float, mass_flux: float) -> float:
        """Compute void fraction from quality and mass flux."""
        return zuber_findlay_void_fraction(
            quality, mass_flux, self.liquid_density, self.vapor_density, self.c0, 1.0
        )

    def slip_ratio(self, quality: float, void_fraction: float) -> float:
        """Slip ratio S = u_g/u_f from quality and void fraction."""
        if void_fraction <= 0 or void_fraction >= 1:
            return 1.0
        if quality <= 0 or quality >= 1:
            return 1.0
        # S = (x/(1-x)) * ((1-alpha)/alpha) * (rho_f/rho_g)
        s = (quality / (1 - quality)) * ((1 - void_fraction) / void_fraction)
        s *= self.liquid_density / self.vapor_density
        return float(np.clip(s, 1.0, 10.0))

    def compute_state(self, quality: float, mass_flux: float) -> TwoPhaseState:
        """Full two-phase state from quality and mass flux."""
        alpha = self.void_fraction(quality, mass_flux)
        slip = self.slip_ratio(quality, alpha)
        return TwoPhaseState(
            pressure=self.pressure,
            quality=quality,
            mass_flux=mass_flux,
            void_fraction=alpha,
            liquid_density=self.liquid_density,
            vapor_density=self.vapor_density,
            slip_ratio=slip,
        )
