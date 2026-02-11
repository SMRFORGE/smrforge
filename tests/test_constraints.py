"""
Tests for design constraints and validation framework.

Tests cover:
- ConstraintSet creation and management
- Pre-defined constraint sets (regulatory, safety margins)
- DesignValidator constraint checking logic
- Violation detection (max/min constraints)
- Warning vs error classification
- Metrics extraction from reactor results
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, Mock

import numpy as np
import pytest

from smrforge.validation.constraints import (
    ConstraintSet,
    ConstraintViolation,
    DesignValidator,
    ValidationResult,
)


class TestConstraintViolation:
    """Tests for ConstraintViolation dataclass."""

    def test_constraint_violation_creation(self):
        """Test creating a constraint violation."""
        violation = ConstraintViolation(
            constraint_name="max_power_density",
            value=150.0,
            limit=100.0,
            unit="W/cm³",
            severity="error",
            message="Power density exceeds limit",
        )

        assert violation.constraint_name == "max_power_density"
        assert violation.value == 150.0
        assert violation.limit == 100.0
        assert violation.severity == "error"


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_validation_result_passed(self):
        """Test validation result with passed status."""
        result = ValidationResult(
            passed=True, violations=[], warnings=[], metrics={"k_eff": 1.05}
        )

        assert result.passed is True
        assert not result.has_errors()
        assert not result.has_warnings()

    def test_validation_result_with_errors(self):
        """Test validation result with errors."""
        violation = ConstraintViolation(
            constraint_name="max_power_density",
            value=150.0,
            limit=100.0,
            unit="W/cm³",
            severity="error",
            message="Exceeds limit",
        )

        result = ValidationResult(passed=False, violations=[violation], warnings=[])

        assert result.passed is False
        assert result.has_errors()
        assert not result.has_warnings()

    def test_validation_result_with_warnings(self):
        """Test validation result with warnings."""
        warning = ConstraintViolation(
            constraint_name="max_power_density",
            value=95.0,
            limit=100.0,
            unit="W/cm³",
            severity="warning",
            message="Close to limit",
        )

        result = ValidationResult(passed=True, violations=[], warnings=[warning])

        assert result.passed is True
        assert not result.has_errors()
        assert result.has_warnings()


class TestConstraintSet:
    """Tests for ConstraintSet class."""

    def test_add_constraint(self):
        """Test adding a constraint to set."""
        constraint_set = ConstraintSet(name="test")

        constraint_set.add_constraint(
            "max_power_density", 100.0, "max", "W/cm³", "Maximum power density"
        )

        assert "max_power_density" in constraint_set.constraints
        assert constraint_set.constraints["max_power_density"]["limit"] == 100.0
        assert constraint_set.constraints["max_power_density"]["type"] == "max"

    def test_get_regulatory_limits(self):
        """Test getting standard regulatory constraint set."""
        constraint_set = ConstraintSet.get_regulatory_limits()

        assert constraint_set.name == "regulatory_limits"
        assert "max_power_density" in constraint_set.constraints
        assert "max_temperature" in constraint_set.constraints
        assert "min_k_eff" in constraint_set.constraints
        assert "max_burnup" in constraint_set.constraints

        # Check values
        assert constraint_set.constraints["max_power_density"]["limit"] == 100.0
        assert constraint_set.constraints["max_temperature"]["limit"] == 1200.0
        assert constraint_set.constraints["min_k_eff"]["limit"] == 1.0

    def test_get_safety_margins(self):
        """Test getting safety margin constraint set."""
        constraint_set = ConstraintSet.get_safety_margins()

        assert constraint_set.name == "safety_margins"
        assert "shutdown_margin" in constraint_set.constraints
        assert "power_peak_factor" in constraint_set.constraints

        # Check values
        assert constraint_set.constraints["shutdown_margin"]["limit"] == 0.005
        assert constraint_set.constraints["power_peak_factor"]["limit"] == 1.5

    def test_save_and_load(self, tmp_path):
        """Test saving and loading constraint set."""
        constraint_set = ConstraintSet.get_regulatory_limits()
        file_path = tmp_path / "constraints.json"

        constraint_set.save(file_path)
        assert file_path.exists()
        with open(file_path) as f:
            data = json.load(f)
        assert data["name"] == "regulatory_limits"
        assert "constraints" in data

        loaded = ConstraintSet.load(file_path)
        assert loaded.name == constraint_set.name
        assert loaded.constraints == constraint_set.constraints
        assert loaded.description == constraint_set.description


class TestDesignValidator:
    """Tests for DesignValidator class."""

    def test_init(self):
        """Test validator initialization."""
        constraint_set = ConstraintSet.get_regulatory_limits()
        validator = DesignValidator(constraint_set)

        assert validator.constraint_set == constraint_set

    def test_validate_analysis_failure(self):
        """Test validation when analysis fails."""
        mock_reactor = Mock()
        mock_reactor.solve.side_effect = RuntimeError("Solver failed")

        constraint_set = ConstraintSet.get_regulatory_limits()
        validator = DesignValidator(constraint_set)

        result = validator.validate(mock_reactor)

        assert result.passed is False
        assert len(result.violations) == 1
        assert "analysis_failure" in result.violations[0].constraint_name

    def test_validate_k_eff_pass(self):
        """Test validation with passing k-eff."""
        mock_reactor = Mock()
        analysis_results = {"k_eff": 1.05}
        mock_reactor.solve.return_value = analysis_results

        constraint_set = ConstraintSet.get_regulatory_limits()
        validator = DesignValidator(constraint_set)

        result = validator.validate(mock_reactor, analysis_results)

        # k_eff = 1.05 > 1.0 (min_k_eff), so should pass
        assert result.passed is True
        assert "k_eff" in result.metrics
        assert result.metrics["k_eff"] == 1.05

    def test_validate_k_eff_fail(self):
        """Test validation with failing k-eff."""
        mock_reactor = Mock()
        analysis_results = {"k_eff": 0.95}  # Below minimum
        mock_reactor.solve.return_value = analysis_results

        constraint_set = ConstraintSet.get_regulatory_limits()
        validator = DesignValidator(constraint_set)

        result = validator.validate(mock_reactor, analysis_results)

        # k_eff = 0.95 < 1.0 (min_k_eff), so should fail
        assert result.passed is False
        assert len(result.violations) > 0
        assert any("min_k_eff" in v.constraint_name for v in result.violations)

    def test_validate_power_density_pass(self):
        """Test validation with passing power density."""
        mock_reactor = Mock()
        power_array = np.array([50.0, 75.0, 90.0])  # All below 100.0
        analysis_results = {"k_eff": 1.05, "power": power_array}
        mock_reactor.solve.return_value = analysis_results

        constraint_set = ConstraintSet.get_regulatory_limits()
        validator = DesignValidator(constraint_set)

        result = validator.validate(mock_reactor, analysis_results)

        assert result.passed is True
        assert "max_power_density" in result.metrics
        assert result.metrics["max_power_density"] == 90.0

    def test_validate_power_density_exceed(self):
        """Test validation with exceeding power density."""
        mock_reactor = Mock()
        power_array = np.array([50.0, 75.0, 150.0])  # Max exceeds 100.0 significantly
        analysis_results = {"k_eff": 1.05, "power": power_array}
        mock_reactor.solve.return_value = analysis_results

        constraint_set = ConstraintSet.get_regulatory_limits()
        validator = DesignValidator(constraint_set)

        result = validator.validate(mock_reactor, analysis_results)

        # 150.0 > 100.0 * 1.1, so should be error
        # Result may have errors or warnings depending on severity logic
        assert any(
            "max_power_density" in v.constraint_name
            for v in result.violations + result.warnings
        )

    def test_validate_power_density_warning(self):
        """Test validation with power density near limit (warning)."""
        mock_reactor = Mock()
        power_array = np.array(
            [50.0, 75.0, 105.0]
        )  # 105.0 just exceeds 100.0 (within 1.1 threshold)
        analysis_results = {"k_eff": 1.05, "power": power_array}
        mock_reactor.solve.return_value = analysis_results

        constraint_set = ConstraintSet.get_regulatory_limits()
        validator = DesignValidator(constraint_set)

        result = validator.validate(mock_reactor, analysis_results)

        # 105.0 > 100.0 but within 1.1 * limit, so may be warning
        # Should pass (no errors) but may have warnings
        assert result.passed is True  # No errors

    def test_validate_min_constraint(self):
        """Test validation with minimum constraint."""
        mock_reactor = Mock()
        analysis_results = {"k_eff": 1.05}
        mock_reactor.solve.return_value = analysis_results

        constraint_set = ConstraintSet(name="test")
        constraint_set.add_constraint("min_k_eff", 1.0, "min", "", "Minimum k-eff")

        validator = DesignValidator(constraint_set)
        result = validator.validate(mock_reactor, analysis_results)

        # k_eff = 1.05 > 1.0, should pass
        assert result.passed is True

    def test_validate_min_constraint_fail(self):
        """Test validation with failing minimum constraint."""
        mock_reactor = Mock()
        analysis_results = {"k_eff": 0.95}
        mock_reactor.solve.return_value = analysis_results

        constraint_set = ConstraintSet(name="test")
        constraint_set.add_constraint("min_k_eff", 1.0, "min", "", "Minimum k-eff")

        validator = DesignValidator(constraint_set)
        result = validator.validate(mock_reactor, analysis_results)

        # k_eff = 0.95 < 1.0, should fail
        assert result.passed is False

    def test_validate_with_preexisting_results(self):
        """Test validation with pre-existing analysis results."""
        mock_reactor = Mock()
        analysis_results = {"k_eff": 1.05, "power": np.array([50.0, 75.0, 80.0])}

        constraint_set = ConstraintSet.get_regulatory_limits()
        validator = DesignValidator(constraint_set)

        result = validator.validate(mock_reactor, analysis_results)

        # Should not call reactor.solve()
        mock_reactor.solve.assert_not_called()
        assert result.passed is True
        assert "k_eff" in result.metrics

    def test_validate_power_peak_factor(self):
        """Test validation of power peak factor."""
        mock_reactor = Mock()
        power_array = np.array(
            [50.0, 75.0, 100.0, 200.0]
        )  # Peak factor = 200/106.25 ≈ 1.88
        analysis_results = {"k_eff": 1.05, "power": power_array}
        mock_reactor.solve.return_value = analysis_results

        constraint_set = ConstraintSet.get_safety_margins()
        validator = DesignValidator(constraint_set)

        result = validator.validate(mock_reactor, analysis_results)

        assert "power_peak_factor" in result.metrics
        peak_factor = result.metrics["power_peak_factor"]
        assert peak_factor == pytest.approx(200.0 / 106.25, rel=0.01)

        # Peak factor 1.88 > 1.5 limit, should have violation
        assert peak_factor > 1.5
        # May be error or warning depending on severity threshold
        assert any(
            "power_peak_factor" in v.constraint_name
            for v in result.violations + result.warnings
        )

    def test_validate_unknown_constraint(self):
        """Test validation with unknown constraint (should skip)."""
        mock_reactor = Mock()
        analysis_results = {"k_eff": 1.05}
        mock_reactor.solve.return_value = analysis_results
        mock_reactor.spec = Mock()  # Has spec but no unknown attribute

        constraint_set = ConstraintSet(name="test")
        constraint_set.add_constraint("unknown_constraint", 100.0, "max", "", "Unknown")

        validator = DesignValidator(constraint_set)
        result = validator.validate(mock_reactor, analysis_results)

        # Should pass (unknown constraint skipped)
        assert result.passed is True

    def test_validate_value_from_reactor_spec(self):
        """Test validation when value comes from reactor.spec."""
        mock_reactor = Mock()
        mock_reactor.spec = Mock()
        mock_reactor.spec.max_burnup = 45.0
        analysis_results = {"k_eff": 1.05}

        constraint_set = ConstraintSet.get_regulatory_limits()
        validator = DesignValidator(constraint_set)
        result = validator.validate(mock_reactor, analysis_results)

        # max_burnup from spec = 45.0 < 50.0 limit, should pass
        assert result.passed is True

    def test_validate_min_constraint_warning_severity(self):
        """Test min constraint from reactor.spec with value just below limit (warning)."""
        mock_reactor = Mock()
        mock_reactor.spec = Mock()
        # limit=10.0, value=9.5: 9.5 >= 9.0 (limit*0.9) so severity=warning
        mock_reactor.spec.min_margin = 9.5
        analysis_results = {"k_eff": 1.05}

        constraint_set = ConstraintSet(name="test")
        constraint_set.add_constraint("min_margin", 10.0, "min", "", "Minimum margin")

        validator = DesignValidator(constraint_set)
        result = validator.validate(mock_reactor, analysis_results)

        assert result.passed is True
        assert len(result.warnings) >= 1

    def test_validate_min_constraint_error_severity(self):
        """Test min constraint from reactor.spec with value far below limit (error)."""
        mock_reactor = Mock()
        mock_reactor.spec = Mock()
        # limit=10.0, value=5.0: 5.0 < 9.0 so severity=error
        mock_reactor.spec.min_margin = 5.0
        analysis_results = {"k_eff": 1.05}

        constraint_set = ConstraintSet(name="test")
        constraint_set.add_constraint("min_margin", 10.0, "min", "", "Minimum margin")

        validator = DesignValidator(constraint_set)
        result = validator.validate(mock_reactor, analysis_results)

        assert result.passed is False
        assert len(result.violations) >= 1

    def test_validate_min_k_eff_max_type(self):
        """Test min_k_eff with max type (k_eff should not exceed limit)."""
        mock_reactor = Mock()
        # constraint_type "max" for min_k_eff: violation when value > limit
        analysis_results = {"k_eff": 1.15}

        constraint_set = ConstraintSet(name="test")
        constraint_set.add_constraint("min_k_eff", 1.10, "max", "", "Max k-eff")

        validator = DesignValidator(constraint_set)
        result = validator.validate(mock_reactor, analysis_results)

        # k_eff=1.15 > 1.10, so violation
        assert result.passed is False

    def test_validate_unknown_constraint_type_skipped(self):
        """Test constraint with unknown type is skipped."""
        mock_reactor = Mock()
        mock_reactor.spec = Mock()
        mock_reactor.spec.some_metric = 50.0
        analysis_results = {"k_eff": 1.05}

        constraint_set = ConstraintSet(name="test")
        constraint_set.add_constraint(
            "some_metric", 100.0, "unknown_type", "", "Unknown type"
        )

        validator = DesignValidator(constraint_set)
        result = validator.validate(mock_reactor, analysis_results)

        # Unknown type should skip (continue), no violation added
        assert result.passed is True

    def test_validate_spec_missing_constraint_attribute_skipped(self):
        """Test constraint not in metrics and not on reactor.spec is skipped (continue)."""
        mock_reactor = Mock()
        # spec without the constraint attribute so we hit the continue path
        mock_reactor.spec = type("Spec", (), {})()
        analysis_results = {"k_eff": 1.05}

        constraint_set = ConstraintSet(name="test")
        constraint_set.add_constraint("missing_attr", 100.0, "max", "", "Not on spec")

        validator = DesignValidator(constraint_set)
        result = validator.validate(mock_reactor, analysis_results)

        assert result.passed is True
        assert "missing_attr" not in result.metrics

    def test_validate_max_constraint_no_violation_severity_none(self):
        """Test max constraint when value <= limit sets severity None (no violation)."""
        mock_reactor = Mock()
        mock_reactor.spec = Mock()
        mock_reactor.spec.some_metric = 50.0
        analysis_results = {"k_eff": 1.05}

        constraint_set = ConstraintSet(name="test")
        constraint_set.add_constraint("some_metric", 100.0, "max", "", "Max 100")

        validator = DesignValidator(constraint_set)
        result = validator.validate(mock_reactor, analysis_results)

        assert result.passed is True
        assert not result.violations

    def test_validate_reactor_no_spec_skipped(self):
        """Test constraint not in metrics when reactor has no .spec is skipped (continue at line 242)."""
        reactor_no_spec = type("Reactor", (), {})()  # no .spec
        analysis_results = {"k_eff": 1.05}

        constraint_set = ConstraintSet(name="test")
        constraint_set.add_constraint("some_metric", 100.0, "max", "", "Not in metrics")

        validator = DesignValidator(constraint_set)
        result = validator.validate(reactor_no_spec, analysis_results)

        assert result.passed is True

    def test_validate_min_constraint_no_violation_severity_none(self):
        """Test min constraint when value >= limit sets severity None (no violation, line 261)."""
        mock_reactor = Mock()
        mock_reactor.spec = Mock()
        mock_reactor.spec.min_margin = 15.0
        analysis_results = {"k_eff": 1.05}

        constraint_set = ConstraintSet(name="test")
        constraint_set.add_constraint("min_margin", 10.0, "min", "", "Min 10")

        validator = DesignValidator(constraint_set)
        result = validator.validate(mock_reactor, analysis_results)

        assert result.passed is True
        assert not result.violations
