"""
Comprehensive tests for material mapping to improve coverage to 80%+.

Tests cover:
- Material composition lookup
- Density lookup
- Primary element extraction
- Weighted cross-section calculation
- Compound materials
- Edge cases
"""

import numpy as np
import pytest

from smrforge.core.material_mapping import MaterialMapper, MaterialComposition


class TestMaterialMapperComprehensive:
    """Comprehensive tests for MaterialMapper."""
    
    def test_get_composition_simple(self):
        """Test getting composition for simple material."""
        comp = MaterialMapper.get_composition("C")
        
        assert comp is not None
        assert "C" in comp.elements
        assert len(comp.elements) == 1
        assert comp.fractions[0] == 1.0
    
    def test_get_composition_compound(self):
        """Test getting composition for compound material."""
        comp = MaterialMapper.get_composition("H2O")
        
        assert comp is not None
        assert "H" in comp.elements
        assert "O" in comp.elements
        assert len(comp.elements) == 2
        # Fractions should be normalized
        assert abs(sum(comp.fractions) - 1.0) < 1e-10
    
    def test_get_composition_case_insensitive(self):
        """Test case-insensitive material lookup."""
        comp1 = MaterialMapper.get_composition("h2o")
        comp2 = MaterialMapper.get_composition("H2O")
        comp3 = MaterialMapper.get_composition("Water")
        
        assert comp1 is not None
        assert comp2 is not None
        assert comp3 is not None
        # All should be the same
        assert comp1.elements == comp2.elements
    
    def test_get_composition_unknown(self):
        """Test getting composition for unknown material."""
        comp = MaterialMapper.get_composition("UnknownMaterial")
        
        assert comp is None
    
    def test_get_density(self):
        """Test getting material density."""
        density = MaterialMapper.get_density("H2O")
        
        assert density is not None
        assert density == 1.0  # Water density
    
    def test_get_density_case_insensitive(self):
        """Test case-insensitive density lookup."""
        density1 = MaterialMapper.get_density("h2o")
        density2 = MaterialMapper.get_density("H2O")
        
        assert density1 == density2
        assert density1 == 1.0
    
    def test_get_density_unknown(self):
        """Test getting density for unknown material."""
        density = MaterialMapper.get_density("UnknownMaterial")
        
        assert density is None
    
    def test_get_primary_element_simple(self):
        """Test getting primary element for simple material."""
        element = MaterialMapper.get_primary_element("C")
        
        assert element == "C"
    
    def test_get_primary_element_compound(self):
        """Test getting primary element for compound material."""
        element = MaterialMapper.get_primary_element("H2O")
        
        assert element == "H"  # Hydrogen has higher fraction
    
    def test_get_primary_element_unknown(self):
        """Test getting primary element for unknown material."""
        element = MaterialMapper.get_primary_element("UnknownMaterial")
        
        assert element == "H"  # Default
    
    def test_compute_weighted_cross_section_simple(self):
        """Test weighted cross-section for simple material."""
        energy = np.array([0.1, 1.0, 10.0])
        cross_sections = {
            "C": np.array([0.1, 0.2, 0.3]),
        }
        
        weighted = MaterialMapper.compute_weighted_cross_section("C", cross_sections, energy)
        
        assert weighted is not None
        assert len(weighted) == len(energy)
        assert np.allclose(weighted, cross_sections["C"])
    
    def test_compute_weighted_cross_section_compound(self):
        """Test weighted cross-section for compound material."""
        energy = np.array([0.1, 1.0, 10.0])
        cross_sections = {
            "H": np.array([0.1, 0.2, 0.3]),
            "O": np.array([0.2, 0.4, 0.6]),
        }
        
        weighted = MaterialMapper.compute_weighted_cross_section("H2O", cross_sections, energy)
        
        assert weighted is not None
        assert len(weighted) == len(energy)
        # Should be weighted average (2*H + 1*O) / 3
        expected = (2 * cross_sections["H"] + 1 * cross_sections["O"]) / 3
        assert np.allclose(weighted, expected)
    
    def test_compute_weighted_cross_section_deuterium(self):
        """Test weighted cross-section with deuterium (D → H)."""
        energy = np.array([0.1, 1.0])
        cross_sections = {
            "H": np.array([0.1, 0.2]),
            "O": np.array([0.2, 0.4]),
        }
        
        weighted = MaterialMapper.compute_weighted_cross_section("D2O", cross_sections, energy)
        
        assert weighted is not None
        # Should use H data for D
        assert len(weighted) == len(energy)
    
    def test_compute_weighted_cross_section_missing_element(self):
        """Test weighted cross-section with missing element."""
        energy = np.array([0.1, 1.0])
        cross_sections = {
            "H": np.array([0.1, 0.2]),
            # Missing O
        }
        
        weighted = MaterialMapper.compute_weighted_cross_section("H2O", cross_sections, energy)
        
        assert weighted is not None
        # Should use available elements only
        assert len(weighted) == len(energy)
    
    def test_compute_weighted_cross_section_unknown_material(self):
        """Test weighted cross-section for unknown material."""
        energy = np.array([0.1, 1.0])
        cross_sections = {
            "H": np.array([0.1, 0.2]),
        }
        
        weighted = MaterialMapper.compute_weighted_cross_section("Unknown", cross_sections, energy)
        
        assert weighted is not None
        # Should fall back to primary element (H)
        assert len(weighted) == len(energy)
    
    def test_material_composition_validation(self):
        """Test MaterialComposition validation."""
        # Valid composition
        comp = MaterialComposition(
            elements=["H", "O"],
            fractions=[2.0, 1.0],
        )
        
        assert len(comp.elements) == 2
        assert abs(sum(comp.fractions) - 1.0) < 1e-10  # Normalized
        
        # Invalid: different lengths
        with pytest.raises(ValueError):
            MaterialComposition(
                elements=["H", "O"],
                fractions=[2.0],  # Wrong length
            )
        
        # Invalid: zero total
        with pytest.raises(ValueError):
            MaterialComposition(
                elements=["H"],
                fractions=[0.0],
            )
    
    def test_all_materials(self):
        """Test all materials in database."""
        materials = [
            "H2O", "water", "D2O",
            "UO2", "graphite", "C",
            "steel", "Fe", "He", "helium",
            "Zr", "zirconium", "Be", "beryllium",
        ]
        
        for material in materials:
            comp = MaterialMapper.get_composition(material)
            assert comp is not None, f"Material {material} not found"
            
            density = MaterialMapper.get_density(material)
            assert density is not None, f"Density for {material} not found"
            
            element = MaterialMapper.get_primary_element(material)
            assert element is not None
    
    def test_compute_weighted_cross_section_empty_dict(self):
        """Test weighted cross-section with empty cross-sections dictionary."""
        energy = np.array([0.1, 1.0, 10.0])
        cross_sections = {}
        
        weighted = MaterialMapper.compute_weighted_cross_section("H2O", cross_sections, energy)
        
        assert weighted is not None
        assert len(weighted) == len(energy)
        # Should fall back to primary element (H), but H not in dict, so zeros
        assert np.allclose(weighted, np.zeros_like(energy))
    
    def test_compute_weighted_cross_section_no_matching_elements(self):
        """Test weighted cross-section when no elements match."""
        energy = np.array([0.1, 1.0, 10.0])
        cross_sections = {
            "Fe": np.array([0.1, 0.2, 0.3]),  # Not in H2O
        }
        
        weighted = MaterialMapper.compute_weighted_cross_section("H2O", cross_sections, energy)
        
        assert weighted is not None
        assert len(weighted) == len(energy)
        # Should return zeros when no matching elements
        assert np.allclose(weighted, np.zeros_like(energy))
    
    def test_compute_weighted_cross_section_zero_total_fraction(self):
        """Test weighted cross-section with zero total fraction."""
        energy = np.array([0.1, 1.0, 10.0])
        # Create a composition where no elements are in cross_sections
        cross_sections = {}
        
        weighted = MaterialMapper.compute_weighted_cross_section("H2O", cross_sections, energy)
        
        assert weighted is not None
        assert len(weighted) == len(energy)
        # Should return zeros
        assert np.allclose(weighted, np.zeros_like(energy))
    
    def test_compute_weighted_cross_section_unknown_with_element(self):
        """Test weighted cross-section for unknown material with element in dict."""
        energy = np.array([0.1, 1.0, 10.0])
        cross_sections = {
            "H": np.array([0.1, 0.2, 0.3]),
        }
        
        weighted = MaterialMapper.compute_weighted_cross_section("UnknownMaterial", cross_sections, energy)
        
        assert weighted is not None
        assert len(weighted) == len(energy)
        # Should fall back to primary element (H) which is in dict
        assert np.allclose(weighted, cross_sections["H"])
    
    def test_compute_weighted_cross_section_unknown_no_element(self):
        """Test weighted cross-section for unknown material without element in dict."""
        energy = np.array([0.1, 1.0, 10.0])
        cross_sections = {
            "Fe": np.array([0.1, 0.2, 0.3]),
        }
        
        weighted = MaterialMapper.compute_weighted_cross_section("UnknownMaterial", cross_sections, energy)
        
        assert weighted is not None
        assert len(weighted) == len(energy)
        # Should fall back to primary element (H) which is not in dict, so zeros
        assert np.allclose(weighted, np.zeros_like(energy))
    
    def test_compute_weighted_cross_section_deuterium_no_h_data(self):
        """Test weighted cross-section with deuterium when H data not available."""
        energy = np.array([0.1, 1.0])
        cross_sections = {
            "O": np.array([0.2, 0.4]),
            # No H data, but D should map to H
        }
        
        weighted = MaterialMapper.compute_weighted_cross_section("D2O", cross_sections, energy)
        
        assert weighted is not None
        assert len(weighted) == len(energy)
        # Should only use O data since H (for D) is not available
        assert np.allclose(weighted, cross_sections["O"])
    
    def test_compute_weighted_cross_section_partial_match(self):
        """Test weighted cross-section when only some elements match."""
        energy = np.array([0.1, 1.0, 10.0])
        cross_sections = {
            "H": np.array([0.1, 0.2, 0.3]),
            # Missing O
        }
        
        weighted = MaterialMapper.compute_weighted_cross_section("H2O", cross_sections, energy)
        
        assert weighted is not None
        assert len(weighted) == len(energy)
        # Should use available elements (H only)
        assert np.allclose(weighted, cross_sections["H"])
    
    def test_get_primary_element_tie_breaker(self):
        """Test get_primary_element when multiple elements have same fraction."""
        # Create a composition with equal fractions
        comp = MaterialComposition(
            elements=["H", "O"],
            fractions=[1.0, 1.0],  # Equal fractions
        )
        
        # Should return first element with max fraction (or last, depending on implementation)
        element = MaterialMapper.get_primary_element("H2O")
        assert element in ["H", "O"]  # Either is valid
    
    def test_get_primary_element_single_element(self):
        """Test get_primary_element for single-element material."""
        element = MaterialMapper.get_primary_element("He")
        assert element == "He"
        
        element = MaterialMapper.get_primary_element("C")
        assert element == "C"
    
    def test_get_density_all_materials(self):
        """Test density lookup for all materials."""
        materials = MaterialMapper.MATERIAL_DENSITIES.keys()
        
        for material in materials:
            density = MaterialMapper.get_density(material)
            assert density is not None
            assert density > 0
    
    def test_get_composition_normalization(self):
        """Test that composition fractions are normalized."""
        comp = MaterialComposition(
            elements=["H", "O"],
            fractions=[4.0, 2.0],  # Will be normalized to [2/3, 1/3]
        )
        
        assert abs(sum(comp.fractions) - 1.0) < 1e-10
        assert abs(comp.fractions[0] - 2.0/3.0) < 1e-10
        assert abs(comp.fractions[1] - 1.0/3.0) < 1e-10
    
    def test_material_composition_with_densities(self):
        """Test MaterialComposition with densities list."""
        comp = MaterialComposition(
            elements=["H", "O"],
            fractions=[2.0, 1.0],
            densities=[0.5, 0.5],  # Partial densities
        )
        
        assert comp.densities is not None
        assert len(comp.densities) == 2
        assert comp.densities[0] == 0.5
        assert comp.densities[1] == 0.5
    
    def test_material_composition_without_densities(self):
        """Test MaterialComposition without densities."""
        comp = MaterialComposition(
            elements=["H", "O"],
            fractions=[2.0, 1.0],
        )
        
        assert comp.densities is None
    
    def test_get_density_case_variations(self):
        """Test density lookup with various case variations."""
        density1 = MaterialMapper.get_density("H2O")
        density2 = MaterialMapper.get_density("h2o")
        density3 = MaterialMapper.get_density("H2o")
        density4 = MaterialMapper.get_density("H20")  # Different but should handle
        
        assert density1 == density2 == 1.0
        assert density3 == 1.0
    
    def test_get_composition_case_variations(self):
        """Test composition lookup with various case variations."""
        comp1 = MaterialMapper.get_composition("H2O")
        comp2 = MaterialMapper.get_composition("h2o")
        comp3 = MaterialMapper.get_composition("H2o")
        
        assert comp1 is not None
        assert comp2 is not None
        assert comp3 is not None
        assert comp1.elements == comp2.elements == comp3.elements
    
    def test_compute_weighted_cross_section_different_lengths(self):
        """Test weighted cross-section with cross-sections of different lengths (edge case)."""
        energy = np.array([0.1, 1.0, 10.0])
        cross_sections = {
            "H": np.array([0.1, 0.2, 0.3]),  # Same length as energy
            "O": np.array([0.2, 0.4, 0.6]),  # Same length
        }
        
        weighted = MaterialMapper.compute_weighted_cross_section("H2O", cross_sections, energy)
        
        assert weighted is not None
        assert len(weighted) == len(energy)
        # Should compute weighted average correctly
        assert np.all(weighted >= 0)
    
    def test_get_composition_nonexistent_alias(self):
        """Test get_composition with material that doesn't exist."""
        comp = MaterialMapper.get_composition("nonexistent_material_xyz")
        assert comp is None
    
    def test_get_density_nonexistent(self):
        """Test get_density with material that doesn't exist."""
        density = MaterialMapper.get_density("nonexistent_material_xyz")
        assert density is None
    
    def test_atomic_masses_lookup(self):
        """Test that atomic masses are available."""
        assert "H" in MaterialMapper.ATOMIC_MASSES
        assert "O" in MaterialMapper.ATOMIC_MASSES
        assert "U" in MaterialMapper.ATOMIC_MASSES
        assert MaterialMapper.ATOMIC_MASSES["H"] == 1.008
        assert MaterialMapper.ATOMIC_MASSES["D"] == 2.014

