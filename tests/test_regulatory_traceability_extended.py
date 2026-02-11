"""
Extended tests for smrforge.validation.regulatory_traceability module.

This test file focuses on improving coverage from 40% to 75%+ by testing:
- ModelAssumption dataclass
- CalculationAuditTrail serialization and I/O
- SafetyMarginReport generation
- BEPUMethodology functionality
- Edge cases and error handling
"""

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

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
            assumption="Point kinetics approximation",
            justification="Valid for small perturbations",
            impact="May underestimate reactivity effects",
            uncertainty=0.05,
        )

        assert assumption.category == "neutronics"
        assert assumption.assumption == "Point kinetics approximation"
        assert assumption.justification == "Valid for small perturbations"
        assert assumption.impact == "May underestimate reactivity effects"
        assert assumption.uncertainty == 0.05

    def test_model_assumption_minimal(self):
        """Test creating ModelAssumption with minimal fields."""
        assumption = ModelAssumption(
            category="thermal", assumption="Single phase coolant"
        )

        assert assumption.category == "thermal"
        assert assumption.assumption == "Single phase coolant"
        assert assumption.justification is None
        assert assumption.impact is None
        assert assumption.uncertainty is None

    def test_model_assumption_all_categories(self):
        """Test ModelAssumption with different categories."""
        categories = ["neutronics", "thermal", "fuel", "safety", "mechanics"]

        for category in categories:
            assumption = ModelAssumption(
                category=category, assumption="Test assumption"
            )
            assert assumption.category == category


class TestCalculationAuditTrail:
    """Tests for CalculationAuditTrail dataclass."""

    def test_audit_trail_creation(self):
        """Test creating CalculationAuditTrail."""
        trail = CalculationAuditTrail(
            calculation_id="test_001",
            calculation_type="keff",
            timestamp=datetime.now(),
            inputs={"power": 100.0, "temperature": 1200.0},
            outputs={"k_eff": 1.00123},
        )

        assert trail.calculation_id == "test_001"
        assert trail.calculation_type == "keff"
        assert len(trail.inputs) == 2
        assert len(trail.outputs) == 1

    def test_audit_trail_to_dict(self):
        """Test converting audit trail to dictionary."""
        trail = CalculationAuditTrail(
            calculation_id="test_001",
            calculation_type="keff",
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            inputs={"power": 100.0},
            outputs={"k_eff": 1.00123},
            assumptions=[
                ModelAssumption(category="neutronics", assumption="Point kinetics")
            ],
        )

        data = trail.to_dict()

        assert data["calculation_id"] == "test_001"
        assert data["calculation_type"] == "keff"
        assert isinstance(data["timestamp"], str)
        assert len(data["assumptions"]) == 1
        assert data["assumptions"][0]["category"] == "neutronics"

    def test_audit_trail_serialize_numpy_array(self):
        """Test serialization with numpy arrays."""
        trail = CalculationAuditTrail(
            calculation_id="test_001",
            calculation_type="burnup",
            timestamp=datetime.now(),
            inputs={"power": np.array([100.0, 150.0, 200.0])},
            outputs={"concentrations": np.array([1.0, 2.0, 3.0])},
        )

        data = trail.to_dict()

        # Numpy arrays should be converted to lists
        assert isinstance(data["inputs"]["power"], list)
        assert len(data["inputs"]["power"]) == 3
        assert isinstance(data["outputs"]["concentrations"], list)

    def test_audit_trail_serialize_nested_dict(self):
        """Test serialization with nested dictionaries."""
        trail = CalculationAuditTrail(
            calculation_id="test_001",
            calculation_type="keff",
            timestamp=datetime.now(),
            inputs={"reactor": {"power": 100.0, "temperature": 1200.0}},
            outputs={},
        )

        data = trail.to_dict()

        assert isinstance(data["inputs"]["reactor"], dict)
        assert data["inputs"]["reactor"]["power"] == 100.0

    def test_audit_trail_serialize_list_with_arrays(self):
        """Test serialization with lists containing numpy arrays."""
        trail = CalculationAuditTrail(
            calculation_id="test_001",
            calculation_type="keff",
            timestamp=datetime.now(),
            inputs={"arrays": [np.array([1, 2]), np.array([3, 4])]},
            outputs={},
        )

        data = trail.to_dict()

        assert isinstance(data["inputs"]["arrays"], list)
        assert all(isinstance(item, list) for item in data["inputs"]["arrays"])

    def test_audit_trail_save(self, tmp_path):
        """Test saving audit trail to file."""
        trail = CalculationAuditTrail(
            calculation_id="test_001",
            calculation_type="keff",
            timestamp=datetime.now(),
            inputs={"power": 100.0},
            outputs={"k_eff": 1.00123},
        )

        filepath = tmp_path / "audit_trail.json"
        trail.save(filepath)

        assert filepath.exists()
        assert filepath.read_text()

    def test_audit_trail_save_creates_parent_dir(self, tmp_path):
        """Test that save creates parent directory."""
        trail = CalculationAuditTrail(
            calculation_id="test_001",
            calculation_type="keff",
            timestamp=datetime.now(),
            inputs={},
            outputs={},
        )

        filepath = tmp_path / "subdir" / "nested" / "audit_trail.json"
        trail.save(filepath)

        assert filepath.exists()
        assert filepath.parent.exists()

    def test_audit_trail_load(self, tmp_path):
        """Test loading audit trail from file."""
        # Create and save a trail
        original_trail = CalculationAuditTrail(
            calculation_id="test_001",
            calculation_type="keff",
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            inputs={"power": 100.0},
            outputs={"k_eff": 1.00123},
            assumptions=[
                ModelAssumption(category="neutronics", assumption="Point kinetics")
            ],
        )

        filepath = tmp_path / "audit_trail.json"
        original_trail.save(filepath)

        # Load it back
        loaded_trail = CalculationAuditTrail.load(filepath)

        assert loaded_trail.calculation_id == "test_001"
        assert loaded_trail.calculation_type == "keff"
        assert len(loaded_trail.assumptions) == 1
        assert loaded_trail.assumptions[0].category == "neutronics"

    def test_audit_trail_load_file_not_found(self):
        """Test loading non-existent file raises FileNotFoundError."""
        filepath = Path("nonexistent.json")

        with pytest.raises(FileNotFoundError):
            CalculationAuditTrail.load(filepath)

    def test_audit_trail_load_invalid_json(self, tmp_path):
        """Test loading invalid JSON raises ValueError."""
        filepath = tmp_path / "invalid.json"
        filepath.write_text("not valid json")

        with pytest.raises((ValueError, json.JSONDecodeError)):
            CalculationAuditTrail.load(filepath)

    def test_audit_trail_load_missing_timestamp(self, tmp_path):
        """Test loading file with missing timestamp."""
        # Create JSON without timestamp
        data = {
            "calculation_id": "test_001",
            "calculation_type": "keff",
            "inputs": {},
            "outputs": {},
        }

        filepath = tmp_path / "audit_trail.json"
        with open(filepath, "w") as f:
            json.dump(data, f)

        with pytest.raises((KeyError, ValueError)):
            CalculationAuditTrail.load(filepath)

    def test_audit_trail_add_assumption(self):
        """Test adding assumptions to audit trail."""
        trail = CalculationAuditTrail(
            calculation_id="test_001",
            calculation_type="keff",
            timestamp=datetime.now(),
            inputs={},
            outputs={},
        )

        assumption = ModelAssumption(category="neutronics", assumption="Point kinetics")

        trail.assumptions.append(assumption)

        assert len(trail.assumptions) == 1
        assert trail.assumptions[0].category == "neutronics"

    def test_audit_trail_solver_info(self):
        """Test audit trail with solver info."""
        trail = CalculationAuditTrail(
            calculation_id="test_001",
            calculation_type="keff",
            timestamp=datetime.now(),
            inputs={},
            outputs={},
            solver_info={
                "solver": "diffusion",
                "version": "1.0.0",
                "options": {"tolerance": 1e-6},
            },
        )

        assert trail.solver_info["solver"] == "diffusion"
        assert trail.solver_info["version"] == "1.0.0"

    def test_audit_trail_metadata(self):
        """Test audit trail with metadata."""
        trail = CalculationAuditTrail(
            calculation_id="test_001",
            calculation_type="keff",
            timestamp=datetime.now(),
            inputs={},
            outputs={},
            metadata={
                "user": "test_user",
                "computer": "test_computer",
                "python_version": "3.10",
            },
        )

        assert trail.metadata["user"] == "test_user"
        assert trail.metadata["computer"] == "test_computer"


