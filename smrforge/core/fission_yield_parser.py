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

from ..utils.logging import get_logger
from .reactor_core import Nuclide

logger = get_logger("smrforge.core.fission_yield_parser")


def _parse_endf_float(field: str) -> float:
    """Parse ENDF-6 style float (e.g. ' 1.234567+5' -> 1.234567e5)."""
    s = (field or "").strip()
    if not s:
        return 0.0
    s = s.replace(" ", "")
    if "e" in s.lower():
        return float(s)
    pos_plus, pos_minus = s.rfind("+", 1), s.rfind("-", 1)
    pos = max(pos_plus, pos_minus)
    if pos > 0:
        s = s[:pos] + "E" + s[pos:]
    return float(s)


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
    energies: Optional[np.ndarray] = (
        None  # Neutron energies in eV (if energy-dependent)
    )

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
        return (
            yield_data.cumulative_yield if cumulative else yield_data.independent_yield
        )

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
            total += (
                yield_data.cumulative_yield
                if cumulative
                else yield_data.independent_yield
            )
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
            raise ValueError(
                f"Could not extract nuclide from filename: {filepath.name}"
            )

        try:
            with open(filepath, "r") as f:
                lines = f.readlines()

            # Parse independent yields (MT=454) and cumulative yields (MT=459)
            independent_yields = self._parse_yields(lines, mt=454)
            cumulative_yields = self._parse_yields(lines, mt=459)

            # Combine into FissionYield objects
            yields = {}
            all_products = set(independent_yields.keys()) | set(
                cumulative_yields.keys()
            )

            for product in all_products:
                ind_yield = independent_yields.get(product, 0.0)
                cum_yield = cumulative_yields.get(product, 0.0)

                yields[product] = FissionYield(
                    product=product,
                    independent_yield=ind_yield,
                    cumulative_yield=cum_yield,
                )

            # If we couldn't extract any yields, treat as unavailable data.
            # This lets callers handle "not found / not parsable" consistently.
            if not yields:
                return None

            # Check if energy-dependent (simplified - full implementation would check energy points)
            energy_dependent = False

            return FissionYieldData(
                parent=parent,
                yields=yields,
                energy_dependent=energy_dependent,
            )
        except Exception as e:
            logger.warning(
                "Failed to parse fission yield data from %s: %s", filepath, e
            )
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

        ENDF LIST format: [E1, 0, LE, I, NN, NFP] then Cn = NFP sets of
        (ZAFP, FPS, Y, DY) with ZAFP=1000*Z+A. Uses first energy point (thermal).

        Args:
            lines: List of file lines.
            mt: Material table number (454 for independent, 459 for cumulative).

        Returns:
            Dictionary mapping product nuclide -> yield (fraction).
        """
        yields: Dict[Nuclide, float] = {}
        in_section = False
        values: List[float] = []
        mt_str = str(mt)

        for line in lines:
            if len(line) < 75:
                continue

            mf = line[70:72].strip()
            line_mt = line[72:75].strip()

            if mf == "8" and line_mt == mt_str:
                in_section = True
                # Parse header: C1=E1, C2, L1=LE, L2, N1=NN, N2=NFP
                try:
                    nn = int(line[55:66].strip() or 0)
                    nfp = int(line[66:70].strip() or 0)
                except (ValueError, IndexError):
                    nn, nfp = 0, 0
                values = []
                # Same line may have start of data; ENDF typically has 6 header values
                for j in range(6):
                    start = j * 11
                    if start + 11 <= len(line):
                        try:
                            values.append(_parse_endf_float(line[start : start + 11]))
                        except (ValueError, TypeError):
                            pass
                continue

            if in_section and (mf != "8" or line_mt != mt_str):
                break

            if in_section and line[0:11].strip():
                for j in range(6):
                    start = j * 11
                    if start + 11 <= len(line):
                        try:
                            values.append(_parse_endf_float(line[start : start + 11]))
                        except (ValueError, TypeError):
                            pass

        # Process 4-tuples: (ZAFP, FPS, Y, DY). Skip first 6 (header).
        for idx in range(6, len(values) - 3, 4):
            zafp = int(round(values[idx]))
            y_val = float(values[idx + 2])
            z_daughter = zafp // 1000
            a_daughter = zafp % 1000
            if 0 < z_daughter < 120 and 0 < a_daughter < 300 and y_val >= 0:
                product = Nuclide(Z=z_daughter, A=a_daughter)
                if product in yields:
                    yields[product] += y_val  # Sum over isomeric states
                else:
                    yields[product] = y_val

        return yields
