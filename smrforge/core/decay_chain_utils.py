"""
Decay chain utilities for SMR burnup and inventory tracking.

Provides enhanced decay chain support including:
- Decay chain construction from nuclide lists
- Chain visualization
- Bateman equation solving
- Chain simplification and truncation
"""

from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy.sparse.linalg import expm_multiply

from ..utils.logging import get_logger
from .reactor_core import DecayData, Nuclide, NuclideInventoryTracker

logger = get_logger("smrforge.core.decay_chain_utils")


class DecayChain:
    """
    Enhanced decay chain representation with visualization and analysis.

    Represents a connected decay chain of nuclides with parent-daughter
    relationships. Provides utilities for chain analysis and evolution.

    Attributes:
        nuclides: List of nuclides in the chain (ordered)
        parent_daughters: Dictionary mapping parent -> list of daughters
        decay_data: DecayData instance for decay constants
    """

    def __init__(
        self,
        nuclides: List[Nuclide],
        decay_data: Optional[DecayData] = None,
    ):
        """
        Initialize decay chain.

        Args:
            nuclides: List of nuclides in the chain
            decay_data: Optional DecayData instance (creates new if None)
        """
        from .reactor_core import DecayData as DecayDataClass

        self.nuclides = nuclides
        self.decay_data = decay_data if decay_data is not None else DecayDataClass()
        self.parent_daughters: Dict[Nuclide, List[Nuclide]] = {}

        # Build parent-daughter relationships
        self._build_relationships()

    def _build_relationships(self):
        """Build parent-daughter relationships from decay data."""
        for parent in self.nuclides:
            daughters = self.decay_data._get_daughters(parent)
            self.parent_daughters[parent] = [
                d[0] for d in daughters if d[0] in self.nuclides
            ]

    def build_decay_matrix(self) -> np.ndarray:
        """
        Build decay matrix for this chain.

        Returns:
            Sparse decay matrix (scipy.sparse.csr_matrix)
        """
        return self.decay_data.build_decay_matrix(self.nuclides)

    def evolve(
        self,
        initial_concentrations: np.ndarray,
        time: float,
    ) -> np.ndarray:
        """
        Evolve decay chain over time using Bateman equations.

        Args:
            initial_concentrations: Initial atom densities [n_nuclides]
            time: Evolution time [seconds]

        Returns:
            Final concentrations [n_nuclides]
        """
        A = self.build_decay_matrix()
        result = expm_multiply(
            A, initial_concentrations, start=0, stop=time, num=2, endpoint=True
        )
        return result[-1]  # Return final state

    def get_chain_depth(self, nuclide: Nuclide) -> int:
        """
        Get depth of nuclide in decay chain (generation number).

        Args:
            nuclide: Nuclide to find depth for

        Returns:
            Depth (0 = initial, 1 = first generation, etc.)
        """
        if nuclide not in self.nuclides:
            return -1

        # Simple depth calculation (would need full chain structure for accurate)
        return 0  # Placeholder

    def get_chain_string(self) -> str:
        """
        Get string representation of decay chain.

        Returns:
            String showing parent -> daughter relationships
        """
        lines = []
        for parent in self.nuclides:
            daughters = self.parent_daughters.get(parent, [])
            if daughters:
                daughter_names = ", ".join(d.name for d in daughters)
                lines.append(f"{parent.name} -> {daughter_names}")
            else:
                lines.append(f"{parent.name} -> (stable)")

        return "\n".join(lines)


def build_fission_product_chain(
    parent: Nuclide,
    max_depth: int = 5,
    decay_data: Optional[DecayData] = None,
) -> DecayChain:
    """
    Build decay chain for a fission product starting from parent.

    Args:
        parent: Parent nuclide (fission product)
        max_depth: Maximum chain depth to include
        decay_data: Optional DecayData instance

    Returns:
        DecayChain instance
    """
    from .reactor_core import DecayData as DecayDataClass

    if decay_data is None:
        decay_data = DecayDataClass()

    # Collect nuclides in chain
    nuclides = [parent]
    visited = {parent}

    def add_daughters(nuc: Nuclide, depth: int):
        if depth >= max_depth:
            return
        daughters = decay_data._get_daughters(nuc)
        for daughter, _ in daughters:
            if daughter not in visited:
                nuclides.append(daughter)
                visited.add(daughter)
                add_daughters(daughter, depth + 1)

    add_daughters(parent, 0)

    return DecayChain(nuclides, decay_data)


def solve_bateman_equations(
    decay_matrix: np.ndarray,
    initial_concentrations: np.ndarray,
    times: np.ndarray,
) -> np.ndarray:
    """
    Solve Bateman equations for decay chain evolution.

    Solves dN/dt = A*N where A is the decay matrix.

    Args:
        decay_matrix: Decay matrix (sparse or dense)
        initial_concentrations: Initial atom densities [n_nuclides]
        times: Time points [seconds] [n_times]

    Returns:
        Concentrations at each time point [n_times, n_nuclides]
    """
    if hasattr(decay_matrix, "toarray"):
        # Sparse matrix
        decay_matrix = decay_matrix.toarray()

    # Use matrix exponential
    if len(times) == 1:
        # Single time point
        result = expm_multiply(decay_matrix * times[0], initial_concentrations)
    else:
        # Multiple time points
        result = expm_multiply(
            decay_matrix,
            initial_concentrations,
            start=times[0],
            stop=times[-1],
            num=len(times),
            endpoint=True,
        )
    return result


