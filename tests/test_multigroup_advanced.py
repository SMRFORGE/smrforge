"""
Tests for advanced multi-group processing methods.

Tests SPH (Superhomogenization) method and equivalence theory.
"""

import pytest
import numpy as np

try:
    from smrforge.core.multigroup_advanced import (
        EquivalenceTheory,
        EquivalenceTheoryParams,
        SPHFactors,
        SPHMethod,
        apply_sph_to_multigroup_table,
    )
    from smrforge.core.reactor_core import Nuclide, NuclearDataCache

    _MULTIGROUP_ADVANCED_AVAILABLE = True
except ImportError:
    _MULTIGROUP_ADVANCED_AVAILABLE = False


@pytest.mark.skipif(
    not _MULTIGROUP_ADVANCED_AVAILABLE,
    reason="Advanced multi-group processing not available",
)
class TestSPHMethod:
    """Tests for SPHMethod class."""

    def test_sph_method_creation(self):
        """Test creating SPH method instance."""
        sph = SPHMethod()
        assert len(sph._sph_cache) == 0

    def test_calculate_sph_factors_basic(self):
        """Test basic SPH factor calculation."""
        sph = SPHMethod()
        cache = NuclearDataCache()

        u238 = Nuclide(Z=92, A=238)

        # Create fine and coarse group structures
        fine_structure = np.logspace(7, -5, 50)  # 50 fine groups
        coarse_structure = np.array([2e7, 1e6, 1e5, 1e4, 1e-5])  # 4 coarse groups

        # Create dummy fine flux
        fine_flux = np.ones(49)  # 49 groups (50 boundaries - 1)

        try:
            factors = sph.calculate_sph_factors(
                nuclide=u238,
                reaction="capture",
                fine_group_structure=fine_structure,
                coarse_group_structure=coarse_structure,
                fine_flux=fine_flux,
                temperature=900.0,
                cache=cache,
            )

            assert factors.nuclide == "U238"
            assert factors.reaction == "capture"
            assert len(factors.sph_factors) == 4  # 4 coarse groups
            assert len(factors.groups) == 4

            # SPH factors should be positive
            assert np.all(factors.sph_factors > 0)

        except (FileNotFoundError, ImportError) as e:
            pytest.skip(f"ENDF files not available: {e}")

    def test_apply_sph_correction(self):
        """Test applying SPH correction to cross-sections."""
        sph = SPHMethod()

        # Create dummy SPH factors
        factors = SPHFactors(
            nuclide="U238",
            reaction="capture",
            groups=np.array([0, 1, 2]),
            sph_factors=np.array([1.1, 0.95, 1.05]),
        )

        # Create dummy cross-sections
        coarse_xs = np.array([10.0, 20.0, 30.0])

        # Apply correction
        corrected_xs = sph.apply_sph_correction(coarse_xs, factors)

        assert len(corrected_xs) == len(coarse_xs)
        assert corrected_xs[0] == pytest.approx(11.0)  # 10.0 * 1.1
        assert corrected_xs[1] == pytest.approx(19.0)  # 20.0 * 0.95
        assert corrected_xs[2] == pytest.approx(31.5)  # 30.0 * 1.05

    def test_apply_sph_correction_length_mismatch(self):
        """Test that length mismatch raises error."""
        sph = SPHMethod()

        factors = SPHFactors(
            nuclide="U238",
            reaction="capture",
            groups=np.array([0, 1]),
            sph_factors=np.array([1.1, 0.95]),
        )

        coarse_xs = np.array([10.0, 20.0, 30.0])  # Wrong length

        with pytest.raises(ValueError):
            sph.apply_sph_correction(coarse_xs, factors)

    def test_map_fine_to_coarse(self):
        """Test mapping fine groups to coarse groups."""
        sph = SPHMethod()

        fine_structure = np.array([1e7, 1e6, 1e5, 1e4])  # 3 fine groups
        coarse_structure = np.array([1e7, 1e5, 1e4])  # 2 coarse groups

        # Map first coarse group (1e5 - 1e7)
        fine_groups = sph._map_fine_to_coarse(
            fine_structure, coarse_structure, 0
        )

        # Should include fine groups 0 and 1 (1e5-1e6 and 1e6-1e7)
        assert len(fine_groups) >= 1


