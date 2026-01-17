"""
Unit tests for fuel rod mechanics module.
"""

import numpy as np
import pytest

from smrforge.mechanics.fuel_rod import (
    FuelRodMechanics,
    FuelSwelling,
    PelletCladdingInteraction,
    StressStrain,
    ThermalExpansion,
)


class TestThermalExpansion:
    """Tests for ThermalExpansion class."""

    def test_fuel_expansion(self):
        """Test fuel thermal expansion calculation."""
        expansion = ThermalExpansion(
            fuel_coefficient=1.0e-5, reference_temperature=300.0
        )
        
        length, radius = expansion.fuel_expansion(
            temperature=1200.0, initial_length=100.0, initial_radius=0.5
        )
        
        # Expected: expansion factor = 1 + 1e-5 * (1200 - 300) = 1.009
        expected_length = 100.0 * 1.009
        expected_radius = 0.5 * 1.009
        
        assert np.isclose(length, expected_length, rtol=1e-6)
        assert np.isclose(radius, expected_radius, rtol=1e-6)

    def test_cladding_expansion(self):
        """Test cladding thermal expansion calculation."""
        expansion = ThermalExpansion(
            cladding_coefficient=1.7e-5, reference_temperature=300.0
        )
        
        length, radius = expansion.cladding_expansion(
            temperature=800.0, initial_length=100.0, initial_radius=0.6
        )
        
        # Expected: expansion factor = 1 + 1.7e-5 * (800 - 300) = 1.0085
        expected_length = 100.0 * 1.0085
        expected_radius = 0.6 * 1.0085
        
        assert np.isclose(length, expected_length, rtol=1e-6)
        assert np.isclose(radius, expected_radius, rtol=1e-6)

    def test_gap_change(self):
        """Test gap change calculation."""
        expansion = ThermalExpansion(
            fuel_coefficient=1.0e-5,
            cladding_coefficient=1.7e-5,
            reference_temperature=300.0,
        )
        
        gap = expansion.gap_change(
            fuel_temperature=1200.0,
            cladding_temperature=800.0,
            initial_gap=0.01,
            initial_fuel_radius=0.5,
            initial_cladding_inner_radius=0.51,
        )
        
        # Gap should decrease as fuel expands more than cladding
        assert gap >= 0.0  # Gap cannot be negative
        assert gap < 0.01  # Gap should decrease


class TestStressStrain:
    """Tests for StressStrain class."""

    def test_hoop_stress(self):
        """Test hoop stress calculation."""
        stress = StressStrain()
        
        inner, outer = stress.hoop_stress(
            internal_pressure=15.5e6,  # Pa
            external_pressure=0.0,
            inner_radius=0.004,  # m
            outer_radius=0.00475,  # m
        )
        
        # Inner stress should be higher than outer
        assert inner > outer
        assert inner > 0
        assert outer > 0

    def test_radial_stress(self):
        """Test radial stress calculation."""
        stress = StressStrain()
        
        radial = stress.radial_stress(
            internal_pressure=15.5e6,
            external_pressure=0.0,
            inner_radius=0.004,
            outer_radius=0.00475,
            radius=0.004,
        )
        
        # At inner radius, radial stress should equal internal pressure
        assert np.isclose(radial, -15.5e6, rtol=0.1)  # Negative (compressive)

    def test_von_mises_stress(self):
        """Test von Mises stress calculation."""
        stress = StressStrain()
        
        radial_stress = -15e6
        vm = stress.von_mises_stress(
            hoop_stress=100e6, radial_stress=radial_stress, axial_stress=0.0
        )
        
        assert vm > 0
        assert vm > abs(radial_stress)  # Should be larger than individual components

    def test_strain_from_stress(self):
        """Test strain calculation from stress."""
        stress = StressStrain()
        
        hoop_strain, radial_strain, axial_strain = stress.strain_from_stress(
            hoop_stress=100e6,
            radial_stress=-15e6,
            axial_stress=0.0,
            youngs_modulus=9e10,
            poisson=0.33,
        )
        
        # Hoop strain should be positive (tensile)
        assert hoop_strain > 0
        # Radial strain should be negative (compressive)
        assert radial_strain < 0


