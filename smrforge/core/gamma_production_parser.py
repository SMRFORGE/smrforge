"""
ENDF Gamma Production Parser - Parses MF=12, 13, 14 (gamma production) sections.

This module provides parsing for gamma-ray production data including:
- Prompt gamma production cross-sections
- Delayed gamma production cross-sections
- Gamma-ray energy spectra
- Gamma production yields
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from .reactor_core import Nuclide


@dataclass
class GammaProductionSpectrum:
    """Gamma production spectrum for a specific reaction."""
    
    reaction: str  # Reaction name (e.g., "fission", "capture")
    energy: np.ndarray  # Gamma energy [MeV]
    intensity: np.ndarray  # Production intensity [gammas/reaction]
    total_yield: float  # Total gamma yield per reaction
    prompt: bool  # True if prompt gamma, False if delayed


@dataclass
class GammaProductionData:
    """Gamma production data for a nuclide."""
    
    nuclide: Nuclide
    prompt_spectra: Dict[str, GammaProductionSpectrum]  # Reaction -> prompt spectrum
    delayed_spectra: Dict[str, GammaProductionSpectrum]  # Reaction -> delayed spectrum
    
    def get_total_gamma_yield(self, reaction: str, prompt: bool = True) -> float:
        """
        Get total gamma yield for a reaction.
        
        Args:
            reaction: Reaction name (e.g., "fission", "capture").
            prompt: If True, return prompt yield; otherwise delayed yield.
        
        Returns:
            Total gamma yield [gammas/reaction], or 0.0 if not found.
        """
        spectra = self.prompt_spectra if prompt else self.delayed_spectra
        if reaction not in spectra:
            return 0.0
        return spectra[reaction].total_yield
    
    def get_gamma_spectrum(self, reaction: str, prompt: bool = True) -> Optional[GammaProductionSpectrum]:
        """
        Get gamma production spectrum for a reaction.
        
        Args:
            reaction: Reaction name (e.g., "fission", "capture").
            prompt: If True, return prompt spectrum; otherwise delayed spectrum.
        
        Returns:
            GammaProductionSpectrum or None if not found.
        """
        spectra = self.prompt_spectra if prompt else self.delayed_spectra
        return spectra.get(reaction)


class ENDFGammaProductionParser:
    """
    Parser for ENDF gamma production data files (MF=12, 13, 14).
    
    Parses gamma production data from ENDF-6 format files, extracting:
    - Prompt gamma production (MF=12)
    - Delayed gamma production (MF=13, 14)
    - Gamma energy spectra
    - Production yields
    
    Usage:
        >>> parser = ENDFGammaProductionParser()
        >>> gamma_data = parser.parse_file(Path("gammas-092_U_235.endf"))
        >>> yield_fission = gamma_data.get_total_gamma_yield("fission", prompt=True)
        >>> print(f"Prompt gamma yield per fission: {yield_fission:.2f}")
    """
    
    def __init__(self):
        """Initialize the gamma production parser."""
        self.reaction_mt_map = {
            18: "fission",
            102: "capture",
            2: "elastic",
            1: "total",
        }
    
    def parse_file(self, filepath: Path) -> Optional[GammaProductionData]:
        """
        Parse gamma production data from an ENDF file.
        
        Args:
            filepath: Path to ENDF gamma production file (e.g., "gammas-092_U_235.endf").
        
        Returns:
            GammaProductionData instance or None if parsing fails.
        """
        if not filepath.exists():
            return None
        
        # Extract nuclide from filename
        nuclide = self._parse_filename(filepath.name)
        if nuclide is None:
            return None
        
        try:
            with open(filepath, "r") as f:
                lines = f.readlines()
            
            # Parse MF=12 (prompt gamma production)
            prompt_spectra = self._parse_mf12(lines)
            
            # Parse MF=13, 14 (delayed gamma production)
            delayed_spectra = self._parse_mf13_14(lines)
            
            return GammaProductionData(
                nuclide=nuclide,
                prompt_spectra=prompt_spectra,
                delayed_spectra=delayed_spectra,
            )
        
        except Exception as e:
            import warnings
            warnings.warn(f"Failed to parse gamma production data from {filepath}: {e}")
            return None
    
    def _parse_filename(self, filename: str) -> Optional[Nuclide]:
        """
        Parse nuclide from gamma production filename.
        
        Format: gammas-ZZZ_Element_AAA.endf or similar
        """
        # Try various patterns
        patterns = [
            r"^gammas-(\d+)_([A-Z][a-z]?)_(\d+)([mM]\d?)?\.endf$",
            r"^gamma-(\d+)_([A-Z][a-z]?)_(\d+)([mM]\d?)?\.endf$",
            r"^(\d+)_([A-Z][a-z]?)_(\d+)([mM]\d?)?\.endf$",  # Alternative format
        ]
        
        for pattern in patterns:
            match = re.match(pattern, filename)
            if match:
                z_str, element, a_str, meta = match.groups()
                try:
                    Z = int(z_str)
                    A = int(a_str)
                    m = 0
                    if meta:
                        m_str = meta[1:] if len(meta) > 1 else "1"
                        m = int(m_str) if m_str else 1
                    return Nuclide(Z=Z, A=A, m=m)
                except (ValueError, KeyError):
                    continue
        
        return None
    
    def _parse_mf12(self, lines: List[str]) -> Dict[str, GammaProductionSpectrum]:
        """
        Parse MF=12 (prompt gamma production) sections.
        
        Returns:
            Dictionary mapping reaction -> GammaProductionSpectrum.
        """
        spectra = {}
        
        # Look for MF=12 sections
        for i, line in enumerate(lines):
            if len(line) < 75:
                continue
            
            mf = line[70:72].strip()
            if mf != "12":
                continue
            
            mt_str = line[72:75].strip()
            try:
                mt = int(mt_str)
            except ValueError:
                continue
            
            # Map MT to reaction name
            reaction = self.reaction_mt_map.get(mt, f"mt{mt}")
            
            # Parse gamma spectrum
            spectrum = self._parse_gamma_spectrum_section(lines, i, mt)
            if spectrum:
                spectra[reaction] = GammaProductionSpectrum(
                    reaction=reaction,
                    energy=spectrum[0],
                    intensity=spectrum[1],
                    total_yield=np.sum(spectrum[1]),
                    prompt=True,
                )
        
        return spectra
    
    def _parse_mf13_14(self, lines: List[str]) -> Dict[str, GammaProductionSpectrum]:
        """
        Parse MF=13, 14 (delayed gamma production) sections.
        
        Returns:
            Dictionary mapping reaction -> GammaProductionSpectrum.
        """
        spectra = {}
        
        # Look for MF=13 and MF=14 sections
        for mf_num in [13, 14]:
            for i, line in enumerate(lines):
                if len(line) < 75:
                    continue
                
                mf = line[70:72].strip()
                if mf != str(mf_num):
                    continue
                
                mt_str = line[72:75].strip()
                try:
                    mt = int(mt_str)
                except ValueError:
                    continue
                
                # Map MT to reaction name
                reaction = self.reaction_mt_map.get(mt, f"mt{mt}")
                
                # Parse gamma spectrum
                spectrum = self._parse_gamma_spectrum_section(lines, i, mt)
                if spectrum:
                    spectra[reaction] = GammaProductionSpectrum(
                        reaction=reaction,
                        energy=spectrum[0],
                        intensity=spectrum[1],
                        total_yield=np.sum(spectrum[1]),
                        prompt=False,
                    )
        
        return spectra
    
    def _parse_gamma_spectrum_section(
        self, lines: List[str], start_idx: int, mt: int
    ) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """
        Parse gamma spectrum from a specific section.
        
        Args:
            lines: List of file lines.
            start_idx: Starting line index of the section.
            mt: Material table number.
        
        Returns:
            Tuple of (energy, intensity) arrays or None if not found.
        """
        energy_list = []
        intensity_list = []
        
        j = start_idx + 1
        while j < len(lines):
            data_line = lines[j]
            if len(data_line) < 75:
                j += 1
                continue
            
            # Check for end of section (new MF section starts)
            # Skip check if line is too short to have MF field
            if len(data_line) >= 72:
                mf_check = data_line[70:72].strip()
                # Only break if we encounter a different MF (not continuation of current MF)
                if mf_check and mf_check not in ["12", "13", "14", ""]:
                    break
            
            # Check for end marker
            if data_line.strip().endswith("-1"):
                break
            
            # Parse data (energy, intensity pairs)
            try:
                for k in range(0, 6, 2):
                    if k * 11 + 11 <= len(data_line):
                        energy_str = data_line[k * 11:(k + 1) * 11].strip()
                        intensity_str = data_line[(k + 1) * 11:(k + 2) * 11].strip()
                        
                        if energy_str and intensity_str:
                            # Handle ENDF scientific notation (e.g., "1.000000+2" -> "1.000000E+2")
                            # Replace "+" or "-" that comes after digits (scientific notation marker)
                            import re
                            energy_str = re.sub(r'([\d.]+)([+-])', r'\1E\2', energy_str)
                            intensity_str = re.sub(r'([\d.]+)([+-])', r'\1E\2', intensity_str)
                            
                            energy = float(energy_str)  # MeV
                            intensity = float(intensity_str)  # gammas/reaction
                            
                            if energy > 0:
                                energy_list.append(energy)
                                intensity_list.append(intensity)
            except (ValueError, IndexError):
                pass
            
            j += 1
        
        if energy_list:
            return np.array(energy_list), np.array(intensity_list)
        
        return None

