"""
Validation and error handling tests for Monte Carlo solver.
"""

import numpy as np
import pytest

from smrforge.neutronics.monte_carlo import (
    MCParticle,
    MCTally,
    MonteCarloSolver,
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


class TestMonteCarloValidation:
    """Test input validation for Monte Carlo solver."""

    def test_invalid_geometry_type(self, simple_xs_data):
        """Test that invalid geometry type raises ValueError."""
        with pytest.raises(ValueError, match="geometry must be SimplifiedGeometry"):
            MonteCarloSolver(
                geometry="invalid",
                xs_data=simple_xs_data,
                n_particles=100,
                n_generations=10,
            )

    def test_invalid_xs_data_type(self, simple_geometry):
        """Test that invalid xs_data type raises ValueError."""
        with pytest.raises(ValueError, match="xs_data must be CrossSectionData"):
            MonteCarloSolver(
                geometry=simple_geometry,
                xs_data="invalid",
                n_particles=100,
                n_generations=10,
            )

    def test_invalid_n_particles_zero(self, simple_geometry, simple_xs_data):
        """Test that n_particles=0 raises ValueError."""
        with pytest.raises(ValueError, match="n_particles must be > 0"):
            MonteCarloSolver(
                geometry=simple_geometry,
                xs_data=simple_xs_data,
                n_particles=0,
                n_generations=10,
            )

    def test_invalid_n_particles_negative(self, simple_geometry, simple_xs_data):
        """Test that negative n_particles raises ValueError."""
        with pytest.raises(ValueError, match="n_particles must be > 0"):
            MonteCarloSolver(
                geometry=simple_geometry,
                xs_data=simple_xs_data,
                n_particles=-10,
                n_generations=10,
            )

    def test_invalid_n_generations_zero(self, simple_geometry, simple_xs_data):
        """Test that n_generations=0 raises ValueError."""
        with pytest.raises(ValueError, match="n_generations must be > 0"):
            MonteCarloSolver(
                geometry=simple_geometry,
                xs_data=simple_xs_data,
                n_particles=100,
                n_generations=0,
            )

    def test_invalid_n_generations_negative(self, simple_geometry, simple_xs_data):
        """Test that negative n_generations raises ValueError."""
        with pytest.raises(ValueError, match="n_generations must be > 0"):
            MonteCarloSolver(
                geometry=simple_geometry,
                xs_data=simple_xs_data,
                n_particles=100,
                n_generations=-10,
            )

    def test_invalid_xs_data_zero_groups(self, simple_geometry):
        """Test that xs_data with zero groups is caught by Pydantic."""
        # Pydantic validation catches this before our validation
        # So we test that Pydantic catches it
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            CrossSectionData(
                n_groups=0,  # Invalid - caught by Pydantic
                n_materials=2,
                sigma_t=np.array([[]]),
                sigma_a=np.array([[]]),
                sigma_f=np.array([[]]),
                nu_sigma_f=np.array([[]]),
                sigma_s=np.array([[]]),
                chi=np.array([[]]),
                D=np.array([[]]),
            )

    def test_seed_parameter(self, simple_geometry, simple_xs_data):
        """Test that seed parameter works for reproducibility."""
        solver1 = MonteCarloSolver(
            geometry=simple_geometry,
            xs_data=simple_xs_data,
            n_particles=10,
            n_generations=5,
            seed=42,
        )

        solver2 = MonteCarloSolver(
            geometry=simple_geometry,
            xs_data=simple_xs_data,
            n_particles=10,
            n_generations=5,
            seed=42,
        )

        # Both should produce same results with same seed
        # Sample a few random numbers
        r1 = [solver1.rng.random() for _ in range(5)]
        r2 = [solver2.rng.random() for _ in range(5)]

        assert np.allclose(r1, r2)

    def test_seed_none(self, simple_geometry, simple_xs_data):
        """Test that seed=None works (random seed)."""
        solver = MonteCarloSolver(
            geometry=simple_geometry,
            xs_data=simple_xs_data,
            n_particles=100,
            n_generations=10,
            seed=None,
        )

        assert solver.rng is not None

    def test_add_tally_invalid_type(self, simple_geometry, simple_xs_data):
        """Test that adding invalid tally type raises ValueError."""
        solver = MonteCarloSolver(
            geometry=simple_geometry,
            xs_data=simple_xs_data,
            n_particles=100,
            n_generations=10,
        )

        with pytest.raises(ValueError, match="tally must be MCTally"):
            solver.add_tally("invalid")

    def test_sample_reaction_invalid_material(self, simple_geometry, simple_xs_data):
        """Test that invalid material ID in _sample_reaction raises IndexError."""
        solver = MonteCarloSolver(
            geometry=simple_geometry,
            xs_data=simple_xs_data,
            n_particles=100,
            n_generations=10,
        )

        with pytest.raises(IndexError):
            solver._sample_reaction(mat_id=-1, energy=2e6)

        with pytest.raises(IndexError):
            solver._sample_reaction(mat_id=100, energy=2e6)

    def test_sample_reaction_zero_sigma_t(self, simple_geometry):
        """Test that zero sigma_t in _sample_reaction raises ValueError."""
        xs_zero = CrossSectionData(
            n_groups=1,
            n_materials=1,
            sigma_t=np.array([[0.0]]),  # Zero total
            sigma_a=np.array([[0.0]]),
            sigma_f=np.array([[0.0]]),
            nu_sigma_f=np.array([[0.0]]),
            sigma_s=np.array([[[0.0]]]),
            chi=np.array([[1.0]]),
            D=np.array([[1.0]]),
        )

        solver = MonteCarloSolver(
            geometry=simple_geometry,
            xs_data=xs_zero,
            n_particles=100,
            n_generations=10,
        )

        with pytest.raises(ValueError, match="Invalid total cross section"):
            solver._sample_reaction(mat_id=0, energy=2e6)

    def test_run_eigenvalue_too_few_generations(self, simple_geometry, simple_xs_data):
        """Test that too few generations raises RuntimeError."""
        solver = MonteCarloSolver(
            geometry=simple_geometry,
            xs_data=simple_xs_data,
            n_particles=10,
            n_generations=5,  # Very few generations - all will be inactive
        )

        # With only 5 generations and n_inactive = max(10, 5//10) = 10,
        # all generations will be inactive, so this should raise RuntimeError
        with pytest.raises(RuntimeError, match="All.*generations were inactive"):
            solver.run_eigenvalue()

    def test_run_eigenvalue_success_with_enough_generations(
        self, simple_geometry, simple_xs_data
    ):
        """Test that eigenvalue calculation succeeds with enough generations."""
        solver = MonteCarloSolver(
            geometry=simple_geometry,
            xs_data=simple_xs_data,
            n_particles=10,
            n_generations=20,  # Enough generations
            seed=42,
        )

        results = solver.run_eigenvalue()

        assert "k_eff" in results
        assert "k_std" in results
        assert "k_history" in results
        assert "tallies" in results
        assert np.isfinite(results["k_eff"])
        assert np.isfinite(results["k_std"])
