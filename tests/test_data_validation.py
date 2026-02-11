"""
Tests for data_validation module.
"""

from types import SimpleNamespace

import numpy as np
import pytest

from smrforge.validation.data_validation import (
    ConsistencyValidator,
    DataValidator,
    GeometryValidator,
    NeutronicsValidator,
    PhysicalValidator,
    ThermalValidator,
    ValidationIssue,
    ValidationLevel,
    ValidationResult,
)


class TestValidationResult:
    """Test ValidationResult class."""

    def test_validation_result_creation(self):
        """Test creating a ValidationResult."""
        result = ValidationResult(valid=True)
        assert result.valid is True
        assert len(result.issues) == 0

    def test_add_issue(self):
        """Test adding validation issues."""
        result = ValidationResult(valid=True)

        result.add_issue(ValidationLevel.WARNING, "test_param", "Test warning")
        assert len(result.issues) == 1
        assert result.issues[0].level == ValidationLevel.WARNING

        # Adding ERROR should mark as invalid
        result.add_issue(ValidationLevel.ERROR, "test_param2", "Test error")
        assert result.valid is False

    def test_has_errors(self):
        """Test has_errors() method."""
        result = ValidationResult(valid=True)
        assert not result.has_errors()

        result.add_issue(ValidationLevel.WARNING, "test", "Warning")
        assert not result.has_errors()

        result.add_issue(ValidationLevel.ERROR, "test", "Error")
        assert result.has_errors()

        result2 = ValidationResult(valid=True)
        result2.add_issue(ValidationLevel.CRITICAL, "test", "Critical")
        assert result2.has_errors()

    def test_summary(self):
        """Test summary() method."""
        result = ValidationResult(valid=True)
        result.add_issue(ValidationLevel.INFO, "p1", "Info")
        result.add_issue(ValidationLevel.WARNING, "p2", "Warning")
        result.add_issue(ValidationLevel.ERROR, "p3", "Error")

        summary = result.summary()
        assert summary["info"] == 1
        assert summary["warning"] == 1
        assert summary["error"] == 1
        assert summary["critical"] == 0

    def test_print_report_no_issues(self, capsys):
        """Cover print_report happy path."""
        result = ValidationResult(valid=True)
        result.print_report()
        captured = capsys.readouterr()
        assert "validations passed" in (captured.out + captured.err).lower()

    def test_print_report_with_errors_and_warnings(self, capsys):
        """Cover print_report sections for critical issues and warnings."""
        result = ValidationResult(valid=True)
        result.add_issue(ValidationLevel.ERROR, "p", "bad", value=1, expected=2)
        result.add_issue(ValidationLevel.WARNING, "q", "warn", value=3, expected=4)
        result.print_report()
        captured = capsys.readouterr()
        text = (captured.out + captured.err).lower()
        assert "validation summary" in text
        assert "critical issues" in text
        assert "warnings" in text


class TestValidationIssue:
    """Test ValidationIssue class."""

    def test_validation_issue_creation(self):
        """Test creating a ValidationIssue."""
        issue = ValidationIssue(
            level=ValidationLevel.WARNING,
            parameter="test_param",
            message="Test message",
            value=100.0,
            expected=50.0,
        )

        assert issue.level == ValidationLevel.WARNING
        assert issue.parameter == "test_param"
        assert issue.message == "Test message"
        assert issue.value == 100.0
        assert issue.expected == 50.0

    def test_validation_issue_str(self):
        """Test ValidationIssue string representation."""
        issue = ValidationIssue(
            ValidationLevel.ERROR, "temp", "Too high", value=500.0, expected=400.0
        )

        str_repr = str(issue)
        assert "ERROR" in str_repr
        assert "temp" in str_repr
        assert "500.0" in str_repr
        assert "400.0" in str_repr


