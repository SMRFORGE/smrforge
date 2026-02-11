"""
Tests for regulatory traceability and audit trail functionality.

Tests ModelAssumption, CalculationAuditTrail, SafetyMargin, SafetyMarginReport,
and convenience functions for regulatory compliance.
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from smrforge.validation.regulatory_traceability import (
    CalculationAuditTrail,
    ModelAssumption,
    SafetyMargin,
    SafetyMarginReport,
    create_audit_trail,
    generate_safety_margins_from_reactor,
)


class TestModelAssumption:
    """Tests for ModelAssumption dataclass."""

    def test_model_assumption_creation(self):
        """Test creating ModelAssumption with all fields."""
        assumption = ModelAssumption(
            category="neutronics",
            assumption="Diffusion approximation valid",
            justification="Large core, low leakage",
            impact="May underestimate flux gradients",
            uncertainty=0.05,
        )

        assert assumption.category == "neutronics"
        assert assumption.assumption == "Diffusion approximation valid"
        assert assumption.justification == "Large core, low leakage"
        assert assumption.impact == "May underestimate flux gradients"
        assert assumption.uncertainty == 0.05

    def test_model_assumption_optional_fields(self):
        """Test creating ModelAssumption with optional fields."""
        assumption = ModelAssumption(
            category="thermal",
            assumption="Steady-state conditions",
        )

        assert assumption.category == "thermal"
        assert assumption.assumption == "Steady-state conditions"
        assert assumption.justification is None
        assert assumption.impact is None
        assert assumption.uncertainty is None


class TestCalculationAuditTrail:
    """Tests for CalculationAuditTrail dataclass."""

    def test_audit_trail_creation(self):
        """Test creating CalculationAuditTrail."""
        timestamp = datetime.now()
        trail = CalculationAuditTrail(
            calculation_id="test_001",
            calculation_type="keff",
            timestamp=timestamp,
            inputs={"reactor_spec": "spec"},
            outputs={"k_eff": 1.00234},
        )

        assert trail.calculation_id == "test_001"
        assert trail.calculation_type == "keff"
        assert trail.timestamp == timestamp
        assert trail.inputs == {"reactor_spec": "spec"}
        assert trail.outputs == {"k_eff": 1.00234}
        assert trail.assumptions == []
        assert trail.solver_info == {}
        assert trail.metadata == {}

    def test_audit_trail_with_assumptions(self):
        """Test creating CalculationAuditTrail with assumptions."""
        assumption = ModelAssumption(
            category="neutronics",
            assumption="Test assumption",
        )
        trail = CalculationAuditTrail(
            calculation_id="test_002",
            calculation_type="burnup",
            timestamp=datetime.now(),
            inputs={},
            outputs={},
            assumptions=[assumption],
        )

        assert len(trail.assumptions) == 1
        assert trail.assumptions[0].category == "neutronics"

    def test_audit_trail_to_dict(self):
        """Test converting CalculationAuditTrail to dictionary."""
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        assumption = ModelAssumption(
            category="thermal",
            assumption="Test",
            justification="Justification",
        )
        trail = CalculationAuditTrail(
            calculation_id="test_003",
            calculation_type="keff",
            timestamp=timestamp,
            inputs={"input1": "value1"},
            outputs={"output1": 1.0},
            assumptions=[assumption],
            solver_info={"version": "1.0"},
            metadata={"user": "test_user"},
        )

        result = trail.to_dict()

        assert result["calculation_id"] == "test_003"
        assert result["calculation_type"] == "keff"
        assert result["timestamp"] == timestamp.isoformat()
        assert result["inputs"] == {"input1": "value1"}
        assert result["outputs"] == {"output1": 1.0}
        assert len(result["assumptions"]) == 1
        assert result["assumptions"][0]["category"] == "thermal"
        assert result["solver_info"] == {"version": "1.0"}
        assert result["metadata"] == {"user": "test_user"}

    def test_audit_trail_serialize_numpy_array(self):
        """Test serializing numpy arrays in to_dict."""
        trail = CalculationAuditTrail(
            calculation_id="test_004",
            calculation_type="keff",
            timestamp=datetime.now(),
            inputs={},
            outputs={"flux": np.array([1.0, 2.0, 3.0])},
        )

        result = trail.to_dict()

        assert result["outputs"]["flux"] == [1.0, 2.0, 3.0]

    def test_audit_trail_serialize_nested_dict(self):
        """Test serializing nested dictionaries."""
        trail = CalculationAuditTrail(
            calculation_id="test_005",
            calculation_type="keff",
            timestamp=datetime.now(),
            inputs={"nested": {"key": "value"}},
            outputs={},
        )

        result = trail.to_dict()

        assert result["inputs"]["nested"]["key"] == "value"

    def test_audit_trail_serialize_list_with_arrays(self):
        """Test serializing lists containing numpy arrays."""
        trail = CalculationAuditTrail(
            calculation_id="test_006",
            calculation_type="keff",
            timestamp=datetime.now(),
            inputs={},
            outputs={"values": [np.array([1.0]), np.array([2.0])]},
        )

        result = trail.to_dict()

        assert result["outputs"]["values"] == [[1.0], [2.0]]

    def test_audit_trail_serialize_datetime(self):
        """Test serializing datetime objects in nested structures."""
        timestamp = datetime.now()
        trail = CalculationAuditTrail(
            calculation_id="test_007",
            calculation_type="keff",
            timestamp=timestamp,
            inputs={"timestamp": timestamp},
            outputs={},
        )

        result = trail.to_dict()

        assert result["inputs"]["timestamp"] == timestamp.isoformat()

    def test_audit_trail_serialize_pydantic_model(self):
        """Test serializing Pydantic models."""
        mock_model = MagicMock()
        mock_model.model_dump.return_value = {"field": "value"}

        trail = CalculationAuditTrail(
            calculation_id="test_008",
            calculation_type="keff",
            timestamp=datetime.now(),
            inputs={"model": mock_model},
            outputs={},
        )

        result = trail.to_dict()

        assert result["inputs"]["model"] == {"field": "value"}
        mock_model.model_dump.assert_called_once()

    def test_audit_trail_save(self):
        """Test saving audit trail to file."""
        trail = CalculationAuditTrail(
            calculation_id="test_009",
            calculation_type="keff",
            timestamp=datetime.now(),
            inputs={"input": "value"},
            outputs={"output": 1.0},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "audit_trail.json"
            trail.save(filepath)

            assert filepath.exists()
            with open(filepath, "r") as f:
                data = json.load(f)

            assert data["calculation_id"] == "test_009"

    def test_audit_trail_save_creates_directory(self):
        """Test that save creates parent directories."""
        trail = CalculationAuditTrail(
            calculation_id="test_010",
            calculation_type="keff",
            timestamp=datetime.now(),
            inputs={},
            outputs={},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "subdir" / "audit_trail.json"
            trail.save(filepath)

            assert filepath.exists()
            assert filepath.parent.exists()

    def test_audit_trail_load(self):
        """Test loading audit trail from file."""
        timestamp = datetime.now()
        assumption = ModelAssumption(
            category="neutronics",
            assumption="Test assumption",
            justification="Justification",
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            data = {
                "calculation_id": "test_011",
                "calculation_type": "keff",
                "timestamp": timestamp.isoformat(),
                "inputs": {"input": "value"},
                "outputs": {"output": 1.0},
                "assumptions": [
                    {
                        "category": "neutronics",
                        "assumption": "Test assumption",
                        "justification": "Justification",
                        "impact": None,
                        "uncertainty": None,
                    }
                ],
                "solver_info": {},
                "metadata": {},
            }
            json.dump(data, f)
            temp_file = Path(f.name)

        try:
            trail = CalculationAuditTrail.load(temp_file)

            assert trail.calculation_id == "test_011"
            assert trail.calculation_type == "keff"
            assert trail.timestamp.isoformat() == timestamp.isoformat()
            assert len(trail.assumptions) == 1
            assert trail.assumptions[0].category == "neutronics"
        finally:
            temp_file.unlink()

    def test_audit_trail_load_file_not_found(self):
        """Test loading non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            CalculationAuditTrail.load(Path("nonexistent_file.json"))

    def test_audit_trail_load_invalid_json(self):
        """Test loading invalid JSON raises ValueError."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json")
            temp_file = Path(f.name)

        try:
            with pytest.raises((ValueError, json.JSONDecodeError)):
                CalculationAuditTrail.load(temp_file)
        finally:
            temp_file.unlink()

    def test_audit_trail_load_missing_timestamp(self):
        """Test loading file with missing timestamp."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            data = {
                "calculation_id": "test_012",
                "calculation_type": "keff",
                "inputs": {},
                "outputs": {},
            }
            json.dump(data, f)
            temp_file = Path(f.name)

        try:
            with pytest.raises((KeyError, ValueError)):
                CalculationAuditTrail.load(temp_file)
        finally:
            temp_file.unlink()