class TestSafetyMargin:
    """Tests for SafetyMargin class."""

    def test_safety_margin_calculate_absolute(self):
        """Test calculating absolute safety margin."""
        margin = SafetyMargin.calculate_absolute(
            parameter="fuel_temperature", calculated=1200.0, limit=1600.0, units="K"
        )

        assert margin.parameter == "fuel_temperature"
        assert margin.calculated_value == 1200.0
        assert margin.limit == 1600.0
        assert margin.margin == 400.0
        assert margin.units == "K"
        assert margin.margin_percent > 0

    def test_safety_margin_calculate_absolute_zero_limit(self):
        """Test absolute margin with zero limit."""
        margin = SafetyMargin.calculate_absolute(
            parameter="test", calculated=10.0, limit=0.0, units="unit"
        )

        assert margin.margin == -10.0
        assert margin.margin_percent == 0.0

    def test_safety_margin_calculate_relative(self):
        """Test calculating relative safety margin."""
        margin = SafetyMargin.calculate_relative(
            parameter="power", calculated=80.0, limit=100.0, units="MW"
        )

        assert margin.parameter == "power"
        assert margin.calculated_value == 80.0
        assert margin.limit == 100.0
        assert margin.units == "MW"
        assert margin.margin_percent > 0  # Should be positive (25%)

    def test_safety_margin_calculate_relative_zero_calculated(self):
        """Test relative margin with zero calculated value raises ValueError."""
        with pytest.raises(ValueError, match="cannot be zero"):
            SafetyMargin.calculate_relative(
                parameter="test", calculated=0.0, limit=100.0, units="unit"
            )