class TestPhysicalValidator:
    """Test PhysicalValidator class."""

    def test_validate_temperature_valid(self):
        """Test temperature validation with valid values."""
        result = PhysicalValidator.validate_temperature(823.15, "inlet_temp")
        assert result.valid is True
        assert not result.has_errors()

    def test_validate_temperature_too_low(self):
        """Test temperature validation with value too low."""
        result = PhysicalValidator.validate_temperature(-10.0, "temp")
        assert result.has_errors()

    def test_validate_temperature_too_high(self):
        """Test temperature validation with value too high."""
        result = PhysicalValidator.validate_temperature(5000.0, "temp")
        assert result.has_errors()

    def test_validate_temperature_rejects_non_numeric_and_nan(self):
        result = PhysicalValidator.validate_temperature("hot", "temp")  # type: ignore[arg-type]
        assert result.has_errors()

        result2 = PhysicalValidator.validate_temperature(float("nan"), "temp")
        assert result2.has_errors()

    def test_validate_pressure_valid(self):
        """Test pressure validation with valid value."""
        result = PhysicalValidator.validate_pressure(7e6, "pressure")
        assert result.valid is True

    def test_validate_pressure_negative(self):
        """Test pressure validation with negative value."""
        result = PhysicalValidator.validate_pressure(-1.0, "pressure")
        assert result.has_errors()

    def test_validate_pressure_too_high(self):
        """Test pressure validation with value too high."""
        result = PhysicalValidator.validate_pressure(100e6, "pressure")
        # This gives a WARNING, not ERROR (above expected max but within physical limits)
        assert len(result.issues) > 0
        assert any(issue.level == ValidationLevel.WARNING for issue in result.issues)

    def test_validate_pressure_rejects_non_numeric_and_inf(self):
        result = PhysicalValidator.validate_pressure("p", "pressure")  # type: ignore[arg-type]
        assert result.has_errors()
        result2 = PhysicalValidator.validate_pressure(float("inf"), "pressure")
        assert result2.has_errors()

    def test_validate_enrichment_valid(self):
        """Test enrichment validation with valid value."""
        from smrforge.validation.models import FuelType

        result = PhysicalValidator.validate_enrichment(0.195, FuelType.UCO)
        assert result.valid is True

    def test_validate_enrichment_too_high(self):
        """Test enrichment validation with value too high."""
        from smrforge.validation.models import FuelType

        result = PhysicalValidator.validate_enrichment(1.5, FuelType.UCO)
        assert result.has_errors()

    def test_validate_enrichment_class_limits(self):
        # LEU limit (20%) is enforced as error.
        result = PhysicalValidator.validate_enrichment(0.25, "LEU")
        assert result.has_errors()

        # HALEU below 5% is a warning (classification mismatch).
        result2 = PhysicalValidator.validate_enrichment(0.03, "HALEU")
        assert any(i.level == ValidationLevel.WARNING for i in result2.issues)

        # HALEU above 20% is an error.
        result3 = PhysicalValidator.validate_enrichment(0.25, "HALEU")
        assert result3.has_errors()

        # HEU below 20% is a warning.
        result4 = PhysicalValidator.validate_enrichment(0.19, "HEU")
        assert any(i.level == ValidationLevel.WARNING for i in result4.issues)

    def test_validate_enrichment_rejects_non_numeric_and_negative(self):
        r = PhysicalValidator.validate_enrichment("e")  # type: ignore[arg-type]
        assert r.has_errors()
        r2 = PhysicalValidator.validate_enrichment(-0.01, "LEU")
        assert r2.has_errors()

    def test_validate_power_valid(self):
        """Test power validation with valid value."""
        result = PhysicalValidator.validate_power(10e6, "SMR")
        assert result.valid is True

    def test_validate_power_negative(self):
        """Test power validation with negative value."""
        result = PhysicalValidator.validate_power(-1e6, "SMR")
        assert result.has_errors()

    def test_validate_power_rejects_non_numeric_and_type_specific_warning(self):
        result = PhysicalValidator.validate_power("p", "SMR")  # type: ignore[arg-type]
        assert result.has_errors()
        result2 = PhysicalValidator.validate_power(20e6, "micro")
        assert any(i.level == ValidationLevel.WARNING for i in result2.issues)

        # Very high power warning and SMR range warning.
        result3 = PhysicalValidator.validate_power(2e9, "SMR")
        assert any(i.level == ValidationLevel.WARNING for i in result3.issues)
        result4 = PhysicalValidator.validate_power(400e6, "SMR")
        assert any(i.level == ValidationLevel.WARNING for i in result4.issues)

    def test_validate_k_eff_branches(self):
        # Non-numeric
        r = PhysicalValidator.validate_k_eff("k")  # type: ignore[arg-type]
        assert r.has_errors()

        # Too supercritical
        r2 = PhysicalValidator.validate_k_eff(2.0)
        assert any(i.level == ValidationLevel.WARNING for i in r2.issues)

        # Unphysical
        r3 = PhysicalValidator.validate_k_eff(4.0)
        assert r3.has_errors()

        # Below critical with margin
        r4 = PhysicalValidator.validate_k_eff(0.95, margin=0.02)
        assert any(i.level == ValidationLevel.WARNING for i in r4.issues)

        # Above critical with margin (info)
        r5 = PhysicalValidator.validate_k_eff(1.05, margin=0.02)
        assert any(i.level == ValidationLevel.INFO for i in r5.issues)


