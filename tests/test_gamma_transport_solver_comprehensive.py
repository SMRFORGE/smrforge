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
    
    def test_initialize_cross_sections_compound_material_with_data(self, simple_geometry, mock_cache):
        """Test cross-section initialization for compound material with data."""
        options = GammaTransportOptions(n_groups=20)
        
        # Mock MaterialMapper to return compound composition
        from unittest.mock import patch, MagicMock
        from smrforge.core.material_mapping import MaterialMapper
        
        mock_comp = MagicMock()
        mock_comp.elements = ["H", "O"]
        
        with patch.object(MaterialMapper, 'get_composition', return_value=mock_comp):
            with patch.object(MaterialMapper, 'compute_weighted_cross_section', return_value=np.ones(20) * 0.1):
                solver = GammaTransportSolver(simple_geometry, options, cache=mock_cache)
                
                assert solver.sigma_total is not None
                assert len(solver.sigma_total) == 20
                assert np.all(solver.sigma_total > 0)
    
    def test_initialize_cross_sections_fallback_primary_element(self, simple_geometry, mock_cache):
        """Test cross-section initialization with fallback to primary element."""
        options = GammaTransportOptions(n_groups=20)
        
        from unittest.mock import patch, MagicMock
        from smrforge.core.material_mapping import MaterialMapper
        
        mock_comp = MagicMock()
        mock_comp.elements = ["H", "O"]
        
        # Mock get_composition to return compound, but no cross-sections found
        with patch.object(MaterialMapper, 'get_composition', return_value=mock_comp):
            with patch.object(MaterialMapper, 'get_primary_element', return_value="H"):
                # Mock cache to return None for elements
                mock_cache.get_photon_cross_section.return_value = None
                
                solver = GammaTransportSolver(simple_geometry, options, cache=mock_cache)
                
                # Should fall back to placeholder
                assert solver.sigma_total is not None
                assert len(solver.sigma_total) == 20
    
    def test_load_photon_data_for_element_exception(self, simple_geometry, mock_cache):
        """Test loading photon data with exception handling."""
        options = GammaTransportOptions(n_groups=20)
        solver = GammaTransportSolver(simple_geometry, options, cache=mock_cache)
        
        # Mock cache to raise exception
        mock_cache.get_photon_cross_section.side_effect = Exception("No photon data")
        
        group_centers = np.logspace(-2, 1, 20)
        photon_data = solver._load_photon_data_for_element("H", group_centers)
        
        # Should return None on exception
        assert photon_data is None
    
    def test_load_photon_data_for_element_no_data(self, simple_geometry, mock_cache):
        """Test loading photon data when no data is available."""
        options = GammaTransportOptions(n_groups=20)
        solver = GammaTransportSolver(simple_geometry, options, cache=mock_cache)
        
        # Mock cache to return None
        mock_cache.get_photon_cross_section.return_value = None
        
        group_centers = np.logspace(-2, 1, 20)
        photon_data = solver._load_photon_data_for_element("H", group_centers)
        
        # Should return None
        assert photon_data is None
    
    def test_build_group_system(self, simple_geometry, mock_cache):
        """Test building group system matrix."""
        options = GammaTransportOptions(n_groups=10)
        solver = GammaTransportSolver(simple_geometry, options, cache=mock_cache)
        
        group = 0
        source_group = np.ones((solver.nz, solver.nr)) * 1e10
        
        A, b = solver._build_group_system(group, source_group)
        
        assert A is not None
        assert b is not None
        assert A.shape == (solver.nz * solver.nr, solver.nz * solver.nr)
        assert len(b) == solver.nz * solver.nr
    
    def test_cell_volume_single(self, simple_geometry, mock_cache):
        """Test single cell volume calculation."""
        options = GammaTransportOptions(n_groups=10)
        solver = GammaTransportSolver(simple_geometry, options, cache=mock_cache)
        
        volume = solver._cell_volume(0, 0)
        
        assert volume > 0
        assert isinstance(volume, (float, np.floating))
    
    def test_calculate_dose_rate_with_provided_flux(self, simple_geometry, mock_cache):
        """Test dose rate calculation with provided flux."""
        options = GammaTransportOptions(n_groups=10)
        solver = GammaTransportSolver(simple_geometry, options, cache=mock_cache)
        
        # Provide flux directly
        flux = np.ones((solver.nz, solver.nr, solver.ng)) * 1e10
        
        dose_rate = solver.compute_dose_rate(flux=flux)
        
        assert dose_rate is not None
        assert dose_rate.shape == (solver.nz, solver.nr)
        assert np.all(dose_rate >= 0)
    
    def test_calculate_dose_rate_no_flux(self, simple_geometry, mock_cache):
        """Test dose rate calculation when flux is None."""
        options = GammaTransportOptions(n_groups=10)
        solver = GammaTransportSolver(simple_geometry, options, cache=mock_cache)
        
        # Ensure flux is None
        solver.flux = None
        
        with pytest.raises(RuntimeError, match="Must solve for flux first"):
            solver.compute_dose_rate()
    
    def test_solve_convergence_verbose(self, simple_geometry, mock_cache):
        """Test solver convergence with verbose output."""
        options = GammaTransportOptions(n_groups=5, max_iterations=5, tolerance=1e-3, verbose=True)
        solver = GammaTransportSolver(simple_geometry, options, cache=mock_cache)
        
        source = np.ones((solver.nz, solver.nr, solver.ng)) * 1e10
        
        flux = solver.solve(source)
        
        assert flux is not None
        assert np.all(flux >= 0)
    
    def test_solve_no_convergence(self, simple_geometry, mock_cache):
        """Test solver when it doesn't converge."""
        options = GammaTransportOptions(n_groups=5, max_iterations=2, tolerance=1e-10, verbose=False)
        solver = GammaTransportSolver(simple_geometry, options, cache=mock_cache)
        
        source = np.ones((solver.nz, solver.nr, solver.ng)) * 1e10
        
        # Should still return flux even if not converged
        flux = solver.solve(source)
        
        assert flux is not None
        assert np.all(flux >= 0)
    
    def test_interpolate_time_dependent_source_single_point(self, simple_geometry, mock_cache):
        """Test time-dependent source interpolation with single time point."""
        options = GammaTransportOptions(n_groups=10)
        solver = GammaTransportSolver(simple_geometry, options, cache=mock_cache)
        
        source_4d = np.ones((1, solver.nz, solver.nr, solver.ng))
        times = np.array([3600])
        
        source = solver._interpolate_time_dependent_source(source_4d, times, 3600.0)
        
        assert source.shape == (solver.nz, solver.nr, solver.ng)
    
    def test_interpolate_time_dependent_source_exact_match(self, simple_geometry, mock_cache):
        """Test time-dependent source interpolation with exact time match."""
        options = GammaTransportOptions(n_groups=10)
        solver = GammaTransportSolver(simple_geometry, options, cache=mock_cache)
        
        source_4d = np.ones((3, solver.nz, solver.nr, solver.ng))
        times = np.array([0, 3600, 7200])
        
        # Exact match at index 1
        source = solver._interpolate_time_dependent_source(source_4d, times, 3600.0)
        
        assert source.shape == (solver.nz, solver.nr, solver.ng)
    
    def test_interpolate_time_dependent_source_before_start(self, simple_geometry, mock_cache):
        """Test time-dependent source interpolation before first time."""
        options = GammaTransportOptions(n_groups=10)
        solver = GammaTransportSolver(simple_geometry, options, cache=mock_cache)
        
        source_4d = np.ones((3, solver.nz, solver.nr, solver.ng))
        times = np.array([3600, 7200, 10800])
        
        # Before first time
        source = solver._interpolate_time_dependent_source(source_4d, times, 0.0)
        
        assert source.shape == (solver.nz, solver.nr, solver.ng)
        # Should return first source
        assert np.allclose(source, source_4d[0, :, :, :])
    
    def test_interpolate_time_dependent_source_after_end(self, simple_geometry, mock_cache):
        """Test time-dependent source interpolation after last time."""
        options = GammaTransportOptions(n_groups=10)
        solver = GammaTransportSolver(simple_geometry, options, cache=mock_cache)
        
        source_4d = np.ones((3, solver.nz, solver.nr, solver.ng))
        times = np.array([3600, 7200, 10800])
        
        # After last time
        source = solver._interpolate_time_dependent_source(source_4d, times, 20000.0)
        
        assert source.shape == (solver.nz, solver.nr, solver.ng)
        # Should return last source
        assert np.allclose(source, source_4d[-1, :, :, :])
    
    def test_interpolate_time_dependent_source_validation(self, simple_geometry, mock_cache):
        """Test time-dependent source interpolation validation."""
        options = GammaTransportOptions(n_groups=10)
        solver = GammaTransportSolver(simple_geometry, options, cache=mock_cache)
        
        source_4d = np.ones((3, solver.nz, solver.nr, solver.ng))
        times = np.array([3600, 7200])  # Wrong length
        
        with pytest.raises(ValueError, match="same length"):
            solver._interpolate_time_dependent_source(source_4d, times, 3600.0)

