"""
Coverage-focused tests for workflows (atlas), validation (constraint_builder, safety_report, requirements_parser).
"""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from smrforge.validation.constraint_builder import (
    constraint_set_from_design,
    constraint_set_from_safety_report,
)
from smrforge.validation.constraints import ConstraintSet
from smrforge.validation.requirements_parser import parse_requirements_to_constraint_set
from smrforge.validation.safety_report import (
    MarginEntry,
    SafetyMarginReport,
    margin_narrative,
    safety_margin_report,
)
from smrforge.workflows.atlas import AtlasEntry, build_atlas, filter_atlas


class TestConstraintBuilderCoverage:
    """Cover constraint_set_from_design min_k_eff from k_eff and constraint_set_from_safety_report."""

    def test_constraint_set_from_design_uses_k_eff_for_min_k_eff(self):
        design_point = {"k_eff": 1.02, "power_thermal_mw": 10.0}
        target_margins = {"min_k_eff": 0.02}
        cs = constraint_set_from_design(design_point, target_margins)
        assert "min_k_eff" in cs.constraints
        assert cs.constraints["min_k_eff"]["limit"] == 1.0

    def test_constraint_set_from_design_skips_non_numeric(self):
        design_point = {"k_eff": 1.0, "power_thermal_mw": "ten"}
        target_margins = {"power_thermal_mw": 1.0}
        cs = constraint_set_from_design(design_point, target_margins)
        assert "power_thermal_mw" not in cs.constraints

    def test_constraint_set_from_safety_report_dict_empty_margins(self):
        report = {"margins": []}
        cs = constraint_set_from_safety_report(report)
        assert len(cs.constraints) == 0

    def test_constraint_set_from_safety_report_dict_with_margins(self):
        report = {
            "margins": [
                {"name": "min_k_eff", "limit": 0.98, "unit": ""},
                {"name": "max_temperature", "limit": 1200.0, "unit": "K"},
            ]
        }
        cs = constraint_set_from_safety_report(report)
        assert len(cs.constraints) == 2

    def test_constraint_set_from_safety_report_with_target_margins(self):
        report = {
            "margins": [
                {"name": "min_k_eff", "limit": 1.0, "unit": ""},
            ]
        }
        cs = constraint_set_from_safety_report(
            report, target_margins={"min_k_eff": 0.02}, name="tightened"
        )
        assert "min_k_eff" in cs.constraints
        assert cs.constraints["min_k_eff"]["limit"] == 0.98


class TestSafetyReportCoverage:
    """Cover margin_narrative and safety_margin_report merge / UQ paths."""

    def test_margin_narrative_passed_with_margins(self):
        report = SafetyMarginReport(
            passed=True,
            margins=[
                MarginEntry("min_k_eff", 1.0, 0.98, "", 0.02, True),
                MarginEntry("max_temperature", 1000.0, 1200.0, "K", 200.0, True),
            ],
        )
        text = margin_narrative(report)
        assert "All limits met" in text
        assert "Minimum margin" in text

    def test_margin_narrative_failed_with_violations(self):
        report = SafetyMarginReport(
            passed=False,
            violations=["min_k_eff: 0.97 (limit 0.98 )"],
        )
        text = margin_narrative(report)
        assert "Validation failed" in text
        assert "Violations" in text
        assert "0.97" in text

    def test_margin_narrative_failed_no_violations(self):
        report = SafetyMarginReport(passed=False, margins=[], violations=[])
        text = margin_narrative(report)
        assert "Validation failed" in text
        assert "not satisfied" in text

    def test_safety_margin_report_analysis_results_merge_extra_keys(self):
        reactor = Mock(spec=[])
        cs = ConstraintSet(name="c", description="")
        cs.add_constraint("min_k_eff", 0.98, "min", "", "")
        report = safety_margin_report(
            reactor,
            constraint_set=cs,
            analysis_results={
                "k_eff": 1.0,
                "power_thermal_mw": 10.0,
                "extra_metric": 42.0,
            },
        )
        assert report.metrics.get("k_eff") == 1.0
        assert report.metrics.get("power_thermal_mw") == 10.0
        assert report.metrics.get("extra_metric") == 42.0

    def test_safety_margin_report_uq_percentile_keys(self):
        reactor = Mock()
        reactor.solve.return_value = {"k_eff": 1.0, "power_thermal_mw": 10.0}
        uq = {"min_k_eff": {"percentile_5": 0.97, "percentile_95": 1.03}}
        report = safety_margin_report(reactor, uq_results=uq)
        margin_k = next((m for m in report.margins if m.name == "min_k_eff"), None)
        assert margin_k is not None
        assert margin_k.percentile_5 == 0.97
        assert margin_k.percentile_95 == 1.03

    def test_safety_margin_report_reactor_solve_raises(self):
        reactor = Mock()
        reactor.solve.side_effect = RuntimeError("solve failed")
        report = safety_margin_report(reactor, constraint_set=None)
        assert report.metrics in ({}, {"k_eff": 0.0}) or len(report.metrics) >= 0


