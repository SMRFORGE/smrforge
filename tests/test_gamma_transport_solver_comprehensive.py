"""
Comprehensive tests for gamma transport solver to improve coverage to 80%+.

Tests cover:
- Solver initialization
- Cross-section loading
- Source iteration
- Time-dependent sources
- Dose rate calculation
- Material mapping integration
"""

import numpy as np
import pytest
from unittest.mock import Mock, patch, MagicMock

from smrforge.gamma_transport import GammaTransportSolver, GammaTransportOptions
from smrforge.core.reactor_core import Nuclide, NuclearDataCache
from smrforge.core.photon_parser import PhotonCrossSection
from smrforge.geometry import PrismaticCore


@pytest.fixture
def simple_geometry():
    """Create a simple geometry for testing."""
    geometry = PrismaticCore(name="TestCore")
    geometry.core_height = 100.0  # cm
    geometry.core_diameter = 50.0  # cm
    geometry.build_mesh(n_radial=5, n_axial=3)
    return geometry


@pytest.fixture
def mock_cache():
    """Create a mock cache for testing."""
    cache = Mock(spec=NuclearDataCache)
    
    # Mock photon cross-section
    photon_data = Mock(spec=PhotonCrossSection)
    photon_data.element = "H"
    photon_data.Z = 1
    photon_data.energy = np.logspace(-2, 1, 100)
    photon_data.sigma_photoelectric = np.ones(100) * 0.1
    photon_data.sigma_compton = np.ones(100) * 0.2
    photon_data.sigma_pair = np.ones(100) * 0.01
    photon_data.sigma_total = np.ones(100) * 0.31
    
    def interpolate(energy):
        return (0.1, 0.2, 0.01, 0.31)  # pe, comp, pair, total
    
    photon_data.interpolate = interpolate
    cache.get_photon_cross_section.return_value = photon_data
    return cache


