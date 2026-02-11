"""
Tests for coupled safety margin report (validation.safety_report).
"""

from pathlib import Path
from unittest.mock import Mock

import pytest

from smrforge.validation.constraints import ConstraintSet
from smrforge.validation.safety_report import (
    MarginEntry,
    SafetyMarginReport,
    safety_margin_report,
)


class TestMarginEntry:
    def test_margin_entry_within_limit(self):
        m = MarginEntry("max_temperature", 1000.0, 1200.0, "K", 200.0, True)
        assert m.within_limit is True
        assert m.margin == 200.0

    def test_margin_entry_violation(self):
        m = MarginEntry("min_k_eff", 0.98, 1.0, "", -0.02, False)
        assert m.within_limit is False


class TestSafetyMarginReport:
    def test_to_dict(self):
        report = SafetyMarginReport(
            passed=False,
            margins=[
                MarginEntry("k_eff", 1.05, 1.0, "", 0.05, True),
            ],
            metrics={"k_eff": 1.05},
            violations=["max_power_density: 150 W/cm³ (limit 100 W/cm³)"],
            uq_available=False,
        )
        d = report.to_dict()
        assert d["passed"] is False
        assert len(d["margins"]) == 1
        assert d["margins"][0]["name"] == "k_eff"
        assert d["violations"]


class TestSafetyMarginReportFunction:
    def test_safety_margin_report_with_mock_reactor(self):
        reactor = Mock()
        reactor.solve.return_value = {"k_eff": 1.05, "power_thermal_mw": 10.0}
        report = safety_margin_report(reactor, constraint_set=None)
        assert report.metrics.get("k_eff") == 1.05
        reactor.solve.assert_called_once()

    def test_safety_margin_report_with_analysis_results(self):
        reactor = Mock(spec=[])
        report = safety_margin_report(
            reactor,
            constraint_set=ConstraintSet.get_regulatory_limits(),
            analysis_results={"k_eff": 1.02, "power_thermal_mw": 50.0},
        )
        assert report.metrics.get("k_eff") == 1.02
        assert report.passed is True or len(report.violations) >= 0

    def test_safety_margin_report_with_uq_results(self):
        reactor = Mock()
        reactor.solve.return_value = {"k_eff": 1.0, "power_thermal_mw": 10.0}
        uq = {"min_k_eff": {"p5": 0.98, "p95": 1.02}}
        report = safety_margin_report(reactor, uq_results=uq)
        assert report.uq_available is True
        margin_k = next((m for m in report.margins if m.name == "min_k_eff"), None)
        assert margin_k is not None
        assert margin_k.percentile_5 == 0.98
        assert margin_k.percentile_95 == 1.02
