"""Tests for quasi-static spatial dynamics solver."""

import numpy as np
import pytest

from smrforge.safety.quasi_static import (
    QuasiStaticOptions,
    QuasiStaticResult,
    QuasiStaticSolver,
)


class TestQuasiStaticSolver:
    """Tests for QuasiStaticSolver."""

    def test_solver_init(self):
        """Test solver initialization."""
        solver = QuasiStaticSolver(n_nodes=5, beta_total=0.007, gen_time=1e-5)
        assert solver.n_nodes == 5
        assert solver.beta_total == 0.007
        assert solver.gen_time == 1e-5

    def test_solve_sinusoidal_reactivity(self):
        """Test solve with sinusoidal reactivity."""
        solver = QuasiStaticSolver(n_nodes=10, beta_total=0.007, gen_time=1e-5)
        reactivity = lambda t: 0.001 * np.sin(0.1 * t)
        result = solver.solve(
            t_span=(0, 10),
            reactivity_fn=reactivity,
            initial_power=1.0,
            n_times=50,
        )
        assert isinstance(result, QuasiStaticResult)
        assert result.times.shape[0] == 50
        assert result.amplitudes.shape[0] == 50
        assert result.power_history.shape[0] == 50
        assert result.converged is True

    def test_solve_constant_reactivity(self):
        """Test solve with constant positive reactivity."""
        solver = QuasiStaticSolver(n_nodes=5, beta_total=0.007, gen_time=1e-5)
        result = solver.solve(
            t_span=(0, 2),
            reactivity_fn=lambda t: 0.0005,
            initial_power=1.0,
            n_times=20,
        )
        assert result.amplitudes[-1] > result.amplitudes[0]
