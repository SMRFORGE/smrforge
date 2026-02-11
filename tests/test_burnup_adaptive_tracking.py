"""
Tests for adaptive nuclide tracking in burnup solver.
"""

import numpy as np
import pytest

from smrforge.burnup import BurnupOptions, BurnupSolver
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


class TestAdaptiveNuclideTracking:
    """Test adaptive nuclide tracking feature."""

    def test_adaptive_tracking_initialization(self, simple_neutronics):
        """Test burnup solver can be initialized with adaptive tracking."""
        options = BurnupOptions(
            time_steps=[0, 30, 60],  # days
            power_density=1e6,  # W/cm³
            initial_enrichment=0.195,
            adaptive_tracking=True,
            nuclide_threshold=1e15,  # atoms/cm³
            nuclide_importance_threshold=1e-3,
            adaptive_update_interval=5,
        )

        burnup = BurnupSolver(simple_neutronics, options)

        assert burnup is not None
        assert burnup.options.adaptive_tracking is True
        assert hasattr(burnup, "_always_track")
        assert hasattr(burnup, "_last_adaptive_update")
        assert len(burnup.nuclides) > 0

    def test_adaptive_tracking_disabled(self, simple_neutronics):
        """Test adaptive tracking is disabled by default."""
        options = BurnupOptions(
            time_steps=[0, 30],
            initial_enrichment=0.195,
        )

        burnup = BurnupSolver(simple_neutronics, options)

        assert burnup.options.adaptive_tracking is False
        assert burnup._last_adaptive_update == -1

    def test_always_track_nuclides(self, simple_neutronics):
        """Test that always-track nuclides are set correctly."""
        u235 = Nuclide(Z=92, A=235)
        u238 = Nuclide(Z=92, A=238)
        pu239 = Nuclide(Z=94, A=239)

        options = BurnupOptions(
            time_steps=[0, 30],
            initial_enrichment=0.195,
            adaptive_tracking=True,
            always_track_nuclides=[pu239],
        )

        burnup = BurnupSolver(simple_neutronics, options)

        # U-235 and U-238 should be in always_track (fissile/fertile)
        assert u235 in burnup._always_track
        assert u238 in burnup._always_track
        assert pu239 in burnup._always_track

    def test_identify_nuclides_to_remove(self, simple_neutronics):
        """Test identification of nuclides to remove."""
        options = BurnupOptions(
            time_steps=[0, 30],
            initial_enrichment=0.195,
            adaptive_tracking=True,
            nuclide_threshold=1e20,  # High threshold
            nuclide_importance_threshold=0.01,
        )

        burnup = BurnupSolver(simple_neutronics, options)

        # Set some concentrations to low values
        time_index = 0
        u235 = Nuclide(Z=92, A=235)
        u238 = Nuclide(Z=92, A=238)

        # U-235 and U-238 should not be removed (always tracked)
        nuclides_to_remove = burnup._identify_nuclides_to_remove(time_index)

        assert u235 not in nuclides_to_remove
        assert u238 not in nuclides_to_remove

        # The method should return a list
        assert isinstance(nuclides_to_remove, list)

    def test_identify_nuclides_to_add(self, simple_neutronics):
        """Test identification of nuclides to add."""
        options = BurnupOptions(
            time_steps=[0, 30],
            initial_enrichment=0.195,
            adaptive_tracking=True,
            nuclide_importance_threshold=0.001,
        )

        burnup = BurnupSolver(simple_neutronics, options)

        time_index = 0
        nuclides_to_add = burnup._identify_nuclides_to_add(time_index)

        # Should return a list (may be empty if no yields available)
        assert isinstance(nuclides_to_add, list)

    def test_update_adaptive_nuclides(self, simple_neutronics):
        """Test adaptive nuclide update method."""
        options = BurnupOptions(
            time_steps=[0, 30, 60, 90],
            initial_enrichment=0.195,
            adaptive_tracking=True,
            adaptive_update_interval=2,
        )

        burnup = BurnupSolver(simple_neutronics, options)

        # Should not update before interval
        initial_update = burnup._last_adaptive_update
        burnup._update_adaptive_nuclides(0)
        assert burnup._last_adaptive_update == initial_update

        # Should update after interval
        burnup._update_adaptive_nuclides(2)
        assert burnup._last_adaptive_update == 2

    def test_adaptive_tracking_options(self, simple_neutronics):
        """Test adaptive tracking configuration options."""
        options = BurnupOptions(
            time_steps=[0, 30],
            initial_enrichment=0.195,
            adaptive_tracking=True,
            nuclide_threshold=1e16,
            nuclide_importance_threshold=0.005,
            adaptive_update_interval=10,
        )

        burnup = BurnupSolver(simple_neutronics, options)

        assert burnup.options.nuclide_threshold == 1e16
        assert burnup.options.nuclide_importance_threshold == 0.005
        assert burnup.options.adaptive_update_interval == 10

    def test_adaptive_tracking_integration(self, simple_neutronics):
        """Test adaptive tracking integrates with solve loop (without actually solving)."""
        options = BurnupOptions(
            time_steps=[0, 10],  # Short time steps for testing
            initial_enrichment=0.195,
            adaptive_tracking=True,
            adaptive_update_interval=1,  # Update every step
        )

        burnup = BurnupSolver(simple_neutronics, options)

        # Verify initialization
        assert burnup.options.adaptive_tracking is True
        assert hasattr(burnup, "_update_adaptive_nuclides")
        assert callable(burnup._update_adaptive_nuclides)
