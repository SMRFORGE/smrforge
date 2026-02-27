"""
Tests for MSR flow-through burnup.
"""

import numpy as np
import pytest

from smrforge.burnup.msr_burnup import MSRBurnupOptions, MSRBurnupSolver
from smrforge.core.reactor_core import DecayData, Nuclide


class TestMSRBurnupSolver:
    """Tests for MSRBurnupSolver."""

    def test_step_advances_concentrations(self):
        """step() advances concentrations with flow-through correction."""
        A = np.array([[-0.01, 0], [0.01, -0.02]])
        n0 = np.array([1e20, 0.0])
        nuclides = [Nuclide(92, 235), Nuclide(92, 236)]
        opts = MSRBurnupOptions(
            core_residence_time=10.0,
            primary_loop_time=60.0,
            n_passes=1,
        )
        solver = MSRBurnupSolver(A, n0, nuclides, opts)
        n1 = solver.step(1000.0)
        assert np.all(n1 >= 0)
        assert not np.allclose(n1, n0)

    def test_create_from_decay_chains_without_decay_data(self):
        """create_from_decay_chains works with decay_data=None."""
        nuclides = [Nuclide(92, 235), Nuclide(92, 236)]
        n0 = np.array([1e20, 0.0])
        solver = MSRBurnupSolver.create_from_decay_chains(
            nuclides, n0, decay_data=None
        )
        assert isinstance(solver, MSRBurnupSolver)
        assert solver.n.shape == (2,)
        np.testing.assert_array_almost_equal(solver.n, n0)

    def test_create_from_decay_chains_with_decay_data(self):
        """create_from_decay_chains builds A from DecayData."""
        nuclides = [Nuclide(92, 235), Nuclide(92, 236)]
        n0 = np.array([1e20, 0.0])
        decay = DecayData()
        solver = MSRBurnupSolver.create_from_decay_chains(
            nuclides, n0, decay_data=decay
        )
        assert isinstance(solver, MSRBurnupSolver)
        assert solver.A.shape == (2, 2)

    def test_create_from_decay_chains_custom_options(self):
        """create_from_decay_chains accepts custom MSRBurnupOptions."""
        nuclides = [Nuclide(1, 1)]
        n0 = np.array([1e20])
        opts = MSRBurnupOptions(
            core_residence_time=5.0,
            primary_loop_time=30.0,
            n_passes=2,
        )
        solver = MSRBurnupSolver.create_from_decay_chains(
            nuclides, n0, decay_data=None, options=opts
        )
        assert solver.options.core_residence_time == 5.0
        assert solver.options.n_passes == 2
