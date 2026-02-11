"""
Unit tests for material mapping module.
"""

import numpy as np
import pytest

from smrforge.core.material_mapping import (
    MaterialComposition,
    MaterialMapper,
)


class TestMaterialComposition:
    """Tests for MaterialComposition dataclass."""

    def test_material_composition_creation(self):
        """Test creating MaterialComposition."""
        comp = MaterialComposition(elements=["H", "O"], fractions=[2.0, 1.0])

        assert comp.elements == ["H", "O"]
        # Fractions should be normalized
        assert np.isclose(sum(comp.fractions), 1.0)

    def test_material_composition_normalization(self):
        """Test that fractions are normalized."""
        comp = MaterialComposition(
            elements=["H", "O"],
            fractions=[2.0, 1.0],  # Sums to 3.0, should normalize to [2/3, 1/3]
        )

        assert np.isclose(comp.fractions[0], 2.0 / 3.0)
        assert np.isclose(comp.fractions[1], 1.0 / 3.0)
        assert np.isclose(sum(comp.fractions), 1.0)

    def test_material_composition_length_mismatch(self):
        """Test that length mismatch raises error."""
        with pytest.raises(ValueError, match="same length"):
            MaterialComposition(
                elements=["H", "O"], fractions=[2.0, 1.0, 0.5]  # Wrong length
            )

    def test_material_composition_zero_total(self):
        """Test that zero total fraction raises error."""
        with pytest.raises(ValueError, match="must be > 0"):
            MaterialComposition(elements=["H", "O"], fractions=[0.0, 0.0])

    def test_material_composition_with_densities(self):
        """Test MaterialComposition with densities."""
        comp = MaterialComposition(
            elements=["H", "O"], fractions=[2.0, 1.0], densities=[0.111, 0.889]
        )

        assert comp.densities == [0.111, 0.889]


class TestMaterialMapper:
    """Tests for MaterialMapper class."""

    def test_get_composition_known_material(self):
        """Test getting composition for known material."""
        comp = MaterialMapper.get_composition("H2O")

        assert comp is not None
        assert "H" in comp.elements
        assert "O" in comp.elements

    def test_get_composition_case_insensitive(self):
        """Test that composition lookup is case-insensitive."""
        comp1 = MaterialMapper.get_composition("H2O")
        comp2 = MaterialMapper.get_composition("h2o")
        comp3 = MaterialMapper.get_composition("Water")

        assert comp1 is not None
        assert comp2 is not None
        assert comp3 is not None

    def test_get_composition_unknown_material(self):
        """Test getting composition for unknown material."""
        comp = MaterialMapper.get_composition("UnknownMaterial")

        assert comp is None

    def test_get_density_known_material(self):
        """Test getting density for known material."""
        density = MaterialMapper.get_density("H2O")

        assert density is not None
        assert density == 1.0

    def test_get_density_case_insensitive(self):
        """Test that density lookup is case-insensitive."""
        density1 = MaterialMapper.get_density("H2O")
        density2 = MaterialMapper.get_density("water")

        assert density1 == density2

    def test_get_density_unknown_material(self):
        """Test getting density for unknown material."""
        density = MaterialMapper.get_density("UnknownMaterial")

        assert density is None

    def test_get_primary_element_simple(self):
        """Test getting primary element for simple material."""
        element = MaterialMapper.get_primary_element("graphite")

        assert element == "C"

    def test_get_primary_element_compound(self):
        """Test getting primary element for compound material."""
        element = MaterialMapper.get_primary_element("H2O")

        # H has higher fraction (2/3) than O (1/3)
        assert element == "H"

    def test_get_primary_element_unknown(self):
        """Test getting primary element for unknown material (defaults to H)."""
        element = MaterialMapper.get_primary_element("UnknownMaterial")

        assert element == "H"

    def test_compute_weighted_cross_section(self):
        """Test computing weighted cross-section."""
        energy = np.array([0.1, 1.0, 10.0])
        cross_sections = {
            "H": np.array([0.1, 0.2, 0.3]),
            "O": np.array([0.2, 0.4, 0.6]),
        }

        weighted = MaterialMapper.compute_weighted_cross_section(
            "H2O", cross_sections, energy
        )

        assert weighted.shape == energy.shape
        # H2O: 2/3 H, 1/3 O
        expected = (2.0 / 3.0) * cross_sections["H"] + (1.0 / 3.0) * cross_sections["O"]
        assert np.allclose(weighted, expected)

    def test_compute_weighted_cross_section_unknown_material(self):
        """Test computing weighted cross-section for unknown material."""
        energy = np.array([0.1, 1.0, 10.0])
        cross_sections = {"H": np.array([0.1, 0.2, 0.3])}

        weighted = MaterialMapper.compute_weighted_cross_section(
            "UnknownMaterial", cross_sections, energy
        )

        # Should fallback to primary element (H)
        assert np.allclose(weighted, cross_sections["H"])

    def test_compute_weighted_cross_section_deuterium(self):
        """Test that deuterium uses H data."""
        energy = np.array([0.1, 1.0, 10.0])
        cross_sections = {
            "H": np.array([0.1, 0.2, 0.3]),
            "O": np.array([0.2, 0.4, 0.6]),
        }

        weighted = MaterialMapper.compute_weighted_cross_section(
            "D2O", cross_sections, energy
        )

        # D2O should use H data for D
        assert weighted.shape == energy.shape
        assert np.all(np.isfinite(weighted))

    def test_compute_weighted_cross_section_missing_element(self):
        """Test computing weighted cross-section with missing element data."""
        energy = np.array([0.1, 1.0, 10.0])
        cross_sections = {
            "H": np.array([0.1, 0.2, 0.3])
            # Missing O
        }

        weighted = MaterialMapper.compute_weighted_cross_section(
            "H2O", cross_sections, energy
        )

        # Should only use available elements
        assert weighted.shape == energy.shape
        assert np.all(np.isfinite(weighted))
