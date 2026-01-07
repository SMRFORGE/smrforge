"""
Comprehensive tests for burnup solver to improve coverage to 80%+.

Tests cover:
- Time step solving
- Decay matrix construction
- Fission product production
- Capture transmutation
- Cross-section updates
- Flux integration
- Burnup calculation
"""

import numpy as np
import pytest
from unittest.mock import Mock, patch, MagicMock

from smrforge.burnup import BurnupOptions, BurnupSolver, NuclideInventory
from smrforge.core.reactor_core import Nuclide, NuclearDataCache, DecayData
from smrforge.geometry import PrismaticCore
from smrforge.neutronics.solver import MultiGroupDiffusion
from smrforge.validation.models import CrossSectionData, SolverOptions


@pytest.fixture
def simple_geometry():
    """Create a simple geometry for testing."""
    geometry = PrismaticCore(name="TestCore")
    geometry.core_height = 100.0  # cm
    geometry.core_diameter = 50.0  # cm
    geometry.generate_mesh(n_radial=5, n_axial=3)
    return geometry


@pytest.fixture
def simple_xs_data():
    """Create simple cross-section data for testing."""
    return CrossSectionData(
        n_groups=2,
        n_materials=1,
        sigma_t=np.array([[0.5, 0.8]]),
        sigma_a=np.array([[0.1, 0.2]]),
        sigma_f=np.array([[0.05, 0.15]]),
        nu_sigma_f=np.array([[0.125, 0.375]]),
        sigma_s=np.array([[[0.39, 0.01], [0.0, 0.58]]]),
        chi=np.array([[1.0, 0.0]]),
        D=np.array([[1.5, 0.4]]),
    )


@pytest.fixture
def simple_neutronics(simple_geometry, simple_xs_data):
    """Create a simple neutronics solver."""
    options = SolverOptions(
        max_iterations=50,
        tolerance=1e-5,
        eigen_method="power",
        verbose=False,
        skip_solution_validation=True,  # Allow simplified cross-sections
    )
    return MultiGroupDiffusion(simple_geometry, simple_xs_data, options)


@pytest.fixture
def mock_cache():
    """Create a mock cache for testing."""
    cache = Mock(spec=NuclearDataCache)
    
    # Mock decay data
    def mock_get_decay_data(nuclide):
        decay_data = Mock(spec=DecayData)
        decay_data.decay_constant = 1e-10 if nuclide.Z == 92 else 1e-8
        decay_data.half_life = 7.04e8 if nuclide.Z == 92 else 1e6
        decay_data.get_daughters.return_value = []
        return decay_data
    
    cache.get_decay_data = mock_get_decay_data
    cache.get_fission_yield_data = Mock(return_value=None)
    cache.get_cross_section = Mock(return_value=(np.array([1e6, 2e6]), np.array([1.0, 2.0])))
    return cache


