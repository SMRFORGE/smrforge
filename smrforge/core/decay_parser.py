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

from ..utils.logging import get_logger
from .reactor_core import Nuclide

logger = get_logger("smrforge.core.decay_parser")


def _parse_endf_float(field: str) -> float:
    """
    Parse an ENDF-6 style floating field.

    ENDF commonly encodes floats like ` 1.234567+5` (meaning 1.234567E+5) or
    `-3.210000-3` (meaning -3.21E-3) without an explicit 'E'.
    """
    s = (field or "").strip()
    if not s:
        return 0.0

    s = s.replace(" ", "")
    if "e" in s.lower():
        return float(s)

    pos_plus = s.rfind("+", 1)
    pos_minus = s.rfind("-", 1)
    pos = max(pos_plus, pos_minus)
    if pos > 0:
        s = s[:pos] + "E" + s[pos:]

    return float(s)


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
            raise ValueError(
                f"Could not extract nuclide from filename: {filepath.name}"
            )

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

            # Determine if stable (very long half-life). Do not rely on `decay_modes`
            # here because `_parse_decay_modes` may be a stub in lightweight builds.
            is_stable = half_life >= 1e20

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
            logger.warning("Failed to parse decay data from %s: %s", filepath, e)
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
        # Look for MF=8, MT=457 section.
        #
        # In ENDF decay files produced from ENSDF, the MT=457 section commonly
        # contains:
        # - A first numeric record with ZA/AWR (not the half-life)
        # - A second numeric record whose first field is the half-life [s]
        #
        # We therefore take the *second* numeric line in the MT=457 section.
        data_line_count = 0
        for line in lines:
            if len(line) < 75:
                continue

            mf = line[70:72].strip()
            mt = line[72:75].strip()
            if mf != "8" or mt != "457":
                continue

            # Skip purely blank "control" records that have no numeric fields.
            if not line[0:11].strip():
                continue

            data_line_count += 1
            if data_line_count == 2:
                try:
                    half_life = _parse_endf_float(line[0:11])
                except (ValueError, IndexError):
                    half_life = 0.0

                if half_life <= 0:
                    return 1e20
                return half_life

        # Default: assume stable
        return 1e20

    def _parse_decay_modes(self, lines: List[str], parent: Nuclide) -> List[DecayMode]:
        """
        Parse decay modes and branching ratios from ENDF file (MF=8, MT=457).

        Reads decay radiation LIST records: each entry is (RTYP, RFS, Q, D, BR, DBR).
        RTYP: 0=gamma, 1=beta-, 2=ec/beta+, 3=it, 4=alpha, 5=n, 6=proton, 7=sf.
        RFS: 1000*Z + A of daughter (0 for gamma/IT). BR: branching ratio.

        Args:
            lines: List of file lines.
            parent: Parent nuclide.

        Returns:
            List of DecayMode instances with branching ratios.
        """
        decay_modes = []
        in_mf8_mt457 = False
        n_values_to_read = 0
        values = []

        for i, line in enumerate(lines):
            if len(line) < 75:
                continue

            mf = line[70:72].strip()
            mt = line[72:75].strip()

            if mf == "8" and mt == "457":
                if not in_mf8_mt457:
                    values = []
                in_mf8_mt457 = True
                continue

            if in_mf8_mt457 and (mf != "8" or mt != "457"):
                break

            if in_mf8_mt457 and line[0:11].strip():
                # Parse numeric fields (11 chars each, 6 per line)
                for j in range(6):
                    start = j * 11
                    end = start + 11
                    if end <= len(line):
                        try:
                            val = _parse_endf_float(line[start:end])
                            values.append(val)
                        except (ValueError, TypeError):
                            pass

        # Process 6-tuples: (RTYP, RFS, Q, D, BR, DBR)
        for idx in range(0, len(values) - 5, 6):
            try:
                rtyp = int(round(values[idx]))
                rfs = int(round(values[idx + 1]))
                br = float(values[idx + 4])
            except (IndexError, ValueError, TypeError):
                continue

            if br <= 0 or br > 1.0:
                continue
            if rtyp < 0 or rtyp > 8:  # Skip non-decay records (e.g. header)
                continue

            mode_str = self.decay_mode_map.get(rtyp, "?")
            daughter = None
            if rfs > 0 and rtyp in (1, 2, 4, 5, 6, 7, 8):  # Particle decays with daughter
                z_daughter = rfs // 1000
                a_daughter = rfs % 1000
                if 0 < z_daughter < 120 and 0 < a_daughter < 300:
                    daughter = Nuclide(Z=z_daughter, A=a_daughter)

            decay_modes.append(
                DecayMode(mode=mode_str, branching_ratio=br, daughter=daughter, q_value=0.0)
            )

        return decay_modes

    def _build_daughters_dict(
        self, decay_modes: List[DecayMode]
    ) -> Dict[Nuclide, float]:
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

    def _parse_gamma_spectrum(self, lines: List[str]) -> Optional[GammaSpectrum]:
        """
        Parse gamma-ray spectrum from ENDF file (MF=8, MT=460 or MT=457 decay radiation).

        Reads energy [MeV] and intensity [photons/decay]. ENDF energies are in eV;
        converted to MeV. Accepts 6-tuples (RTYP, RFS, Q, D, BR, DBR) with RTYP=0.
        """
        energies: List[float] = []
        intensities: List[float] = []
        # Try MT=460 first
        values_460 = self._collect_section_values(lines, "8", "460")
        if values_460:
            self._extract_gamma_from_tuples(values_460, energies, intensities)

        # Fallback: MT=457 decay radiation (RTYP=0)
        if not energies:
            values_457 = self._collect_section_values(lines, "8", "457")
            self._extract_gamma_from_tuples(values_457, energies, intensities)

        if not energies and values_460 and len(values_460) >= 2:
            for i in range(0, len(values_460) - 1, 2):
                e_val = float(values_460[i]) / 1e6  # eV -> MeV
                i_val = float(values_460[i + 1])
                if 0 < e_val < 20 and i_val >= 0:
                    energies.append(e_val)
                    intensities.append(i_val)

        if not energies:
            return None
        energy_arr = np.array(energies)
        intensity_arr = np.array(intensities)
        total = np.sum(energy_arr * intensity_arr)
        return GammaSpectrum(
            energy=energy_arr,
            intensity=intensity_arr,
            total_energy=float(total),
        )

    def _collect_section_values(
        self, lines: List[str], mf: str, mt: str
    ) -> List[float]:
        """Collect 11-char numeric fields from ENDF section MF/MT."""
        values: List[float] = []
        in_section = False

        for line in lines:
            if len(line) < 75:
                continue
            line_mf = line[70:72].strip()
            line_mt = line[72:75].strip()

            if line_mf == mf and line_mt == mt:
                in_section = True
            elif in_section:
                break
            if in_section and line[0:11].strip():
                for j in range(6):
                    start = j * 11
                    if start + 11 <= len(line):
                        try:
                            values.append(_parse_endf_float(line[start : start + 11]))
                        except (ValueError, TypeError):
                            pass
        return values

    def _extract_gamma_from_tuples(
        self,
        values: List[float],
        energies: List[float],
        intensities: List[float],
    ) -> None:
        """Extract (E, I) from 6-tuples (RTYP=0, RFS, Q, D, BR, DBR). Q in eV, BR intensity."""
        for i in range(0, len(values) - 5, 6):
            try:
                rtyp = int(round(values[i]))
            except (ValueError, TypeError):
                continue
            if rtyp == 0:  # Gamma
                e_val = float(values[i + 2]) / 1e6  # eV -> MeV
                i_val = float(values[i + 4])  # BR = intensity
                if e_val > 0 and i_val >= 0:
                    energies.append(e_val)
                    intensities.append(i_val)

    def _parse_beta_spectrum(self, lines: List[str]) -> Optional[BetaSpectrum]:
        """
        Parse beta emission spectrum from ENDF file (MF=8, MT=455 or MT=457).

        Reads energy [MeV] and intensity. Accepts 6-tuples (RTYP=1 beta-, RTYP=8 beta+).
        Q in eV, converted to MeV.
        """
        energies: List[float] = []
        intensities: List[float] = []
        values_455 = self._collect_section_values(lines, "8", "455")
        if values_455:
            self._extract_beta_from_tuples(values_455, energies, intensities)

        if not energies:
            values_457 = self._collect_section_values(lines, "8", "457")
            self._extract_beta_from_tuples(values_457, energies, intensities)

        if not energies and values_455 and len(values_455) >= 2:
            for i in range(0, len(values_455) - 1, 2):
                e_val = float(values_455[i]) / 1e6  # eV -> MeV
                i_val = float(values_455[i + 1])
                if e_val >= 0 and i_val >= 0:
                    energies.append(e_val)
                    intensities.append(i_val)

        if not energies:
            return None

        energy_arr = np.array(energies)
        intensity_arr = np.array(intensities)
        endpoint = float(np.max(energy_arr)) if len(energy_arr) > 0 else 0.0
        total_int = np.sum(intensity_arr)
        avg = (
            float(np.sum(energy_arr * intensity_arr) / total_int)
            if total_int > 0
            else 0.0
        )
        return BetaSpectrum(
            energy=energy_arr,
            intensity=intensity_arr,
            endpoint_energy=endpoint,
            average_energy=avg,
        )

    def _extract_beta_from_tuples(
        self,
        values: List[float],
        energies: List[float],
        intensities: List[float],
    ) -> None:
        """Extract (E, I) from 6-tuples (RTYP=1/8, RFS, Q, D, BR, DBR). Q in eV, BR intensity."""
        for i in range(0, len(values) - 5, 6):
            try:
                rtyp = int(round(values[i]))
            except (ValueError, TypeError):
                continue
            if rtyp in (1, 8):  # Beta- or beta+
                e_val = float(values[i + 2]) / 1e6  # eV -> MeV
                i_val = float(values[i + 4])  # BR = intensity
                if e_val >= 0 and i_val >= 0:
                    energies.append(e_val)
                    intensities.append(i_val)
