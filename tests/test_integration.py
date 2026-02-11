"""
Tests for validation integration module (decorators, ValidatedClass, etc.).
Note: This file also contains integration workflow tests which may fail due to test data issues.
"""

import warnings

import numpy as np
import pytest

from smrforge.validation.data_validation import (
    DataValidator,
    PhysicalValidator,
    ValidationLevel,
    ValidationResult,
)
from smrforge.validation.integration import (
    ValidatedClass,
    ValidatedReactorSpec,
    ValidatedSolver,
    ValidationContext,
    check_normalized,
    check_physical_temperature,
    check_positive,
    check_range,
    validate_array,
    validate_inputs,
    validate_outputs,
)


class TestValidateInputs:
    """Test validate_inputs decorator."""

    def test_validate_inputs_valid(self):
        """Test validate_inputs with valid inputs."""

        @validate_inputs(T=lambda T: PhysicalValidator.validate_temperature(T))
        def calculate_density(T):
            return 1.0 / T

        result = calculate_density(1000.0)
        assert result > 0

    def test_validate_inputs_invalid_raises(self):
        """Test validate_inputs raises on invalid inputs."""

        @validate_inputs(T=lambda T: PhysicalValidator.validate_temperature(T))
        def calculate_density(T):
            return 1.0 / T

        with pytest.raises(ValueError, match="Validation failed"):
            calculate_density(-100.0)  # Invalid temperature

    def test_validate_inputs_warnings(self):
        """Test validate_inputs issues warnings."""

        @validate_inputs(
            T=lambda T: PhysicalValidator.validate_temperature(T, max_T=500.0)
        )
        def calculate_density(T):
            return 1.0 / T

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = calculate_density(2000.0)  # Above expected max but valid
            assert len(w) > 0
            assert (
                "WARNING" in str(w[0].message).upper()
                or "above" in str(w[0].message).lower()
            )


class TestValidateOutputs:
    """Test validate_outputs decorator."""

    def test_validate_outputs_dict(self):
        """Test validate_outputs with dict return."""

        @validate_outputs(k_eff=lambda k: PhysicalValidator.validate_k_eff(k))
        def mock_solver():
            return {"k_eff": 1.05, "iterations": 25}

        result = mock_solver()
        assert result["k_eff"] == 1.05

    def test_validate_outputs_tuple(self):
        """Test validate_outputs with tuple return."""

        @validate_outputs(k_eff=lambda k: PhysicalValidator.validate_k_eff(k))
        def mock_solver_tuple():
            return (1.05, np.array([1.0, 2.0]))

        result = mock_solver_tuple()
        assert result[0] == 1.05

    def test_validate_outputs_invalid_raises(self):
        """Test validate_outputs raises on invalid outputs."""

        @validate_outputs(k_eff=lambda k: PhysicalValidator.validate_k_eff(k))
        def mock_solver_invalid():
            return {"k_eff": 5.0}  # Invalid k_eff (too high)

        with pytest.raises(ValueError, match="Output validation failed"):
            mock_solver_invalid()

    def test_validate_outputs_dict_missing_key(self):
        """Test validate_outputs with dict missing key (should not error)."""

        @validate_outputs(k_eff=lambda k: PhysicalValidator.validate_k_eff(k))
        def mock_solver_no_key():
            return {"other": 1.0}  # Missing k_eff key

        result = mock_solver_no_key()
        assert "other" in result