class TestBurnupSolverComprehensive:
    """Comprehensive tests for BurnupSolver to improve coverage."""
    
    def test_solve_time_step(self, simple_neutronics, mock_cache):
        """Test solving a single time step."""
        options = BurnupOptions(
            time_steps=[0, 30],  # days
            power_density=1e6,
            initial_enrichment=0.195,
        )
        
        burnup = BurnupSolver(simple_neutronics, options, cache=mock_cache)
        
        # Set initial concentrations
        u235 = Nuclide(Z=92, A=235)
        u238 = Nuclide(Z=92, A=238)
        if u235 in burnup.nuclides:
            idx_u235 = burnup.nuclides.index(u235)
            burnup.concentrations[idx_u235, 0] = 1e20
        
        # Solve time step
        burnup._solve_time_step(1, 0.0, 30.0 * 24 * 3600, 30.0 * 24 * 3600)
        
        # Check concentrations were updated
        assert burnup.concentrations[:, 1].sum() >= 0
    
    def test_build_decay_matrix(self, simple_neutronics, mock_cache):
        """Test building decay matrix."""
        options = BurnupOptions(
            time_steps=[0, 30],
            initial_enrichment=0.195,
        )
        
        burnup = BurnupSolver(simple_neutronics, options, cache=mock_cache)
        
        # Build decay matrix
        decay_matrix = burnup._build_decay_matrix()
        
        assert decay_matrix is not None
        assert decay_matrix.shape[0] == len(burnup.nuclides)
        assert decay_matrix.shape[1] == len(burnup.nuclides)
    
    def test_build_fission_production_vector(self, simple_neutronics, mock_cache):
        """Test building fission production vector."""
        options = BurnupOptions(
            time_steps=[0, 30],
            initial_enrichment=0.195,
        )
        
        burnup = BurnupSolver(simple_neutronics, options, cache=mock_cache)
        
        # Set flux - get shape from xs data
        n_groups = burnup.neutronics.xs.n_groups
        burnup.neutronics.flux = np.ones((burnup.neutronics.nz, burnup.neutronics.nr, n_groups))
        
        # Build production vector
        production_vector = burnup._build_fission_production_vector(0)
        
        assert production_vector is not None
        assert len(production_vector) == len(burnup.nuclides)
        assert np.all(production_vector >= 0)
    
    def test_build_capture_matrix(self, simple_neutronics, mock_cache):
        """Test building capture transmutation matrix."""
        options = BurnupOptions(
            time_steps=[0, 30],
            initial_enrichment=0.195,
        )
        
        burnup = BurnupSolver(simple_neutronics, options, cache=mock_cache)
        
        # Build capture matrix (requires time_index argument)
        capture_matrix = burnup._build_capture_matrix(0)
        
        assert capture_matrix is not None
        assert capture_matrix.shape[0] == len(burnup.nuclides)
    
    
    def test_update_cross_sections(self, simple_neutronics, mock_cache):
        """Test updating cross-sections based on composition."""
        options = BurnupOptions(
            time_steps=[0, 30],
            initial_enrichment=0.195,
        )
        
        burnup = BurnupSolver(simple_neutronics, options, cache=mock_cache)
        
        # Update cross-sections
        burnup._update_cross_sections(1)
        
        # Check that cross-sections exist (use xs instead of xs_data)
        assert burnup.neutronics.xs is not None
    
    def test_update_burnup(self, simple_neutronics, mock_cache):
        """Test updating burnup calculation."""
        options = BurnupOptions(
            time_steps=[0, 30],
            power_density=1e6,
            initial_enrichment=0.195,
        )
        
        burnup = BurnupSolver(simple_neutronics, options, cache=mock_cache)
        
        # Set some concentrations
        u235 = Nuclide(Z=92, A=235)
        if u235 in burnup.nuclides:
            idx_u235 = burnup.nuclides.index(u235)
            burnup.concentrations[idx_u235, 0] = 1e20
            burnup.concentrations[idx_u235, 1] = 0.9e20
        
        # Set flux - get shape from xs data
        n_groups = burnup.neutronics.xs.n_groups
        burnup.neutronics.flux = np.ones((burnup.neutronics.nz, burnup.neutronics.nr, n_groups))
        
        # Update burnup
        burnup._update_burnup(1)
        
        # Check burnup was calculated
        assert burnup.burnup_mwd_per_kg[1] >= 0
    
    def test_compute_decay_heat(self, simple_neutronics, mock_cache):
        """Test decay heat computation."""
        options = BurnupOptions(
            time_steps=[0, 30],
            initial_enrichment=0.195,
        )
        
        burnup = BurnupSolver(simple_neutronics, options, cache=mock_cache)
        
        # Compute decay heat
        decay_heat = burnup.compute_decay_heat()
        
        assert decay_heat >= 0
    
    def test_solve_full_burnup(self, simple_neutronics, mock_cache):
        """Test solving full burnup problem."""
        options = BurnupOptions(
            time_steps=[0, 30, 60],
            power_density=1e6,
            initial_enrichment=0.195,
        )
        
        burnup = BurnupSolver(simple_neutronics, options, cache=mock_cache)
        
        # Mock neutronics solve to avoid convergence issues
        with patch.object(burnup.neutronics, 'solve_steady_state', return_value=(1.0, np.ones((3, 5, 2)))):
            inventory = burnup.solve()
        
        assert inventory is not None
        assert isinstance(inventory, NuclideInventory)
        assert len(inventory.nuclides) > 0
        assert inventory.concentrations.shape[0] == len(inventory.nuclides)
        assert inventory.concentrations.shape[1] == len(options.time_steps)
    
    def test_track_fission_products(self, simple_neutronics, mock_cache):
        """Test tracking fission products."""
        options = BurnupOptions(
            time_steps=[0, 30],
            track_fission_products=True,
            initial_enrichment=0.195,
        )
        
        burnup = BurnupSolver(simple_neutronics, options, cache=mock_cache)
        
        # Check that fission products are tracked
        cs137 = Nuclide(Z=55, A=137)
        assert cs137 in burnup.nuclides or not options.track_fission_products
    
    def test_track_actinides(self, simple_neutronics, mock_cache):
        """Test tracking actinides."""
        options = BurnupOptions(
            time_steps=[0, 30],
            track_actinides=True,
            initial_enrichment=0.195,
        )
        
        burnup = BurnupSolver(simple_neutronics, options, cache=mock_cache)
        
        # Check that actinides are tracked
        pu239 = Nuclide(Z=94, A=239)
        assert pu239 in burnup.nuclides or not options.track_actinides
    
    def test_power_density_array(self, simple_neutronics, mock_cache):
        """Test time-dependent power density."""
        power_array = np.array([1e6, 0.9e6, 0.8e6])  # Decreasing power
        options = BurnupOptions(
            time_steps=[0, 30, 60],
            power_density=power_array,
            initial_enrichment=0.195,
        )
        
        burnup = BurnupSolver(simple_neutronics, options, cache=mock_cache)
        
        assert burnup.options.power_density is not None
        assert len(burnup.options.power_density) == len(options.time_steps) or isinstance(burnup.options.power_density, (int, float))
    
    def test_initial_concentrations_calculation(self, simple_neutronics, mock_cache):
        """Test initial concentration calculation."""
        options = BurnupOptions(
            time_steps=[0, 30],
            initial_enrichment=0.195,
        )
        
        burnup = BurnupSolver(simple_neutronics, options, cache=mock_cache)
        
        u235 = Nuclide(Z=92, A=235)
        u238 = Nuclide(Z=92, A=238)
        
        if u235 in burnup.nuclides and u238 in burnup.nuclides:
            idx_u235 = burnup.nuclides.index(u235)
            idx_u238 = burnup.nuclides.index(u238)
            
            # Check initial concentrations
            assert burnup.concentrations[idx_u235, 0] > 0
            assert burnup.concentrations[idx_u238, 0] > 0
            # U-235 should be less than U-238
            assert burnup.concentrations[idx_u235, 0] < burnup.concentrations[idx_u238, 0]
    
    def test_get_fission_yield_data_caching(self, simple_neutronics, mock_cache):
        """Test fission yield data caching."""
        options = BurnupOptions(
            time_steps=[0, 30],
            initial_enrichment=0.195,
        )
        
        burnup = BurnupSolver(simple_neutronics, options, cache=mock_cache)
        
        u235 = Nuclide(Z=92, A=235)
        
        # First call - should fetch from cache
        yield_data1 = burnup._get_fission_yield_data(u235)
        
        # Second call - should use cached value
        yield_data2 = burnup._get_fission_yield_data(u235)
        
        # Should be the same object (or None if not available)
        assert yield_data1 is yield_data2
    
    def test_build_capture_matrix_with_cross_section(self, simple_neutronics, mock_cache):
        """Test building capture matrix with cross-section retrieval."""
        options = BurnupOptions(
            time_steps=[0, 30],
            initial_enrichment=0.195,
        )
        
        burnup = BurnupSolver(simple_neutronics, options, cache=mock_cache)
        
        # Set flux - get shape from xs data
        n_groups = burnup.neutronics.xs.n_groups
        burnup.neutronics.flux = np.ones((burnup.neutronics.nz, burnup.neutronics.nr, n_groups))
        
        # Mock get_cross_section to return data
        def mock_get_cross_section(nuclide, reaction, temperature=None):
            return np.array([1e6, 1e7]), np.array([1.0, 1.5])  # energy, xs
        
        mock_cache.get_cross_section = mock_get_cross_section
        
        # Build capture matrix
        capture_matrix = burnup._build_capture_matrix(0)
        
        assert capture_matrix is not None
        assert capture_matrix.shape[0] == len(burnup.nuclides)
    
    def test_build_capture_matrix_with_fallback(self, simple_neutronics, mock_cache):
        """Test building capture matrix with fallback when cross-section fails."""
        options = BurnupOptions(
            time_steps=[0, 30],
            initial_enrichment=0.195,
        )
        
        burnup = BurnupSolver(simple_neutronics, options, cache=mock_cache)
        
        # Set flux - get shape from xs data
        n_groups = burnup.neutronics.xs.n_groups
        burnup.neutronics.flux = np.ones((burnup.neutronics.nz, burnup.neutronics.nr, n_groups))
        
        # Mock get_cross_section to raise exception (forces fallback)
        mock_cache.get_cross_section.side_effect = Exception("No cross-section data")
        
        # Build capture matrix (should use fallback)
        capture_matrix = burnup._build_capture_matrix(0)
        
        assert capture_matrix is not None
    
    def test_update_burnup_zero_mass(self, simple_neutronics, mock_cache):
        """Test burnup update with zero mass (edge case)."""
        options = BurnupOptions(
            time_steps=[0, 30],
            power_density=1e6,
            initial_enrichment=0.195,
        )
        
        burnup = BurnupSolver(simple_neutronics, options, cache=mock_cache)
        
        # Set concentrations to zero
        burnup.concentrations[:, 0] = 0.0
        burnup.concentrations[:, 1] = 0.0
        
        # Update burnup (should handle zero mass)
        burnup._update_burnup(1)
        
        # Should not raise error, burnup should remain at previous value
        assert burnup.burnup_mwd_per_kg[1] >= 0
    
    def test_compute_decay_heat_specific_time(self, simple_neutronics, mock_cache):
        """Test decay heat computation at specific time index."""
        options = BurnupOptions(
            time_steps=[0, 30, 60],
            initial_enrichment=0.195,
        )
        
        burnup = BurnupSolver(simple_neutronics, options, cache=mock_cache)
        
        # Set some concentrations
        u235 = Nuclide(Z=92, A=235)
        if u235 in burnup.nuclides:
            idx_u235 = burnup.nuclides.index(u235)
            burnup.concentrations[idx_u235, 0] = 1e20
            burnup.concentrations[idx_u235, 1] = 0.9e20
            burnup.concentrations[idx_u235, 2] = 0.8e20
        
        # Compute decay heat at specific time index
        decay_heat_0 = burnup.compute_decay_heat(time_index=0)
        decay_heat_1 = burnup.compute_decay_heat(time_index=1)
        decay_heat_2 = burnup.compute_decay_heat(time_index=2)
        
        assert decay_heat_0 >= 0
        assert decay_heat_1 >= 0
        assert decay_heat_2 >= 0
    
    def test_solve_time_step_ode_failure(self, simple_neutronics, mock_cache):
        """Test time step solving when ODE solver fails."""
        options = BurnupOptions(
            time_steps=[0, 30],
            initial_enrichment=0.195,
        )
        
        burnup = BurnupSolver(simple_neutronics, options, cache=mock_cache)
        
        # Set initial concentrations
        u235 = Nuclide(Z=92, A=235)
        if u235 in burnup.nuclides:
            idx_u235 = burnup.nuclides.index(u235)
            burnup.concentrations[idx_u235, 0] = 1e20
        
        # Set flux - get shape from xs data
        n_groups = burnup.neutronics.xs.n_groups
        burnup.neutronics.flux = np.ones((burnup.neutronics.nz, burnup.neutronics.nr, n_groups))
        
        # Mock solve_ivp to return unsuccessful result
        from unittest.mock import patch
        from scipy.integrate import solve_ivp
        
        class MockResult:
            success = False
            y = np.array([[1e20]])
        
        with patch('smrforge.burnup.solver.solve_ivp', return_value=MockResult()):
            # Should fall back to Euler step
            burnup._solve_time_step(1, 0.0, 30.0 * 24 * 3600, 30.0 * 24 * 3600)
            
            # Concentrations should be updated (non-negative)
            assert burnup.concentrations[:, 1].sum() >= 0
    
    def test_solve_time_step_exception(self, simple_neutronics, mock_cache):
        """Test time step solving when exception occurs."""
        options = BurnupOptions(
            time_steps=[0, 30],
            initial_enrichment=0.195,
        )
        
        burnup = BurnupSolver(simple_neutronics, options, cache=mock_cache)
        
        # Set initial concentrations
        u235 = Nuclide(Z=92, A=235)
        if u235 in burnup.nuclides:
            idx_u235 = burnup.nuclides.index(u235)
            burnup.concentrations[idx_u235, 0] = 1e20
        
        # Set flux - get shape from xs data
        n_groups = burnup.neutronics.xs.n_groups
        burnup.neutronics.flux = np.ones((burnup.neutronics.nz, burnup.neutronics.nr, n_groups))
        
        # Mock solve_ivp to raise exception
        from unittest.mock import patch
        from scipy.integrate import solve_ivp
        
        with patch('smrforge.burnup.solver.solve_ivp', side_effect=Exception("Solver error")):
            # Should fall back to Euler step
            burnup._solve_time_step(1, 0.0, 30.0 * 24 * 3600, 30.0 * 24 * 3600)
            
            # Concentrations should be updated (non-negative)
            assert burnup.concentrations[:, 1].sum() >= 0
    
    def test_solve_neutronics_error_handling(self, simple_neutronics, mock_cache):
        """Test solve method handles neutronics re-solve errors."""
        options = BurnupOptions(
            time_steps=[0, 30, 60],
            power_density=1e6,
            initial_enrichment=0.195,
        )
        
        burnup = BurnupSolver(simple_neutronics, options, cache=mock_cache)
        
        # Track call count to return success first, then failures
        call_count = [0]
        
        def mock_solve():
            call_count[0] += 1
            if call_count[0] == 1:
                # First call (initial solve) succeeds
                n_groups = burnup.neutronics.xs.n_groups
                burnup.neutronics.flux = np.ones((burnup.neutronics.nz, burnup.neutronics.nr, n_groups))
                burnup.neutronics.k_eff = 1.0
                return 1.0, burnup.neutronics.flux
            else:
                # Subsequent calls (re-solves) fail - should be caught and logged
                raise Exception("Neutronics solve failed")
        
        with patch.object(burnup.neutronics, 'solve_steady_state', side_effect=mock_solve):
            # Should handle error and continue
            # The error should be caught in solve() method and logged as warning
            inventory = burnup.solve()
            
            assert inventory is not None
            assert isinstance(inventory, NuclideInventory)
            # Even though neutronics re-solve failed, burnup calculation should complete
    
    def test_build_fission_production_vector_no_flux(self, simple_neutronics, mock_cache):
        """Test fission production vector when flux is None."""
        options = BurnupOptions(
            time_steps=[0, 30],
            initial_enrichment=0.195,
        )
        
        burnup = BurnupSolver(simple_neutronics, options, cache=mock_cache)
        
        # Ensure flux is None
        burnup.neutronics.flux = None
        
        # Build production vector
        production_vector = burnup._build_fission_production_vector(0)
        
        assert production_vector is not None
        assert len(production_vector) == len(burnup.nuclides)
        assert np.all(production_vector == 0)
    
    def test_build_capture_matrix_no_flux(self, simple_neutronics, mock_cache):
        """Test capture matrix when flux is None."""
        options = BurnupOptions(
            time_steps=[0, 30],
            initial_enrichment=0.195,
        )
        
        burnup = BurnupSolver(simple_neutronics, options, cache=mock_cache)
        
        # Ensure flux is None
        burnup.neutronics.flux = None
        
        # Build capture matrix
        capture_matrix = burnup._build_capture_matrix(0)
        
        assert capture_matrix is not None
        assert capture_matrix.shape[0] == len(burnup.nuclides)
        # Should be zero matrix when flux is None
        assert np.all(capture_matrix.data == 0) or capture_matrix.nnz == 0

    def test_init_decay_data_fallback(self, simple_neutronics, mock_cache):
        """Test BurnupSolver.__init__ with DecayData fallback path."""
        options = BurnupOptions(
            time_steps=[0, 30],
            initial_enrichment=0.195,
        )
        
        # Mock DecayData: first call (with cache) raises TypeError, second call (without cache) succeeds
        call_count = [0]
        def mock_decay_data(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1 and 'cache' in kwargs:
                # First call with cache parameter raises TypeError
                raise TypeError("Invalid args")
            # Second call (fallback) succeeds
            decay_data_mock = Mock(spec=DecayData)
            decay_data_mock._cache = mock_cache
            return decay_data_mock
        
        with patch('smrforge.burnup.solver.DecayData', side_effect=mock_decay_data):
            burnup = BurnupSolver(simple_neutronics, options, cache=mock_cache)
            
            # Should still initialize with fallback
            assert burnup.decay_data is not None
            assert burnup.cache == mock_cache

    def test_build_capture_matrix_nuclide_specific_xs_failure(self, simple_neutronics, mock_cache):
        """Test _build_capture_matrix when nuclide-specific XS retrieval fails."""
        options = BurnupOptions(
            time_steps=[0, 30],
            initial_enrichment=0.195,
        )
        
        burnup = BurnupSolver(simple_neutronics, options, cache=mock_cache)
        
        # Set flux - get shape from xs data
        n_groups = burnup.neutronics.xs.n_groups
        burnup.neutronics.flux = np.ones((burnup.neutronics.nz, burnup.neutronics.nr, n_groups))
        
        # Set concentrations
        u235 = Nuclide(Z=92, A=235)
        if u235 in burnup.nuclides:
            idx_u235 = burnup.nuclides.index(u235)
            burnup.concentrations[idx_u235, 0] = 1e20
        
        # Mock get_cross_section to raise exception (triggers fallback)
        mock_cache.get_cross_section.side_effect = Exception("Cross-section not found")
        
        # Should fall back to material average
        capture_matrix = burnup._build_capture_matrix(0)
        
        assert capture_matrix is not None
        assert capture_matrix.shape[0] == len(burnup.nuclides)

    def test_build_capture_matrix_zero_concentration(self, simple_neutronics, mock_cache):
        """Test _build_capture_matrix with zero nuclide concentration."""
        options = BurnupOptions(
            time_steps=[0, 30],
            initial_enrichment=0.195,
        )
        
        burnup = BurnupSolver(simple_neutronics, options, cache=mock_cache)
        
        # Set flux - get shape from xs data
        n_groups = burnup.neutronics.xs.n_groups
        burnup.neutronics.flux = np.ones((burnup.neutronics.nz, burnup.neutronics.nr, n_groups))
        
        # Set all concentrations to zero
        burnup.concentrations[:, 0] = 0.0
        
        # Should handle zero concentrations gracefully
        capture_matrix = burnup._build_capture_matrix(0)
        
        assert capture_matrix is not None
        # Should have zero capture rates when concentrations are zero
        assert np.all(capture_matrix.data == 0) or capture_matrix.nnz == 0

    def test_update_burnup_zero_mass_kg(self, simple_neutronics, mock_cache):
        """Test _update_burnup when mass_u_kg is zero."""
        options = BurnupOptions(
            time_steps=[0, 30],
            initial_enrichment=0.195,
        )
        
        burnup = BurnupSolver(simple_neutronics, options, cache=mock_cache)
        
        # Set all U concentrations to zero
        u235 = Nuclide(Z=92, A=235)
        u238 = Nuclide(Z=92, A=238)
        if u235 in burnup.nuclides:
            idx_u235 = burnup.nuclides.index(u235)
            burnup.concentrations[idx_u235, 0] = 0.0
            burnup.concentrations[idx_u235, 1] = 0.0
        if u238 in burnup.nuclides:
            idx_u238 = burnup.nuclides.index(u238)
            burnup.concentrations[idx_u238, 0] = 0.0
            burnup.concentrations[idx_u238, 1] = 0.0
        
        # Set initial burnup
        burnup.burnup_mwd_per_kg[0] = 0.0
        
        # Should handle zero mass gracefully (burnup stays same)
        burnup._update_burnup(1)
        
        assert burnup.burnup_mwd_per_kg[1] == burnup.burnup_mwd_per_kg[0]

    def test_solve_with_neutronics_resolve_condition(self, simple_neutronics, mock_cache):
        """Test solve method when neutronics re-solve condition is met."""
        # Create enough time steps to trigger re-solve condition
        options = BurnupOptions(
            time_steps=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
            power_density=1e6,
            initial_enrichment=0.195,
        )
        
        burnup = BurnupSolver(simple_neutronics, options, cache=mock_cache)
        
        # Mock solve_steady_state to return valid results
        def mock_solve():
            n_groups = burnup.neutronics.xs.n_groups
            burnup.neutronics.flux = np.ones((burnup.neutronics.nz, burnup.neutronics.nr, n_groups))
            burnup.neutronics.k_eff = 1.0
            return 1.0, burnup.neutronics.flux
        
        with patch.object(burnup.neutronics, 'solve_steady_state', side_effect=mock_solve):
            # Set flux to None so _build_fission_production_vector returns zeros
            # This simplifies the test
            burnup.neutronics.flux = None
            
            # Should complete without error
            inventory = burnup.solve()
            
            assert inventory is not None
            assert isinstance(inventory, NuclideInventory)