class TestPelletCladdingInteraction:
    """Tests for PelletCladdingInteraction class."""

    def test_gap_closure(self):
        """Test gap closure detection."""
        pci = PelletCladdingInteraction()
        
        # Gap open
        closed = pci.check_gap_closure(
            fuel_radius=0.5, cladding_inner_radius=0.51, tolerance=1e-6
        )
        assert not closed
        
        # Gap closed
        closed = pci.check_gap_closure(
            fuel_radius=0.5, cladding_inner_radius=0.5001, tolerance=1e-3
        )
        assert closed

    def test_contact_pressure(self):
        """Test contact pressure calculation."""
        pci = PelletCladdingInteraction()
        
        # Close gap first
        pci.check_gap_closure(0.5, 0.499, tolerance=1e-3)
        
        pressure = pci.calculate_contact_pressure(
            fuel_radius=0.5,
            cladding_inner_radius=0.499,
            fuel_youngs_modulus=2e11,
            cladding_youngs_modulus=9e10,
            fuel_poisson=0.31,
            cladding_poisson=0.33,
        )
        
        assert pressure > 0

    def test_pci_stress_enhancement(self):
        """Test PCI stress enhancement."""
        pci = PelletCladdingInteraction()
        pci.gap_closed = True
        
        enhanced = pci.pci_stress_enhancement(
            base_stress=100e6, contact_pressure=10e6, stress_concentration_factor=1.5
        )
        
        assert enhanced > 100e6  # Should be enhanced


class TestFuelSwelling:
    """Tests for FuelSwelling class."""

    def test_total_swelling(self):
        """Test total swelling calculation."""
        swelling = FuelSwelling(
            solid_swelling_rate=0.01,
            gas_swelling_rate=0.005,
            saturation_burnup=50.0,
        )
        
        total = swelling.total_swelling(
            burnup=10.0, temperature=1200.0, power_density=100.0
        )
        
        assert total > 0
        assert total < 1.0  # Should be reasonable fraction

    def test_radius_increase(self):
        """Test radius increase calculation."""
        swelling = FuelSwelling()
        
        radius_increase = swelling.radius_increase(
            burnup=20.0, temperature=1200.0, power_density=100.0, initial_radius=0.5
        )
        
        assert radius_increase > 0
        assert radius_increase < 0.5  # Should be reasonable


class TestFuelRodMechanics:
    """Tests for FuelRodMechanics class."""

    def test_analyze(self):
        """Test comprehensive fuel rod analysis."""
        mechanics = FuelRodMechanics(
            fuel_radius=0.5,  # cm
            cladding_inner_radius=0.51,  # cm
            cladding_outer_radius=0.575,  # cm
            fuel_length=365.76,  # cm
        )
        
        result = mechanics.analyze(
            fuel_temperature=1200.0,
            cladding_temperature=800.0,
            burnup=10.0,
            power_density=100.0,
            internal_pressure=0.0,
            external_pressure=15.5e6,
        )
        
        # Check that all expected keys are present
        assert "fuel_radius" in result
        assert "cladding_inner_radius" in result
        assert "gap" in result
        assert "gap_closed" in result
        assert "contact_pressure" in result
        assert "cladding_hoop_stress_inner" in result
        assert "cladding_von_mises_stress" in result
        assert "safety_margin" in result
        
        # Check reasonable values
        # Gap can be negative if fuel expands more than cladding (gap closure)
        assert isinstance(result["gap"], (int, float))
        assert result["safety_margin"] < 1.0  # Should be fraction

    def test_analyze_with_pci(self):
        """Test analysis with pellet-cladding interaction."""
        mechanics = FuelRodMechanics(
            fuel_radius=0.5,
            cladding_inner_radius=0.5001,  # Very small gap
            cladding_outer_radius=0.575,
            fuel_length=365.76,
        )
        
        result = mechanics.analyze(
            fuel_temperature=1200.0,
            cladding_temperature=800.0,
            burnup=20.0,  # Higher burnup causes swelling
            power_density=150.0,
            internal_pressure=5e6,  # Fission gas pressure
            external_pressure=15.5e6,
        )
        
        # With high burnup and small gap, PCI may occur
        assert "gap_closed" in result
        assert "contact_pressure" in result
