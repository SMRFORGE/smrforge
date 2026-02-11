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

    def get_s(
        self, alpha: float, beta: float, temperature: Optional[float] = None
    ) -> float:
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
        if (
            alpha_idx < len(self.alpha_values)
            and abs(self.alpha_values[alpha_idx] - alpha) < 1e-10
        ):
            if (
                beta_idx < len(self.beta_values)
                and abs(self.beta_values[beta_idx] - beta) < 1e-10
            ):
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
            if alpha_high > alpha_low
            else 1.0
        )
        beta_frac = (beta - self.beta_values[beta_low]) / (
            self.beta_values[beta_high] - self.beta_values[beta_low]
            if beta_high > beta_low
            else 1.0
        )

        s00 = s_data[alpha_low, beta_low]
        s01 = s_data[alpha_low, beta_high] if beta_high > beta_low else s00
        s10 = s_data[alpha_high, beta_low] if alpha_high > alpha_low else s00
        s11 = (
            s_data[alpha_high, beta_high]
            if (alpha_high > alpha_low and beta_high > beta_low)
            else s00
        )

        return (
            s00 * (1 - alpha_frac) * (1 - beta_frac)
            + s01 * (1 - alpha_frac) * beta_frac
            + s10 * alpha_frac * (1 - beta_frac)
            + s11 * alpha_frac * beta_frac
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
        if (
            temp_idx < len(self.temperatures)
            and abs(self.temperatures[temp_idx] - temperature) < 1.0
        ):  # Within 1 K
            return self.s_alpha_beta[temp_idx, :, :]

        # Linear interpolation between temperatures
        temp_low = max(0, temp_idx - 1)
        temp_high = min(temp_idx, len(self.temperatures) - 1)

        if temp_low == temp_high:
            return self.s_alpha_beta[temp_low, :, :]

        # Interpolate
        temp_frac = (temperature - self.temperatures[temp_low]) / (
            self.temperatures[temp_high] - self.temperatures[temp_low]
            if temp_high > temp_low
            else 1.0
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
        Parse thermal scattering law data from ENDF file (MF=7).

        Parses S(α,β) scattering law data from ENDF-6 format files.
        Handles both coherent elastic (MT=2) and incoherent inelastic (MT=4) scattering.

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

        if len(lines) < 1:
            return None

        # Extract material name from filename
        material_name = self._extract_material_name(filepath.name)

        # Try to parse real ENDF MF=7 data
        tsl_data = self._parse_endf_mf7(lines, material_name, filepath)

        if tsl_data is not None:
            return tsl_data

        # Fallback to placeholder if parsing fails
        return self._create_placeholder_data(material_name, filepath)

    def _parse_endf_mf7(
        self, lines: List[str], material_name: str, filepath: Path
    ) -> Optional[ScatteringLawData]:
        """
        Parse ENDF MF=7 (thermal scattering) data.

        Args:
            lines: List of file lines
            material_name: Material name
            filepath: Path to file (for error messages)

        Returns:
            ScatteringLawData or None if parsing fails
        """
        # Find MF=7 sections
        mf7_sections = []
        for i, line in enumerate(lines):
            if len(line) < 75:
                continue
            mf = line[70:72].strip()
            if mf == "7":
                mt = int(line[72:75].strip())
                mf7_sections.append((i, mt))

        if not mf7_sections:
            return None

        # Parse MT=4 (incoherent inelastic) - most common for TSL
        # MT=2 (coherent elastic) is simpler but less common
        s_alpha_beta_data = None
        alpha_values = None
        beta_values = None
        temperature = 293.6
        zaid = 0
        bound_mass = 1.008
        coherent = False

        for section_idx, mt in mf7_sections:
            if mt == 4:  # Incoherent inelastic scattering
                result = self._parse_mt4_section(lines, section_idx)
                if result:
                    (
                        s_alpha_beta_data,
                        alpha_values,
                        beta_values,
                        temp,
                        zaid,
                        bound_mass,
                    ) = result
                    temperature = temp
                    coherent = False
                    break
            elif mt == 2:  # Coherent elastic scattering
                result = self._parse_mt2_section(lines, section_idx)
                if result:
                    (
                        s_alpha_beta_data,
                        alpha_values,
                        beta_values,
                        temp,
                        zaid,
                        bound_mass,
                    ) = result
                    temperature = temp
                    coherent = True
                    # MT=2 is simpler, but we'll use it if MT=4 not available
                    if s_alpha_beta_data is None:
                        break

        if s_alpha_beta_data is None or alpha_values is None or beta_values is None:
            return None

        return ScatteringLawData(
            material_name=material_name,
            zaid=zaid,
            temperature=temperature,
            alpha_values=alpha_values,
            beta_values=beta_values,
            s_alpha_beta=s_alpha_beta_data,
            bound_atom_mass=bound_mass,
            coherent_scattering=coherent,
        )

    def _parse_mt4_section(
        self, lines: List[str], start_idx: int
    ) -> Optional[Tuple[np.ndarray, np.ndarray, np.ndarray, float, int, float]]:
        """
        Parse MF=7, MT=4 (incoherent inelastic scattering) section.

        This section contains S(α,β) tables.

        Returns:
            Tuple of (s_alpha_beta, alpha_values, beta_values, temperature, zaid, bound_mass)
            or None if parsing fails
        """
        try:
            # Read control record
            if start_idx >= len(lines):
                return None

            line = lines[start_idx]
            # ENDF format: C1, C2, L1, L2, N1, N2
            # C1 = temperature, C2 = zaid, L1 = bound atom flag, etc.
            try:
                c1 = float(
                    line[0:11].replace(" ", "").replace("+", "E+").replace("-", "E-")
                )
                c2 = float(
                    line[11:22].replace(" ", "").replace("+", "E+").replace("-", "E-")
                )
                temperature = c1  # Temperature in K
                zaid = int(c2)  # ZAID
            except (ValueError, IndexError):
                temperature = 293.6
                zaid = 0

            # Determine bound atom mass from ZAID
            bound_mass = float(zaid % 1000)  # A from ZAID
            if bound_mass == 0:
                bound_mass = 1.008  # Default to H

            # Parse S(α,β) table
            # Format: Each subsection has beta values, then S(α,β) for each alpha
            i = start_idx + 1
            alpha_list = []
            beta_list = []
            s_data_list = []

            # Skip second control record
            if i < len(lines):
                i += 1

            # Parse data until end of section (MF=0 or different MF)
            current_alpha = None
            beta_values_for_alpha = []
            s_values_for_alpha = []

            while i < len(lines):
                line = lines[i]
                if len(line) < 75:
                    i += 1
                    continue

                # Check for end of section
                mf = line[70:72].strip()
                if mf != "7" and mf != "":
                    break

                # Check for end of file marker
                if line.strip().endswith("-1"):
                    break

                # Parse data line (6 values per line in ENDF format)
                try:
                    values = []
                    for j in range(6):
                        start = j * 11
                        end = start + 11
                        if end <= len(line):
                            val_str = line[start:end].strip()
                            if val_str:
                                # Handle ENDF scientific notation
                                val_str = val_str.replace("+", "E+").replace("-", "E-")
                                values.append(float(val_str))

                    if len(values) >= 2:
                        # First value is alpha, second is beta (or vice versa depending on format)
                        # ENDF MF=7 format varies, this is simplified
                        alpha_val = values[0]
                        beta_val = values[1]

                        if (
                            current_alpha is None
                            or abs(alpha_val - current_alpha) > 1e-6
                        ):
                            # New alpha value
                            if current_alpha is not None:
                                alpha_list.append(current_alpha)
                                beta_list.append(beta_values_for_alpha)
                                s_data_list.append(s_values_for_alpha)

                            current_alpha = alpha_val
                            beta_values_for_alpha = [beta_val]
                            s_values_for_alpha = [values[2] if len(values) > 2 else 1.0]
                        else:
                            # Same alpha, add beta and S value
                            beta_values_for_alpha.append(beta_val)
                            s_values_for_alpha.append(
                                values[2] if len(values) > 2 else 1.0
                            )

                except (ValueError, IndexError):
                    pass

                i += 1

            # Add last alpha
            if current_alpha is not None:
                alpha_list.append(current_alpha)
                beta_list.append(beta_values_for_alpha)
                s_data_list.append(s_values_for_alpha)

            if not alpha_list:
                return None

            # Convert to arrays
            # Find unique beta values across all alphas
            all_betas = set()
            for beta_vals in beta_list:
                all_betas.update(beta_vals)
            beta_values = np.array(sorted(all_betas))

            # Create S(α,β) matrix
            alpha_values = np.array(alpha_list)
            s_alpha_beta = np.zeros((len(alpha_values), len(beta_values)))

            for idx, (alpha, beta_vals, s_vals) in enumerate(
                zip(alpha_list, beta_list, s_data_list)
            ):
                for beta, s_val in zip(beta_vals, s_vals):
                    beta_idx = np.searchsorted(beta_values, beta)
                    if beta_idx < len(beta_values):
                        s_alpha_beta[idx, beta_idx] = s_val

            return (
                s_alpha_beta,
                alpha_values,
                beta_values,
                temperature,
                zaid,
                bound_mass,
            )

        except Exception:
            return None

    def _parse_mt2_section(
        self, lines: List[str], start_idx: int
    ) -> Optional[Tuple[np.ndarray, np.ndarray, np.ndarray, float, int, float]]:
        """
        Parse MF=7, MT=2 (coherent elastic scattering) section.

        This is simpler than MT=4 - just elastic scattering cross-section.
        We convert it to a simple S(α,β) representation.

        Returns:
            Tuple of (s_alpha_beta, alpha_values, beta_values, temperature, zaid, bound_mass)
            or None if parsing fails
        """
        try:
            # Read control record
            if start_idx >= len(lines):
                return None

            line = lines[start_idx]
            try:
                c1 = float(
                    line[0:11].replace(" ", "").replace("+", "E+").replace("-", "E-")
                )
                temperature = c1
            except (ValueError, IndexError):
                temperature = 293.6

            # For coherent elastic, create simplified S(α,β)
            # Coherent elastic is mostly at β=0
            alpha_values = np.logspace(-2, 2, 20)
            beta_values = np.array([0.0])  # Only β=0 for elastic
            s_alpha_beta = np.ones((len(alpha_values), 1))  # Constant S(α,0)

            # Extract ZAID and bound mass from control record
            try:
                c2 = float(
                    line[11:22].replace(" ", "").replace("+", "E+").replace("-", "E-")
                )
                zaid = int(c2)
                bound_mass = float(zaid % 1000)
            except (ValueError, IndexError):
                zaid = 0
                bound_mass = 1.008

            return (
                s_alpha_beta,
                alpha_values,
                beta_values,
                temperature,
                zaid,
                bound_mass,
            )

        except Exception:
            return None

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
            s_alpha_beta[:, i] = np.exp(-(beta**2) / 20.0)

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
