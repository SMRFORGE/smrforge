"""
Tests for Monte Carlo neutronics solver.
"""

import numpy as np
import pytest

from smrforge.neutronics.monte_carlo import (
    MCParticle,
    MCTally,
    MonteCarloSolver,
    ReactionType,
    SimplifiedGeometry,
)
from smrforge.validation.models import CrossSectionData


@pytest.fixture
def simple_geometry():
    """Create a simple geometry for testing."""
    return SimplifiedGeometry(
        core_diameter=200.0, core_height=400.0, reflector_thickness=50.0
    )


@pytest.fixture
def simple_xs_data():
    """Create simple 1-group cross section data."""
    return CrossSectionData(
        n_groups=1,
        n_materials=2,
        sigma_t=np.array([[0.5], [0.3]]),
        sigma_a=np.array([[0.05], [0.01]]),
        sigma_f=np.array([[0.04], [0.0]]),
        nu_sigma_f=np.array([[0.10], [0.0]]),
        sigma_s=np.array([[[0.41]], [[0.29]]]),
        chi=np.array([[1.0], [1.0]]),
        D=np.array([[1.0], [1.5]]),
    )


@pytest.fixture
def mc_solver(simple_geometry, simple_xs_data):
    """Create a Monte Carlo solver instance."""
    return MonteCarloSolver(
        geometry=simple_geometry,
        xs_data=simple_xs_data,
        n_particles=100,
        n_generations=10,
        seed=42,  # Fixed seed for reproducibility
    )


class TestMCParticle:
    """Test MCParticle class."""

    def test_particle_creation(self):
        """Test creating a particle."""
        particle = MCParticle(
            x=1.0, y=2.0, z=3.0, u=0.5, v=0.5, w=0.707, energy=2e6, weight=1.0
        )

        assert particle.x == 1.0
        assert particle.y == 2.0
        assert particle.z == 3.0
        assert particle.u == 0.5
        assert particle.v == 0.5
        assert particle.w == 0.707
        assert particle.energy == 2e6
        assert particle.weight == 1.0
        assert particle.alive is True
        assert particle.generation == 0

    def test_particle_defaults(self):
        """Test particle default values."""
        particle = MCParticle()

        assert particle.x == 0.0
        assert particle.y == 0.0
        assert particle.z == 0.0
        assert particle.u == 0.0
        assert particle.v == 0.0
        assert particle.w == 1.0
        assert particle.energy == 2e6
        assert particle.weight == 1.0
        assert particle.alive is True

    def test_particle_position(self):
        """Test position property."""
        particle = MCParticle(x=1.0, y=2.0, z=3.0)
        pos = particle.position()

        assert isinstance(pos, np.ndarray)
        assert np.allclose(pos, [1.0, 2.0, 3.0])

    def test_particle_direction(self):
        """Test direction property."""
        particle = MCParticle(u=0.5, v=0.5, w=0.707)
        dir_vec = particle.direction()

        assert isinstance(dir_vec, np.ndarray)
        assert np.allclose(dir_vec, [0.5, 0.5, 0.707])


class TestMCTally:
    """Test MCTally class."""

    def test_tally_creation(self):
        """Test creating a tally."""
        tally = MCTally(name="test_tally", tally_type="flux")

        assert tally.name == "test_tally"
        assert tally.tally_type == "flux"
        assert tally.score == 0.0
        assert tally.score_sq == 0.0
        assert tally.count == 0

    def test_tally_with_bins(self):
        """Test tally with spatial bins."""
        r_bins = np.linspace(0, 100, 11)
        z_bins = np.linspace(0, 400, 21)
        tally = MCTally(
            name="flux_tally", tally_type="flux", r_bins=r_bins, z_bins=z_bins
        )

        assert tally.r_bins is not None
        assert tally.z_bins is not None
        assert tally.bin_scores is not None
        assert tally.bin_scores.shape == (10, 20)
        assert tally.bin_scores_sq.shape == (10, 20)
        assert tally.bin_counts.shape == (10, 20)

    def test_tally_add_score(self):
        """Test adding score to tally."""
        tally = MCTally(name="test", tally_type="flux")
        tally.add_score(1.5)

        assert tally.score == 1.5
        assert tally.score_sq == 1.5**2
        assert tally.count == 1

        tally.add_score(2.0)
        assert tally.score == 3.5
        assert tally.score_sq == 1.5**2 + 2.0**2
        assert tally.count == 2

    def test_tally_add_score_with_position(self):
        """Test adding score with position binning."""
        r_bins = np.linspace(0, 100, 11)
        z_bins = np.linspace(0, 400, 21)
        tally = MCTally(
            name="flux_tally", tally_type="flux", r_bins=r_bins, z_bins=z_bins
        )

        tally.add_score(1.0, position=(50.0, 200.0))

        # Check that bin was updated
        ir = np.searchsorted(r_bins, 50.0) - 1
        iz = np.searchsorted(z_bins, 200.0) - 1
        assert tally.bin_scores[ir, iz] == 1.0
        assert tally.bin_counts[ir, iz] == 1

    def test_tally_mean(self):
        """Test tally mean calculation."""
        tally = MCTally(name="test", tally_type="flux")
        assert tally.mean == 0.0  # No scores yet

        tally.add_score(1.0)
        tally.add_score(2.0)
        tally.add_score(3.0)

        assert tally.mean == 2.0

    def test_tally_std(self):
        """Test tally standard deviation."""
        tally = MCTally(name="test", tally_type="flux")

        # Need at least 2 scores
        tally.add_score(1.0)
        assert tally.std == 0.0  # Only one score

        tally.add_score(2.0)
        tally.add_score(3.0)

        # Mean = 2.0, variance = ((1-2)^2 + (2-2)^2 + (3-2)^2)/3 = 2/3
        # std = sqrt(variance/count) = sqrt((2/3)/3) = sqrt(2/9)
        std = tally.std
        assert std > 0
        assert np.isfinite(std)

    def test_tally_relative_error(self):
        """Test tally relative error."""
        tally = MCTally(name="test", tally_type="flux")

        # Zero mean
        assert tally.relative_error == float("inf")

        tally.add_score(1.0)
        tally.add_score(1.0)

        # Non-zero mean, should have finite relative error
        rel_err = tally.relative_error
        assert np.isfinite(rel_err)
        assert rel_err >= 0