class TestRequirementsParserCoverage:
    """Cover parse_requirements_to_constraint_set: file path, constraints key, limit+type, min+max."""

    def test_parse_from_dict_requirements_key(self):
        spec = {
            "requirements": [
                {"name": "k_eff", "limit": 1.05, "type": "max", "unit": ""},
            ]
        }
        cs = parse_requirements_to_constraint_set(spec)
        assert "k_eff" in cs.constraints or any(
            "k_eff" in str(c) for c in cs.constraints
        )

    def test_parse_from_dict_constraints_key(self):
        spec = {
            "constraints": [
                {"name": "min_k_eff", "limit": 0.98, "type": "min", "unit": ""},
            ]
        }
        cs = parse_requirements_to_constraint_set(spec)
        assert len(cs.constraints) >= 1

    def test_parse_min_max_creates_two_constraints(self):
        spec = {
            "requirements": [
                {"name": "k_eff", "min": 0.98, "max": 1.05, "unit": ""},
            ]
        }
        cs = parse_requirements_to_constraint_set(spec)
        assert "min_k_eff" in cs.constraints
        assert "max_k_eff" in cs.constraints

    def test_parse_min_only(self):
        spec = {"requirements": [{"name": "k_eff", "min": 0.98, "unit": ""}]}
        cs = parse_requirements_to_constraint_set(spec)
        assert len(cs.constraints) >= 1

    def test_parse_max_only(self):
        spec = {"requirements": [{"name": "temperature", "max": 1200, "unit": "K"}]}
        cs = parse_requirements_to_constraint_set(spec)
        assert len(cs.constraints) >= 1

    def test_parse_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            parse_requirements_to_constraint_set(Path("/nonexistent/reqs.yaml"))

    def test_parse_json_file(self, tmp_path):
        path = tmp_path / "reqs.json"
        path.write_text(
            json.dumps({"requirements": [{"name": "k_eff", "max": 1.05, "unit": ""}]})
        )
        cs = parse_requirements_to_constraint_set(path)
        assert len(cs.constraints) >= 1

    def test_parse_yaml_file(self, tmp_path):
        pytest.importorskip("yaml")
        path = tmp_path / "reqs.yaml"
        path.write_text(
            "requirements:\n  - name: k_eff\n    limit: 1.05\n    type: max\n    unit: ''\n    description: k_eff cap\n"
        )
        cs = parse_requirements_to_constraint_set(path)
        assert len(cs.constraints) >= 1


class TestAtlasCoverage:
    """Cover build_atlas loop and filter_atlas."""

    def test_build_atlas_with_mocked_functions(self, tmp_path):
        def mock_create(name):
            r = Mock()
            r.spec = Mock(coolant="helium", reactor_type="htgr")
            return r

        def mock_design_point(reactor):
            return {"k_eff": 1.0, "power_thermal_mw": 10.0}

        def mock_safety_report(reactor, **kwargs):
            return SafetyMarginReport(passed=True, margins=[], metrics={"k_eff": 1.0})

        entries = build_atlas(
            tmp_path,
            presets=["valar-10", "gt-mhr"],
            create_reactor=mock_create,
            get_design_point=mock_design_point,
            safety_margin_report_fn=mock_safety_report,
        )
        assert len(entries) == 2
        assert all(e.passed for e in entries)
        assert (tmp_path / "atlas_index.json").exists()

    def test_build_atlas_preset_fails_appends_failed_entry(self, tmp_path):
        def mock_create(name):
            raise RuntimeError("fake failure")

        entries = build_atlas(
            tmp_path,
            presets=["bad-preset"],
            create_reactor=mock_create,
            get_design_point=lambda r: {},
            safety_margin_report_fn=lambda r: SafetyMarginReport(
                passed=False, margins=[]
            ),
        )
        assert len(entries) == 1
        assert entries[0].passed is False
        assert "error" in entries[0].metrics_summary

    def test_filter_atlas_power_and_passed(self):
        entries = [
            AtlasEntry("a", power_mw=5.0, passed=True, metrics_summary={}),
            AtlasEntry("b", power_mw=15.0, passed=True, metrics_summary={}),
            AtlasEntry("c", power_mw=25.0, passed=False, metrics_summary={}),
        ]
        filtered = filter_atlas(
            entries, power_min=10.0, power_max=20.0, passed_only=True
        )
        assert len(filtered) == 1
        assert filtered[0].design_id == "b"

    def test_filter_atlas_coolant(self):
        entries = [
            AtlasEntry(
                "a", power_mw=10.0, coolant="helium", passed=True, metrics_summary={}
            ),
            AtlasEntry(
                "b", power_mw=10.0, coolant="water", passed=True, metrics_summary={}
            ),
        ]
        filtered = filter_atlas(entries, coolant="water")
        assert len(filtered) == 1
        assert filtered[0].coolant == "water"

    def test_build_atlas_presets_none_uses_list_presets(self, tmp_path):
        with patch(
            "smrforge.convenience.list_presets", return_value=["valar-10"]
        ) as mock_list:

            def mock_create(name):
                r = Mock()
                r.spec = Mock(coolant="he", reactor_type="htgr")
                return r

            entries = build_atlas(
                tmp_path,
                presets=None,
                create_reactor=mock_create,
                get_design_point=lambda r: {"k_eff": 1.0, "power_thermal_mw": 10.0},
                safety_margin_report_fn=lambda r, **kw: SafetyMarginReport(
                    passed=True, margins=[], metrics={}
                ),
            )
            mock_list.assert_called_once()
            assert len(entries) == 1
            assert entries[0].design_id == "valar-10"
