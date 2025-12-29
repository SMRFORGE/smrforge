"""
Tests for Transport class (high-level interface).
"""

import numpy as np
import pytest

try:
    from smrforge.neutronics.transport import (
        Cylinder,
        Material,
        Neutron,
        Region,
        Sphere,
        Tally,
        Transport,
        CrossSection,
        FluxTally,
    )
except ImportError:
    pytest.skip("Transport module not available", allow_module_level=True)


@pytest.fixture
def simple_setup():
    """Create a simple transport setup."""
    sphere = Sphere(center=np.array([0.0, 0.0, 0.0]), radius=10.0)
    energy_grid = np.array([0.001, 0.1, 1.0, 10.0])
    xs = CrossSection(
        energy_grid=energy_grid,
        total=np.array([8.0, 7.0, 6.5, 6.0]),
        scatter=np.array([6.0, 5.5, 5.0, 4.5]),
        absorption=np.array([1.5, 1.0, 0.8, 0.6]),
        fission=np.array([2.5, 2.0, 1.5, 1.0]),
        nu=np.array([2.5, 2.5, 2.5, 2.5]),
    )
    material = Material(name="U-235", density=19.1, cross_section=xs, atomic_mass=235.0)
    region = Region(geometry=sphere, material=material)

    def source():
        return Neutron(
            position=np.array([0.0, 0.0, 0.0]),
            direction=np.array([1.0, 0.0, 0.0]),
            energy=2.0,
        )

    return region, source


class TestTransportCreation:
    """Test Transport class creation and validation."""

    def test_transport_creation(self, simple_setup):
        """Test creating Transport instance."""
        region, source = simple_setup

        transport = Transport(regions=[region], source=source, seed=42)

        assert len(transport.regions) == 1
        assert transport.n_histories == 0
        assert transport.n_collisions == 0

    def test_transport_invalid_regions_not_list(self, simple_setup):
        """Test that non-list regions raises ValueError."""
        _, source = simple_setup

        with pytest.raises(ValueError, match="regions must be a list"):
            Transport(regions="invalid", source=source)

    def test_transport_empty_regions(self, simple_setup):
        """Test that empty regions list raises ValueError."""
        _, source = simple_setup

        with pytest.raises(ValueError, match="regions list cannot be empty"):
            Transport(regions=[], source=source)

    def test_transport_invalid_region_type(self, simple_setup):
        """Test that invalid region type raises ValueError."""
        _, source = simple_setup

        with pytest.raises(ValueError, match="must be Region"):
            Transport(regions=["invalid"], source=source)

    def test_transport_invalid_source_not_callable(self, simple_setup):
        """Test that non-callable source raises ValueError."""
        region, _ = simple_setup

        with pytest.raises(ValueError, match="source must be callable"):
            Transport(regions=[region], source="invalid")

    def test_transport_seed_parameter(self, simple_setup):
        """Test that seed parameter works."""
        region, source = simple_setup

        transport1 = Transport(regions=[region], source=source, seed=42)
        transport2 = Transport(regions=[region], source=source, seed=42)

        # Both should work (seed passed to engine)
        assert transport1.n_histories == 0
        assert transport2.n_histories == 0


