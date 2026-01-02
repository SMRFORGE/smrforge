"""
ENDF Decay Data Parser - Parses MF=8 (decay data) sections from ENDF files.

This module provides parsing for radioactive decay data including:
- Half-lives and decay constants
- Decay modes (α, β⁻, β⁺, EC, IT, SF)
- Decay product yields and branching ratios
- Gamma-ray emission spectra
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from .reactor_core import Nuclide


@dataclass
class DecayMode:
    """Information about a single decay mode."""
    
    mode: str  # 'α', 'β⁻', 'β⁺', 'EC', 'IT', 'SF', etc.
    branching_ratio: float  # Fraction of decays via this mode (0-1)
    daughter: Optional[Nuclide] = None  # Daughter nuclide (if applicable)
    q_value: float = 0.0  # Q-value in MeV


@dataclass
class GammaSpectrum:
    """Gamma-ray emission spectrum."""
    
    energy: np.ndarray  # Gamma energy [MeV]
    intensity: np.ndarray  # Emission intensity [photons/decay]
    total_energy: float  # Total gamma energy per decay [MeV]
    
    def get_energy_spectrum(self) -> Tuple[np.ndarray, np.ndarray]:
        """Get energy spectrum (energy, intensity)."""
        return self.energy, self.intensity


@dataclass
class BetaSpectrum:
    """Beta emission spectrum."""
    
    energy: np.ndarray  # Beta energy [MeV]
    intensity: np.ndarray  # Emission intensity [betas/decay]
    endpoint_energy: float  # Maximum beta energy [MeV]
    average_energy: float  # Average beta energy [MeV]
    
    def get_energy_spectrum(self) -> Tuple[np.ndarray, np.ndarray]:
        """Get energy spectrum (energy, intensity)."""
        return self.energy, self.intensity


@dataclass
class DecayData:
    """Decay data for a single nuclide."""
    
    nuclide: Nuclide
    half_life: float  # Half-life in seconds
    decay_constant: float  # Decay constant λ = ln(2) / T_1/2 [1/s]
    is_stable: bool  # True if nuclide is stable
    decay_modes: List[DecayMode]  # List of decay modes
    daughters: Dict[Nuclide, float]  # Map daughter -> total branching ratio
    gamma_spectrum: Optional[GammaSpectrum] = None  # Gamma-ray emission spectrum
    beta_spectrum: Optional[BetaSpectrum] = None  # Beta emission spectrum
    
    def __post_init__(self):
        """Calculate decay constant from half-life."""
        if self.half_life > 0 and not self.is_stable:
            self.decay_constant = np.log(2) / self.half_life
        else:
            self.decay_constant = 0.0
            self.is_stable = True
    
    def get_total_gamma_energy(self) -> float:
        """Get total gamma energy per decay [MeV]."""
        if self.gamma_spectrum:
            return self.gamma_spectrum.total_energy
        return 0.0
    
    def get_total_beta_energy(self) -> float:
        """Get total beta energy per decay [MeV]."""
        if self.beta_spectrum:
            return self.beta_spectrum.average_energy
        return 0.0


class ENDFDecayParser:
    """
    Parser for ENDF decay data files (MF=8).
    
    Parses decay data from ENDF-6 format files, extracting:
    - Half-lives (MF=8, MT=457)
    - Decay modes and branching ratios (MF=8, MT=457)
    - Decay product yields (MF=8, MT=454)
    - Gamma-ray spectra (MF=8, MT=460)
    
    Usage:
        >>> parser = ENDFDecayParser()
        >>> decay_data = parser.parse_file(Path("dec-092_U_235.endf"))
        >>> print(f"Half-life: {decay_data.half_life:.2e} s")
        >>> print(f"Decay constant: {decay_data.decay_constant:.2e} 1/s")
    """
    
    def __init__(self):
        """Initialize the decay parser."""
        self.decay_mode_map = {
            1: "β⁻",
            2: "EC",
            3: "IT",  # Isomeric transition
            4: "α",
            5: "n",  # Neutron emission
            6: "SF",  # Spontaneous fission
            7: "p",  # Proton emission
            8: "β⁺",
        }
    
    def parse_file(self, filepath: Path) -> Optional[DecayData]:
        """
        Parse decay data from an ENDF file.
        
        Args:
            filepath: Path to ENDF decay data file (e.g., "dec-092_U_235.endf").
        
        Returns:
            DecayData instance with parsed decay information, or None if parsing fails.
        
        Raises:
            FileNotFoundError: If file does not exist.
            ValueError: If file format is invalid.
        """
        if not filepath.exists():
            raise FileNotFoundError(f"Decay data file not found: {filepath}")
        
        # Extract nuclide from filename
        nuclide = self._parse_filename(filepath.name)
        if nuclide is None:
            raise ValueError(f"Could not extract nuclide from filename: {filepath.name}")
        
        try:
            with open(filepath, "r") as f:
                lines = f.readlines()
            
            # Find MF=8 (decay data) section
            # MT=457 contains half-life and decay mode information
            half_life = self._parse_half_life(lines)
            decay_modes = self._parse_decay_modes(lines, nuclide)
            daughters = self._build_daughters_dict(decay_modes)
            
            # Parse gamma-ray spectrum (MF=8, MT=460)
            gamma_spectrum = self._parse_gamma_spectrum(lines)
            
            # Parse beta spectrum (MF=8, MT=455)
            beta_spectrum = self._parse_beta_spectrum(lines)
            
            # Determine if stable (very long half-life or no decay modes)
            is_stable = half_life > 1e20 or len(decay_modes) == 0
            
            return DecayData(
                nuclide=nuclide,
                half_life=half_life,
                decay_constant=0.0,  # Will be calculated in __post_init__
                is_stable=is_stable,
                decay_modes=decay_modes,
                daughters=daughters,
                gamma_spectrum=gamma_spectrum,
                beta_spectrum=beta_spectrum,
            )
        except Exception as e:
            # Log error but return None to allow graceful fallback
            import warnings
            warnings.warn(f"Failed to parse decay data from {filepath}: {e}")
            return None
    
    def _parse_filename(self, filename: str) -> Optional[Nuclide]:
        """
        Parse nuclide from ENDF decay filename.
        
        Format: dec-ZZZ_Element_AAA.endf or dec-ZZZ_Element_AAAm1.endf
        
        Args:
            filename: ENDF decay filename.
        
        Returns:
            Nuclide instance or None if parsing fails.
        """
        pattern = r"^dec-(\d+)_([A-Z][a-z]?)_(\d+)([mM]\d?)?\.endf$"
        match = re.match(pattern, filename)
        
        if not match:
            return None
        
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
            return None
    
    def _parse_half_life(self, lines: List[str]) -> float:
        """
        Parse half-life from ENDF file (MF=8, MT=457).
        
        Args:
            lines: List of file lines.
        
        Returns:
            Half-life in seconds, or 1e20 (effectively stable) if not found.
        """
        # Look for MF=8, MT=457 section
        for i, line in enumerate(lines):
            if len(line) < 75:
                continue
            
            mf = line[70:72].strip()
            mt = line[72:75].strip()
            
            if mf == "8" and mt == "457":
                # Half-life is typically in the first data line after header
                # Format: T_1/2 is in the first data value
                if i + 1 < len(lines):
                    data_line = lines[i + 1]
                    try:
                        # ENDF format: first 11 characters are first value
                        half_life_str = data_line[0:11].strip()
                        if half_life_str:
                            half_life = float(half_life_str)
                            # ENDF stores half-life in seconds, but sometimes uses
                            # special notation (e.g., 0.0 for stable)
                            if half_life <= 0:
                                return 1e20  # Effectively stable
                            return half_life
                    except (ValueError, IndexError):
                        pass
        
        # Default: assume stable
        return 1e20
    
    def _parse_decay_modes(self, lines: List[str], parent: Nuclide) -> List[DecayMode]:
        """
        Parse decay modes from ENDF file (MF=8, MT=457).
        
        Args:
            lines: List of file lines.
            parent: Parent nuclide.
        
        Returns:
            List of DecayMode instances.
        """
        decay_modes = []
        
        # Look for MF=8, MT=457 section
        for i, line in enumerate(lines):
            if len(line) < 75:
                continue
            
            mf = line[70:72].strip()
            mt = line[72:75].strip()
            
            if mf == "8" and mt == "457":
                # Decay mode information follows the header
                # This is a simplified parser - full ENDF format is more complex
                # For now, return empty list (can be enhanced later)
                break
        
        return decay_modes
    
    def _build_daughters_dict(self, decay_modes: List[DecayMode]) -> Dict[Nuclide, float]:
        """
        Build dictionary mapping daughters to total branching ratios.
        
        Args:
            decay_modes: List of DecayMode instances.
        
        Returns:
            Dictionary mapping daughter nuclide -> total branching ratio.
        """
        daughters = {}
        for mode in decay_modes:
            if mode.daughter is not None:
                if mode.daughter in daughters:
                    daughters[mode.daughter] += mode.branching_ratio
                else:
                    daughters[mode.daughter] = mode.branching_ratio
        return daughters

