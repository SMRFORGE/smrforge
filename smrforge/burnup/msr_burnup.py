"""
MSR (Molten Salt Reactor) flow-through burnup.

Circulating fuel: fuel flows through core with residence time.
Different from solid fuel: no fixed lattice, flow homogenizes composition.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np

from ..core.reactor_core import DecayData, Nuclide
from ..utils.logging import get_logger

logger = get_logger("smrforge.burnup.msr")


@dataclass
class MSRBurnupOptions:
    """Options for MSR flow-through burnup."""

    core_residence_time: float  # seconds - time fuel spends in core per pass
    primary_loop_time: float  # seconds - full loop circulation time
    n_passes: int = 1  # Number of core passes per depletion step
    power_density: float = 1e6  # W/cm³


class MSRBurnupSolver:
    """
    Burnup solver for circulating-fuel MSR.

    Models flow-through: fuel composition is spatially averaged in core,
    with residence time determining exposure per pass.
    """

    def __init__(
        self,
        transmutation_matrix: np.ndarray,
        initial_concentrations: np.ndarray,
        nuclides: List[Nuclide],
        options: MSRBurnupOptions,
    ):
        self.A = transmutation_matrix
        self.n = np.array(initial_concentrations, dtype=float)
        self.nuclides = nuclides
        self.options = options

    def step(self, dt: float) -> np.ndarray:
        """
        Advance one time step with flow-through correction.

        Effective exposure = (core_residence_time / primary_loop_time) * dt
        per pass, summed over passes.
        """
        effective_dt = dt * self.options.n_passes * (
            self.options.core_residence_time / self.options.primary_loop_time
        )
        from scipy.sparse import csr_matrix
        from scipy.sparse.linalg import expm_multiply

        A_sparse = csr_matrix(self.A)
        self.n = expm_multiply(A_sparse, self.n, start=0, stop=effective_dt, num=2)[-1]
        self.n = np.maximum(self.n, 0.0)
        return self.n.copy()

    @classmethod
    def create_from_decay_chains(
        cls,
        nuclides: List[Nuclide],
        initial_concentrations: np.ndarray,
        decay_data: Optional[DecayData] = None,
        options: Optional[MSRBurnupOptions] = None,
    ) -> "MSRBurnupSolver":
        """
        Create MSR burnup solver from nuclide list and decay data.

        Builds transmutation matrix from decay constants (Bateman chains).
        For activation-only (no neutron capture), use this; for full burnup
        combine with BurnupSolver or provide pre-built A matrix.

        Args:
            nuclides: List of Nuclide instances
            initial_concentrations: [n_nuclides] atoms/cm³
            decay_data: DecayData for half-lives and branching
            options: MSRBurnupOptions; default if not provided

        Returns:
            MSRBurnupSolver instance
        """
        if decay_data is not None:
            A_sparse = decay_data.build_decay_matrix(nuclides)
            A = A_sparse.toarray()
        else:
            A = np.zeros((len(nuclides), len(nuclides)))
        if options is None:
            options = MSRBurnupOptions(
                core_residence_time=10.0,
                primary_loop_time=60.0,
            )
        return cls(
            transmutation_matrix=A,
            initial_concentrations=np.asarray(initial_concentrations, dtype=float),
            nuclides=nuclides,
            options=options,
        )