class TestGeometryValidator:
    """Test GeometryValidator class."""

    def test_validate_dimensions_valid(self):
        """Test dimension validation with valid values."""
        result = GeometryValidator.validate_dimensions(200.0, 100.0)
        assert result.valid is True

    def test_validate_dimensions_negative(self):
        """Test dimension validation with negative values."""
        result = GeometryValidator.validate_dimensions(-100.0, 50.0)
        assert result.has_errors()

        result2 = GeometryValidator.validate_dimensions(100.0, -50.0)
        assert result2.has_errors()

    def test_validate_dimensions_extremes_and_aspect_ratio(self):
        # Very small height/diameter -> warnings
        r = GeometryValidator.validate_dimensions(
            0.5, 0.5, min_size=1.0, max_size=2000.0
        )
        assert any(i.level == ValidationLevel.WARNING for i in r.issues)

        # Very large -> warnings
        r2 = GeometryValidator.validate_dimensions(
            3000.0, 3000.0, min_size=1.0, max_size=2000.0
        )
        assert any(i.level == ValidationLevel.WARNING for i in r2.issues)

        # Flat core aspect ratio warning
        r3 = GeometryValidator.validate_dimensions(10.0, 100.0)
        assert any(i.parameter == "aspect_ratio" for i in r3.issues)

        # Tall core aspect ratio warning
        r4 = GeometryValidator.validate_dimensions(600.0, 100.0)
        assert any(i.parameter == "aspect_ratio" for i in r4.issues)

    def test_validate_mesh_valid(self):
        """Test mesh validation with valid mesh sizes."""
        result = GeometryValidator.validate_mesh(20, 40)
        assert result.valid is True

    def test_validate_mesh_too_small(self):
        """Test mesh validation with mesh too small."""
        result = GeometryValidator.validate_mesh(1, 2)
        # This gives WARNING, not ERROR
        assert len(result.issues) > 0
        assert any(issue.level == ValidationLevel.WARNING for issue in result.issues)

    def test_validate_mesh_too_large(self):
        """Test mesh validation with mesh too large."""
        result = GeometryValidator.validate_mesh(1000, 2000)
        # This gives WARNING, not ERROR
        assert len(result.issues) > 0
        assert any(issue.level == ValidationLevel.WARNING for issue in result.issues)


