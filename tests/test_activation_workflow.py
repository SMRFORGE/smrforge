"""
Tests for R2S-style activation workflow.
"""

import numpy as np
import pytest

from smrforge.safety.activation import (
    PhotonSourceMesh,
    R2SResult,
    compute_activation_photon_source,
    r2s_available,
    r2s_shutdown_dose,
)


class TestActivationWorkflow:
    """Tests for activation (R2S) workflow."""

    def test_r2s_available_returns_bool(self):
        """r2s_available returns a boolean."""
        assert isinstance(r2s_available(), bool)

    def test_compute_activation_photon_source_shape(self):
        """compute_activation_photon_source returns list of PhotonSourceMesh."""
        flux = np.ones((2, 3, 5))  # nz, nr, ng
        sigma = np.ones((2, 5))
        comp = np.zeros((2, 3), dtype=int)
        times = np.array([0, 3600])
        sources = compute_activation_photon_source(
            flux, sigma, comp, times
        )
        assert len(sources) == 2
        for s in sources:
            assert isinstance(s, PhotonSourceMesh)
            assert s.source_strength.shape[0] == 6  # 2*3 cells
            assert s.decay_time in times

    def test_r2s_shutdown_dose_returns_result(self):
        """r2s_shutdown_dose returns R2SResult."""
        flux = np.ones((2, 3, 5))
        sigma = np.ones((2, 5))
        comp = np.zeros((2, 3), dtype=int)
        detectors = np.array([[0.5, 1.0, 0.0]])
        times = np.array([0, 3600])
        result = r2s_shutdown_dose(
            flux, sigma, comp, detectors, times
        )
        assert isinstance(result, R2SResult)
        assert result.dose_rate.shape == (1,)
        assert result.dose_vs_time.shape == (1, 2)

    def test_r2s_shutdown_dose_multiple_detectors(self):
        """r2s_shutdown_dose handles multiple detectors."""
        flux = np.ones((2, 2, 4))
        sigma = np.ones((1, 4))
        comp = np.zeros((2, 2), dtype=int)
        detectors = np.array([[0, 0, 0], [1, 10, 0]])
        times = np.array([0])
        result = r2s_shutdown_dose(flux, sigma, comp, detectors, times)
        assert result.dose_rate.shape == (2,)
        assert result.detector_positions.shape[0] == 2