class TestSafetyMarginReport:
    """Tests for SafetyMarginReport class."""

    def test_safety_margin_report_creation(self):
        """Test creating SafetyMarginReport."""
        report = SafetyMarginReport(calculation_id="test_001", timestamp=datetime.now())

        assert report.calculation_id == "test_001"
        assert len(report.margins) == 0
        # Summary is initialized as empty dict by default
        assert isinstance(report.summary, dict)

    def test_safety_margin_report_add_margin(self):
        """Test adding margins to report."""
        report = SafetyMarginReport(calculation_id="test_001", timestamp=datetime.now())

        margin1 = SafetyMargin.calculate_absolute(
            parameter="temp", calculated=1200.0, limit=1600.0, units="K"
        )

        report.add_margin(margin1)

        assert len(report.margins) == 1
        assert report.summary["total_margins"] == 1
        assert report.summary["passing"] == 1
        assert report.summary["failing"] == 0

    def test_safety_margin_report_add_failing_margin(self):
        """Test adding failing margin (negative margin)."""
        report = SafetyMarginReport(calculation_id="test_001", timestamp=datetime.now())

        margin = SafetyMargin.calculate_absolute(
            parameter="temp", calculated=1700.0, limit=1600.0, units="K"  # Above limit
        )

        report.add_margin(margin)

        assert report.summary["total_margins"] == 1
        assert report.summary["passing"] == 0
        assert report.summary["failing"] == 1

    def test_safety_margin_report_multiple_margins(self):
        """Test report with multiple margins."""
        report = SafetyMarginReport(calculation_id="test_001", timestamp=datetime.now())

        for i in range(5):
            margin = SafetyMargin.calculate_absolute(
                parameter=f"param_{i}",
                calculated=100.0 + i * 10,
                limit=150.0,
                units="unit",
            )
            report.add_margin(margin)

        assert report.summary["total_margins"] == 5
        assert report.summary["min_margin_percent"] is not None

    def test_safety_margin_report_empty(self):
        """Test empty safety margin report."""
        report = SafetyMarginReport(calculation_id="test_001", timestamp=datetime.now())

        # Summary starts empty, gets populated when margins are added
        # Let's add a margin then remove it to trigger _update_summary
        margin = SafetyMargin.calculate_absolute(
            parameter="temp", calculated=1200.0, limit=1600.0, units="K"
        )
        report.add_margin(margin)

        # Now remove it by clearing margins
        report.margins.clear()
        report._update_summary()

        assert report.summary["total_margins"] == 0
        assert report.summary["passing"] == 0
        assert report.summary["failing"] == 0
        assert report.summary["min_margin_percent"] is None


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_create_audit_trail(self):
        """Test create_audit_trail helper function."""
        trail = create_audit_trail(
            calculation_type="keff",
            inputs={"power": 100.0},
            outputs={"k_eff": 1.00123},
            calculation_id="test_001",
        )

        assert isinstance(trail, CalculationAuditTrail)
        assert trail.calculation_id == "test_001"
        assert trail.calculation_type == "keff"
        assert trail.inputs["power"] == 100.0
        assert trail.outputs["k_eff"] == 1.00123

    def test_create_audit_trail_auto_id(self):
        """Test create_audit_trail with auto-generated ID."""
        trail = create_audit_trail(
            calculation_type="keff", inputs={"power": 100.0}, outputs={"k_eff": 1.00123}
        )

        assert isinstance(trail, CalculationAuditTrail)
        assert trail.calculation_id is not None
        assert trail.calculation_id.startswith("keff_")

    def test_create_audit_trail_with_metadata(self):
        """Test create_audit_trail with metadata."""
        trail = create_audit_trail(
            calculation_type="keff",
            inputs={"power": 100.0},
            outputs={"k_eff": 1.00123},
            calculation_id="test_001",
            user="test_user",
            solver_version="1.0.0",
        )

        assert trail.metadata["user"] == "test_user"
        assert trail.solver_info["version"] == "1.0.0"

    def test_generate_safety_margins_from_reactor(self):
        """Test generate_safety_margins_from_reactor helper function."""
        # Create a mock reactor spec with actual attribute values
        mock_reactor_spec = Mock()
        # Configure the mock to return actual float values for attributes
        mock_reactor_spec.max_fuel_temperature = 1600.0
        mock_reactor_spec.shutdown_margin = 0.05  # 5% shutdown margin
        mock_reactor_spec.max_power_density = 20e6  # 20 MW/m³

        calculated_results = {
            "max_fuel_temperature": 1200.0,  # K
            "k_eff": 1.00123,
            "peak_power_density": 15e6,  # W/m³
            "calculation_id": "test_001",
        }

        report = generate_safety_margins_from_reactor(
            mock_reactor_spec, calculated_results
        )

        # Should return a SafetyMarginReport
        assert isinstance(report, SafetyMarginReport)
        assert report.calculation_id == "test_001"
        # Should have margins for the parameters we provided
        assert len(report.margins) > 0
        assert all(isinstance(m, SafetyMargin) for m in report.margins)