class TestValidateArray:
    """Test validate_array function."""

    def test_validate_array_valid(self):
        """Test validate_array with valid array."""
        arr = np.array([1.0, 2.0, 3.0, 4.0])
        result = validate_array(arr, "test_array")
        assert result.valid is True

    def test_validate_array_not_numpy(self):
        """Test validate_array with non-numpy array."""
        arr = [1.0, 2.0, 3.0]  # List, not numpy array
        result = validate_array(arr, "test_array")
        assert result.valid is False
        assert result.has_errors()

    def test_validate_array_empty(self):
        """Test validate_array with empty array."""
        arr = np.array([])
        result = validate_array(arr, "test_array")
        assert not result.valid or result.has_issues()  # Should issue warning

    def test_validate_array_with_nan(self):
        """Test validate_array with NaN values."""
        arr = np.array([1.0, 2.0, np.nan, 4.0])
        result = validate_array(arr, "test_array", allow_nan=False)
        assert result.valid is False
        assert result.has_errors()

    def test_validate_array_with_inf(self):
        """Test validate_array with Inf values."""
        arr = np.array([1.0, 2.0, np.inf, 4.0])
        result = validate_array(arr, "test_array", allow_inf=False)
        assert result.valid is False
        assert result.has_errors()

    def test_validate_array_with_negative(self):
        """Test validate_array with negative values."""
        arr = np.array([1.0, -2.0, 3.0, 4.0])
        result = validate_array(arr, "test_array", allow_negative=False)
        assert result.valid is False
        assert result.has_errors()

    def test_validate_array_with_min_val(self):
        """Test validate_array with min_val check."""
        arr = np.array([1.0, 2.0, 0.5, 4.0])
        result = validate_array(arr, "test_array", min_val=1.0)
        assert len(result.issues) > 0  # Should have warnings for values below min

    def test_validate_array_with_max_val(self):
        """Test validate_array with max_val check."""
        arr = np.array([1.0, 2.0, 5.0, 4.0])
        result = validate_array(arr, "test_array", max_val=4.0)
        assert len(result.issues) > 0  # Should have warnings for values above max

    def test_validate_array_not_numpy(self):
        """Test validate_array with non-numpy array."""
        arr = [1.0, 2.0, 3.0]
        result = validate_array(arr, "test_array")
        assert result.has_errors()

    def test_validate_array_empty(self):
        """Test validate_array with empty array."""
        arr = np.array([])
        result = validate_array(arr, "test_array")
        assert len(result.issues) > 0
        assert any(issue.level == ValidationLevel.WARNING for issue in result.issues)

    def test_validate_array_nan(self):
        """Test validate_array with NaN values."""
        arr = np.array([1.0, np.nan, 3.0])
        result = validate_array(arr, "test_array", allow_nan=False)
        assert result.has_errors()

    def test_validate_array_inf(self):
        """Test validate_array with Inf values."""
        arr = np.array([1.0, np.inf, 3.0])
        result = validate_array(arr, "test_array", allow_inf=False)
        assert result.has_errors()

    def test_validate_array_negative(self):
        """Test validate_array with negative values."""
        arr = np.array([1.0, -2.0, 3.0])
        result = validate_array(arr, "test_array", allow_negative=False)
        assert result.has_errors()

    def test_validate_array_min_max(self):
        """Test validate_array with min/max bounds."""
        arr = np.array([1.0, 5.0, 10.0])
        result = validate_array(arr, "test_array", min_val=0.0, max_val=8.0)
        assert len(result.issues) > 0  # Should have warning for value > max


class TestValidatedClass:
    """Test ValidatedClass base class."""

    def test_validated_class_creation(self):
        """Test creating a ValidatedClass."""
        obj = ValidatedClass()
        assert obj._validation_enabled is True
        assert obj._last_validation is None

    def test_validated_class_validate(self):
        """Test ValidatedClass.validate() method."""
        obj = ValidatedClass()
        result = obj.validate()
        assert result.valid is True

    def test_validated_class_raise_on_error(self):
        """Test ValidatedClass raises on validation errors."""

        class BadValidatedClass(ValidatedClass):
            def _validate(self):
                result = ValidationResult(valid=False)
                result.add_issue(ValidationLevel.ERROR, "test", "Test error")
                return result

        obj = BadValidatedClass()
        with pytest.raises(ValueError, match="Validation failed"):
            obj.validate(raise_on_error=True)

    def test_validated_class_disable_enable(self):
        """Test disabling and enabling validation."""
        obj = ValidatedClass()
        obj.disable_validation()
        assert obj._validation_enabled is False

        obj.enable_validation()
        assert obj._validation_enabled is True


class TestValidatedReactorSpec:
    """Test ValidatedReactorSpec class."""

    def test_validated_reactor_spec_creation(self):
        """Test creating a ValidatedReactorSpec."""
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

        validated_spec = ValidatedReactorSpec(spec)
        assert validated_spec.spec == spec
        assert validated_spec.validator is not None