class TestNeutronicsValidator:
    """Test NeutronicsValidator class."""

    def test_validate_cross_sections_valid(self):
        """Test cross-section validation with valid data."""
        from smrforge.validation.models import CrossSectionData

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

        result = NeutronicsValidator.validate_cross_sections(xs_data)
        # Should be valid (Pydantic already caught physical issues)
        assert isinstance(result, ValidationResult)

    def test_validate_flux_valid(self):
        """Test flux validation with valid flux."""
        flux = np.ones((10, 10, 2))
        result = NeutronicsValidator.validate_flux(flux, 10e6)
        assert isinstance(result, ValidationResult)

    def test_validate_cross_sections_invalid_branches(self):
        xs = SimpleNamespace(
            sigma_t=np.array([[1.0, -1.0]]),
            sigma_a=np.array([[2.0, 0.5]]),  # absorption > total (non-physical)
            sigma_f=np.array([[0.6, -0.1]]),  # fission > absorption and negative
            D=np.array([[0.0, 11.0]]),  # non-positive + very large
            chi=np.array([[0.2, 0.2]]),  # not normalized
        )
        r = NeutronicsValidator.validate_cross_sections(xs)
        assert r.has_errors()
        assert any(i.level == ValidationLevel.WARNING for i in r.issues)

    def test_validate_flux_invalid_branches(self):
        flux = np.ones((2, 2, 1))
        flux[0, 0, 0] = -1.0
        flux[0, 1, 0] = np.nan
        flux[1, 0, 0] = np.inf
        r = NeutronicsValidator.validate_flux(flux, 10e6)
        assert r.has_errors()


class TestThermalValidator:
    """Test ThermalValidator class."""

    def test_validate_heat_transfer_valid(self):
        """Test heat transfer validation with valid parameters."""
        result = ThermalValidator.validate_heat_transfer(h=500.0, regime="turbulent")
        assert result.valid is True

    def test_validate_heat_transfer_invalid(self):
        """Test heat transfer validation with invalid parameters."""
        result = ThermalValidator.validate_heat_transfer(h=-10.0, regime="turbulent")
        assert result.has_errors()

    def test_validate_reynolds_number(self):
        """Test Reynolds number validation."""
        result = ThermalValidator.validate_reynolds_number(5000.0)
        assert result.valid is True

        result2 = ThermalValidator.validate_reynolds_number(-100.0)
        assert result2.has_errors()

    def test_validate_heat_transfer_regime_warnings(self):
        r = ThermalValidator.validate_heat_transfer(h=2000.0, regime="laminar")
        assert any(i.level == ValidationLevel.WARNING for i in r.issues)
        r2 = ThermalValidator.validate_heat_transfer(h=10.0, regime="turbulent")
        assert any(i.level == ValidationLevel.WARNING for i in r2.issues)

    def test_validate_reynolds_number_high_and_transitional(self):
        r = ThermalValidator.validate_reynolds_number(2e7)
        assert any(i.level == ValidationLevel.WARNING for i in r.issues)
        r2 = ThermalValidator.validate_reynolds_number(3000.0)
        assert any(i.level == ValidationLevel.INFO for i in r2.issues)


class TestConsistencyValidator:
    """Test ConsistencyValidator class."""

    def test_validate_material_conservation_valid(self):
        """Test material conservation validation with valid values."""
        result = ConsistencyValidator.validate_material_conservation(
            mass_in=100.0, mass_out=95.0, mass_accumulated=5.0
        )
        assert result.valid is True

    def test_validate_energy_balance_error_and_warning(self):
        # Error case
        r = ConsistencyValidator.validate_energy_balance(100.0, 50.0, tolerance=0.05)
        assert r.has_errors()
        # Warning case (> tolerance/2 but <= tolerance)
        r2 = ConsistencyValidator.validate_energy_balance(100.0, 97.0, tolerance=0.05)
        assert any(i.level == ValidationLevel.WARNING for i in r2.issues)

    def test_validate_material_conservation_error(self):
        r = ConsistencyValidator.validate_material_conservation(
            mass_in=100.0, mass_out=90.0, mass_accumulated=5.0, tolerance=1e-6
        )
        assert r.has_errors()


