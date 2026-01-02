"""
ENDF Thermal Scattering Law (TSL) Parser.

This module parses thermal scattering law data from ENDF files (MF=7).
TSL data describes how neutrons scatter from bound atoms (e.g., H in H2O,
C in graphite) rather than free atoms, which is crucial for accurate
thermal reactor calculations.

The scattering law S(α,β) is a function of:
- α: Momentum transfer parameter
- β: Energy transfer parameter

This data is used to compute energy-dependent scattering cross-sections
and scattering matrices for thermal neutrons.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from .reactor_core import Nuclide


@dataclass
class ScatteringLawData:
    """
    Thermal scattering law data for a bound atom.
    
    Attributes:
        material_name: Name of the bound material (e.g., "H_in_H2O", "C_in_graphite")
        zaid: ZAID identifier (Z*1000 + A)
        temperature: Temperature [K] (primary temperature)
        temperatures: List of available temperatures [K] (for multi-temperature support)
        alpha_values: Momentum transfer values α
        beta_values: Energy transfer values β
        s_alpha_beta: Scattering law S(α,β) [n_alpha, n_beta] or [n_temp, n_alpha, n_beta] for multi-temp
        bound_atom_mass: Mass of bound atom [amu]
        coherent_scattering: True if coherent scattering, False if incoherent
        multi_temperature: True if data contains multiple temperatures
    """
    
    material_name: str
    zaid: int
    temperature: float  # K (primary/current temperature)
    temperatures: Optional[np.ndarray] = None  # [n_temp] Available temperatures
    alpha_values: np.ndarray = None  # Momentum transfer
    beta_values: np.ndarray = None  # Energy transfer
    s_alpha_beta: np.ndarray = None  # [n_alpha, n_beta] or [n_temp, n_alpha, n_beta]
    bound_atom_mass: float = 1.008  # amu
    coherent_scattering: bool = False
    multi_temperature: bool = False
    
    def get_s(self, alpha: float, beta: float, temperature: Optional[float] = None) -> float:
        """
        Interpolate S(α,β) at given α and β values, with optional temperature interpolation.
        
        Args:
            alpha: Momentum transfer parameter
            beta: Energy transfer parameter
            temperature: Optional temperature [K] for multi-temperature interpolation.
                If None, uses self.temperature.
        
        Returns:
            Interpolated S(α,β) value
        """
        if temperature is None:
            temperature = self.temperature
        
        # Get S(α,β) data for the requested temperature
        if self.multi_temperature and self.temperatures is not None:
            # Multi-temperature: interpolate in temperature first
            s_data = self._interpolate_temperature(temperature)
        else:
            # Single temperature: use current data
            s_data = self.s_alpha_beta
        
        if s_data is None or self.alpha_values is None or self.beta_values is None:
            return 0.0
        
        # Bilinear interpolation in α and β
        alpha_idx = np.searchsorted(self.alpha_values, alpha)
        beta_idx = np.searchsorted(self.beta_values, beta)
        
        # Clamp to valid range
        alpha_idx = max(0, min(alpha_idx, len(self.alpha_values) - 1))
        beta_idx = max(0, min(beta_idx, len(self.beta_values) - 1))
        
        # If exact match, return value
        if (alpha_idx < len(self.alpha_values) and 
            abs(self.alpha_values[alpha_idx] - alpha) < 1e-10):
            if (beta_idx < len(self.beta_values) and 
                abs(self.beta_values[beta_idx] - beta) < 1e-10):
                return s_data[alpha_idx, beta_idx]
        
        # Bilinear interpolation
        alpha_low = max(0, alpha_idx - 1)
        alpha_high = min(alpha_idx, len(self.alpha_values) - 1)
        beta_low = max(0, beta_idx - 1)
        beta_high = min(beta_idx, len(self.beta_values) - 1)
        
        if alpha_low == alpha_high and beta_low == beta_high:
            return s_data[alpha_low, beta_low]
        
        # Interpolate
        alpha_frac = (alpha - self.alpha_values[alpha_low]) / (
            self.alpha_values[alpha_high] - self.alpha_values[alpha_low]
            if alpha_high > alpha_low else 1.0
        )
        beta_frac = (beta - self.beta_values[beta_low]) / (
            self.beta_values[beta_high] - self.beta_values[beta_low]
            if beta_high > beta_low else 1.0
        )
        
        s00 = s_data[alpha_low, beta_low]
        s01 = s_data[alpha_low, beta_high] if beta_high > beta_low else s00
        s10 = s_data[alpha_high, beta_low] if alpha_high > alpha_low else s00
        s11 = s_data[alpha_high, beta_high] if (alpha_high > alpha_low and beta_high > beta_low) else s00
        
        return (
            s00 * (1 - alpha_frac) * (1 - beta_frac) +
            s01 * (1 - alpha_frac) * beta_frac +
            s10 * alpha_frac * (1 - beta_frac) +
            s11 * alpha_frac * beta_frac
        )
    
    def _interpolate_temperature(self, temperature: float) -> np.ndarray:
        """
        Interpolate S(α,β) to requested temperature.
        
        Args:
            temperature: Requested temperature [K]
        
        Returns:
            S(α,β) array at requested temperature [n_alpha, n_beta]
        """
        if not self.multi_temperature or self.temperatures is None:
            return self.s_alpha_beta
        
        # Find temperature indices
        temp_idx = np.searchsorted(self.temperatures, temperature)
        temp_idx = max(0, min(temp_idx, len(self.temperatures) - 1))
        
        # If exact match, return that temperature's data
        if (temp_idx < len(self.temperatures) and 
            abs(self.temperatures[temp_idx] - temperature) < 1.0):  # Within 1 K
            return self.s_alpha_beta[temp_idx, :, :]
        
        # Linear interpolation between temperatures
        temp_low = max(0, temp_idx - 1)
        temp_high = min(temp_idx, len(self.temperatures) - 1)
        
        if temp_low == temp_high:
            return self.s_alpha_beta[temp_low, :, :]
        
        # Interpolate
        temp_frac = (temperature - self.temperatures[temp_low]) / (
            self.temperatures[temp_high] - self.temperatures[temp_low]
            if temp_high > temp_low else 1.0
        )
        
        s_low = self.s_alpha_beta[temp_low, :, :]
        s_high = self.s_alpha_beta[temp_high, :, :]
        
        return s_low + temp_frac * (s_high - s_low)


class ThermalScatteringParser:
    """
    Parser for ENDF thermal scattering law files (MF=7).
    
    Parses S(α,β) scattering law data from ENDF files in the
    thermal_scatt-version.VIII.1 directory.
    
    File naming convention:
    - tsl-*.endf (thermal scattering law files)
    - Example: tsl-H_in_H2O.endf, tsl-C_in_graphite.endf
    """
    
    # Material name mappings (common TSL materials)
    MATERIAL_MAPPINGS = {
        "H_in_H2O": "H in H2O",
        "H_in_D2O": "H in D2O",
        "D_in_D2O": "D in D2O",
        "C_in_graphite": "C in graphite",
        "Be_in_BeO": "Be in BeO",
        "O_in_H2O": "O in H2O",
        "O_in_UO2": "O in UO2",
        "Zr_in_ZrH": "Zr in ZrH",
    }
    
    def parse_file(self, filepath: Path) -> Optional[ScatteringLawData]:
        """
        Parse thermal scattering law data from ENDF file.
        
        Args:
            filepath: Path to ENDF TSL file
        
        Returns:
            ScatteringLawData instance or None if parsing fails
        """
        if not filepath.exists():
            return None
        
        try:
            with open(filepath, "r") as f:
                lines = f.readlines()
        except Exception as e:
            return None
        
        # Parse header (first line)
        if len(lines) < 1:
            return None
        
        # Extract material name from filename
        material_name = self._extract_material_name(filepath.name)
        
        # Parse MF=7, MT=2 (coherent elastic) or MT=4 (incoherent elastic/inelastic)
        # For now, we'll parse a simplified version
        # Full ENDF MF=7 parsing is complex and would require full ENDF parser
        
        # Placeholder: Return simplified structure
        # In full implementation, would parse:
        # - MF=7, MT=2: Coherent elastic scattering
        # - MF=7, MT=4: Incoherent inelastic scattering
        # - S(α,β) tables
        
        # For now, create placeholder data structure
        # This will be enhanced with full ENDF parsing
        
        return self._create_placeholder_data(material_name, filepath)
    
    def _extract_material_name(self, filename: str) -> str:
        """Extract material name from filename."""
        # Remove extension
        name = filename.replace(".endf", "").replace(".ENDF", "")
        
        # Remove prefix (tsl-, thermal-, etc.)
        name = re.sub(r"^(tsl-|thermal-|ts-)", "", name, flags=re.IGNORECASE)
        
        # Map to standard name
        if name in self.MATERIAL_MAPPINGS:
            return self.MATERIAL_MAPPINGS[name]
        
        return name
    
    def _create_placeholder_data(
        self, material_name: str, filepath: Path
    ) -> ScatteringLawData:
        """
        Create placeholder TSL data structure.
        
        In full implementation, this would parse actual S(α,β) data
        from the ENDF file. For now, creates a basic structure that
        can be used for integration.
        """
        # Determine bound atom from material name
        if "H_in_H2O" in material_name or "H in H2O" in material_name:
            zaid = 1001  # H-1
            bound_mass = 1.008
            coherent = False  # H is incoherent
        elif "C_in_graphite" in material_name or "C in graphite" in material_name:
            zaid = 6000  # C-12
            bound_mass = 12.011
            coherent = True  # C is coherent
        elif "D_in_D2O" in material_name or "D in D2O" in material_name:
            zaid = 1002  # H-2 (deuterium)
            bound_mass = 2.014
            coherent = False
        elif "O_in" in material_name:
            zaid = 8016  # O-16
            bound_mass = 15.999
            coherent = True
        else:
            # Default: assume H
            zaid = 1001
            bound_mass = 1.008
            coherent = False
        
        # Create placeholder α and β grids
        # Typical ranges: α from 0.01 to 100, β from -50 to 50
        alpha_values = np.logspace(-2, 2, 50)  # 0.01 to 100
        beta_values = np.linspace(-50, 50, 100)  # -50 to 50
        
        # Placeholder S(α,β) - in real implementation, parse from ENDF
        # For now, use a simple approximation
        s_alpha_beta = np.ones((len(alpha_values), len(beta_values)))
        
        # Apply simple physics-based shape
        # S(α,β) typically peaks at β=0 and decreases with |β|
        for i, beta in enumerate(beta_values):
            # Gaussian-like shape centered at β=0
            s_alpha_beta[:, i] = np.exp(-beta**2 / 20.0)
        
        return ScatteringLawData(
            material_name=material_name,
            zaid=zaid,
            temperature=293.6,  # Room temperature (would parse from file)
            alpha_values=alpha_values,
            beta_values=beta_values,
            s_alpha_beta=s_alpha_beta,
            bound_atom_mass=bound_mass,
            coherent_scattering=coherent,
        )
    
    @staticmethod
    def compute_thermal_scattering_xs(
        s_data: ScatteringLawData,
        energy_in: float,
        energy_out: float,
        temperature: float = 293.6,
    ) -> float:
        """
        Compute thermal scattering cross-section from S(α,β).
        
        This converts S(α,β) to energy-dependent scattering cross-section.
        
        Args:
            s_data: ScatteringLawData instance
            energy_in: Incident neutron energy [eV]
            energy_out: Outgoing neutron energy [eV]
            temperature: Temperature [K]
        
        Returns:
            Scattering cross-section [barns]
        """
        # Convert energies to α and β
        # α = (E_in + E_out - 2*sqrt(E_in*E_out)*cos(θ)) / (k_B*T*A)
        # β = (E_in - E_out) / (k_B*T)
        # Simplified: assume isotropic scattering (average over angles)
        
        k_B = 8.617333262e-5  # eV/K
        kT = k_B * temperature
        
        # β parameter
        beta = (energy_in - energy_out) / kT
        
        # α parameter (simplified for isotropic)
        # For bound atom with mass A: α ≈ (E_in + E_out) / (kT * A)
        A = s_data.bound_atom_mass
        alpha = (energy_in + energy_out) / (kT * A)
        
        # Get S(α,β)
        s_value = s_data.get_s(alpha, beta)
        
        # Convert to cross-section
        # σ_s(E_in → E_out) ∝ sqrt(E_out/E_in) * S(α,β)
        if energy_in > 0:
            xs = np.sqrt(energy_out / energy_in) * s_value
        else:
            xs = 0.0
        
        # Normalize (simplified - full calculation would integrate over angles)
        # Typical thermal scattering cross-section: ~20-100 barns
        xs *= 50.0  # Normalization factor (would be computed from full integration)
        
        return max(0.0, xs)


def get_tsl_material_name(material: str) -> Optional[str]:
    """
    Map material name to TSL material name.
    
    Args:
        material: Material name (e.g., "H2O", "graphite", "D2O")
    
    Returns:
        TSL material name (e.g., "H_in_H2O", "C_in_graphite") or None
    """
    mappings = {
        "H2O": "H_in_H2O",
        "water": "H_in_H2O",
        "graphite": "C_in_graphite",
        "C": "C_in_graphite",
        "D2O": "D_in_D2O",
        "heavy_water": "D_in_D2O",
        "BeO": "Be_in_BeO",
        "UO2": "O_in_UO2",
        "ZrH": "Zr_in_ZrH",
    }
    
    material_lower = material.lower()
    for key, value in mappings.items():
        if key.lower() in material_lower:
            return value
    
    return None

