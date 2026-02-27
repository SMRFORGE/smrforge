"""Tests for S2/S4 discrete ordinates transport solver (1D, 2D r-z, 3D, hexagonal)."""

import numpy as np
import pytest

from smrforge.neutronics.sn_transport import (
    SN2DCylindricalResult,
    SN2DCylindricalSolver,
    SN2DHexagonalResult,
    SN2DHexagonalSolver,
    SN3DCartesianResult,
    SN3DCartesianSolver,
    SNTransportResult,
    SNTransportSolver,
)


class TestSNTransportSolver:
    """Tests for SNTransportSolver."""

    def test_s2_init(self):
        """Test S2 solver initialization."""
        n = 10
        solver = SNTransportSolver(
            n_cells=n,
            sigma_t=0.5,
            sigma_s=0.4,
            nu_sigma_f=0.05,
            order=2,
        )
        assert solver.n_cells == n
        assert solver.n_angles == 2

    def test_s4_init(self):
        """Test S4 solver initialization."""
        solver = SNTransportSolver(
            n_cells=20,
            sigma_t=np.ones(20) * 0.5,
            sigma_s=np.ones(20) * 0.4,
            nu_sigma_f=np.ones(20) * 0.05,
            order=4,
        )
        assert solver.n_angles == 4

    def test_solve_eigenvalue(self):
        """Test k-eigenvalue solve."""
        solver = SNTransportSolver(
            n_cells=10,
            sigma_t=0.5,
            sigma_s=0.4,
            nu_sigma_f=0.08,
            order=2,
        )
        result = solver.solve_eigenvalue(max_iter=100)
        assert isinstance(result, SNTransportResult)
        assert result.scalar_flux.shape[0] == 10
        assert result.k_eff > 0


class TestSN2DCylindricalSolver:
    """Tests for 2D r-z cylindrical SN transport."""

    def test_init_and_solve(self):
        """Test 2D cylindrical solver init and eigenvalue solve."""
        solver = SN2DCylindricalSolver(
            n_r=4,
            n_z=4,
            sigma_t=0.5,
            sigma_s=0.4,
            nu_sigma_f=0.1,
            order=2,
        )
        result = solver.solve_eigenvalue(max_iter=50)
        assert isinstance(result, SN2DCylindricalResult)
        assert result.scalar_flux.shape == (4, 4)
        assert result.k_eff > 0
        assert 0.5 < result.k_eff < 1.5


class TestSN3DCartesianSolver:
    """Tests for 3D Cartesian SN transport."""

    def test_init_and_solve(self):
        """Test 3D Cartesian solver init and eigenvalue solve."""
        solver = SN3DCartesianSolver(
            n_x=3,
            n_y=3,
            n_z=3,
            sigma_t=0.5,
            sigma_s=0.4,
            nu_sigma_f=0.1,
            order=2,
        )
        result = solver.solve_eigenvalue(max_iter=50)
        assert isinstance(result, SN3DCartesianResult)
        assert result.scalar_flux.shape == (3, 3, 3)
        assert result.k_eff > 0
        assert 0.5 < result.k_eff < 1.5


class TestSN2DHexagonalSolver:
    """Tests for 2D hexagonal SN transport."""

    def test_init_and_solve(self):
        """Test hexagonal solver init and eigenvalue solve."""
        solver = SN2DHexagonalSolver(
            n_rings=2,
            sigma_t=0.5,
            sigma_s=0.4,
            nu_sigma_f=0.1,
            order=2,
        )
        result = solver.solve_eigenvalue(max_iter=50)
        assert isinstance(result, SN2DHexagonalResult)
        assert result.scalar_flux.size == solver.n_cells
        assert result.k_eff > 0
        assert 0.5 < result.k_eff < 1.5