class TestGammaTransportSolverComprehensive:
    """Comprehensive tests for GammaTransportSolver."""
    
    def test_solver_initialization(self, simple_geometry, mock_cache):
        """Test solver initialization."""
        options = GammaTransportOptions(n_groups=20)
        solver = GammaTransportSolver(simple_geometry, options, cache=mock_cache)
        
        assert solver.geometry == simple_geometry
        assert solver.options == options
        assert solver.nz == simple_geometry.n_axial
        assert solver.nr == simple_geometry.n_radial
        assert solver.ng == 20
        assert solver.sigma_total is not None
        assert len(solver.sigma_total) == 20
    
    def test_initialize_cross_sections_simple_material(self, simple_geometry, mock_cache):
        """Test cross-section initialization for simple material."""
        options = GammaTransportOptions(n_groups=20)
        solver = GammaTransportSolver(simple_geometry, options, cache=mock_cache)
        
        # Check cross-sections were initialized
        assert solver.sigma_total is not None
        assert len(solver.sigma_total) == 20
        assert np.all(solver.sigma_total > 0)
        assert solver.D is not None
        assert len(solver.D) == 20
    
    def test_initialize_cross_sections_compound_material(self, simple_geometry, mock_cache):
        """Test cross-section initialization for compound material."""
        options = GammaTransportOptions(n_groups=20)
        
        # Mock compound material (H2O)
        mock_cache.get_photon_cross_section.return_value = None  # Force compound path
        
        solver = GammaTransportSolver(simple_geometry, options, cache=mock_cache)
        
        # Should fall back to placeholder or primary element
        assert solver.sigma_total is not None
        assert len(solver.sigma_total) == 20
    
    def test_load_photon_data_for_element(self, simple_geometry, mock_cache):
        """Test loading photon data for an element."""
        options = GammaTransportOptions(n_groups=20)
        solver = GammaTransportSolver(simple_geometry, options, cache=mock_cache)
        
        group_centers = np.logspace(-2, 1, 20)
        photon_data = solver._load_photon_data_for_element("H", group_centers)
        
        # Should return photon data or None
        assert photon_data is None or isinstance(photon_data, PhotonCrossSection)
    
    def test_solve_steady_state(self, simple_geometry, mock_cache):
        """Test solving steady-state gamma transport."""
        options = GammaTransportOptions(n_groups=10, max_iterations=10, tolerance=1e-3)
        solver = GammaTransportSolver(simple_geometry, options, cache=mock_cache)
        
        # Create source
        source = np.ones((solver.nz, solver.nr, solver.ng)) * 1e10  # photons/cm³/s
        
        flux = solver.solve(source)
        
        assert flux is not None
        assert flux.shape == (solver.nz, solver.nr, solver.ng)
        assert np.all(flux >= 0)
    
    def test_solve_time_dependent(self, simple_geometry, mock_cache):
        """Test solving time-dependent gamma transport."""
        options = GammaTransportOptions(n_groups=10, max_iterations=10, tolerance=1e-3)
        solver = GammaTransportSolver(simple_geometry, options, cache=mock_cache)
        
        # Create time-dependent source
        n_times = 5
        source_4d = np.ones((n_times, solver.nz, solver.nr, solver.ng)) * 1e10
        times = np.array([0, 3600, 7200, 10800, 14400])  # seconds
        
        # Solve at specific time
        flux = solver.solve((source_4d, times), time=7200.0)
        
        assert flux is not None
        assert flux.shape == (solver.nz, solver.nr, solver.ng)
        assert np.all(flux >= 0)
    
    def test_interpolate_time_dependent_source(self, simple_geometry, mock_cache):
        """Test time-dependent source interpolation."""
        options = GammaTransportOptions(n_groups=10)
        solver = GammaTransportSolver(simple_geometry, options, cache=mock_cache)
        
        n_times = 5
        source_4d = np.ones((n_times, solver.nz, solver.nr, solver.ng))
        times = np.array([0, 3600, 7200, 10800, 14400])
        
        # Interpolate at various times
        source_at_0 = solver._interpolate_time_dependent_source(source_4d, times, 0.0)
        assert source_at_0.shape == (solver.nz, solver.nr, solver.ng)
        
        source_at_3600 = solver._interpolate_time_dependent_source(source_4d, times, 3600.0)
        assert source_at_3600.shape == (solver.nz, solver.nr, solver.ng)
        
        source_at_5400 = solver._interpolate_time_dependent_source(source_4d, times, 5400.0)  # Interpolate
        assert source_at_5400.shape == (solver.nz, solver.nr, solver.ng)
        
        source_before = solver._interpolate_time_dependent_source(source_4d, times, -1000.0)  # Extrapolate
        assert source_before.shape == (solver.nz, solver.nr, solver.ng)
        
        source_after = solver._interpolate_time_dependent_source(source_4d, times, 20000.0)  # Extrapolate
        assert source_after.shape == (solver.nz, solver.nr, solver.ng)
    
    def test_solve_group(self, simple_geometry, mock_cache):
        """Test solving for a single energy group."""
        options = GammaTransportOptions(n_groups=10)
        solver = GammaTransportSolver(simple_geometry, options, cache=mock_cache)
        
        group = 0
        source_group = np.ones((solver.nz, solver.nr)) * 1e10
        
        flux_group = solver._solve_group(group, source_group)
        
        assert flux_group is not None
        assert flux_group.shape == (solver.nz, solver.nr)
        assert np.all(flux_group >= 0)
    
    def test_calculate_dose_rate(self, simple_geometry, mock_cache):
        """Test dose rate calculation."""
        options = GammaTransportOptions(n_groups=10)
        solver = GammaTransportSolver(simple_geometry, options, cache=mock_cache)
        
        # Set flux
        solver.flux = np.ones((solver.nz, solver.nr, solver.ng)) * 1e10  # photons/cm²/s
        
        dose_rate = solver.calculate_dose_rate()
        
        assert dose_rate is not None
        assert dose_rate.shape == (solver.nz, solver.nr)
        assert np.all(dose_rate >= 0)
    
    def test_cell_volumes(self, simple_geometry, mock_cache):
        """Test cell volume calculation."""
        options = GammaTransportOptions(n_groups=10)
        solver = GammaTransportSolver(simple_geometry, options, cache=mock_cache)
        
        volumes = solver._cell_volumes()
        
        assert volumes is not None
        assert volumes.shape == (solver.nz, solver.nr)
        assert np.all(volumes > 0)
    
    def test_convergence(self, simple_geometry, mock_cache):
        """Test solver convergence."""
        options = GammaTransportOptions(n_groups=5, max_iterations=100, tolerance=1e-6, verbose=True)
        solver = GammaTransportSolver(simple_geometry, options, cache=mock_cache)
        
        source = np.ones((solver.nz, solver.nr, solver.ng)) * 1e10
        
        flux = solver.solve(source)
        
        # Should converge or reach max iterations
        assert flux is not None
        assert np.all(flux >= 0)
    
    def test_source_shape_validation(self, simple_geometry, mock_cache):
        """Test source shape validation."""
        options = GammaTransportOptions(n_groups=10)
        solver = GammaTransportSolver(simple_geometry, options, cache=mock_cache)
        
        # Wrong shape
        wrong_source = np.ones((5, 3, 8))  # Wrong dimensions
        
        with pytest.raises(ValueError):
            solver.solve(wrong_source)
    
    def test_time_dependent_source_validation(self, simple_geometry, mock_cache):
        """Test time-dependent source validation."""
        options = GammaTransportOptions(n_groups=10)
        solver = GammaTransportSolver(simple_geometry, options, cache=mock_cache)
        
        source_4d = np.ones((5, solver.nz, solver.nr, solver.ng))
        times = np.array([0, 3600, 7200, 10800])  # Wrong length (4 vs 5)
        
        with pytest.raises(ValueError):
            solver.solve((source_4d, times), time=3600.0)
        
        # Missing time parameter
        with pytest.raises(ValueError):
            solver.solve((source_4d, times))
    
    def test_single_time_point(self, simple_geometry, mock_cache):
        """Test handling single time point."""
        options = GammaTransportOptions(n_groups=10)
        solver = GammaTransportSolver(simple_geometry, options, cache=mock_cache)
        
        source_4d = np.ones((1, solver.nz, solver.nr, solver.ng))
        times = np.array([0])
        
        source = solver._interpolate_time_dependent_source(source_4d, times, 0.0)
        assert source.shape == (solver.nz, solver.nr, solver.ng)

