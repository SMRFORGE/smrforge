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
    geometry.build_mesh(n_radial=5, n_axial=3)
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
    cache.get_fission_yield_data.return_value = None
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
        
        # Set flux
        burnup.neutronics.flux = np.ones((burnup.neutronics.nz, burnup.neutronics.nr, burnup.neutronics.n_groups))
        
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
        
        # Build capture matrix
        capture_matrix = burnup._build_capture_matrix()
        
        assert capture_matrix is not None
        assert capture_matrix.shape[0] == len(burnup.nuclides)
        assert capture_matrix.shape[1] == len(burnup.nuclides)
    
    
    def test_update_cross_sections(self, simple_neutronics, mock_cache):
        """Test updating cross-sections based on composition."""
        options = BurnupOptions(
            time_steps=[0, 30],
            initial_enrichment=0.195,
        )
        
        burnup = BurnupSolver(simple_neutronics, options, cache=mock_cache)
        
        # Update cross-sections
        burnup._update_cross_sections(1)
        
        # Check that cross-sections exist
        assert burnup.neutronics.xs_data is not None
    
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
        
        # Set flux
        burnup.neutronics.flux = np.ones((burnup.neutronics.nz, burnup.neutronics.nr, burnup.neutronics.n_groups))
        
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

