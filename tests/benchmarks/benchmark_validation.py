# tests/test_validation.py
"""
Tests for Pydantic validation in SMRForge.
"""

import numpy as np
import pytest
from pydantic import ValidationError
from smrforge.validation.models import (
    CrossSectionData,
    FuelType,
    GeometryParameters,
    MaterialComposition,
    ReactorSpecification,
    ReactorType,
    SolverOptions,
    TransientConditions,
)


class TestReactorSpecification:
    """Test ReactorSpecification Pydantic validation."""

    def test_valid_specification(self):
        """Test that valid spec is accepted."""
        spec = ReactorSpecification(
            name="Test-Reactor",
            reactor_type=ReactorType.PRISMATIC,
            power_thermal=10e6,
            inlet_temperature=823.15,
            outlet_temperature=1023.15,
            max_fuel_temperature=1873.15,
            primary_pressure=7.0e6,
            core_height=200.0,
            core_diameter=100.0,
            reflector_thickness=30.0,
            fuel_type=FuelType.UCO,
            enrichment=0.195,
            heavy_metal_loading=150.0,
            coolant_flow_rate=8.0,
            cycle_length=3650,
            capacity_factor=0.95,
            target_burnup=150.0,
            doppler_coefficient=-3.5e-5,
            shutdown_margin=0.05,
        )

        assert spec.name == "Test-Reactor"
        assert spec.power_thermal == 10e6
        assert spec.enrichment == 0.195

    def test_negative_power_rejected(self):
        """Test that negative power is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ReactorSpecification(
                name="Bad-Reactor",
                reactor_type=ReactorType.PRISMATIC,
                power_thermal=-100,  # Invalid!
                inlet_temperature=823.15,
                outlet_temperature=1023.15,
                max_fuel_temperature=1873.15,
                primary_pressure=7.0e6,
                core_height=200.0,
                core_diameter=100.0,
                reflector_thickness=30.0,
                fuel_type=FuelType.UCO,
                enrichment=0.195,
                heavy_metal_loading=150.0,
                coolant_flow_rate=8.0,
                cycle_length=3650,
                capacity_factor=0.95,
                target_burnup=150.0,
                doppler_coefficient=-3.5e-5,
                shutdown_margin=0.05,
            )

        # Check that error mentions power_thermal
        assert "power_thermal" in str(exc_info.value)
        assert "greater than 0" in str(exc_info.value)

    def test_temperature_order_validated(self):
        """Test that inlet < outlet is enforced."""
        with pytest.raises(ValidationError) as exc_info:
            ReactorSpecification(
                name="Bad-Temps",
                reactor_type=ReactorType.PRISMATIC,
                power_thermal=10e6,
                inlet_temperature=1000.0,  # Higher than outlet!
                outlet_temperature=800.0,
                max_fuel_temperature=1873.15,
                primary_pressure=7.0e6,
                core_height=200.0,
                core_diameter=100.0,
                reflector_thickness=30.0,
                fuel_type=FuelType.UCO,
                enrichment=0.195,
                heavy_metal_loading=150.0,
                coolant_flow_rate=8.0,
                cycle_length=3650,
                capacity_factor=0.95,
                target_burnup=150.0,
                doppler_coefficient=-3.5e-5,
                shutdown_margin=0.05,
            )

        assert "Inlet temperature" in str(exc_info.value)
        assert "less than outlet" in str(exc_info.value)

    def test_enrichment_bounds(self):
        """Test enrichment must be in [0, 1]."""
        with pytest.raises(ValidationError):
            ReactorSpecification(
                name="Over-Enriched",
                reactor_type=ReactorType.PRISMATIC,
                power_thermal=10e6,
                inlet_temperature=823.15,
                outlet_temperature=1023.15,
                max_fuel_temperature=1873.15,
                primary_pressure=7.0e6,
                core_height=200.0,
                core_diameter=100.0,
                reflector_thickness=30.0,
                fuel_type=FuelType.UCO,
                enrichment=1.5,  # > 100%!
                heavy_metal_loading=150.0,
                coolant_flow_rate=8.0,
                cycle_length=3650,
                capacity_factor=0.95,
                target_burnup=150.0,
                doppler_coefficient=-3.5e-5,
                shutdown_margin=0.05,
            )

    def test_doppler_coefficient_must_be_negative(self):
        """Test that Doppler coefficient must be negative for safety."""
        with pytest.raises(ValidationError) as exc_info:
            ReactorSpecification(
                name="Unsafe",
                reactor_type=ReactorType.PRISMATIC,
                power_thermal=10e6,
                inlet_temperature=823.15,
                outlet_temperature=1023.15,
                max_fuel_temperature=1873.15,
                primary_pressure=7.0e6,
                core_height=200.0,
                core_diameter=100.0,
                reflector_thickness=30.0,
                fuel_type=FuelType.UCO,
                enrichment=0.195,
                heavy_metal_loading=150.0,
                coolant_flow_rate=8.0,
                cycle_length=3650,
                capacity_factor=0.95,
                target_burnup=150.0,
                doppler_coefficient=1.0e-5,  # Positive! Unsafe!
                shutdown_margin=0.05,
            )

        assert "doppler_coefficient" in str(exc_info.value)
        assert "negative" in str(exc_info.value).lower()

    def test_computed_properties(self):
        """Test computed properties work correctly."""
        spec = ReactorSpecification(
            name="Test",
            reactor_type=ReactorType.PRISMATIC,
            power_thermal=10e6,
            power_electric=3.5e6,
            inlet_temperature=823.15,
            outlet_temperature=1023.15,
            max_fuel_temperature=1873.15,
            primary_pressure=7.0e6,
            core_height=200.0,
            core_diameter=100.0,
            reflector_thickness=30.0,
            fuel_type=FuelType.UCO,
            enrichment=0.195,
            heavy_metal_loading=150.0,
            coolant_flow_rate=8.0,
            cycle_length=3650,
            capacity_factor=0.95,
            target_burnup=150.0,
            doppler_coefficient=-3.5e-5,
            shutdown_margin=0.05,
        )

        # Test computed properties
        assert spec.aspect_ratio == pytest.approx(2.0, rel=0.01)
        assert spec.thermal_efficiency == pytest.approx(0.35, rel=0.01)
        assert spec.power_density > 0
        assert spec.enrichment_class.value == "HALEU"

    def test_json_serialization(self):
        """Test JSON serialization round-trip."""
        spec = ReactorSpecification(
            name="Test-JSON",
            reactor_type=ReactorType.PRISMATIC,
            power_thermal=10e6,
            inlet_temperature=823.15,
            outlet_temperature=1023.15,
            max_fuel_temperature=1873.15,
            primary_pressure=7.0e6,
            core_height=200.0,
            core_diameter=100.0,
            reflector_thickness=30.0,
            fuel_type=FuelType.UCO,
            enrichment=0.195,
            heavy_metal_loading=150.0,
            coolant_flow_rate=8.0,
            cycle_length=3650,
            capacity_factor=0.95,
            target_burnup=150.0,
            doppler_coefficient=-3.5e-5,
            shutdown_margin=0.05,
        )

        # Serialize
        json_str = spec.model_dump_json()

        # Deserialize
        spec_reloaded = ReactorSpecification.model_validate_json(json_str)

        # Check equality
        assert spec_reloaded.name == spec.name
        assert spec_reloaded.power_thermal == spec.power_thermal
        assert spec_reloaded.enrichment == spec.enrichment


class TestCrossSectionData:
    """Test CrossSectionData validation."""

    def test_valid_cross_sections(self):
        """Test valid cross sections are accepted."""
        xs = CrossSectionData(
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

        assert xs.n_groups == 2
        assert xs.n_materials == 1

    def test_negative_cross_sections_rejected(self):
        """Test that negative XS are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CrossSectionData(
                n_groups=2,
                n_materials=1,
                sigma_t=np.array([[0.5, 0.8]]),
                sigma_a=np.array([[-0.1, 0.2]]),  # Negative!
                sigma_f=np.array([[0.05, 0.15]]),
                nu_sigma_f=np.array([[0.125, 0.375]]),
                sigma_s=np.array([[[0.39, 0.01], [0.0, 0.58]]]),
                chi=np.array([[1.0, 0.0]]),
                D=np.array([[1.5, 0.4]]),
            )

        assert "negative" in str(exc_info.value).lower()

    def test_absorption_exceeds_total_rejected(self):
        """Test that sigma_a > sigma_t is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CrossSectionData(
                n_groups=2,
                n_materials=1,
                sigma_t=np.array([[0.5, 0.8]]),
                sigma_a=np.array([[0.6, 0.9]]),  # > sigma_t!
                sigma_f=np.array([[0.05, 0.15]]),
                nu_sigma_f=np.array([[0.125, 0.375]]),
                sigma_s=np.array([[[0.39, 0.01], [0.0, 0.58]]]),
                chi=np.array([[1.0, 0.0]]),
                D=np.array([[1.5, 0.4]]),
            )

        assert "Absorption" in str(exc_info.value)
        assert "total" in str(exc_info.value).lower()

    def test_fission_spectrum_normalization(self):
        """Test that chi must sum to 1."""
        with pytest.raises(ValidationError) as exc_info:
            CrossSectionData(
                n_groups=2,
                n_materials=1,
                sigma_t=np.array([[0.5, 0.8]]),
                sigma_a=np.array([[0.1, 0.2]]),
                sigma_f=np.array([[0.05, 0.15]]),
                nu_sigma_f=np.array([[0.125, 0.375]]),
                sigma_s=np.array([[[0.39, 0.01], [0.0, 0.58]]]),
                chi=np.array([[0.5, 0.3]]),  # Sums to 0.8, not 1!
                D=np.array([[1.5, 0.4]]),
            )

        assert "sum to 1" in str(exc_info.value).lower()


class TestSolverOptions:
    """Test SolverOptions validation."""

    def test_valid_options(self):
        """Test valid solver options."""
        options = SolverOptions(
            max_iterations=500,
            tolerance=1e-6,
            acceleration="chebyshev",
            eigen_method="power",
            verbose=True,
        )

        assert options.max_iterations == 500
        assert options.tolerance == 1e-6

    def test_tolerance_bounds(self):
        """Test tolerance must be positive and reasonable."""
        with pytest.raises(ValidationError):
            SolverOptions(tolerance=-1e-6)  # Negative!

        with pytest.raises(ValidationError):
            SolverOptions(tolerance=1.0)  # Too large!

    def test_max_iterations_bounds(self):
        """Test max_iterations must be reasonable."""
        with pytest.raises(ValidationError):
            SolverOptions(max_iterations=5)  # Too few!

        with pytest.raises(ValidationError):
            SolverOptions(max_iterations=100000)  # Too many!


class TestIntegration:
    """Integration tests with real designs."""

    def test_valar_atomics_design_validates(self):
        """Test that Valar Atomics reference design validates."""
        from smrforge.presets.htgr_designs import ValarAtomicsReactor

        reactor = ValarAtomicsReactor()

        # Spec should be valid
        assert reactor.spec.name == "Valar-10"
        assert reactor.spec.power_thermal == 10e6
        assert reactor.spec.reactor_type == ReactorType.PRISMATIC

    def test_design_library_all_valid(self):
        """Test that all reference designs validate."""
        from smrforge.presets.htgr_designs import DesignLibrary

        library = DesignLibrary()

        # All should be valid
        assert library.validate_all_designs()

    def test_solver_accepts_pydantic_inputs(self):
        """Test that solver accepts Pydantic-validated inputs."""
        from smrforge.geometry.core import PrismaticCore
        from smrforge.neutronics.solver import MultiGroupDiffusion

        # Create validated inputs
        xs_data = CrossSectionData(
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

        options = SolverOptions(max_iterations=100, tolerance=1e-6, verbose=False)

        # Create simple geometry
        class SimpleGeometry:
            def __init__(self):
                self.radial_mesh = np.linspace(0, 200, 21)
                self.axial_mesh = np.linspace(0, 800, 41)
                self.core_diameter = 300.0

        geometry = SimpleGeometry()

        # Should not raise
        solver = MultiGroupDiffusion(geometry, xs_data, options)

        assert solver.xs.n_groups == 2
        assert solver.options.max_iterations == 100


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