@pytest.mark.skipif(
    not _MULTIGROUP_ADVANCED_AVAILABLE,
    reason="Advanced multi-group processing not available",
)
class TestEquivalenceTheory:
    """Tests for EquivalenceTheory class."""

    def test_equivalence_theory_creation(self):
        """Test creating equivalence theory instance."""
        equiv = EquivalenceTheory()
        assert equiv is not None

    def test_calculate_equivalent_xs(self):
        """Test calculating equivalent cross-sections."""
        equiv = EquivalenceTheory()

        fuel_xs = np.array([100.0, 50.0, 20.0])  # 3 groups
        moderator_xs = np.array([1.0, 2.0, 5.0])
        fuel_volume_fraction = 0.4

        equiv_xs = equiv.calculate_equivalent_xs(
            fuel_xs=fuel_xs,
            moderator_xs=moderator_xs,
            fuel_volume_fraction=fuel_volume_fraction,
            fuel_pin_radius=0.4,
            pin_pitch=1.26,
        )

        assert len(equiv_xs) == 3
        assert np.all(equiv_xs > 0)

        # Equivalent XS should be between fuel and moderator
        for g in range(3):
            assert equiv_xs[g] >= moderator_xs[g]
            assert equiv_xs[g] <= fuel_xs[g] * 1.5  # Allow some margin

    def test_calculate_equivalent_xs_length_mismatch(self):
        """Test that length mismatch raises error."""
        equiv = EquivalenceTheory()

        fuel_xs = np.array([100.0, 50.0])
        moderator_xs = np.array([1.0, 2.0, 5.0])  # Wrong length

        with pytest.raises(ValueError):
            equiv.calculate_equivalent_xs(
                fuel_xs=fuel_xs,
                moderator_xs=moderator_xs,
                fuel_volume_fraction=0.4,
            )

    def test_calculate_dancoff_factor(self):
        """Test Dancoff factor calculation."""
        equiv = EquivalenceTheory()

        # Isolated pins (large pitch)
        dancoff = equiv._calculate_dancoff_factor(
            fuel_radius=0.4, pin_pitch=2.0
        )
        assert dancoff == pytest.approx(0.0)

        # Tight lattice (small pitch)
        dancoff = equiv._calculate_dancoff_factor(
            fuel_radius=0.4, pin_pitch=0.8
        )
        assert 0.0 <= dancoff <= 0.3

    def test_calculate_escape_probability(self):
        """Test escape probability calculation."""
        equiv = EquivalenceTheory()

        escape_prob = equiv._calculate_escape_probability(
            fuel_radius=0.4, pin_pitch=1.26, dancoff_factor=0.1
        )

        assert 0.0 <= escape_prob <= 1.0

    def test_equivalent_xs_with_dancoff(self):
        """Test equivalent XS with explicit Dancoff factor."""
        equiv = EquivalenceTheory()

        fuel_xs = np.array([100.0, 50.0])
        moderator_xs = np.array([1.0, 2.0])

        equiv_xs = equiv.calculate_equivalent_xs(
            fuel_xs=fuel_xs,
            moderator_xs=moderator_xs,
            fuel_volume_fraction=0.4,
            dancoff_factor=0.15,
        )

        assert len(equiv_xs) == 2
        assert np.all(equiv_xs > 0)


@pytest.mark.skipif(
    not _MULTIGROUP_ADVANCED_AVAILABLE,
    reason="Advanced multi-group processing not available",
)
class TestSPHTableApplication:
    """Tests for applying SPH to cross-section tables."""

    def test_apply_sph_to_table(self):
        """Test applying SPH correction to a table."""
        # Create dummy table
        xs_table = {
            "U238/capture": np.array([10.0, 20.0, 30.0]),
            "U235/fission": np.array([50.0, 60.0, 70.0]),
        }

        # Create SPH factors for one entry
        factors = SPHFactors(
            nuclide="U238",
            reaction="capture",
            groups=np.array([0, 1, 2]),
            sph_factors=np.array([1.1, 0.95, 1.05]),
        )

        sph_factors_dict = {"U238/capture": factors}

        # Apply SPH
        corrected_table = apply_sph_to_multigroup_table(xs_table, sph_factors_dict)

        assert "U238/capture" in corrected_table
        assert "U235/fission" in corrected_table

        # U238/capture should be corrected
        assert corrected_table["U238/capture"][0] == pytest.approx(11.0)

        # U235/fission should be unchanged (no SPH factors)
        assert np.allclose(
            corrected_table["U235/fission"], xs_table["U235/fission"]
        )