class TestSimplifiedGeometry:
    """Test SimplifiedGeometry class."""

    def test_geometry_creation(self):
        """Test creating geometry."""
        geometry = SimplifiedGeometry(
            core_diameter=200.0, core_height=400.0, reflector_thickness=50.0
        )

        assert geometry.r_core == 100.0
        assert geometry.h_core == 400.0
        assert geometry.r_reflector == 150.0

    def test_get_material_fuel(self, simple_geometry):
        """Test getting material in fuel region."""
        mat_id = simple_geometry.get_material(x=50.0, y=0.0, z=200.0)
        assert mat_id == 0  # Fuel

    def test_get_material_reflector(self, simple_geometry):
        """Test getting material in reflector region."""
        mat_id = simple_geometry.get_material(x=120.0, y=0.0, z=200.0)
        assert mat_id == 1  # Reflector

    def test_get_material_outside(self, simple_geometry):
        """Test getting material outside geometry."""
        # Outside radially
        mat_id = simple_geometry.get_material(x=200.0, y=0.0, z=200.0)
        assert mat_id == -1  # Outside

        # Outside axially (below)
        mat_id = simple_geometry.get_material(x=50.0, y=0.0, z=-10.0)
        assert mat_id == -1

        # Outside axially (above)
        mat_id = simple_geometry.get_material(x=50.0, y=0.0, z=500.0)
        assert mat_id == -1

    def test_distance_to_boundary_inside(self, simple_geometry):
        """Test distance to boundary from inside."""
        particle = MCParticle(x=50.0, y=0.0, z=200.0, u=1.0, v=0.0, w=0.0)
        distance, next_mat = simple_geometry.distance_to_boundary(particle)

        assert distance > 0
        assert next_mat in [1, -1]  # Reflector or outside

    def test_distance_to_boundary_radial(self, simple_geometry):
        """Test distance to radial boundary."""
        # Particle moving radially outward from center
        particle = MCParticle(x=0.0, y=0.0, z=200.0, u=1.0, v=0.0, w=0.0)
        distance, next_mat = simple_geometry.distance_to_boundary(particle)

        # Should hit core boundary at r=100
        assert abs(distance - 100.0) < 1.0
        assert next_mat == 1  # Entering reflector

    def test_distance_to_boundary_axial(self, simple_geometry):
        """Test distance to axial boundary."""
        # Particle moving upward
        particle = MCParticle(x=50.0, y=0.0, z=300.0, u=0.0, v=0.0, w=1.0)
        distance, next_mat = simple_geometry.distance_to_boundary(particle)

        # Should hit top at z=400
        assert abs(distance - 100.0) < 1.0
        assert next_mat == -1  # Escaping