class TestTransportMethods:
    """Test Transport class methods."""

    def test_add_tally(self, simple_setup):
        """Test adding a tally."""
        region, source = simple_setup
        transport = Transport(regions=[region], source=source)

        flux_tally = FluxTally(name="flux", region=region)
        transport.add_tally(flux_tally)

        assert len(transport.tallies) == 1
        assert transport.tallies[0] == flux_tally

    def test_add_tally_invalid_type(self, simple_setup):
        """Test that invalid tally type raises ValueError."""
        region, source = simple_setup
        transport = Transport(regions=[region], source=source)

        with pytest.raises(ValueError, match="tally must be Tally"):
            transport.add_tally("invalid")

    def test_enable_variance_reduction(self, simple_setup):
        """Test enabling variance reduction."""
        region, source = simple_setup
        transport = Transport(regions=[region], source=source)

        transport.enable_variance_reduction(importance_map=None, weight_window=True)
        # Should not raise exception

    def test_run_batch(self, simple_setup):
        """Test run_batch method."""
        region, source = simple_setup
        transport = Transport(regions=[region], source=source, seed=42)

        result = transport.run_batch(n_histories=10)

        assert "k_eff" in result
        assert "n_histories" in result
        assert "n_collisions" in result
        assert result["n_histories"] == 10
        assert transport.n_histories == 10

    def test_run_batch_invalid_n_histories(self, simple_setup):
        """Test run_batch with invalid n_histories."""
        region, source = simple_setup
        transport = Transport(regions=[region], source=source)

        with pytest.raises(ValueError, match="n_histories must be >= 0"):
            transport.run_batch(n_histories=-1)

    def test_run_eigenvalue(self, simple_setup):
        """Test run_eigenvalue method."""
        region, source = simple_setup
        transport = Transport(regions=[region], source=source, seed=42)

        # Run with small numbers for speed
        result = transport.run_eigenvalue(
            n_generations=5, n_per_generation=10, n_skip=2
        )

        assert "k_eff_mean" in result
        assert "k_eff_std" in result
        assert "k_eff_history" in result
        assert "n_generations" in result
        assert "n_per_generation" in result
        assert result["n_generations"] == 5
        assert len(result["k_eff_history"]) == 5
        assert np.isfinite(result["k_eff_mean"])

    def test_run_eigenvalue_invalid_n_generations(self, simple_setup):
        """Test run_eigenvalue with invalid n_generations."""
        region, source = simple_setup
        transport = Transport(regions=[region], source=source)

        with pytest.raises(ValueError, match="n_generations must be > 0"):
            transport.run_eigenvalue(n_generations=0)

    def test_run_eigenvalue_invalid_n_per_generation(self, simple_setup):
        """Test run_eigenvalue with invalid n_per_generation."""
        region, source = simple_setup
        transport = Transport(regions=[region], source=source)

        with pytest.raises(ValueError, match="n_per_generation must be > 0"):
            transport.run_eigenvalue(n_generations=10, n_per_generation=0)

    def test_run_eigenvalue_invalid_n_skip_negative(self, simple_setup):
        """Test run_eigenvalue with negative n_skip."""
        region, source = simple_setup
        transport = Transport(regions=[region], source=source)

        with pytest.raises(ValueError, match="n_skip must be >= 0"):
            transport.run_eigenvalue(n_generations=10, n_skip=-1)

    def test_run_eigenvalue_invalid_n_skip_too_large(self, simple_setup):
        """Test run_eigenvalue with n_skip >= n_generations."""
        region, source = simple_setup
        transport = Transport(regions=[region], source=source)

        with pytest.raises(ValueError, match="n_skip.*must be < n_generations"):
            transport.run_eigenvalue(n_generations=10, n_skip=10)

    def test_tallies_property(self, simple_setup):
        """Test tallies property."""
        region, source = simple_setup
        transport = Transport(regions=[region], source=source)

        flux_tally = FluxTally(name="flux", region=region)
        transport.add_tally(flux_tally)

        assert len(transport.tallies) == 1
        assert transport.tallies[0] == flux_tally

    def test_n_histories_property(self, simple_setup):
        """Test n_histories property."""
        region, source = simple_setup
        transport = Transport(regions=[region], source=source, seed=42)

        assert transport.n_histories == 0

        transport.run_batch(n_histories=5)
        assert transport.n_histories == 5

    def test_n_collisions_property(self, simple_setup):
        """Test n_collisions property."""
        region, source = simple_setup
        transport = Transport(regions=[region], source=source, seed=42)

        assert transport.n_collisions == 0

        transport.run_batch(n_histories=5)
        assert transport.n_collisions >= 0