class TestDataValidator:
    """Test DataValidator class."""

    def test_data_validator_initialization(self):
        """Test DataValidator initialization."""
        validator = DataValidator()
        assert validator.physical is not None
        assert validator.geometry is not None
        assert validator.neutronics is not None
        assert validator.thermal is not None
        assert validator.consistency is not None

    def test_validate_reactor_spec_valid(self):
        """Test validate_reactor_spec with valid specification."""
        from smrforge.validation.models import (
            FuelType,
            ReactorSpecification,
            ReactorType,
        )

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

        validator = DataValidator()
        result = validator.validate_reactor_spec(spec)
        # Should be valid (Pydantic already validated)
        assert isinstance(result, ValidationResult)

    def test_validate_reactor_spec_inlet_ge_outlet_adds_error(self):
        """Cover reactor spec consistency check (inlet >= outlet)."""
        validator = DataValidator()
        spec = SimpleNamespace(
            inlet_temperature=600.0,
            outlet_temperature=500.0,
            primary_pressure=7.0e6,
            enrichment=0.045,
            fuel_type="LEU",
            power_thermal=400e6,
            reactor_type=SimpleNamespace(value="SMR"),
            core_height=10.0,
            core_diameter=100.0,
        )
        result = validator.validate_reactor_spec(spec)
        assert result.has_errors()

    def test_validate_solver_inputs_branches(self):
        """Cover validate_solver_inputs warnings (mesh, cross sections, options)."""
        validator = DataValidator()
        geometry = SimpleNamespace(radial_mesh=np.arange(3), axial_mesh=np.arange(3))
        xs_data = SimpleNamespace(
            sigma_t=np.array([[1.0, 1.0]]),
            sigma_a=np.array([[0.1, 0.1]]),
            sigma_f=np.array([[0.0, 0.0]]),
            D=np.array([[1.0, 1.0]]),
            chi=np.array([[0.5, 0.5]]),
        )
        options = SimpleNamespace(tolerance=1e-12, max_iterations=5)
        result = validator.validate_solver_inputs(geometry, xs_data, options)
        assert any(i.level == ValidationLevel.WARNING for i in result.issues)

        options2 = SimpleNamespace(tolerance=1e-2, max_iterations=50)
        result2 = validator.validate_solver_inputs(geometry, xs_data, options2)
        assert any(i.parameter == "tolerance" for i in result2.issues)

    def test_validate_solution_valid(self):
        """Test validate_solution with valid solution."""
        validator = DataValidator()

        k_eff = 1.0
        flux = np.ones((10, 10, 2)) * 1e14
        power = np.ones((10, 10)) * 1e6
        power_target = 10e6

        result = validator.validate_solution(k_eff, flux, power, power_target)
        assert isinstance(result, ValidationResult)


def test_validate_k_eff_additional_branches():
    # k_eff <= 0 error
    r = PhysicalValidator.validate_k_eff(0.0)
    assert r.has_errors()
    # k_eff < 0.9 warning
    r2 = PhysicalValidator.validate_k_eff(0.8)
    assert any(i.level == ValidationLevel.WARNING for i in r2.issues)


def test_validate_cross_sections_additional_branches():
    xs = SimpleNamespace(
        sigma_t=np.array([[1.0, 1.0]]),
        sigma_a=np.array([[-0.1, 0.5]]),  # negative absorption
        sigma_f=np.array([[0.6, 0.6]]),  # fission > absorption for second group
        D=np.array([[1.0, 1.0]]),
        chi=np.array([[0.5, 0.5]]),
    )
    r = NeutronicsValidator.validate_cross_sections(xs)
    assert r.has_errors()


def test_validate_flux_high_flux_warning():
    flux = np.ones((1, 1, 1)) * 1e17
    r = NeutronicsValidator.validate_flux(flux, 10e6)
    assert any(i.level == ValidationLevel.WARNING for i in r.issues)
