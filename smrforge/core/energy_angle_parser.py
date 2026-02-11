"""
ENDF MF=6 (Energy-Angle Distributions) Parser.

Parses energy-angle distribution data from ENDF-6 format files (MF=6).
This data is essential for accurate anisotropic scattering calculations,
providing Legendre moments or angular distributions for scattering reactions.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ..utils.logging import get_logger
from .reactor_core import Nuclide

logger = get_logger("smrforge.core.energy_angle_parser")


@dataclass
class AngularDistribution:
    """
    Angular distribution data for a specific incident energy.

    Attributes:
        incident_energy: Incident neutron energy [eV]
        distribution_type: Type of distribution (0=isotropic, 1=Legendre, 2=tabular)
        legendre_coefficients: Legendre coefficients [a0, a1, a2, ...] (if type=1)
        angle_cosines: Scattering angle cosines μ (if type=2)
        probabilities: Probability density f(μ) (if type=2)
    """

    incident_energy: float  # eV
    distribution_type: int  # 0=isotropic, 1=Legendre, 2=tabular
    legendre_coefficients: Optional[np.ndarray] = None  # [a0, a1, a2, ...]
    angle_cosines: Optional[np.ndarray] = None  # μ values
    probabilities: Optional[np.ndarray] = None  # f(μ) values


@dataclass
class EnergyAngleData:
    """
    Energy-angle distribution data for a scattering reaction.

    Contains angular distributions as a function of incident energy.
    Used to compute Legendre moments for anisotropic scattering.

    Attributes:
        nuclide: Nuclide instance
        mt_number: Material table number (typically 2 for elastic scattering)
        reaction_name: Reaction name
        incident_energies: Incident energy points [eV]
        angular_distributions: List of AngularDistribution for each energy
        law_type: Distribution law type (1=continuum, 2=discrete)
    """

    nuclide: Nuclide
    mt_number: int
    reaction_name: str
    incident_energies: np.ndarray  # [eV]
    angular_distributions: List[AngularDistribution]
    law_type: int = 1  # 1=continuum, 2=discrete

    def get_legendre_moments(
        self, incident_energy: float, max_order: int = 2
    ) -> Optional[np.ndarray]:
        """
        Get Legendre moments for a given incident energy.

        Args:
            incident_energy: Incident neutron energy [eV]
            max_order: Maximum Legendre order (0=P0, 1=P1, 2=P2, ...)

        Returns:
            Legendre moments [a0, a1, a2, ...] or None if not available
        """
        # Find closest incident energy
        idx = np.argmin(np.abs(self.incident_energies - incident_energy))
        dist = self.angular_distributions[idx]

        if dist.distribution_type == 1 and dist.legendre_coefficients is not None:
            # Return requested number of coefficients
            n_coeffs = min(max_order + 1, len(dist.legendre_coefficients))
            return dist.legendre_coefficients[:n_coeffs]
        elif dist.distribution_type == 2:
            # Convert tabular distribution to Legendre moments
            return self._tabular_to_legendre(dist, max_order)

        return None

    def _tabular_to_legendre(
        self, dist: AngularDistribution, max_order: int
    ) -> np.ndarray:
        """
        Convert tabular angular distribution to Legendre moments.

        Uses numerical integration of P_l(μ) * f(μ) dμ.
        """
        if dist.angle_cosines is None or dist.probabilities is None:
            return np.zeros(max_order + 1)

        mu = dist.angle_cosines
        f_mu = dist.probabilities

        # Normalize probability distribution
        norm = np.trapz(f_mu, mu)
        if norm > 0:
            f_mu = f_mu / norm

        # Compute Legendre moments
        moments = np.zeros(max_order + 1)

        for l in range(max_order + 1):
            # Compute P_l(μ) using recurrence relation
            if l == 0:
                P_l = np.ones_like(mu)
            elif l == 1:
                P_l = mu
            else:
                # Recurrence: (l+1) * P_{l+1}(μ) = (2l+1) * μ * P_l(μ) - l * P_{l-1}(μ)
                P_prev = np.ones_like(mu)  # P_0
                P_curr = mu  # P_1
                for k in range(2, l + 1):
                    P_next = ((2 * k - 1) * mu * P_curr - (k - 1) * P_prev) / k
                    P_prev = P_curr
                    P_curr = P_next
                P_l = P_curr

            # Integrate: a_l = (2l+1)/2 * ∫ P_l(μ) * f(μ) dμ
            integrand = P_l * f_mu
            integral = np.trapz(integrand, mu)
            moments[l] = (2 * l + 1) / 2.0 * integral

        # P0 should be 1.0 for normalized distribution (a0 = 1/2 * ∫ P0(μ) * f(μ) dμ = 1/2 * ∫ f(μ) dμ = 1/2)
        # But we want P0 = 1.0, so we normalize
        if moments[0] > 0:
            moments = (
                moments / moments[0] * 0.5
            )  # Normalize so P0 = 0.5 (standard normalization)

        return moments


class ENDFEnergyAngleParser:
    """
    Parser for ENDF MF=6 (energy-angle distributions) data.

    Parses angular distribution data from ENDF-6 format files, extracting:
    - Legendre coefficients for anisotropic scattering
    - Tabular angular distributions
    - Energy-dependent angular distributions

    Usage:
        >>> parser = ENDFEnergyAngleParser()
        >>> endf_file = Path("U238.endf")
        >>> energy_angle_data = parser.parse_file(endf_file, mt=2)  # Elastic scattering
        >>>
        >>> # Get Legendre moments at 1 MeV
        >>> moments = energy_angle_data.get_legendre_moments(1e6, max_order=2)
        >>> print(f"P0, P1, P2 moments: {moments}")
    """

    def __init__(self):
        """Initialize the energy-angle parser."""
        self.mt_to_reaction = {
            2: "elastic",
            4: "inelastic",
            16: "n,2n",
            18: "fission",
        }

    def parse_file(
        self, filepath: Path, mt: int = 2, nuclide: Optional[Nuclide] = None
    ) -> Optional[EnergyAngleData]:
        """
        Parse energy-angle distribution data from an ENDF file.

        Args:
            filepath: Path to ENDF-6 format file
            mt: Material table number (typically 2 for elastic scattering)
            nuclide: Optional Nuclide instance (extracted from filename if not provided)

        Returns:
            EnergyAngleData instance or None if parsing fails
        """
        if not filepath.exists():
            logger.warning(f"ENDF file not found: {filepath}")
            return None

        # Extract nuclide from filename if not provided
        if nuclide is None:
            nuclide = self._parse_filename(filepath.name)
            if nuclide is None:
                logger.warning(
                    f"Could not extract nuclide from filename: {filepath.name}"
                )
                return None

        try:
            with open(filepath, "r") as f:
                lines = f.readlines()

            # Find MF=6, MT=mt section
            mf6_section = self._find_mf6_section(lines, mt)
            if mf6_section is None:
                logger.debug(f"MF=6, MT={mt} section not found in {filepath}")
                return None

            # Parse the section
            energy_angle_data = self._parse_mf6_section(lines, mf6_section, mt, nuclide)

            return energy_angle_data

        except Exception as e:
            logger.warning(f"Failed to parse MF=6 data from {filepath}: {e}")
            return None

    def _find_mf6_section(self, lines: List[str], mt: int) -> Optional[int]:
        """Find the start index of MF=6, MT=mt section."""
        for i, line in enumerate(lines):
            if len(line) < 75:
                continue

            try:
                mf = int(line[70:72].strip())
                mt_line = int(line[72:75].strip())

                if mf == 6 and mt_line == mt:
                    return i
            except (ValueError, IndexError):
                continue

        return None

    def _parse_mf6_section(
        self, lines: List[str], start_idx: int, mt: int, nuclide: Nuclide
    ) -> Optional[EnergyAngleData]:
        """
        Parse MF=6 section starting at start_idx.

        ENDF MF=6 format:
        - Control record: ZA, AWR, LCT, LAW, ... (line at start_idx)
        - Sub-sections for each incident energy
        - Each sub-section has angular distribution data
        """
        if start_idx >= len(lines):
            return None

        # Parse control record
        control_line = lines[start_idx]
        try:
            # ENDF format: 6 values per line (6E11.0)
            za = float(control_line[0:11])
            awr = float(control_line[11:22])
            lct = int(float(control_line[22:33]))  # LAB or CM frame
            law = int(float(control_line[33:44]))  # Distribution law
        except (ValueError, IndexError):
            logger.warning("Failed to parse MF=6 control record")
            return None

        # Parse incident energy points and angular distributions
        incident_energies = []
        angular_distributions = []

        i = start_idx + 1

        # Parse sub-sections (one per incident energy)
        while i < len(lines):
            line = lines[i]

            # Check for end of section (MF=0 or different MF)
            if len(line) >= 75:
                try:
                    mf_check = int(line[70:72].strip())
                    if mf_check != 6:
                        break  # End of MF=6 section
                except (ValueError, IndexError):
                    pass

            # Parse incident energy and distribution
            try:
                # First line: incident energy and number of points
                if len(line) < 22:
                    i += 1
                    continue

                e_incident = float(line[0:11])  # Incident energy
                n_points = int(float(line[11:22]))  # Number of points

                # Check if this is a valid energy point
                if e_incident > 0 and n_points > 0:
                    incident_energies.append(e_incident)

                    # Parse angular distribution
                    dist = self._parse_angular_distribution(lines, i, n_points, law)
                    if dist:
                        angular_distributions.append(dist)

                    # Skip to next incident energy
                    # Each distribution takes multiple lines
                    i += self._count_distribution_lines(n_points, law)
                else:
                    i += 1

            except (ValueError, IndexError):
                i += 1
                continue

        if not incident_energies:
            return None

        reaction_name = self.mt_to_reaction.get(mt, f"mt{mt}")

        return EnergyAngleData(
            nuclide=nuclide,
            mt_number=mt,
            reaction_name=reaction_name,
            incident_energies=np.array(incident_energies),
            angular_distributions=angular_distributions,
            law_type=law,
        )

    def _parse_angular_distribution(
        self, lines: List[str], start_idx: int, n_points: int, law: int
    ) -> Optional[AngularDistribution]:
        """
        Parse angular distribution for one incident energy.

        Args:
            lines: File lines
            start_idx: Start index of distribution data
            n_points: Number of points in distribution
            law: Distribution law type
        """
        if start_idx >= len(lines):
            return None

        # Get incident energy from first line
        try:
            line = lines[start_idx]
            e_incident = float(line[0:11])
        except (ValueError, IndexError):
            return None

        # Parse based on law type
        if law == 1:  # Continuum energy-angle distribution
            # LAW=1: Tabular distribution
            return self._parse_tabular_distribution(
                lines, start_idx, e_incident, n_points
            )
        elif law == 2:  # Discrete two-body scattering
            # LAW=2: Simple two-body kinematics
            return AngularDistribution(
                incident_energy=e_incident,
                distribution_type=0,  # Isotropic for now
            )
        elif law == 7:  # Legendre coefficients
            # LAW=7: Legendre polynomial representation
            return self._parse_legendre_distribution(
                lines, start_idx, e_incident, n_points
            )
        else:
            # Unknown law type - return isotropic
            logger.debug(f"Unknown distribution law type: {law}, using isotropic")
            return AngularDistribution(
                incident_energy=e_incident,
                distribution_type=0,  # Isotropic
            )

    def _parse_tabular_distribution(
        self, lines: List[str], start_idx: int, e_incident: float, n_points: int
    ) -> Optional[AngularDistribution]:
        """Parse tabular angular distribution (LAW=1)."""
        mu_values = []
        prob_values = []

        i = start_idx + 1
        values_read = 0

        while i < len(lines) and values_read < n_points * 2:  # μ and f(μ) pairs
            line = lines[i]

            if len(line) < 66:
                i += 1
                continue

            try:
                # Read up to 6 values per line (6E11.0 format)
                for j in range(0, 6):
                    if values_read >= n_points * 2:
                        break

                    start_col = j * 11
                    end_col = start_col + 11

                    if end_col > len(line):
                        break

                    val_str = line[start_col:end_col].strip()
                    if val_str:
                        val = float(val_str)

                        if values_read % 2 == 0:
                            mu_values.append(val)  # μ (cosine of angle)
                        else:
                            prob_values.append(val)  # f(μ) (probability)

                        values_read += 1

                i += 1

            except (ValueError, IndexError):
                i += 1
                continue

        if len(mu_values) == len(prob_values) and len(mu_values) > 0:
            return AngularDistribution(
                incident_energy=e_incident,
                distribution_type=2,  # Tabular
                angle_cosines=np.array(mu_values),
                probabilities=np.array(prob_values),
            )

        return None

    def _parse_legendre_distribution(
        self, lines: List[str], start_idx: int, e_incident: float, n_coeffs: int
    ) -> Optional[AngularDistribution]:
        """Parse Legendre coefficient distribution (LAW=7)."""
        coeffs = []

        i = start_idx + 1
        values_read = 0

        while i < len(lines) and values_read < n_coeffs:
            line = lines[i]

            if len(line) < 66:
                i += 1
                continue

            try:
                # Read up to 6 values per line
                for j in range(0, 6):
                    if values_read >= n_coeffs:
                        break

                    start_col = j * 11
                    end_col = start_col + 11

                    if end_col > len(line):
                        break

                    val_str = line[start_col:end_col].strip()
                    if val_str:
                        coeffs.append(float(val_str))
                        values_read += 1

                i += 1

            except (ValueError, IndexError):
                i += 1
                continue

        if len(coeffs) > 0:
            return AngularDistribution(
                incident_energy=e_incident,
                distribution_type=1,  # Legendre
                legendre_coefficients=np.array(coeffs),
            )

        return None

    def _count_distribution_lines(self, n_points: int, law: int) -> int:
        """Estimate number of lines needed for distribution data."""
        if law == 1:  # Tabular
            # Each line has 6 values, need n_points * 2 values (μ and f(μ))
            return 1 + (n_points * 2 + 5) // 6
        elif law == 7:  # Legendre
            # Each line has 6 coefficients
            return 1 + (n_points + 5) // 6
        else:
            return 1

    def _parse_filename(self, filename: str) -> Optional[Nuclide]:
        """
        Extract nuclide from ENDF filename.

        Examples:
        - "U238.endf" -> Nuclide(Z=92, A=238)
        - "092_U_238.endf" -> Nuclide(Z=92, A=238)
        """
        from .constants import ELEMENT_SYMBOLS

        # Try various filename patterns
        name_upper = filename.upper().replace(".ENDF", "").replace(".ENDF6", "")

        # Pattern: "U238" or "U-238"
        # ELEMENT_SYMBOLS is Dict[int, str] mapping Z -> symbol
        for Z, symbol in ELEMENT_SYMBOLS.items():
            if isinstance(symbol, str) and name_upper.startswith(symbol):
                remainder = name_upper[len(symbol) :].replace("-", "").replace("_", "")
                try:
                    A = int(remainder)
                    return Nuclide(Z=Z, A=A)
                except ValueError:
                    continue

        # Pattern: "092_U_238"
        parts = name_upper.split("_")
        if len(parts) >= 3:
            try:
                Z = int(parts[0])
                A = int(parts[2])
                return Nuclide(Z=Z, A=A)
            except ValueError:
                pass

        return None


def get_energy_angle_data(
    nuclide: Nuclide,
    mt: int = 2,
    cache: Optional[Any] = None,
) -> Optional[EnergyAngleData]:
    """
    Get energy-angle distribution data for a nuclide.

    Args:
        nuclide: Nuclide instance
        mt: Material table number (typically 2 for elastic scattering)
        cache: Optional NuclearDataCache instance

    Returns:
        EnergyAngleData instance or None if not available
    """
    from .reactor_core import NuclearDataCache

    if cache is None:
        cache = NuclearDataCache()

    # Find ENDF file
    endf_file = cache._find_local_endf_file(nuclide)
    if endf_file is None:
        return None

    # Parse MF=6 data
    parser = ENDFEnergyAngleParser()
    return parser.parse_file(endf_file, mt=mt, nuclide=nuclide)