def get_prompt_delayed_chi_for_transient(
    cache,
    nuclide: Nuclide,
    group_structure: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, Dict[str, np.ndarray]]:
    """
    Get prompt and delayed chi for transient analysis.

    Convenience function that combines prompt/delayed chi extraction
    with delayed neutron data for complete transient analysis setup.

    Args:
        cache: NuclearDataCache instance
        nuclide: Nuclide instance
        group_structure: Energy group boundaries [eV]

    Returns:
        Tuple of:
        - chi_prompt: Prompt fission spectrum [n_groups]
        - chi_delayed: Delayed fission spectrum [n_groups]
        - delayed_data: Dictionary with delayed neutron parameters:
            - 'beta': Total delayed fraction
            - 'beta_i': Per-group delayed fractions [6 groups]
            - 'lambda_i': Decay constants [1/s] [6 groups]

    Example:
        >>> from smrforge.core.reactor_core import NuclearDataCache, Nuclide
        >>> from smrforge.core.decay_chain_utils import get_prompt_delayed_chi_for_transient
        >>>
        >>> cache = NuclearDataCache()
        >>> u235 = Nuclide(Z=92, A=235)
        >>> group_structure = np.logspace(7, -5, 26)
        >>>
        >>> chi_p, chi_d, delayed = get_prompt_delayed_chi_for_transient(
        ...     cache, u235, group_structure
        ... )
        >>>
        >>> # Use for transient solver
        >>> beta_total = delayed['beta']
        >>> lambda_i = delayed['lambda_i']
    """
    from .endf_extractors import extract_chi_prompt_delayed
    from .reactor_core import get_delayed_neutron_data

    # Get prompt/delayed chi
    chi_prompt, chi_delayed = extract_chi_prompt_delayed(
        cache, nuclide, group_structure
    )

    # Get delayed neutron data
    delayed_data = get_delayed_neutron_data(cache, nuclide)

    if delayed_data is None:
        # Use default values
        delayed_data = {
            "beta": 0.0065,
            "beta_i": np.array([2.13e-4, 1.43e-3, 1.27e-3, 2.56e-3, 7.48e-4, 2.73e-4]),
            "lambda_i": np.array([0.0124, 0.0305, 0.111, 0.301, 1.14, 3.01]),
        }

    return chi_prompt, chi_delayed, delayed_data


def collapse_with_adjoint_for_sensitivity(
    fine_group_structure: np.ndarray,
    coarse_group_structure: np.ndarray,
    fine_xs: np.ndarray,
    fine_flux: np.ndarray,
    fine_adjoint: np.ndarray,
    reaction: str = "fission",
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Collapse cross-sections with adjoint weighting for sensitivity analysis.

    Convenience function that combines adjoint-weighted collapse with
    sensitivity calculation preparation.

    Args:
        fine_group_structure: Fine-group energy boundaries [eV]
        coarse_group_structure: Coarse-group energy boundaries [eV]
        fine_xs: Fine-group cross-sections [n_fine]
        fine_flux: Fine-group forward flux [n_fine]
        fine_adjoint: Fine-group adjoint flux [n_fine]
        reaction: Reaction type (for logging)

    Returns:
        Tuple of:
        - coarse_xs: Collapsed cross-sections [n_coarse]
        - coarse_adjoint: Collapsed adjoint flux [n_coarse]

    Example:
        >>> from smrforge.core.multigroup_advanced import collapse_with_adjoint_weighting
        >>> from smrforge.core.decay_chain_utils import collapse_with_adjoint_for_sensitivity
        >>>
        >>> fine_groups = np.logspace(7, -5, 100)
        >>> coarse_groups = np.array([2e7, 1e6, 1e5, 1e4, 1e-5])
        >>>
        >>> coarse_xs, coarse_adj = collapse_with_adjoint_for_sensitivity(
        ...     fine_groups, coarse_groups, fine_xs, fine_flux, fine_adjoint
        ... )
    """
    from .multigroup_advanced import collapse_with_adjoint_weighting

    # Collapse with adjoint weighting
    coarse_xs = collapse_with_adjoint_weighting(
        fine_group_structure,
        coarse_group_structure,
        fine_xs,
        fine_flux,
        fine_adjoint,
    )

    # Also collapse adjoint flux for sensitivity calculations
    n_coarse = len(coarse_group_structure) - 1
    n_fine = len(fine_group_structure) - 1
    coarse_adjoint = np.zeros(n_coarse)

    # Map fine groups to coarse groups
    for g_coarse in range(n_coarse):
        e_low = coarse_group_structure[g_coarse]
        e_high = coarse_group_structure[g_coarse + 1]

        # Find fine groups in this coarse group
        fine_in_coarse = []
        for g_fine in range(n_fine):
            e_fine_low = fine_group_structure[g_fine]
            e_fine_high = fine_group_structure[g_fine + 1]

            if e_fine_high > e_low and e_fine_low < e_high:
                dE = min(e_fine_high, e_high) - max(e_fine_low, e_low)
                fine_in_coarse.append((g_fine, dE))

        # Collapse adjoint flux
        if fine_in_coarse:
            total_dE = sum(dE for _, dE in fine_in_coarse)
            coarse_adjoint[g_coarse] = (
                sum(fine_adjoint[g_fine] * dE for g_fine, dE in fine_in_coarse)
                / total_dE
                if total_dE > 0
                else 0.0
            )

    return coarse_xs, coarse_adjoint
