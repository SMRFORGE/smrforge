"""Tests for predictor-corrector depletion integrator."""

import numpy as np
import pytest

from smrforge.burnup.predictor_corrector import pc_depletion_step


class TestPredictorCorrectorDepletion:
    """Tests for pc_depletion_step."""

    def test_pc_depletion_step(self):
        """Test predictor-corrector depletion step."""
        A = np.array([[-0.1, 0.05], [0.1, -0.05]])
        n = np.array([1.0, 0.5])
        dt = 1.0
        n_new = pc_depletion_step(A, n, dt)
        assert n_new.shape == n.shape
        assert np.all(n_new >= 0)
        assert np.sum(n_new) <= np.sum(n) * 1.1  # Approximate conservation

    def test_pc_vs_si_ce_small_step(self):
        """PC and SI-CE should be similar for small step."""
        from smrforge.burnup.si_ce import si_ce_depletion_step

        A = np.array([[-0.01, 0.005], [0.01, -0.005]])
        n = np.array([1.0, 0.5])
        dt = 0.1
        n_pc = pc_depletion_step(A, n, dt)
        n_si = si_ce_depletion_step(A, n, dt)
        np.testing.assert_allclose(n_pc, n_si, rtol=0.1)
