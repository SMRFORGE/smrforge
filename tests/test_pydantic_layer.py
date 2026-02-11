"""
Tests for Pydantic validation layer (pydantic_layer.py).

This module tests the validation functions, model validators, properties,
and utility functions that are not fully covered by other tests.
"""

import tempfile
import warnings
from pathlib import Path

import numpy as np
import pytest
import yaml
from pydantic import ValidationError

from smrforge.validation.pydantic_layer import (
    EnrichmentClass,
    FuelType,
    GeometryParameters,
    MaterialComposition,
    ReactorSpecification,
    ReactorType,
    SMRForgeSettings,
    SolverOptions,
    TransientConditions,
    load_reactor_from_json,
    load_reactor_from_yaml,
    save_reactor_to_json,
    validate_normalized_array,
    validate_numpy_array,
    validate_positive_array,
)

# ============================================================================
# Validation Functions
# ============================================================================


class TestValidationFunctions:
    """Test validation helper functions."""

    def test_validate_numpy_array_from_list(self):
        """Test validate_numpy_array converts list to array."""
        arr = validate_numpy_array([1.0, 2.0, 3.0])
        assert isinstance(arr, np.ndarray)
        assert np.allclose(arr, [1.0, 2.0, 3.0])

    def test_validate_numpy_array_from_array(self):
        """Test validate_numpy_array accepts numpy array."""
        arr = np.array([1.0, 2.0, 3.0])
        result = validate_numpy_array(arr)
        assert result is arr

    def test_validate_numpy_array_rejects_non_array(self):
        """Test validate_numpy_array rejects non-array types."""
        with pytest.raises(ValueError, match="Must be numpy array or list"):
            validate_numpy_array("not an array")

    def test_validate_positive_array_valid(self):
        """Test validate_positive_array accepts non-negative arrays."""
        arr = validate_positive_array([1.0, 2.0, 0.0, 3.0])
        assert isinstance(arr, np.ndarray)
        assert np.allclose(arr, [1.0, 2.0, 0.0, 3.0])

    def test_validate_positive_array_rejects_negative(self):
        """Test validate_positive_array rejects negative values."""
        with pytest.raises(ValueError, match="Contains negative values"):
            validate_positive_array([1.0, -2.0, 3.0])

    def test_validate_positive_array_rejects_nan(self):
        """Test validate_positive_array rejects NaN values."""
        with pytest.raises(ValueError, match="Contains NaN values"):
            validate_positive_array([1.0, np.nan, 3.0])

    def test_validate_positive_array_rejects_inf(self):
        """Test validate_positive_array rejects Inf values."""
        with pytest.raises(ValueError, match="Contains Inf values"):
            validate_positive_array([1.0, np.inf, 3.0])

    def test_validate_normalized_array_valid(self):
        """Test validate_normalized_array accepts arrays summing to 1."""
        arr = validate_normalized_array([0.3, 0.7])
        assert isinstance(arr, np.ndarray)
        assert np.allclose(arr, [0.3, 0.7])

    def test_validate_normalized_array_rejects_not_normalized(self):
        """Test validate_normalized_array rejects arrays not summing to 1."""
        with pytest.raises(ValueError, match="Array must sum to 1.0"):
            validate_normalized_array([0.3, 0.5])  # Sums to 0.8


# ============================================================================
# ReactorSpecification Validators and Properties
# ============================================================================