class TestSafetyMargin:
    """Tests for SafetyMargin dataclass."""

    def test_safety_margin_creation(self):
        """Test creating SafetyMargin."""
        margin = SafetyMargin(
            parameter="fuel_temperature",
            calculated_value=1800.0,
            limit=2000.0,
            margin=200.0,
            margin_percent=10.0,
            units="K",
        )

        assert margin.parameter == "fuel_temperature"
        assert margin.calculated_value == 1800.0
        assert margin.limit == 2000.0
        assert margin.margin == 200.0
        assert margin.margin_percent == 10.0
        assert margin.units == "K"

    def test_calculate_absolute_margin(self):
        """Test calculating absolute safety margin."""
        margin = SafetyMargin.calculate_absolute(
            parameter="fuel_temperature",
            calculated=1800.0,
            limit=2000.0,
            units="K",
        )

        assert margin.parameter == "fuel_temperature"
        assert margin.calculated_value == 1800.0
        assert margin.limit == 2000.0
        assert margin.margin == 200.0
        assert abs(margin.margin_percent - 10.0) < 1e-6  # (200/2000) * 100
        assert margin.units == "K"

    def test_calculate_absolute_margin_zero_limit(self):
        """Test calculating absolute margin with zero limit."""
        margin = SafetyMargin.calculate_absolute(
            parameter="test",
            calculated=100.0,
            limit=0.0,
            units="unit",
        )

        assert margin.margin == -100.0
        assert margin.margin_percent == 0.0  # Should handle zero limit

    def test_calculate_absolute_margin_negative(self):
        """Test calculating absolute margin when calculated exceeds limit."""
        margin = SafetyMargin.calculate_absolute(
            parameter="fuel_temperature",
            calculated=2100.0,
            limit=2000.0,
            units="K",
        )

        assert margin.margin == -100.0  # Negative margin (failing)
        assert margin.margin_percent < 0

    def test_calculate_relative_margin(self):
        """Test calculating relative safety margin."""
        margin = SafetyMargin.calculate_relative(
            parameter="shutdown_margin",
            calculated=0.95,
            limit=1.0,
            units="dk/k",
        )

        assert margin.parameter == "shutdown_margin"
        assert margin.calculated_value == 0.95
        assert margin.limit == 1.0
        # margin_percent = ((1.0/0.95) - 1) * 100 ≈ 5.26%
        assert margin.margin_percent > 0
        assert margin.units == "dk/k"

    def test_calculate_relative_margin_zero_calculated(self):
        """Test calculating relative margin with zero calculated value."""
        with pytest.raises(ValueError, match="cannot be zero"):
            SafetyMargin.calculate_relative(
                parameter="test",
                calculated=0.0,
                limit=1.0,
                units="unit",
            )

    def test_calculate_relative_margin_negative(self):
        """Test calculating relative margin when calculated exceeds limit."""
        margin = SafetyMargin.calculate_relative(
            parameter="test",
            calculated=1.1,
            limit=1.0,
            units="unit",
        )

        # margin_percent = ((1.0/1.1) - 1) * 100 ≈ -9.09%
        assert margin.margin_percent < 0


