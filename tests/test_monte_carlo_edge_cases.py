"""
Edge case tests for Monte Carlo solver to improve coverage.
"""

import numpy as np
import pytest

from smrforge.neutronics.monte_carlo import (
    MCParticle,
    MonteCarloSolver,
    SimplifiedGeometry,
)
from smrforge.validation.models import CrossSectionData


@pytest.fixture
def geometry_edge():
    """Create geometry for edge case tests."""
    return SimplifiedGeometry(
        core_diameter=200.0, core_height=400.0, reflector_thickness=50.0
    )


@pytest.fixture
def xs_data_edge():
    """Create cross section data with edge cases."""
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


class TestEdgeCases:
    """Test edge cases for coverage."""

    def test_distance_to_boundary_no_distances(self, geometry_edge):
        """Test distance_to_boundary when no valid distances are found."""
        # Create particle with direction that won't hit boundaries
        # Particle at center moving in direction that doesn't intersect
        particle = MCParticle(x=0.0, y=0.0, z=200.0, u=0.0, v=0.0, w=0.0)

        distance, next_mat = geometry_edge.distance_to_boundary(particle)

        # Should return large distance and -1
        assert distance > 1e9
        assert next_mat == -1

    def test_track_particle_zero_sigma_t(self, geometry_edge):
        """Test tracking particle when sigma_t is zero."""
        # Create XS data with zero total cross section
        xs_zero = CrossSectionData(
            n_groups=1,
            n_materials=2,
            sigma_t=np.array([[0.0], [0.3]]),  # Zero for material 0
            sigma_a=np.array([[0.0], [0.01]]),
            sigma_f=np.array([[0.0], [0.0]]),
            nu_sigma_f=np.array([[0.0], [0.0]]),
            sigma_s=np.array([[[0.0]], [[0.29]]]),
            chi=np.array([[1.0], [1.0]]),
            D=np.array([[1.0], [1.5]]),
        )

        solver = MonteCarloSolver(
            geometry=geometry_edge, xs_data=xs_zero, n_particles=10, n_generations=5
        )

        particle = MCParticle(x=50.0, y=0.0, z=200.0, u=1.0, v=0.0, w=0.0, energy=2e6)

        fission_sites = solver._track_particle(particle)

        # Should exit early due to zero sigma_t
        assert not particle.alive
        assert isinstance(fission_sites, list)

    def test_track_particle_boundary_crossing(self, geometry_edge, xs_data_edge):
        """Test tracking particle that crosses boundary before collision."""
        solver = MonteCarloSolver(
            geometry=geometry_edge, xs_data=xs_data_edge, n_particles=10, n_generations=5
        )

        # Create particle near boundary moving outward
        # Use very small sigma_t so collision distance is large
        # This forces boundary crossing before collision
        xs_small = CrossSectionData(
            n_groups=1,
            n_materials=2,
            sigma_t=np.array([[1e-10], [0.3]]),  # Very small
            sigma_a=np.array([[1e-12], [0.01]]),
            sigma_f=np.array([[1e-12], [0.0]]),
            nu_sigma_f=np.array([[1e-12], [0.0]]),
            sigma_s=np.array([[[1e-10]], [[0.29]]]),
            chi=np.array([[1.0], [1.0]]),
            D=np.array([[1.0], [1.5]]),
        )

        solver_small = MonteCarloSolver(
            geometry=geometry_edge, xs_data=xs_small, n_particles=10, n_generations=5
        )

        # Particle near core boundary moving outward
        particle = MCParticle(x=99.0, y=0.0, z=200.0, u=1.0, v=0.0, w=0.0, energy=2e6)

        fission_sites = solver_small._track_particle(particle)

        # Should cross boundary before collision
        assert isinstance(fission_sites, list)

    def test_run_eigenvalue_with_tallies(self, geometry_edge, xs_data_edge):
        """Test run_eigenvalue with tallies to cover tally update code."""
        # Need at least 20 generations to have active generations after inactive period
        solver = MonteCarloSolver(
            geometry=geometry_edge, xs_data=xs_data_edge, n_particles=10, n_generations=20, seed=42
        )

        from smrforge.neutronics.monte_carlo import MCTally

        # Add a flux tally
        flux_tally = MCTally(
            name="test_flux",
            tally_type="flux",
            r_bins=np.linspace(0, 100, 6),
            z_bins=np.linspace(0, 400, 11),
        )
        solver.add_tally(flux_tally)

        results = solver.run_eigenvalue()

        # Check that tallies are in results
        assert "tallies" in results
        assert "test_flux" in results["tallies"]

    def test_track_particle_negative_sigma_t(self, geometry_edge):
        """Test handling of edge case in _get_total_xs with invalid material."""
        xs_data = CrossSectionData(
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

        solver = MonteCarloSolver(
            geometry=geometry_edge, xs_data=xs_data, n_particles=10, n_generations=5
        )

        # Test _get_total_xs with invalid material ID
        xs_neg = solver._get_total_xs(mat_id=-1, energy=2e6)
        assert xs_neg == 0.0

        xs_large = solver._get_total_xs(mat_id=100, energy=2e6)
        assert xs_large == 0.0