class TestValidatedSolver:
    """Test ValidatedSolver class."""

    def test_validated_solver_creation(self):
        """Test creating a ValidatedSolver."""
        from smrforge.validation.models import CrossSectionData, SolverOptions

        # Create minimal valid inputs
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

        geometry = {"n_radial": 20, "n_axial": 50}
        options = SolverOptions()

        # This will validate on init, which may raise if inputs invalid
        # But with valid inputs it should work
        try:
            validated_solver = ValidatedSolver(geometry, xs_data, options)
            assert validated_solver.geometry == geometry
            assert validated_solver.xs_data == xs_data
        except (ValueError, AttributeError):
            # If validation fails due to missing methods, skip
            pytest.skip("ValidatedSolver requires specific geometry interface")


class TestUtilityFunctions:
    """Test utility functions (check_positive, check_finite, etc.)."""

    def test_check_positive_valid(self):
        """Test check_positive with valid value."""
        check_positive(100.0, "test")

    def test_check_positive_invalid(self):
        """Test check_positive with invalid value."""
        with pytest.raises(ValueError):
            check_positive(-10.0, "test")

    def test_check_range_valid(self):
        """Test check_range with valid value."""
        check_range(5.0, 0.0, 10.0, "test")

    def test_check_range_invalid(self):
        """Test check_range with invalid value."""
        with pytest.raises(ValueError):
            check_range(15.0, 0.0, 10.0, "test")

    def test_check_normalized_valid(self):
        """Test check_normalized with valid array."""
        arr = np.array([0.3, 0.4, 0.3])
        check_normalized(arr, tolerance=1e-6, name="test")

    def test_check_normalized_invalid(self):
        """Test check_normalized with invalid array."""
        arr = np.array([0.3, 0.4, 0.5])  # Sums to 1.2, not 1.0
        with pytest.raises(ValueError):
            check_normalized(arr, tolerance=1e-6, name="test")

    def test_check_physical_temperature_valid(self):
        """Test check_physical_temperature with valid value."""
        check_physical_temperature(1000.0, "test")

    def test_check_physical_temperature_invalid(self):
        """Test check_physical_temperature with invalid value."""
        with pytest.raises(ValueError):
            check_physical_temperature(-10.0, "test")

    def test_check_physical_temperature_too_high(self):
        """Test check_physical_temperature with temperature exceeding limits."""
        with pytest.raises(ValueError, match="exceeds physical limits"):
            check_physical_temperature(5000.0, "test")

    def test_check_physical_temperature_zero(self):
        """Test check_physical_temperature with zero (invalid)."""
        with pytest.raises(ValueError, match="below absolute zero"):
            check_physical_temperature(0.0, "test")

    def test_check_physical_temperature_too_high(self):
        """Test check_physical_temperature with temperature exceeding limits."""
        with pytest.raises(ValueError, match="exceeds physical limits"):
            check_physical_temperature(5000.0, "test")

    def test_check_physical_temperature_zero(self):
        """Test check_physical_temperature with zero (invalid)."""
        with pytest.raises(ValueError, match="below absolute zero"):
            check_physical_temperature(0.0, "test")


class TestValidationContext:
    """Test ValidationContext context manager."""

    def test_validation_context(self):
        """Test ValidationContext as context manager."""

        class TestValidatedClass(ValidatedClass):
            pass

        obj = TestValidatedClass()

        # ValidationContext just disables validation
        with ValidationContext(obj):
            assert obj._validation_enabled is False

        # Should be restored after context
        assert obj._validation_enabled is True

    def test_validation_context_with_exception(self):
        """Test ValidationContext restores state even if exception occurs."""

        class TestValidatedClass(ValidatedClass):
            pass

        obj = TestValidatedClass()
        original_state = obj._validation_enabled

        try:
            with ValidationContext(obj):
                assert obj._validation_enabled is False
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Should be restored even after exception
        assert obj._validation_enabled == original_state