class TestReactorSpecificationValidators:
    """Test ReactorSpecification model validators."""

    @pytest.fixture
    def base_spec_dict(self):
        """Create base dictionary for ReactorSpecification."""
        return {
            "name": "Test-Reactor",
            "reactor_type": ReactorType.PRISMATIC,
            "power_thermal": 10e6,
            "inlet_temperature": 823.15,
            "outlet_temperature": 1023.15,
            "max_fuel_temperature": 1873.15,
            "primary_pressure": 7.0e6,
            "core_height": 200.0,
            "core_diameter": 100.0,
            "reflector_thickness": 30.0,
            "fuel_type": FuelType.UCO,
            "enrichment": 0.195,
            "heavy_metal_loading": 150.0,
            "coolant_flow_rate": 8.0,
            "cycle_length": 3650,
            "capacity_factor": 0.95,
            "target_burnup": 150.0,
            "doppler_coefficient": -3.5e-5,
            "shutdown_margin": 0.05,
        }

    def test_validate_temperatures_inlet_equals_outlet(self):
        """Test that inlet >= outlet is rejected."""
        with pytest.raises(
            ValueError, match="Inlet temperature.*must be.*less than outlet"
        ):
            ReactorSpecification(
                name="Test",
                reactor_type=ReactorType.PRISMATIC,
                power_thermal=10e6,
                inlet_temperature=900.0,  # Within field bounds (<= 900)
                outlet_temperature=900.0,  # Equal! Within field bounds (<= 1500)
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

    def test_validate_temperatures_outlet_exceeds_max_fuel(self):
        """Test that outlet > max_fuel_temperature is rejected."""
        with pytest.raises(
            ValueError, match="Outlet temperature.*exceeds.*max fuel temperature"
        ):
            ReactorSpecification(
                name="Test",
                reactor_type=ReactorType.PRISMATIC,
                power_thermal=10e6,
                inlet_temperature=823.15,
                outlet_temperature=1500.0,  # Within field bounds, but > max_fuel
                max_fuel_temperature=1400.0,  # Less than outlet
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

    def test_validate_temperatures_small_delta_t_warning(self, base_spec_dict):
        """Test warning for very small temperature rise."""
        base_spec_dict["inlet_temperature"] = 823.15
        base_spec_dict["outlet_temperature"] = 860.0  # Delta-T = 36.9 K < 50 K

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            ReactorSpecification(**base_spec_dict)
            assert len(w) > 0
            assert "small temperature rise" in str(w[0].message).lower()

    def test_validate_temperatures_large_delta_t_warning(self, base_spec_dict):
        """Test warning for very large temperature rise."""
        base_spec_dict["inlet_temperature"] = 823.15
        base_spec_dict["outlet_temperature"] = 1400.0  # Delta-T = 576.9 K > 500 K

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            ReactorSpecification(**base_spec_dict)
            assert len(w) > 0
            assert "large temperature rise" in str(w[0].message).lower()

    def test_validate_enrichment_heu_warning(self, base_spec_dict):
        """Test warning for enrichment > 20% (HEU)."""
        base_spec_dict["enrichment"] = 0.25  # 25% > 20%

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            ReactorSpecification(**base_spec_dict)
            assert len(w) > 0
            assert "exceeds leu limit" in str(w[0].message).lower()

    def test_validate_enrichment_haleu_warning(self, base_spec_dict):
        """Test warning for enrichment 5-20% (HALEU)."""
        base_spec_dict["enrichment"] = 0.10  # 10% in HALEU range

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            ReactorSpecification(**base_spec_dict)
            assert len(w) > 0
            assert "haleu" in str(w[0].message).lower()

    def test_validate_geometry_flat_core_warning(self, base_spec_dict):
        """Test warning for very flat core (H/D < 0.5)."""
        base_spec_dict["core_height"] = 40.0  # H/D = 0.4 < 0.5
        base_spec_dict["core_diameter"] = 100.0
        base_spec_dict["enrichment"] = 0.04  # Avoid HALEU warning

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            ReactorSpecification(**base_spec_dict)
            assert len(w) > 0
            # Check for flat core warning (may be mixed with others)
            warning_messages = [str(warn.message).lower() for warn in w]
            assert any("flat core" in msg for msg in warning_messages)

    def test_validate_geometry_tall_core_warning(self, base_spec_dict):
        """Test warning for very tall core (H/D > 5.0)."""
        base_spec_dict["core_height"] = 600.0  # H/D = 6.0 > 5.0
        base_spec_dict["core_diameter"] = 100.0
        base_spec_dict["enrichment"] = 0.04  # Avoid HALEU warning

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            ReactorSpecification(**base_spec_dict)
            assert len(w) > 0
            # Check for tall core warning (may be mixed with others)
            warning_messages = [str(warn.message).lower() for warn in w]
            assert any("tall core" in msg for msg in warning_messages)

    def test_validate_power_density_low_warning(self, base_spec_dict):
        """Test warning for very low power density."""
        base_spec_dict["power_thermal"] = 1e5  # Very low power
        base_spec_dict["core_height"] = 2000.0  # Large volume
        base_spec_dict["core_diameter"] = 1000.0
        base_spec_dict["enrichment"] = 0.04  # Avoid HALEU warning

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            ReactorSpecification(**base_spec_dict)
            assert len(w) > 0
            # Check for low power density warning (may be mixed with others)
            warning_messages = [str(warn.message).lower() for warn in w]
            assert any("low power density" in msg for msg in warning_messages)

    def test_validate_power_density_high_warning(self, base_spec_dict):
        """Test warning for very high power density."""
        base_spec_dict["power_thermal"] = 100e6  # Very high power
        base_spec_dict["core_height"] = 50.0  # Small volume
        base_spec_dict["core_diameter"] = 50.0
        base_spec_dict["enrichment"] = 0.04  # Avoid HALEU warning

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            ReactorSpecification(**base_spec_dict)
            assert len(w) > 0
            # Check for high power density warning (may be mixed with others)
            warning_messages = [str(warn.message).lower() for warn in w]
            assert any("high power density" in msg for msg in warning_messages)

    def test_validate_doppler_strong_warning(self, base_spec_dict):
        """Test warning for very strong Doppler coefficient."""
        base_spec_dict["doppler_coefficient"] = -2e-4  # < -1e-4

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            ReactorSpecification(**base_spec_dict)
            assert len(w) > 0
            assert "strong doppler" in str(w[0].message).lower()


class TestReactorSpecificationProperties:
    """Test ReactorSpecification computed properties."""

    @pytest.fixture
    def spec(self):
        """Create a valid ReactorSpecification."""
        return ReactorSpecification(
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

    def test_aspect_ratio(self, spec):
        """Test aspect_ratio property."""
        assert spec.aspect_ratio == pytest.approx(2.0, rel=0.01)

    def test_thermal_efficiency(self, spec):
        """Test thermal_efficiency property."""
        assert spec.thermal_efficiency == pytest.approx(0.35, rel=0.01)

    def test_thermal_efficiency_none(self):
        """Test thermal_efficiency is None when power_electric is None."""
        spec = ReactorSpecification(
            name="Test",
            reactor_type=ReactorType.PRISMATIC,
            power_thermal=10e6,
            power_electric=None,
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
        assert spec.thermal_efficiency is None

    def test_enrichment_class_natural(self):
        """Test enrichment_class for natural uranium."""
        spec = ReactorSpecification(
            name="Test",
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
            enrichment=0.005,  # < 1%
            heavy_metal_loading=150.0,
            coolant_flow_rate=8.0,
            cycle_length=3650,
            capacity_factor=0.95,
            target_burnup=150.0,
            doppler_coefficient=-3.5e-5,
            shutdown_margin=0.05,
        )
        assert spec.enrichment_class == EnrichmentClass.NATURAL

    def test_enrichment_class_leu(self):
        """Test enrichment_class for LEU."""
        spec = ReactorSpecification(
            name="Test",
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
            enrichment=0.04,  # 4% (LEU range)
            heavy_metal_loading=150.0,
            coolant_flow_rate=8.0,
            cycle_length=3650,
            capacity_factor=0.95,
            target_burnup=150.0,
            doppler_coefficient=-3.5e-5,
            shutdown_margin=0.05,
        )
        assert spec.enrichment_class == EnrichmentClass.LEU

    def test_enrichment_class_haleu(self, spec):
        """Test enrichment_class for HALEU."""
        assert spec.enrichment_class == EnrichmentClass.HALEU

    def test_enrichment_class_heu(self):
        """Test enrichment_class for HEU."""
        spec = ReactorSpecification(
            name="Test",
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
            enrichment=0.25,  # 25% (HEU)
            heavy_metal_loading=150.0,
            coolant_flow_rate=8.0,
            cycle_length=3650,
            capacity_factor=0.95,
            target_burnup=150.0,
            doppler_coefficient=-3.5e-5,
            shutdown_margin=0.05,
        )
        assert spec.enrichment_class == EnrichmentClass.HEU

    def test_core_volume(self, spec):
        """Test core_volume property."""
        # Volume in m³: π * (diameter/200)² * (height/100)
        # π * (100/200)² * (200/100) = π * 0.5² * 2 = π * 0.5 = 1.571 m³
        expected = np.pi * (100.0 / 200) ** 2 * (200.0 / 100)
        assert spec.core_volume == pytest.approx(expected, rel=0.01)

    def test_power_density(self, spec):
        """Test power_density property."""
        # Power density = (power_thermal / 1e6) / core_volume [MW/m³]
        expected = (10e6 / 1e6) / spec.core_volume
        assert spec.power_density == pytest.approx(expected, rel=0.01)

    def test_specific_power(self, spec):
        """Test specific_power property."""
        # Specific power = (power_thermal / 1000) / heavy_metal_loading [kW/kg HM]
        expected = (10e6 / 1000) / 150.0
        assert spec.specific_power == pytest.approx(expected, rel=0.01)


# ============================================================================
# GeometryParameters Validators
# ============================================================================


class TestGeometryParameters:
    """Test GeometryParameters validators."""

    def test_validate_mesh_quality_coarse_radial_warning(self):
        """Test warning for coarse radial mesh."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            GeometryParameters(n_radial_mesh=5)  # < 10
            assert len(w) > 0
            assert "radial mesh is coarse" in str(w[0].message).lower()

    def test_validate_mesh_quality_coarse_axial_warning(self):
        """Test warning for coarse axial mesh."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            GeometryParameters(n_axial_mesh=15)  # < 20
            assert len(w) > 0
            assert "axial mesh is coarse" in str(w[0].message).lower()

    def test_validate_mesh_quality_fine_warning(self):
        """Test warning for very fine mesh."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            GeometryParameters(n_radial_mesh=150, n_axial_mesh=250)  # > 100 and > 200
            assert len(w) > 0
            assert "fine mesh" in str(w[0].message).lower()


# ============================================================================
# MaterialComposition Validators and Properties
# ============================================================================


class TestMaterialComposition:
    """Test MaterialComposition validators and properties."""

    def test_validate_composition_empty_rejected(self):
        """Test that empty composition is rejected."""
        with pytest.raises(ValueError, match="Composition cannot be empty"):
            MaterialComposition(
                material_id="test",
                composition={},
                temperature=900.0,
                density=2.0,
            )

    def test_validate_composition_negative_density_rejected(self):
        """Test that negative atom density is rejected."""
        with pytest.raises(ValueError, match="Negative atom density"):
            MaterialComposition(
                material_id="test",
                composition={"U235": -0.01},
                temperature=900.0,
                density=2.0,
            )

    def test_validate_composition_high_density_warning(self):
        """Test warning for very high atom density."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            MaterialComposition(
                material_id="test",
                composition={"U235": 0.25},  # > 0.2
                temperature=900.0,
                density=2.0,
            )
            assert len(w) > 0
            assert "high atom density" in str(w[0].message).lower()

    def test_total_number_density(self):
        """Test total_number_density property."""
        comp = MaterialComposition(
            material_id="test",
            composition={"U235": 0.01, "U238": 0.02, "C": 0.05},
            temperature=900.0,
            density=2.0,
        )
        assert comp.total_number_density == pytest.approx(0.08, rel=0.01)


# ============================================================================
# TransientConditions Validators
# ============================================================================


class TestTransientConditions:
    """Test TransientConditions validators."""

    def test_validate_times_t_end_equals_t_start_rejected(self):
        """Test that t_end <= t_start is rejected."""
        with pytest.raises(ValueError, match="t_end must be greater than t_start"):
            TransientConditions(
                initial_power=10e6,
                initial_temperature=900.0,
                initial_flow_rate=8.0,
                initial_pressure=7e6,
                transient_type="LOFC",
                trigger_time=10.0,
                t_start=100.0,
                t_end=100.0,  # Equal to t_start!
            )

    def test_validate_times_trigger_before_start_rejected(self):
        """Test that trigger_time < t_start is rejected."""
        with pytest.raises(ValueError, match="trigger_time must be within"):
            TransientConditions(
                initial_power=10e6,
                initial_temperature=900.0,
                initial_flow_rate=8.0,
                initial_pressure=7e6,
                transient_type="LOFC",
                trigger_time=5.0,  # Before t_start!
                t_start=10.0,
                t_end=100.0,
            )

    def test_validate_times_trigger_after_end_rejected(self):
        """Test that trigger_time > t_end is rejected."""
        with pytest.raises(ValueError, match="trigger_time must be within"):
            TransientConditions(
                initial_power=10e6,
                initial_temperature=900.0,
                initial_flow_rate=8.0,
                initial_pressure=7e6,
                transient_type="LOFC",
                trigger_time=150.0,  # After t_end!
                t_start=10.0,
                t_end=100.0,
            )


# ============================================================================
# SolverOptions Validators
# ============================================================================


class TestSolverOptions:
    """Test SolverOptions validators."""

    def test_validate_tolerance_tight_warning(self):
        """Test warning for very tight tolerance."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            SolverOptions(tolerance=1e-12)  # < 1e-10
            assert len(w) > 0
            assert "tight tolerance" in str(w[0].message).lower()

    def test_validate_tolerance_loose_warning(self):
        """Test warning for loose tolerance."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            SolverOptions(tolerance=5e-3)  # > 1e-3
            assert len(w) > 0
            assert "loose tolerance" in str(w[0].message).lower()


# ============================================================================
# Utility Functions
# ============================================================================


class TestUtilityFunctions:
    """Test utility functions for loading/saving reactor specifications."""

    @pytest.fixture
    def sample_spec(self):
        """Create a sample ReactorSpecification."""
        return ReactorSpecification(
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

    def test_save_and_load_json(self, sample_spec):
        """Test save_reactor_to_json and load_reactor_from_json."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            filepath = Path(f.name)

        try:
            # Save
            save_reactor_to_json(sample_spec, filepath)

            # Load
            loaded_spec = load_reactor_from_json(filepath)

            # Verify
            assert loaded_spec.name == sample_spec.name
            assert loaded_spec.power_thermal == sample_spec.power_thermal
            assert loaded_spec.enrichment == sample_spec.enrichment
        finally:
            filepath.unlink()

    def test_load_reactor_from_yaml(self, sample_spec):
        """Test load_reactor_from_yaml."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            filepath = Path(f.name)

        try:
            # Save as YAML - convert enum values to strings for proper serialization
            data = sample_spec.model_dump(mode="python")
            # Convert enum values to their string representations
            data["reactor_type"] = (
                data["reactor_type"].value
                if hasattr(data["reactor_type"], "value")
                else str(data["reactor_type"])
            )
            data["fuel_type"] = (
                data["fuel_type"].value
                if hasattr(data["fuel_type"], "value")
                else str(data["fuel_type"])
            )

            with open(filepath, "w") as yaml_file:
                yaml.dump(data, yaml_file)

            # Load
            loaded_spec = load_reactor_from_yaml(filepath)

            # Verify
            assert loaded_spec.name == sample_spec.name
            assert loaded_spec.power_thermal == sample_spec.power_thermal
            assert loaded_spec.enrichment == sample_spec.enrichment
        finally:
            if filepath.exists():
                filepath.unlink()


# ============================================================================
# SMRForgeSettings
# ============================================================================


class TestSMRForgeSettings:
    """Test SMRForgeSettings configuration."""

    def test_default_settings(self):
        """Test default settings are loaded."""
        settings = SMRForgeSettings()
        assert settings.nuclear_data_library == "endfb8.0"
        assert settings.n_threads == 4
        assert settings.use_numba is True
        assert settings.strict_validation is True
        assert settings.log_level == "INFO"

    def test_settings_fields(self):
        """Test that all expected fields are present."""
        settings = SMRForgeSettings()
        assert hasattr(settings, "cache_dir")
        assert hasattr(settings, "output_dir")
        assert hasattr(settings, "nuclear_data_library")
        assert hasattr(settings, "n_threads")
        assert hasattr(settings, "use_numba")
        assert hasattr(settings, "strict_validation")
        assert hasattr(settings, "validation_warnings")
        assert hasattr(settings, "log_level")
