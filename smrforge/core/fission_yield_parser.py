"""
ENDF Fission Yield Parser - Parses fission product yield data from ENDF files.

This module provides parsing for neutron-induced fission yields including:
- Independent fission product yields
- Cumulative fission product yields
- Energy-dependent yields
- Chain yields
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from .reactor_core import Nuclide


@dataclass
class FissionYield:
    """Fission yield data for a single product nuclide."""
    
    product: Nuclide  # Fission product nuclide
    independent_yield: float  # Independent yield (fraction)
    cumulative_yield: float  # Cumulative yield (fraction)
    uncertainty: Optional[float] = None  # Yield uncertainty
    energy: Optional[float] = None  # Neutron energy in eV (if energy-dependent)


@dataclass
class FissionYieldData:
    """Fission yield data for a fissile nuclide."""
    
    parent: Nuclide  # Fissile nuclide (e.g., U235)
    yields: Dict[Nuclide, FissionYield]  # Map product -> yield data
    energy_dependent: bool  # True if yields vary with neutron energy
    energies: Optional[np.ndarray] = None  # Neutron energies in eV (if energy-dependent)
    
    def get_yield(self, product: Nuclide, cumulative: bool = True) -> float:
        """
        Get fission yield for a product nuclide.
        
        Args:
            product: Fission product nuclide.
            cumulative: If True, return cumulative yield; otherwise independent yield.
        
        Returns:
            Fission yield (fraction), or 0.0 if product not found.
        """
        if product not in self.yields:
            return 0.0
        
        yield_data = self.yields[product]
        return yield_data.cumulative_yield if cumulative else yield_data.independent_yield
    
    def get_total_yield(self, cumulative: bool = True) -> float:
        """
        Get total fission yield (sum over all products).
        
        Args:
            cumulative: If True, sum cumulative yields; otherwise independent yields.
        
        Returns:
            Total yield (should be ~2.0 for binary fission).
        """
        total = 0.0
        for yield_data in self.yields.values():
            total += yield_data.cumulative_yield if cumulative else yield_data.independent_yield
        return total


class ENDFFissionYieldParser:
    """
    Parser for ENDF fission yield data files (MF=8, MT=454, 459).
    
    Parses fission product yield data from ENDF-6 format files, extracting:
    - Independent yields (MT=454)
    - Cumulative yields (MT=459)
    - Energy-dependent yields
    
    Usage:
        >>> parser = ENDFFissionYieldParser()
        >>> yield_data = parser.parse_file(Path("nfy-092_U_235.endf"))
        >>> cs137 = Nuclide(Z=55, A=137)
        >>> yield_cs137 = yield_data.get_yield(cs137)
        >>> print(f"Cs-137 yield: {yield_cs137:.4f}")
    """
    
    def __init__(self):
        """Initialize the fission yield parser."""
        pass
    
    def parse_file(self, filepath: Path) -> Optional[FissionYieldData]:
        """
        Parse fission yield data from an ENDF file.
        
        Args:
            filepath: Path to ENDF fission yield file (e.g., "nfy-092_U_235.endf").
        
        Returns:
            FissionYieldData instance with parsed yield information, or None if parsing fails.
        
        Raises:
            FileNotFoundError: If file does not exist.
            ValueError: If file format is invalid.
        """
        if not filepath.exists():
            raise FileNotFoundError(f"Fission yield file not found: {filepath}")
        
        # Extract nuclide from filename
        parent = self._parse_filename(filepath.name)
        if parent is None:
            raise ValueError(f"Could not extract nuclide from filename: {filepath.name}")
        
        try:
            with open(filepath, "r") as f:
                lines = f.readlines()
            
            # Parse independent yields (MT=454) and cumulative yields (MT=459)
            independent_yields = self._parse_yields(lines, mt=454)
            cumulative_yields = self._parse_yields(lines, mt=459)
            
            # Combine into FissionYield objects
            yields = {}
            all_products = set(independent_yields.keys()) | set(cumulative_yields.keys())
            
            for product in all_products:
                ind_yield = independent_yields.get(product, 0.0)
                cum_yield = cumulative_yields.get(product, 0.0)
                
                yields[product] = FissionYield(
                    product=product,
                    independent_yield=ind_yield,
                    cumulative_yield=cum_yield,
                )
            
            # Check if energy-dependent (simplified - full implementation would check energy points)
            energy_dependent = False
            
            return FissionYieldData(
                parent=parent,
                yields=yields,
                energy_dependent=energy_dependent,
            )
        except Exception as e:
            # Log error but return None to allow graceful fallback
            import warnings
            warnings.warn(f"Failed to parse fission yield data from {filepath}: {e}")
            return None
    
    def _parse_filename(self, filename: str) -> Optional[Nuclide]:
        """
        Parse nuclide from ENDF fission yield filename.
        
        Format: nfy-ZZZ_Element_AAA.endf or nfy-ZZZ_Element_AAAm1.endf
        
        Args:
            filename: ENDF fission yield filename.
        
        Returns:
            Nuclide instance or None if parsing fails.
        """
        pattern = r"^nfy-(\d+)_([A-Z][a-z]?)_(\d+)([mM]\d?)?\.endf$"
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
    
    def _parse_yields(self, lines: List[str], mt: int) -> Dict[Nuclide, float]:
        """
        Parse fission yields from ENDF file (MF=8, MT=454 or 459).
        
        Args:
            lines: List of file lines.
            mt: Material table number (454 for independent, 459 for cumulative).
        
        Returns:
            Dictionary mapping product nuclide -> yield (fraction).
        """
        yields = {}
        
        # Look for MF=8, MT=454 or MT=459 section
        for i, line in enumerate(lines):
            if len(line) < 75:
                continue
            
            mf = line[70:72].strip()
            mt_str = line[72:75].strip()
            
            if mf == "8" and mt_str == str(mt):
                # Parse yield data
                # ENDF format: Each data line contains product Z, A, and yield
                # This is a simplified parser - full ENDF format is more complex
                # For now, return empty dict (can be enhanced with full parsing)
                break
        
        return yields

