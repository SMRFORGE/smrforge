"""
Integration tests for burnup solver.
"""

import numpy as np
import pytest

from smrforge.burnup import BurnupOptions, BurnupSolver, NuclideInventory
from smrforge.core.reactor_core import Nuclide
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
    )
    return MultiGroupDiffusion(simple_geometry, simple_xs_data, options)


class TestBurnupSolver:
    """Test BurnupSolver class."""

    def test_burnup_solver_initialization(self, simple_neutronics):
        """Test burnup solver can be initialized."""
        options = BurnupOptions(
            time_steps=[0, 30, 60],  # days
            power_density=1e6,  # W/cm³
            initial_enrichment=0.195,
        )

        burnup = BurnupSolver(simple_neutronics, options)
        
        assert burnup is not None
        assert len(burnup.nuclides) > 0
        assert burnup.concentrations.shape[0] == len(burnup.nuclides)

    def test_nuclide_initialization(self, simple_neutronics):
        """Test nuclides are initialized correctly."""
        options = BurnupOptions(
            time_steps=[0, 30],
            initial_enrichment=0.195,
        )

        burnup = BurnupSolver(simple_neutronics, options)
        
        # Should have U-235 and U-238 at minimum
        u235 = Nuclide(Z=92, A=235)
        u238 = Nuclide(Z=92, A=238)
        
        assert u235 in burnup.nuclides
        assert u238 in burnup.nuclides

    def test_initial_concentrations(self, simple_neutronics):
        """Test initial concentrations are set correctly."""
        options = BurnupOptions(
            time_steps=[0, 30],
            initial_enrichment=0.195,
        )

        burnup = BurnupSolver(simple_neutronics, options)
        
        u235 = Nuclide(Z=92, A=235)
        u238 = Nuclide(Z=92, A=238)
        
        idx_u235 = burnup.nuclides.index(u235)
        idx_u238 = burnup.nuclides.index(u238)
        
        # U-235 should have non-zero initial concentration
        assert burnup.concentrations[idx_u235, 0] > 0
        # U-238 should have non-zero initial concentration
        assert burnup.concentrations[idx_u238, 0] > 0
        # U-235 should be less than U-238 (19.5% enrichment)
        assert burnup.concentrations[idx_u235, 0] < burnup.concentrations[idx_u238, 0]


class TestNuclideInventory:
    """Test NuclideInventory class."""

    def test_nuclide_inventory_creation(self):
        """Test creating NuclideInventory."""
        nuclides = [Nuclide(Z=92, A=235), Nuclide(Z=92, A=238)]
        concentrations = np.array([[1e20, 1e21], [2e20, 2e21]])  # [n_nuclides, n_times]
        times = np.array([0, 86400])  # seconds
        burnup = np.array([0.0, 1.0])  # MWd/kgU

        inventory = NuclideInventory(
            nuclides=nuclides,
            concentrations=concentrations,
            times=times,
            burnup=burnup,
        )

        assert len(inventory.nuclides) == 2
        assert inventory.concentrations.shape == (2, 2)

    def test_get_concentration(self):
        """Test getting concentration for a nuclide."""
        u235 = Nuclide(Z=92, A=235)
        u238 = Nuclide(Z=92, A=238)
        nuclides = [u235, u238]
        concentrations = np.array([[1e20, 1e21], [2e20, 2e21]])
        times = np.array([0, 86400])
        burnup = np.array([0.0, 1.0])

        inventory = NuclideInventory(
            nuclides=nuclides,
            concentrations=concentrations,
            times=times,
            burnup=burnup,
        )

        # Get initial concentration
        conc_initial = inventory.get_concentration(u235, time_index=0)
        assert conc_initial == 1e20

        # Get final concentration (default)
        conc_final = inventory.get_concentration(u235)
        assert conc_final == 1e21

    def test_get_total_inventory(self):
        """Test getting total inventory."""
        u235 = Nuclide(Z=92, A=235)
        u238 = Nuclide(Z=92, A=238)
        nuclides = [u235, u238]
        concentrations = np.array([[1e20, 1e21], [2e20, 2e21]])
        times = np.array([0, 86400])
        burnup = np.array([0.0, 1.0])

        inventory = NuclideInventory(
            nuclides=nuclides,
            concentrations=concentrations,
            times=times,
            burnup=burnup,
        )

        total_initial = inventory.get_total_inventory(time_index=0)
        assert total_initial == 3e20  # 1e20 + 2e20

        total_final = inventory.get_total_inventory()
        assert total_final == 3e21  # 1e21 + 2e21


class TestBurnupOptions:
    """Test BurnupOptions dataclass."""

    def test_burnup_options_creation(self):
        """Test creating BurnupOptions."""
        options = BurnupOptions(
            time_steps=[0, 30, 60, 90],
            power_density=1e6,
            initial_enrichment=0.195,
        )

        assert len(options.time_steps) == 4
        assert options.power_density == 1e6
        assert options.initial_enrichment == 0.195
        assert options.track_fission_products is True  # Default
        assert options.track_actinides is True  # Default

    def test_burnup_options_defaults(self):
        """Test BurnupOptions default values."""
        options = BurnupOptions(time_steps=[0, 30])

        assert options.power_density == 1e6  # Default
        assert options.initial_enrichment == 0.195  # Default
        assert len(options.fissile_nuclides) > 0  # Should have defaults