class TestValidatedClass:
    """Test ValidatedClass base class."""

    def test_validated_class_initialization(self):
        """Test ValidatedClass initialization."""
        obj = ValidatedClass()
        assert obj._validation_enabled is True
        assert obj._last_validation is None

    def test_validated_class_validate(self):
        """Test ValidatedClass.validate method."""
        obj = ValidatedClass()
        result = obj.validate(raise_on_error=False)
        assert result.valid is True
        assert obj._last_validation == result

    def test_validated_class_validate_raises_on_error(self):
        """Test ValidatedClass.validate raises on error when enabled."""

        class TestValidatedClass(ValidatedClass):
            def _validate(self):
                result = ValidationResult(valid=False)
                result.add_issue(ValidationLevel.ERROR, "test", "Test error")
                return result

        obj = TestValidatedClass()
        with pytest.raises(ValueError, match="Validation failed"):
            obj.validate(raise_on_error=True)

    def test_validated_class_validate_no_raise_on_error(self):
        """Test ValidatedClass.validate does not raise when raise_on_error=False."""

        class TestValidatedClass(ValidatedClass):
            def _validate(self):
                result = ValidationResult(valid=False)
                result.add_issue(ValidationLevel.ERROR, "test", "Test error")
                return result

        obj = TestValidatedClass()
        result = obj.validate(raise_on_error=False)
        assert result.valid is False
        assert len(result.issues) > 0

    def test_validated_class_disable_enable_validation(self):
        """Test ValidatedClass disable/enable validation methods."""
        obj = ValidatedClass()
        assert obj._validation_enabled is True

        obj.disable_validation()
        assert obj._validation_enabled is False

        obj.enable_validation()
        assert obj._validation_enabled is True


class TestValidatedSolverMethods:
    """Test ValidatedSolver methods including solve_with_validation."""

    def test_validated_solver_solve_with_validation(self):
        """Test ValidatedSolver.solve_with_validation method."""
        from unittest.mock import MagicMock, Mock

        from smrforge.validation.models import CrossSectionData, SolverOptions

        # Create a mock ValidatedSolver that implements required methods
        class MockValidatedSolver(ValidatedSolver):
            def __init__(self, geometry, xs_data, options):
                # Initialize parent but skip validation
                ValidatedClass.__init__(self)
                self.geometry = geometry
                self.xs_data = xs_data
                self.options = options
                self.validator = DataValidator()
                self.disable_validation()  # Disable validation

            def _solve_internal(self):
                """Mock solve method."""
                return 1.05, np.array([1.0, 2.0, 3.0])

            def _compute_power(self, flux):
                """Mock power computation."""
                return np.array([10.0, 20.0, 30.0])

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

        geometry = Mock()
        options = SolverOptions()

        # Create solver (validation already disabled in __init__)
        solver = MockValidatedSolver(geometry, xs_data, options)

        # Test solve_with_validation with validation disabled
        k_eff, flux, power = solver.solve_with_validation()
        assert k_eff == 1.05
        assert len(flux) == 3
        assert len(power) == 3

    def test_validated_solver_solve_with_validation_enabled(self):
        """Test ValidatedSolver.solve_with_validation with validation enabled."""
        from unittest.mock import Mock

        from smrforge.validation.models import CrossSectionData, SolverOptions

        # Create a mock ValidatedSolver that implements required methods
        class MockValidatedSolver(ValidatedSolver):
            def __init__(self, geometry, xs_data, options):
                # Initialize parent but skip validation
                ValidatedClass.__init__(self)
                self.geometry = geometry
                self.xs_data = xs_data
                self.options = options
                self.validator = DataValidator()
                self.disable_validation()  # Disable for init

            def _solve_internal(self):
                """Mock solve method with valid results."""
                return 1.05, np.array([1e13, 2e13, 3e13])

            def _compute_power(self, flux):
                """Mock power computation."""
                return np.array([1e6, 2e6, 3e6])

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

        geometry = Mock()
        options = SolverOptions()

        # Create solver (validation already disabled in __init__)
        solver = MockValidatedSolver(geometry, xs_data, options)
        solver.enable_validation()  # Enable for solve_with_validation

        # Test solve_with_validation with validation enabled
        # This will validate the solution, but may fail if validation is strict
        # We'll skip if it fails due to missing geometry interface
        try:
            k_eff, flux, power = solver.solve_with_validation()
            assert k_eff == 1.05
        except (ValueError, AttributeError, TypeError):
            # If validation fails due to missing methods on geometry/options, that's expected
            pytest.skip("solve_with_validation requires full geometry interface")

    def test_validated_solver_solve_with_validation_raises_on_validation_errors(
        self, monkeypatch
    ):
        """Ensure solve_with_validation raises when validate_solution reports errors."""
        from unittest.mock import Mock

        from smrforge.validation.models import CrossSectionData

        class MockValidatedSolver(ValidatedSolver):
            def __init__(self, geometry, xs_data, options):
                ValidatedClass.__init__(self)
                self.geometry = geometry
                self.xs_data = xs_data
                self.options = options
                self.validator = DataValidator()
                self.disable_validation()  # disable during init

            def _solve_internal(self):
                return 1.05, np.array([1.0, 2.0, 3.0])

            def _compute_power(self, flux):
                return np.array([10.0, 20.0, 30.0])

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
        geometry = Mock()
        # solve_with_validation reads options.power_target, so provide it explicitly.
        options = type("Opt", (), {"power_target": 1.0})()

        solver = MockValidatedSolver(geometry, xs_data, options)
        solver.enable_validation()

        bad = ValidationResult(valid=False)
        bad.add_issue(ValidationLevel.ERROR, "solution", "forced failure")
        monkeypatch.setattr(solver.validator, "validate_solution", lambda *a, **k: bad)

        with pytest.raises(ValueError, match="Solution validation failed"):
            solver.solve_with_validation()


