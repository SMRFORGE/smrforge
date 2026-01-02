"""
ENDF Photon Atomic Data Parser - Parses MF=23 (photon atomic data) sections.

This module provides parsing for photon interaction cross-sections including:
- Photoelectric absorption
- Compton scattering
- Pair production
- Atomic form factors
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from .reactor_core import Nuclide


@dataclass
class PhotonCrossSection:
    """Photon cross-section data for a single element."""
    
    element: str  # Element symbol (e.g., "H", "U")
    Z: int  # Atomic number
    energy: np.ndarray  # Photon energy [MeV]
    sigma_photoelectric: np.ndarray  # Photoelectric cross-section [barn]
    sigma_compton: np.ndarray  # Compton scattering cross-section [barn]
    sigma_pair: np.ndarray  # Pair production cross-section [barn]
    sigma_total: np.ndarray  # Total cross-section [barn]
    
    def interpolate(self, energy: float) -> Tuple[float, float, float, float]:
        """
        Interpolate cross-sections at given energy.
        
        Args:
            energy: Photon energy [MeV]
        
        Returns:
            Tuple of (sigma_photoelectric, sigma_compton, sigma_pair, sigma_total) [barn]
        """
        if energy <= self.energy[0]:
            return (
                self.sigma_photoelectric[0],
                self.sigma_compton[0],
                self.sigma_pair[0],
                self.sigma_total[0],
            )
        if energy >= self.energy[-1]:
            return (
                self.sigma_photoelectric[-1],
                self.sigma_compton[-1],
                self.sigma_pair[-1],
                self.sigma_total[-1],
            )
        
        idx = np.searchsorted(self.energy, energy)
        e1, e2 = self.energy[idx - 1], self.energy[idx]
        
        # Linear interpolation
        f = (energy - e1) / (e2 - e1) if e2 != e1 else 0.0
        
        sigma_pe = self.sigma_photoelectric[idx - 1] + f * (
            self.sigma_photoelectric[idx] - self.sigma_photoelectric[idx - 1]
        )
        sigma_comp = self.sigma_compton[idx - 1] + f * (
            self.sigma_compton[idx] - self.sigma_compton[idx - 1]
        )
        sigma_pair_val = self.sigma_pair[idx - 1] + f * (
            self.sigma_pair[idx] - self.sigma_pair[idx - 1]
        )
        sigma_tot = self.sigma_total[idx - 1] + f * (
            self.sigma_total[idx] - self.sigma_total[idx - 1]
        )
        
        return sigma_pe, sigma_comp, sigma_pair_val, sigma_tot


class ENDFPhotonParser:
    """
    Parser for ENDF photon atomic data files (MF=23).
    
    Parses photon interaction cross-sections from ENDF-6 format files, extracting:
    - Photoelectric absorption (MT=501)
    - Compton scattering (MT=502)
    - Pair production (MT=516)
    
    Usage:
        >>> parser = ENDFPhotonParser()
        >>> photon_data = parser.parse_file(Path("p-001_H_001.endf"))
        >>> sigma_pe, sigma_comp, sigma_pair, sigma_tot = photon_data.interpolate(1.0)  # 1 MeV
    """
    
    def __init__(self):
        """Initialize the photon parser."""
        self.mt_map = {
            501: "photoelectric",
            502: "compton",
            516: "pair",
        }
    
    def parse_file(self, filepath: Path) -> Optional[PhotonCrossSection]:
        """
        Parse photon atomic data from an ENDF file.
        
        Args:
            filepath: Path to ENDF photon file (e.g., "p-001_H_001.endf").
        
        Returns:
            PhotonCrossSection instance or None if parsing fails.
        """
        if not filepath.exists():
            return None
        
        # Extract element from filename
        element_info = self._parse_filename(filepath.name)
        if element_info is None:
            return None
        
        element, Z = element_info
        
        try:
            with open(filepath, "r") as f:
                lines = f.readlines()
            
            # Parse MF=23 sections
            # MT=501: Photoelectric
            # MT=502: Compton scattering
            # MT=516: Pair production
            
            sigma_pe = self._parse_mt_section(lines, 501)
            sigma_comp = self._parse_mt_section(lines, 502)
            sigma_pair = self._parse_mt_section(lines, 516)
            
            # Combine energies (use union of all energy points)
            all_energies = set()
            if sigma_pe:
                all_energies.update(sigma_pe[0])
            if sigma_comp:
                all_energies.update(sigma_comp[0])
            if sigma_pair:
                all_energies.update(sigma_pair[0])
            
            if not all_energies:
                return None
            
            # Create common energy grid
            energy = np.array(sorted(all_energies))
            
            # Interpolate cross-sections to common grid
            sigma_pe_interp = self._interpolate_to_grid(energy, sigma_pe) if sigma_pe else np.zeros_like(energy)
            sigma_comp_interp = self._interpolate_to_grid(energy, sigma_comp) if sigma_comp else np.zeros_like(energy)
            sigma_pair_interp = self._interpolate_to_grid(energy, sigma_pair) if sigma_pair else np.zeros_like(energy)
            
            # Total cross-section
            sigma_total = sigma_pe_interp + sigma_comp_interp + sigma_pair_interp
            
            return PhotonCrossSection(
                element=element,
                Z=Z,
                energy=energy,
                sigma_photoelectric=sigma_pe_interp,
                sigma_compton=sigma_comp_interp,
                sigma_pair=sigma_pair_interp,
                sigma_total=sigma_total,
            )
        
        except Exception as e:
            import warnings
            warnings.warn(f"Failed to parse photon data from {filepath}: {e}")
            return None
    
    def _parse_filename(self, filename: str) -> Optional[Tuple[str, int]]:
        """
        Parse element and Z from photon filename.
        
        Format: p-ZZZ_Element_AAA.endf or p-ZZZ_Element.endf
        """
        pattern = r"^p-(\d+)_([A-Z][a-z]?)(?:_\d+)?\.endf$"
        match = re.match(pattern, filename)
        
        if not match:
            return None
        
        z_str, element = match.groups()
        
        try:
            Z = int(z_str)
            return element, Z
        except ValueError:
            return None
    
    def _parse_mt_section(self, lines: List[str], mt: int) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """
        Parse a specific MT section from ENDF file.
        
        Args:
            lines: List of file lines
            mt: Material table number (501, 502, or 516)
        
        Returns:
            Tuple of (energy, cross_section) arrays or None if not found
        """
        # Look for MF=23, MT=mt section
        for i, line in enumerate(lines):
            if len(line) < 75:
                continue
            
            mf = line[70:72].strip()
            mt_str = line[72:75].strip()
            
            if mf == "23" and mt_str == str(mt):
                # Parse data
                energy_list = []
                xs_list = []
                
                j = i + 1
                while j < len(lines):
                    data_line = lines[j]
                    if len(data_line) < 75:
                        j += 1
                        continue
                    
                    # Check for end of section
                    mf_check = data_line[70:72].strip()
                    if mf_check != "23" and mf_check != "":
                        break
                    
                    # Check for end marker
                    if data_line.strip().endswith("-1"):
                        break
                    
                    # Parse data (energy, xs pairs)
                    try:
                        for k in range(0, 6, 2):
                            if k * 11 + 11 <= len(data_line):
                                energy_str = data_line[k * 11:(k + 1) * 11].strip()
                                xs_str = data_line[(k + 1) * 11:(k + 2) * 11].strip()
                                
                                if energy_str and xs_str:
                                    # Handle ENDF scientific notation
                                    energy_str = energy_str.replace("+", "E+").replace("-", "E-")
                                    xs_str = xs_str.replace("+", "E+").replace("-", "E-")
                                    
                                    energy = float(energy_str)  # MeV
                                    xs = float(xs_str)  # barn
                                    
                                    if energy > 0:
                                        energy_list.append(energy)
                                        xs_list.append(xs)
                    except (ValueError, IndexError):
                        pass
                    
                    j += 1
                
                if energy_list:
                    return np.array(energy_list), np.array(xs_list)
        
        return None
    
    def _interpolate_to_grid(
        self, target_energy: np.ndarray, source_data: Tuple[np.ndarray, np.ndarray]
    ) -> np.ndarray:
        """Interpolate cross-section data to target energy grid."""
        source_energy, source_xs = source_data
        
        if len(source_energy) == 0:
            return np.zeros_like(target_energy)
        
        # Interpolate
        xs_interp = np.interp(target_energy, source_energy, source_xs, left=0.0, right=0.0)
        
        return xs_interp

