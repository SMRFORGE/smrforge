"""
Material-to-element mapping for photon cross-section loading.

This module provides sophisticated material mapping for compound materials,
allowing gamma transport solver to load appropriate photon cross-sections
for complex materials like H2O, UO2, etc.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np


@dataclass
class MaterialComposition:
    """
    Composition of a material by element.
    
    Attributes:
        elements: List of element symbols
        fractions: List of atomic fractions (should sum to 1.0)
        densities: Optional list of partial densities [g/cm³]
    """
    
    elements: List[str]
    fractions: List[float]
    densities: Optional[List[float]] = None
    
    def __post_init__(self):
        """Validate composition."""
        if len(self.elements) != len(self.fractions):
            raise ValueError("Elements and fractions must have same length")
        
        # Normalize fractions
        total = sum(self.fractions)
        if total > 0:
            self.fractions = [f / total for f in self.fractions]
        else:
            raise ValueError("Total fraction must be > 0")


class MaterialMapper:
    """
    Maps material names to element compositions for photon cross-section loading.
    
    Supports:
    - Simple materials (H2O → H)
    - Compound materials (H2O → H + O with weighted average)
    - Material density database
    """
    
    # Material composition database
    MATERIAL_COMPOSITIONS: Dict[str, MaterialComposition] = {
        # Water
        "H2O": MaterialComposition(
            elements=["H", "O"],
            fractions=[2.0, 1.0],  # H2O: 2 H, 1 O
        ),
        "water": MaterialComposition(
            elements=["H", "O"],
            fractions=[2.0, 1.0],
        ),
        
        # Heavy water
        "D2O": MaterialComposition(
            elements=["D", "O"],  # Deuterium (use H data)
            fractions=[2.0, 1.0],
        ),
        
        # Uranium dioxide
        "UO2": MaterialComposition(
            elements=["U", "O"],
            fractions=[1.0, 2.0],
        ),
        
        # Graphite
        "graphite": MaterialComposition(
            elements=["C"],
            fractions=[1.0],
        ),
        "C": MaterialComposition(
            elements=["C"],
            fractions=[1.0],
        ),
        
        # Steel/Iron
        "steel": MaterialComposition(
            elements=["Fe"],
            fractions=[1.0],
        ),
        "Fe": MaterialComposition(
            elements=["Fe"],
            fractions=[1.0],
        ),
        
        # Helium (gas)
        "He": MaterialComposition(
            elements=["He"],
            fractions=[1.0],
        ),
        "helium": MaterialComposition(
            elements=["He"],
            fractions=[1.0],
        ),
        
        # Zirconium
        "Zr": MaterialComposition(
            elements=["Zr"],
            fractions=[1.0],
        ),
        "zirconium": MaterialComposition(
            elements=["Zr"],
            fractions=[1.0],
        ),
        
        # Beryllium
        "Be": MaterialComposition(
            elements=["Be"],
            fractions=[1.0],
        ),
        "beryllium": MaterialComposition(
            elements=["Be"],
            fractions=[1.0],
        ),
    }
    
    # Material density database [g/cm³]
    MATERIAL_DENSITIES: Dict[str, float] = {
        "H2O": 1.0,
        "water": 1.0,
        "D2O": 1.1,
        "UO2": 10.96,
        "graphite": 2.25,
        "C": 2.25,
        "steel": 7.85,
        "Fe": 7.85,
        "He": 0.0001785,  # At STP
        "helium": 0.0001785,
        "Zr": 6.52,
        "zirconium": 6.52,
        "Be": 1.85,
        "beryllium": 1.85,
    }
    
    # Atomic masses [g/mol] for unit conversion
    ATOMIC_MASSES: Dict[str, float] = {
        "H": 1.008,
        "D": 2.014,  # Deuterium
        "O": 16.00,
        "U": 238.03,  # Average for natural U
        "C": 12.01,
        "Fe": 55.85,
        "He": 4.003,
        "Zr": 91.22,
        "Be": 9.012,
    }
    
    @classmethod
    def get_composition(cls, material: str) -> Optional[MaterialComposition]:
        """
        Get element composition for a material.
        
        Args:
            material: Material name (e.g., "H2O", "steel", "UO2").
        
        Returns:
            MaterialComposition or None if material not found.
        """
        material_lower = material.lower()
        
        # Direct lookup
        if material_lower in cls.MATERIAL_COMPOSITIONS:
            return cls.MATERIAL_COMPOSITIONS[material_lower]
        
        # Case-insensitive lookup
        for key, comp in cls.MATERIAL_COMPOSITIONS.items():
            if key.lower() == material_lower:
                return comp
        
        return None
    
    @classmethod
    def get_density(cls, material: str) -> Optional[float]:
        """
        Get material density.
        
        Args:
            material: Material name.
        
        Returns:
            Density [g/cm³] or None if not found.
        """
        material_lower = material.lower()
        
        # Direct lookup
        if material_lower in cls.MATERIAL_DENSITIES:
            return cls.MATERIAL_DENSITIES[material_lower]
        
        # Case-insensitive lookup
        for key, density in cls.MATERIAL_DENSITIES.items():
            if key.lower() == material_lower:
                return density
        
        return None
    
    @classmethod
    def get_primary_element(cls, material: str) -> str:
        """
        Get primary element for a material (for simple mapping).
        
        For compound materials, returns the element with highest fraction.
        
        Args:
            material: Material name.
        
        Returns:
            Element symbol (defaults to "H" if material not found).
        """
        comp = cls.get_composition(material)
        if comp is None:
            return "H"  # Default to hydrogen
        
        # Return element with highest fraction
        max_idx = np.argmax(comp.fractions)
        return comp.elements[max_idx]
    
    @classmethod
    def compute_weighted_cross_section(
        cls,
        material: str,
        cross_sections: Dict[str, np.ndarray],
        energy: np.ndarray,
    ) -> np.ndarray:
        """
        Compute weighted average cross-section for a compound material.
        
        Args:
            material: Material name.
            cross_sections: Dictionary mapping element -> cross-section array.
            energy: Energy array [MeV] (for interpolation if needed).
        
        Returns:
            Weighted average cross-section array.
        """
        comp = cls.get_composition(material)
        if comp is None:
            # Fallback to primary element
            primary = cls.get_primary_element(material)
            return cross_sections.get(primary, np.zeros_like(energy))
        
        # Compute weighted average
        weighted_xs = np.zeros_like(energy)
        total_fraction = 0.0
        
        for element, fraction in zip(comp.elements, comp.fractions):
            if element in cross_sections:
                # Handle deuterium (use H data)
                element_key = "H" if element == "D" else element
                if element_key in cross_sections:
                    weighted_xs += fraction * cross_sections[element_key]
                    total_fraction += fraction
        
        if total_fraction > 0:
            weighted_xs /= total_fraction
        
        return weighted_xs