class TestMonteCarloSolver:
    """Test MonteCarloSolver class."""

    def test_solver_creation(self, simple_geometry, simple_xs_data):
        """Test creating solver."""
        solver = MonteCarloSolver(
            geometry=simple_geometry,
            xs_data=simple_xs_data,
            n_particles=1000,
            n_generations=50,
        )

        assert solver.geometry == simple_geometry
        assert solver.xs_data == simple_xs_data
        assert solver.n_particles == 1000
        assert solver.n_generations == 50
        assert len(solver.tallies) == 0
        assert len(solver.k_eff_history) == 0

    def test_add_tally(self, mc_solver):
        """Test adding a tally."""
        tally = MCTally(name="test_flux", tally_type="flux")
        mc_solver.add_tally(tally)

        assert "test_flux" in mc_solver.tallies
        assert mc_solver.tallies["test_flux"] == tally

    def test_initialize_source(self, mc_solver):
        """Test source initialization."""
        source = mc_solver._initialize_source()

        assert len(source) == mc_solver.n_particles
        for particle in source:
            assert isinstance(particle, MCParticle)
            assert particle.alive is True
            # Check particle is in core (roughly)
            r = np.sqrt(particle.x**2 + particle.y**2)
            assert r < mc_solver.geometry.r_core * 1.1  # Allow some margin
            assert 0 <= particle.z <= mc_solver.geometry.h_core

    def test_sample_isotropic_direction(self, mc_solver):
        """Test isotropic direction sampling."""
        u, v, w = mc_solver._sample_isotropic_direction()

        # Check direction is normalized
        norm = np.sqrt(u**2 + v**2 + w**2)
        assert np.isclose(norm, 1.0, rtol=1e-5)

        # Check multiple samples are different
        dirs = [mc_solver._sample_isotropic_direction() for _ in range(10)]
        # At least some should be different
        assert len(set(dirs)) > 1

    def test_sample_fission_spectrum(self, mc_solver):
        """Test fission spectrum sampling."""
        energies = [mc_solver._sample_fission_spectrum() for _ in range(100)]

        # All should be positive
        assert all(e > 0 for e in energies)

        # Should have some variance
        assert np.std(energies) > 0

    def test_get_total_xs(self, mc_solver):
        """Test getting total cross section."""
        xs = mc_solver._get_total_xs(mat_id=0, energy=2e6)
        assert xs > 0
        assert xs == mc_solver.xs_data.sigma_t[0, 0]

        # Invalid material
        xs = mc_solver._get_total_xs(mat_id=10, energy=2e6)
        assert xs == 0.0

    def test_sample_reaction(self, mc_solver):
        """Test reaction type sampling."""
        # Sample multiple reactions
        reactions = [
            mc_solver._sample_reaction(mat_id=0, energy=2e6) for _ in range(100)
        ]

        # Should have at least some reactions
        assert len(reactions) == 100
        # All should be valid ReactionType
        assert all(isinstance(r, ReactionType) for r in reactions)

        # Should have some variation (not all the same)
        unique_reactions = set(reactions)
        assert len(unique_reactions) > 1

    def test_resample_source(self, mc_solver):
        """Test source resampling."""
        # Create a fission bank
        fission_bank = [
            MCParticle(x=50.0, y=0.0, z=200.0, energy=2e6, weight=1.0)
            for _ in range(50)
        ]

        source = mc_solver._resample_source(fission_bank, n_target=100)

        assert len(source) == 100
        for particle in source:
            assert particle.alive is True
            # Direction and energy should be resampled
            assert particle.u != 0 or particle.v != 0 or particle.w != 0

    def test_resample_source_empty(self, mc_solver):
        """Test resampling with empty bank."""
        source = mc_solver._resample_source([], n_target=100)

        # Should initialize new source
        assert len(source) == 100

    def test_track_particle(self, mc_solver):
        """Test tracking a particle."""
        particle = MCParticle(x=50.0, y=0.0, z=200.0, u=1.0, v=0.0, w=0.0, energy=2e6)

        fission_sites = mc_solver._track_particle(particle)

        # Particle should be processed
        # May or may not produce fissions depending on random sampling
        assert isinstance(fission_sites, list)

    def test_track_particle_outside(self, mc_solver):
        """Test tracking particle that starts outside."""
        particle = MCParticle(x=200.0, y=0.0, z=200.0, u=1.0, v=0.0, w=0.0, energy=2e6)

        fission_sites = mc_solver._track_particle(particle)

        # Should exit immediately
        assert len(fission_sites) == 0
        assert not particle.alive

    def test_score_tallies(self, mc_solver):
        """Test scoring tallies."""
        tally = MCTally(name="flux", tally_type="flux")
        mc_solver.add_tally(tally)

        particle = MCParticle(x=50.0, y=0.0, z=200.0, energy=2e6, weight=1.0)
        distance = 1.0

        initial_score = tally.score
        mc_solver._score_tallies(particle, distance)

        # Score should have increased
        assert tally.score > initial_score

    def test_run_eigenvalue_small(self, mc_solver):
        """Test running eigenvalue calculation with small parameters."""
        # Use small parameters for fast test
        # Need at least 20 generations to have active generations after inactive period
        solver = MonteCarloSolver(
            geometry=mc_solver.geometry,
            xs_data=mc_solver.xs_data,
            n_particles=10,
            n_generations=20,
            seed=42,
        )

        results = solver.run_eigenvalue()

        assert "k_eff" in results
        assert "k_std" in results
        assert "k_history" in results
        assert "tallies" in results
        assert isinstance(results["k_eff"], float)
        assert len(results["k_history"]) == 20

    def test_print_results(self, mc_solver):
        """Test printing results."""
        tally = MCTally(name="test_flux", tally_type="flux")
        tally.add_score(1.0)
        mc_solver.add_tally(tally)

        # Should not raise
        mc_solver.print_results()
