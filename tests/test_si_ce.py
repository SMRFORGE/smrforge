"""Tests for SI-CE depletion integrator."""

import numpy as np
import pytest

from smrforge.burnup.si_ce import si_ce_available, si_ce_depletion_step


class TestSICEIntegrator:
    """Tests for SI-CE integrator."""

    def test_si_ce_available(self):
        """Test si_ce_available returns True."""
        assert si_ce_available() is True

    def test_si_ce_depletion_step(self):
        """Test SI-CE depletion step."""
        A = np.array([[-0.1, 0.0], [0.1, -0.2]])
        n = np.array([1.0, 0.5])
        dt = 1.0
        n_new = si_ce_depletion_step(A, n, dt)
        assert n_new.shape == n.shape
        assert np.all(n_new >= 0)