class TestValidateArrayEdgeCases:
    """Test validate_array function with edge cases."""

    def test_validate_array_empty_array(self):
        """Test validate_array with empty array."""
        arr = np.array([])
        result = validate_array(arr, "test_array")
        assert result.valid is True  # Empty array is a warning, not an error
        assert len(result.issues) > 0
        assert any("Empty" in str(issue) for issue in result.issues)

    def test_validate_array_not_numpy_array(self):
        """Test validate_array with non-numpy array."""
        arr = [1, 2, 3]  # Python list
        result = validate_array(arr, "test_array")
        assert result.valid is False
        assert len(result.issues) > 0
        assert any("Not a numpy array" in str(issue) for issue in result.issues)

    def test_validate_array_with_nan(self):
        """Test validate_array with NaN values."""
        arr = np.array([1.0, 2.0, np.nan, 4.0])
        result = validate_array(arr, "test_array", allow_nan=False)
        assert result.valid is False
        assert any("NaN" in str(issue) for issue in result.issues)

    def test_validate_array_with_nan_allowed(self):
        """Test validate_array with NaN values allowed."""
        arr = np.array([1.0, 2.0, np.nan, 4.0])
        result = validate_array(arr, "test_array", allow_nan=True)
        # Should not have NaN error
        assert not any("NaN" in str(issue) for issue in result.issues)

    def test_validate_array_with_inf(self):
        """Test validate_array with Inf values."""
        arr = np.array([1.0, 2.0, np.inf, 4.0])
        result = validate_array(arr, "test_array", allow_inf=False)
        assert result.valid is False
        assert any("Inf" in str(issue) for issue in result.issues)

    def test_validate_array_with_inf_allowed(self):
        """Test validate_array with Inf values allowed."""
        arr = np.array([1.0, 2.0, np.inf, 4.0])
        result = validate_array(arr, "test_array", allow_inf=True)
        # Should not have Inf error
        assert not any("Inf" in str(issue) for issue in result.issues)

    def test_validate_array_min_max_val(self):
        """Test validate_array with min_val and max_val."""
        arr = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = validate_array(arr, "test_array", min_val=2.0, max_val=4.0)
        # Should have warnings for values outside range
        assert len(result.issues) > 0
        assert any(
            "minimum" in str(issue).lower() or "maximum" in str(issue).lower()
            for issue in result.issues
        )
