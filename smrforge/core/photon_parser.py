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
        
        Format: photoat-ZZZ_Element_AAA.endf or photoat-ZZZ_Element.endf
        Also supports: p-ZZZ_Element_AAA.endf (legacy format)
        """
        # Try photoat- prefix first (ENDF-B-VIII.1 format)
        pattern1 = r"^photoat-(\d+)_([A-Z][a-z]?)(?:_\d+)?\.endf$"
        match = re.match(pattern1, filename, re.IGNORECASE)
        
        if not match:
            # Try legacy p- prefix
            pattern2 = r"^p-(\d+)_([A-Z][a-z]?)(?:_\d+)?\.endf$"
            match = re.match(pattern2, filename, re.IGNORECASE)
        
        if not match:
            return None
        
        z_str, element = match.groups()
        
        try:
            Z = int(z_str)
            # Normalize element symbol (capitalize first letter)
            element = element.capitalize()
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
        # Look for MF=23, MT=mt section header
        # ENDF format: MF/MT are in the last 5 characters (columns 66-72 for MF, 72-75 for MT)
        # For photon files, MT is 3-digit (501, 502, 516)
        section_start = None
        
        for i, line in enumerate(lines):
            if len(line) < 75:
                continue
            
            # Check for MF=23, MT=mt in standard ENDF positions (columns 66-75)
            # Format: "MF MT" or "MFMT" at end of line
            line_end = line[66:].strip() if len(line) > 66 else ""
            
            # Try to extract MF and MT from ENDF format
            # Standard ENDF: columns 66-70 = MAT, 70-72 = MF, 72-75 = MT
            # But photon files may have different formatting
            if len(line) >= 75:
                try:
                    # Standard positions: MF at 70-72, MT at 72-75
                    mf_str = line[70:72].strip()
                    mt_str = line[72:75].strip()
                    
                    # Try parsing standard positions
                    if mf_str.isdigit() and mt_str.isdigit():
                        mf_val = int(mf_str)
                        mt_val = int(mt_str)
                    else:
                        # Fallback: try parsing from line end. Some files use a trailing
                        # MAT+MF+MT numeric token like "10023501" (8 digits).
                        line_end = line[66:].strip()
                        parts = line_end.split()
                        token = parts[-1] if parts else ""
                        if token.isdigit() and len(token) >= 8:
                            mf_val = int(token[3:5])
                            mt_val = int(token[5:8])
                        else:
                            continue
                    
                    if mf_val == 23 and mt_val == mt:
                        section_start = i
                        break
                except (ValueError, IndexError, AttributeError):
                    continue
            
            # Also check for text header lines (e.g., "23        501")
            if "23" in line[66:72] and str(mt) in line[72:80]:
                # Check if this is a header line (not data)
                if "MF/MT" in line or "Description" in line or line.strip().startswith("23"):
                    # This might be a header, continue to find actual data section
                    continue
                # Check if it's a section marker
                try:
                    parts = line[66:].split()
                    if len(parts) >= 2:
                        if parts[0] == "23" and parts[1] == str(mt):
                            section_start = i
                            break
                except (ValueError, IndexError):
                    continue
        
        if section_start is None:
            return None
        
        # Parse data section starting from section_start
        # ENDF format: After MF/MT header line, there are header lines:
        # Line 1: "1000.00000 .999242000 ..." (control parameters - C1, C2, etc.)
        # Line 2: "0.0 0.0 ... 1 NPOINTS" (NPOINTS = number of data points, interpolation flag)
        # Line 3: "NPOINTS INTERP" (interpolation flag line, sometimes combined with line 2)
        # Line 4+: actual data pairs (energy, xs)
        
        energy_list = []
        xs_list = []
        
        # Skip header lines - look for actual data
        # Data lines have energy values in reasonable range (1e-7 to 1e5 MeV)
        i = section_start + 1
        data_start = None
        header_count = 0
        
        # Skip up to 4 header lines
        while i < len(lines) and header_count < 4:
            line = lines[i]
            if len(line) < 22:
                i += 1
                header_count += 1
                continue
            
            # Check first two fields
            first_field = line[0:11].strip()
            second_field = line[11:22].strip()
            
            try:
                first_val = float(first_field)
                second_val = float(second_field)
                
                # Header lines typically have:
                # - "0.0 0.0" (control line)
                # - "1000.00000 .999242000" (control parameters)
                # - Very large integers (NPOINTS like 2021, 362) - these appear as first or second field
                # - Lines where first field is a large integer (NPOINTS) or second field is large integer
                
                # Data lines have:
                # - Energy in MeV: typically 1e-7 to 1e5
                # - Cross-section in barns: typically 1e-12 to 1e6
                
                # Check if this looks like header (has large integers that are likely NPOINTS)
                is_header = (
                    first_val == 0.0 and second_val == 0.0  # Control line "0.0 0.0"
                    or first_val == 1000.0  # Control parameter line
                    or (first_val > 100 and first_val == int(first_val) and first_val < 1e6)  # NPOINTS (like 2021, 362)
                    or (second_val > 100 and second_val == int(second_val) and second_val < 1e6)  # NPOINTS
                    or (first_val > 1e6)  # Very large numbers (unlikely to be energy)
                    or (second_val > 1e6)  # Very large numbers
                )
                
                if not is_header and first_val > 0:
                    # Check if values are in reasonable ranges for photon data
                    # Energy: 1e-7 to 1e5 MeV, XS: 1e-12 to 1e6 barns
                    if (1e-7 <= first_val <= 1e5) and (1e-12 <= second_val <= 1e6):
                        data_start = i
                        break
            except (ValueError, IndexError):
                pass
            
            header_count += 1
            i += 1
        
        if data_start is None:
            # Default: skip 3 header lines
            data_start = section_start + 3
        
        # Parse data pairs starting from data_start
        i = data_start
        while i < len(lines):
            line = lines[i]
            
            # Check for end of section (next MF/MT or end marker)
            if len(line) >= 75:
                # Check if this is a new MF/MT section
                mf_check_str = line[70:72].strip() if len(line) >= 72 else ""
                mt_check_str = line[72:75].strip() if len(line) >= 75 else ""
                
                if mf_check_str.isdigit() and mt_check_str.isdigit():
                    mf_check = int(mf_check_str)
                    mt_check = int(mt_check_str)
                    if mf_check == 23 and mt_check != mt:
                        # New section started
                        break
                
                # Check for end marker
                if line.strip().endswith("-1") or "SEND" in line or line.strip().endswith("0  0"):
                    break
            
            # Parse data pairs (energy, xs) - ENDF format: 6 pairs per line, 11 chars each
            try:
                for k in range(0, 6, 2):  # Process pairs: 0-1, 2-3, 4-5
                    start_pos = k * 11
                    if start_pos + 22 <= len(line):
                        energy_str = line[start_pos:start_pos + 11].strip()
                        xs_str = line[start_pos + 11:start_pos + 22].strip()
                        
                        if energy_str and xs_str:
                            # Handle ENDF scientific notation (e.g., "1.000000+2" -> "1.000000E+2")
                            energy_str_clean = re.sub(r'([\d.]+)([+-])', r'\1E\2', energy_str)
                            xs_str_clean = re.sub(r'([\d.]+)([+-])', r'\1E\2', xs_str)
                            
                            try:
                                energy = float(energy_str_clean)  # MeV
                                xs = float(xs_str_clean)  # barn
                                
                                # Only add valid data (energy > 0, xs >= 0, reasonable ranges for photon data)
                                # Photon energies: typically 1e-7 to 1e5 MeV
                                # Photon cross-sections: typically 1e-12 to 1e6 barns
                                if (energy > 0 and xs >= 0 and 
                                    1e-7 <= energy <= 1e5 and 
                                    1e-12 <= xs <= 1e6):
                                    energy_list.append(energy)
                                    xs_list.append(xs)
                            except (ValueError, OverflowError):
                                pass
            except (ValueError, IndexError):
                pass
            
            i += 1
        
        if energy_list and xs_list:
            return np.array(energy_list), np.array(xs_list)
        
        return None
    
    def _interpolate_to_grid(
        self, target_energy: np.ndarray, source_data: Tuple[np.ndarray, np.ndarray]
    ) -> np.ndarray:
        """Interpolate cross-section data to target energy grid."""
        source_energy, source_xs = source_data
        
        if len(source_energy) == 0:
            return np.zeros_like(target_energy)
        
        # Handle single point case - use constant value
        if len(source_energy) == 1:
            return np.full_like(target_energy, source_xs[0])
        
        # Interpolate
        xs_interp = np.interp(target_energy, source_energy, source_xs, left=0.0, right=0.0)
        
        return xs_interp