class TestSafetyMarginReport:
    """Tests for SafetyMarginReport dataclass."""

    def test_safety_margin_report_creation(self):
        """Test creating SafetyMarginReport."""
        report = SafetyMarginReport(
            calculation_id="test_001",
            timestamp=datetime.now(),
        )

        assert report.calculation_id == "test_001"
        assert report.margins == []
        assert report.summary == {}

    def test_add_margin(self):
        """Test adding margin to report."""
        report = SafetyMarginReport(
            calculation_id="test_002",
            timestamp=datetime.now(),
        )

        margin = SafetyMargin.calculate_absolute(
            parameter="fuel_temperature",
            calculated=1800.0,
            limit=2000.0,
            units="K",
        )

        report.add_margin(margin)

        assert len(report.margins) == 1
        assert report.margins[0].parameter == "fuel_temperature"

    def test_update_summary_empty(self):
        """Test summary update with no margins."""
        report = SafetyMarginReport(
            calculation_id="test_003",
            timestamp=datetime.now(),
        )

        report._update_summary()

        assert report.summary["total_margins"] == 0
        assert report.summary["passing"] == 0
        assert report.summary["failing"] == 0
        assert report.summary["min_margin_percent"] is None

    def test_update_summary_with_margins(self):
        """Test summary update with margins."""
        report = SafetyMarginReport(
            calculation_id="test_004",
            timestamp=datetime.now(),
        )

        margin1 = SafetyMargin.calculate_absolute(
            parameter="param1",
            calculated=100.0,
            limit=200.0,
            units="unit",
        )
        margin2 = SafetyMargin.calculate_absolute(
            parameter="param2",
            calculated=250.0,
            limit=200.0,
            units="unit",
        )

        report.add_margin(margin1)  # Passing (margin > 0)
        report.add_margin(margin2)  # Failing (margin < 0)

        assert report.summary["total_margins"] == 2
        assert report.summary["passing"] == 1
        assert report.summary["failing"] == 1
        assert report.summary["min_margin_percent"] is not None

    def test_to_dict(self):
        """Test converting SafetyMarginReport to dictionary."""
        timestamp = datetime.now()
        report = SafetyMarginReport(
            calculation_id="test_005",
            timestamp=timestamp,
        )

        margin = SafetyMargin.calculate_absolute(
            parameter="fuel_temperature",
            calculated=1800.0,
            limit=2000.0,
            units="K",
        )
        report.add_margin(margin)

        result = report.to_dict()

        assert result["calculation_id"] == "test_005"
        assert result["timestamp"] == timestamp.isoformat()
        assert len(result["margins"]) == 1
        assert result["margins"][0]["parameter"] == "fuel_temperature"
        assert "summary" in result

    def test_save(self):
        """Test saving safety margin report to file."""
        report = SafetyMarginReport(
            calculation_id="test_006",
            timestamp=datetime.now(),
        )

        margin = SafetyMargin.calculate_absolute(
            parameter="fuel_temperature",
            calculated=1800.0,
            limit=2000.0,
            units="K",
        )
        report.add_margin(margin)

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "report.json"
            report.save(filepath)

            assert filepath.exists()
            with open(filepath, "r") as f:
                data = json.load(f)

            assert data["calculation_id"] == "test_006"

    def test_save_creates_directory(self):
        """Test that save creates parent directories."""
        report = SafetyMarginReport(
            calculation_id="test_007",
            timestamp=datetime.now(),
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "subdir" / "report.json"
            report.save(filepath)

            assert filepath.exists()
            assert filepath.parent.exists()

    def test_to_text(self):
        """Test generating text report."""
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        report = SafetyMarginReport(
            calculation_id="test_008",
            timestamp=timestamp,
        )

        margin1 = SafetyMargin.calculate_absolute(
            parameter="fuel_temperature",
            calculated=1800.0,
            limit=2000.0,
            units="K",
        )
        margin2 = SafetyMargin.calculate_absolute(
            parameter="power_density",
            calculated=25e6,
            limit=20e6,
            units="W/m³",
        )

        report.add_margin(margin1)  # Passing
        report.add_margin(margin2)  # Failing

        text = report.to_text()

        assert "SAFETY MARGIN REPORT" in text
        assert "test_008" in text
        assert "fuel_temperature" in text
        assert "power_density" in text
        assert "PASS" in text
        assert "FAIL" in text

    def test_format_margin_falls_back_to_str_on_typeerror(self):
        """Cover _format_margin exception path (TypeError/ValueError)."""
        report = SafetyMarginReport(calculation_id="fmt_001", timestamp=datetime.now())

        class Weird:
            def __float__(self):
                raise TypeError("no float")

            def __str__(self):
                return "WEIRD"

        assert report._format_margin(Weird()) == "WEIRD"


class TestCreateAuditTrail:
    """Tests for create_audit_trail convenience function."""

    def test_create_audit_trail_basic(self):
        """Test creating audit trail with basic parameters."""
        trail = create_audit_trail(
            calculation_type="keff",
            inputs={"input": "value"},
            outputs={"output": 1.0},
        )

        assert trail.calculation_type == "keff"
        assert trail.inputs == {"input": "value"}
        assert trail.outputs == {"output": 1.0}
        assert trail.calculation_id is not None
        assert trail.calculation_id.startswith("keff_")

    def test_create_audit_trail_with_id(self):
        """Test creating audit trail with specified ID."""
        trail = create_audit_trail(
            calculation_type="burnup",
            inputs={},
            outputs={},
            calculation_id="custom_id_001",
        )

        assert trail.calculation_id == "custom_id_001"

    def test_create_audit_trail_with_assumptions(self):
        """Test creating audit trail with assumptions."""
        assumptions = [
            ModelAssumption(
                category="neutronics",
                assumption="Test assumption",
            )
        ]

        trail = create_audit_trail(
            calculation_type="keff",
            inputs={},
            outputs={},
            assumptions=assumptions,
        )

        assert len(trail.assumptions) == 1
        assert trail.assumptions[0].category == "neutronics"

    def test_create_audit_trail_with_metadata(self):
        """Test creating audit trail with metadata."""
        trail = create_audit_trail(
            calculation_type="keff",
            inputs={},
            outputs={},
            user="test_user",
            computer="test_computer",
        )

        assert trail.metadata["user"] == "test_user"
        assert trail.metadata["computer"] == "test_computer"

    def test_create_audit_trail_solver_info(self):
        """Test creating audit trail with solver info."""
        trail = create_audit_trail(
            calculation_type="keff",
            inputs={},
            outputs={},
            solver_version="1.0.0",
            solver_method="diffusion",
        )

        assert trail.solver_info["version"] == "1.0.0"
        assert trail.solver_info["method"] == "diffusion"

    def test_create_audit_trail_solver_info_defaults(self):
        """Test creating audit trail with default solver info."""
        trail = create_audit_trail(
            calculation_type="keff",
            inputs={},
            outputs={},
        )

        assert trail.solver_info["version"] == "unknown"
        assert trail.solver_info["method"] == "unknown"


class TestGenerateSafetyMarginsFromReactor:
    """Tests for generate_safety_margins_from_reactor function."""

    def test_generate_safety_margins_fuel_temperature(self):
        """Test generating safety margins for fuel temperature."""
        mock_reactor = MagicMock()
        mock_reactor.max_fuel_temperature = 2000.0

        results = {
            "max_fuel_temperature": 1800.0,
            "calculation_id": "calc_001",
        }

        report = generate_safety_margins_from_reactor(mock_reactor, results)

        assert report.calculation_id == "calc_001"
        assert len(report.margins) == 1
        assert report.margins[0].parameter == "max_fuel_temperature"
        assert report.margins[0].calculated_value == 1800.0
        assert report.margins[0].limit == 2000.0
        assert report.margins[0].margin > 0  # Passing

    def test_generate_safety_margins_shutdown_margin(self):
        """Test generating safety margins for shutdown margin."""
        mock_reactor = MagicMock()
        mock_reactor.shutdown_margin = 0.05  # 5% shutdown margin

        results = {
            "k_eff": 0.95,
            "calculation_id": "calc_002",
        }

        report = generate_safety_margins_from_reactor(mock_reactor, results)

        assert len(report.margins) >= 1
        shutdown_margin = next(
            (m for m in report.margins if m.parameter == "shutdown_margin"), None
        )
        assert shutdown_margin is not None
        # k_eff = 0.95, shutdown_k = 1.0 - 0.05 = 0.95
        # margin should be positive (k_eff < shutdown_k is good)

    def test_generate_safety_margins_power_density(self):
        """Test generating safety margins for power density."""
        mock_reactor = MagicMock()
        mock_reactor.max_power_density = 20e6  # W/m³

        results = {
            "peak_power_density": 15e6,
            "calculation_id": "calc_003",
        }

        report = generate_safety_margins_from_reactor(mock_reactor, results)

        assert len(report.margins) >= 1
        power_margin = next(
            (m for m in report.margins if m.parameter == "peak_power_density"), None
        )
        assert power_margin is not None
        assert power_margin.calculated_value == 15e6
        assert power_margin.limit == 20e6

    def test_generate_safety_margins_power_density_default_limit(self):
        """Test generating safety margins with default power density limit."""
        mock_reactor = MagicMock()
        # Remove max_power_density attribute to trigger default
        del mock_reactor.max_power_density

        results = {
            "peak_power_density": 15e6,
            "calculation_id": "calc_004",
        }

        report = generate_safety_margins_from_reactor(mock_reactor, results)

        assert len(report.margins) >= 1
        power_margin = next(
            (m for m in report.margins if m.parameter == "peak_power_density"), None
        )
        assert power_margin is not None
        assert power_margin.limit == 20e6  # Default limit

    def test_generate_safety_margins_all_parameters(self):
        """Test generating safety margins for all parameters."""
        mock_reactor = MagicMock()
        mock_reactor.max_fuel_temperature = 2000.0
        mock_reactor.shutdown_margin = 0.05
        mock_reactor.max_power_density = 20e6

        results = {
            "max_fuel_temperature": 1800.0,
            "k_eff": 0.95,
            "peak_power_density": 15e6,
            "calculation_id": "calc_005",
        }

        report = generate_safety_margins_from_reactor(mock_reactor, results)

        assert len(report.margins) == 3
        assert report.summary["total_margins"] == 3

    def test_generate_safety_margins_no_shutdown_margin_attr(self):
        """Test generating margins when reactor has no shutdown_margin attribute."""
        mock_reactor = MagicMock()
        mock_reactor.max_fuel_temperature = 2000.0
        # Remove shutdown_margin attribute to test hasattr check
        if hasattr(mock_reactor, "shutdown_margin"):
            delattr(mock_reactor, "shutdown_margin")

        results = {
            "max_fuel_temperature": 1800.0,
            "k_eff": 0.95,
            "calculation_id": "calc_006",
        }

        report = generate_safety_margins_from_reactor(mock_reactor, results)

        # Should only have fuel temperature margin, not shutdown margin
        assert len(report.margins) == 1
        assert report.margins[0].parameter == "max_fuel_temperature"

    def test_generate_safety_margins_calculation_id_none(self):
        """Test generating margins with None calculation_id."""
        mock_reactor = MagicMock()
        mock_reactor.max_fuel_temperature = 2000.0

        results = {
            "max_fuel_temperature": 1800.0,
            "calculation_id": None,
        }

        report = generate_safety_margins_from_reactor(mock_reactor, results)

        assert report.calculation_id == "unknown"

    def test_generate_safety_margins_calculation_id_not_string(self):
        """Test generating margins with non-string calculation_id."""
        mock_reactor = MagicMock()
        mock_reactor.max_fuel_temperature = 2000.0

        results = {
            "max_fuel_temperature": 1800.0,
            "calculation_id": 12345,  # Integer ID
        }

        report = generate_safety_margins_from_reactor(mock_reactor, results)

        assert report.calculation_id == "12345"  # Converted to string

    def test_generate_safety_margins_no_calculation_id(self):
        """Test generating margins without calculation_id in results."""
        mock_reactor = MagicMock()
        mock_reactor.max_fuel_temperature = 2000.0

        results = {
            "max_fuel_temperature": 1800.0,
        }

        report = generate_safety_margins_from_reactor(mock_reactor, results)

        assert report.calculation_id == "unknown"


class TestRegulatoryTraceabilityEdgeCases70Percent:
    """Edge case tests to improve regulatory_traceability.py coverage from 40% to 70%+."""

    def test_serialize_dict_mixed_types(self):
        """Test _serialize_dict with mixed data types."""
        trail = CalculationAuditTrail(
            calculation_id="test",
            calculation_type="keff",
            timestamp=datetime.now(),
            inputs={},
            outputs={},
        )

        mixed_data = {
            "array": np.array([1.0, 2.0]),
            "pydantic": MagicMock(model_dump=lambda: {"field": "value"}),
            "datetime": datetime(2024, 1, 1),
            "dict": {"nested": "value"},
            "list": [np.array([1.0]), np.array([2.0])],
            "string": "value",
            "number": 42,
        }

        result = trail._serialize_dict(mixed_data)

        assert result["array"] == [1.0, 2.0]
        assert result["pydantic"] == {"field": "value"}
        assert result["datetime"] == datetime(2024, 1, 1).isoformat()
        assert result["dict"]["nested"] == "value"
        assert result["list"] == [[1.0], [2.0]]
        assert result["string"] == "value"
        assert result["number"] == 42

    def test_serialize_dict_nested_mixed(self):
        """Test _serialize_dict with deeply nested mixed types."""
        trail = CalculationAuditTrail(
            calculation_id="test",
            calculation_type="keff",
            timestamp=datetime.now(),
            inputs={},
            outputs={},
        )

        nested_data = {
            "level1": {
                "level2": {
                    "array": np.array([1.0]),
                    "datetime": datetime(2024, 1, 1),
                }
            }
        }

        result = trail._serialize_dict(nested_data)

        assert result["level1"]["level2"]["array"] == [1.0]
        assert (
            result["level1"]["level2"]["datetime"] == datetime(2024, 1, 1).isoformat()
        )

    def test_safety_margin_calculate_absolute_zero_calculated(self):
        """Test calculate_absolute with zero calculated value."""
        margin = SafetyMargin.calculate_absolute(
            parameter="test",
            calculated=0.0,
            limit=100.0,
            units="unit",
        )

        # margin = limit - calculated = 100.0 - 0.0 = 100.0
        assert margin.margin == 100.0
        assert margin.margin_percent == 100.0  # (100.0 / 100.0) * 100 = 100%

    def test_safety_margin_calculate_absolute_exact_match(self):
        """Test calculate_absolute when calculated equals limit."""
        margin = SafetyMargin.calculate_absolute(
            parameter="test",
            calculated=100.0,
            limit=100.0,
            units="unit",
        )

        assert margin.margin == 0.0
        assert margin.margin_percent == 0.0

    def test_safety_margin_calculate_relative_exact_match(self):
        """Test calculate_relative when calculated equals limit."""
        margin = SafetyMargin.calculate_relative(
            parameter="test",
            calculated=1.0,
            limit=1.0,
            units="unit",
        )

        assert abs(margin.margin_percent) < 1e-6

    def test_safety_margin_report_update_summary_all_passing(self):
        """Test _update_summary when all margins are passing."""
        report = SafetyMarginReport(
            calculation_id="test",
            timestamp=datetime.now(),
        )

        margin1 = SafetyMargin.calculate_absolute(
            parameter="param1",
            calculated=100.0,
            limit=200.0,
            units="unit",
        )
        margin2 = SafetyMargin.calculate_absolute(
            parameter="param2",
            calculated=150.0,
            limit=300.0,
            units="unit",
        )

        report.add_margin(margin1)
        report.add_margin(margin2)

        assert report.summary["total_margins"] == 2
        assert report.summary["passing"] == 2
        assert report.summary["failing"] == 0

    def test_safety_margin_report_update_summary_min_margin(self):
        """Test _update_summary calculates minimum margin correctly."""
        report = SafetyMarginReport(
            calculation_id="test",
            timestamp=datetime.now(),
        )

        margin1 = SafetyMargin.calculate_absolute(
            parameter="param1",
            calculated=100.0,
            limit=200.0,
            units="unit",
        )  # 50% margin
        margin2 = SafetyMargin.calculate_absolute(
            parameter="param2",
            calculated=50.0,
            limit=200.0,
            units="unit",
        )  # 75% margin

        report.add_margin(margin1)
        report.add_margin(margin2)

        assert report.summary["min_margin_percent"] == 50.0

    def test_safety_margin_report_to_text_empty(self):
        """Test to_text with empty report."""
        report = SafetyMarginReport(
            calculation_id="test",
            timestamp=datetime.now(),
        )

        text = report.to_text()

        assert "SAFETY MARGIN REPORT" in text
        assert "test" in text

    def test_create_audit_trail_all_parameters(self):
        """Test create_audit_trail with all optional parameters."""
        assumptions = [ModelAssumption(category="test", assumption="test")]

        trail = create_audit_trail(
            calculation_type="keff",
            inputs={"input": "value"},
            outputs={"output": 1.0},
            calculation_id="custom_id",
            assumptions=assumptions,
            user="test_user",
            computer="test_computer",
            solver_version="2.0.0",
            solver_method="monte_carlo",
        )

        assert trail.calculation_id == "custom_id"
        assert len(trail.assumptions) == 1
        assert trail.metadata["user"] == "test_user"
        assert trail.solver_info["version"] == "2.0.0"
        assert trail.solver_info["method"] == "monte_carlo"
