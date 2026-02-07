"""
Tests for new workflow features: sensitivity, sobol, pareto report, audit log,
surrogate, scenario design, constraint builder, requirements parser, margin narrative.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock

from smrforge.workflows.sensitivity import one_at_a_time_from_sweep, SensitivityRanking
from smrforge.workflows.sobol_indices import sobol_indices_from_sweep_results
from smrforge.workflows.pareto_report import pareto_knee_point, pareto_summary_report
from smrforge.workflows.audit_log import append_run, RunRecord
from smrforge.workflows.surrogate import fit_surrogate, surrogate_from_sweep_results
from smrforge.workflows.scenario_design import run_scenario_design, ScenarioResult, scenario_comparison_report
from smrforge.validation.constraint_builder import constraint_set_from_design
from smrforge.validation.requirements_parser import parse_requirements_to_constraint_set
from smrforge.validation.safety_report import margin_narrative, SafetyMarginReport, MarginEntry


class TestSensitivityOAT:
    def test_one_at_a_time_from_sweep(self):
        results = [
            {"parameters": {"x": 0.0, "y": 0.0}, "k_eff": 1.0},
            {"parameters": {"x": 1.0, "y": 0.0}, "k_eff": 1.1},
            {"parameters": {"x": 2.0, "y": 0.0}, "k_eff": 1.2},
            {"parameters": {"x": 0.0, "y": 1.0}, "k_eff": 1.0},
        ]
        rankings = one_at_a_time_from_sweep(results, ["x", "y"], output_metric="k_eff")
        assert len(rankings) == 2
        assert rankings[0].parameter == "x"
        assert rankings[0].rank == 1


class TestSobolFromSweep:
    def test_sobol_indices_from_sweep_results(self):
        import numpy as np
        np.random.seed(42)
        results = [
            {"parameters": {"a": 0.1 * i, "b": 0.2 * j}, "k_eff": 1.0 + 0.01 * i + 0.02 * j}
            for i in range(5) for j in range(5)
        ]
        si = sobol_indices_from_sweep_results(results, ["a", "b"], output_metric="k_eff")
        assert "Y0" in si
        assert "S1" in si["Y0"]
        assert "ST" in si["Y0"]
        assert len(si["Y0"]["S1"]) == 2


class TestParetoReport:
    def test_pareto_knee_point(self):
        import numpy as np
        x = np.array([1.0, 2.0, 3.0])
        y = np.array([3.0, 2.0, 1.0])
        idx = pareto_knee_point(x, y, maximize_x=True, maximize_y=True)
        assert idx is not None
        assert 0 <= idx < 3

    def test_pareto_summary_report(self):
        points = [
            {"parameters": {"p": 1}, "k_eff": 1.0, "cost": 100},
            {"parameters": {"p": 2}, "k_eff": 1.1, "cost": 120},
        ]
        report = pareto_summary_report(points, "k_eff", "cost", maximize_x=True, maximize_y=False)
        assert report["n_pareto"] == 2
        assert "trade_off_summary" in report


class TestAuditLog:
    def test_append_run(self, tmp_path):
        log_path = tmp_path / "runs.json"
        append_run("design-study", args_summary={"reactor": "valar-10"}, passed=True, log_path=log_path)
        assert log_path.exists()
        data = json.loads(log_path.read_text())
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["workflow"] == "design-study"
        assert data[0]["passed"] is True


class TestSurrogate:
    def test_fit_surrogate_linear(self):
        import numpy as np
        X = np.array([[0, 0], [1, 0], [0, 1], [1, 1]])
        y = np.array([0.0, 1.0, 1.0, 2.0])
        sur = fit_surrogate(X, y, method="linear")
        pred = sur.predict(np.array([[0.5, 0.5]]))
        assert pred.shape == (1,)
        assert 0.5 <= pred[0] <= 2.0

    def test_surrogate_from_sweep_results(self):
        results = [
            {"parameters": {"x": 0.0}, "k_eff": 1.0},
            {"parameters": {"x": 0.5}, "k_eff": 1.05},
            {"parameters": {"x": 1.0}, "k_eff": 1.1},
        ]
        sur = surrogate_from_sweep_results(results, ["x"], output_metric="k_eff", method="linear")
        assert sur.n_samples == 3
        assert sur.predict([[0.25]])[0] >= 1.0


class TestScenarioDesign:
    def test_run_scenario_design_mock(self):
        reactor = Mock()
        reactor.solve.return_value = {"k_eff": 1.05, "power_thermal_mw": 10.0}
        scenarios = {"baseload": "regulatory_limits"}
        results = run_scenario_design(reactor, scenarios)
        assert "baseload" in results
        assert isinstance(results["baseload"], ScenarioResult)
        assert results["baseload"].passed in (True, False)

    def test_scenario_comparison_report(self):
        from smrforge.workflows.scenario_design import ScenarioResult
        results = {"s1": ScenarioResult("s1", True, {"k_eff": 1.0}, [], {}), "s2": ScenarioResult("s2", False, {}, ["v1"], {})}
        text = scenario_comparison_report(results)
        assert "s1" in text and "s2" in text
        assert "PASS" in text and "FAIL" in text


class TestConstraintBuilder:
    def test_constraint_set_from_design(self):
        design_point = {"k_eff": 1.05, "power_thermal_mw": 50.0}
        target_margins = {"min_k_eff": 0.02, "power_thermal_mw": 5.0}
        cs = constraint_set_from_design(design_point, target_margins)
        assert "min_k_eff" in cs.constraints or any("k_eff" in str(k) for k in cs.constraints)


class TestRequirementsParser:
    def test_parse_requirements_dict(self):
        spec = {
            "requirements": [
                {"name": "k_eff", "min": 0.98, "max": 1.05},
                {"name": "max_power_density", "max": 100, "unit": "W/cm³"},
            ]
        }
        cs = parse_requirements_to_constraint_set(spec)
        assert len(cs.constraints) >= 1

    def test_parse_requirements_yaml_file(self, tmp_path):
        yaml_file = tmp_path / "req.yaml"
        yaml_file.write_text("requirements:\n  - name: k_eff\n    limit: 1.0\n    type: min\n", encoding="utf-8")
        try:
            cs = parse_requirements_to_constraint_set(yaml_file)
            assert len(cs.constraints) >= 1
        except ImportError:
            pytest.skip("PyYAML required")


class TestMarginNarrative:
    def test_margin_narrative_passed(self):
        report = SafetyMarginReport(
            passed=True,
            margins=[MarginEntry("min_k_eff", 1.02, 1.0, "", 0.02, True)],
            metrics={"k_eff": 1.02},
            violations=[],
        )
        text = margin_narrative(report)
        assert "All limits met" in text
        assert "min_k_eff" in text or "1.02" in text

    def test_margin_narrative_failed(self):
        report = SafetyMarginReport(passed=False, margins=[], metrics={}, violations=["min_k_eff: 0.98 (limit 1.0)"])
        text = margin_narrative(report)
        assert "failed" in text.lower() or "Violations" in text
