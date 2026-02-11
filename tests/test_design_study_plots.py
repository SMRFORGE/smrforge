"""
Tests for design-study visualizations (sensitivity, Sobol, Pareto+knee, margins, scenario, atlas).
"""

from unittest.mock import Mock

import pytest

from smrforge.validation.safety_report import MarginEntry, SafetyMarginReport
from smrforge.workflows.scenario_design import ScenarioResult
from smrforge.workflows.sensitivity import SensitivityRanking


def _has_plotly():
    try:
        import plotly.graph_objects

        return True
    except ImportError:
        return False


def _has_matplotlib():
    try:
        import matplotlib.pyplot

        return True
    except ImportError:
        return False


class TestPlotSensitivityRanking:
    def test_plot_sensitivity_ranking_plotly(self):
        pytest.importorskip("plotly")
        from smrforge.visualization.design_study_plots import plot_sensitivity_ranking

        rankings = [
            SensitivityRanking("a", 0.8, 1, "oat"),
            SensitivityRanking("b", 0.3, 2, "oat"),
        ]
        fig = plot_sensitivity_ranking(rankings, backend="plotly")
        assert fig is not None
        assert hasattr(fig, "to_dict") or hasattr(fig, "write_html")

    def test_plot_sensitivity_ranking_matplotlib(self):
        pytest.importorskip("matplotlib")
        from smrforge.visualization.design_study_plots import plot_sensitivity_ranking

        rankings = [SensitivityRanking("x", 0.5, 1, "oat")]
        fig, ax = plot_sensitivity_ranking(rankings, backend="matplotlib")
        assert fig is not None
        assert ax is not None


class TestPlotSobolWorkflow:
    def test_plot_sobol_workflow_plotly(self):
        pytest.importorskip("plotly")
        from smrforge.visualization.design_study_plots import plot_sobol_workflow

        sobol_dict = {
            "Y0": {"S1": [0.1, 0.5], "ST": [0.2, 0.6], "param_names": ["a", "b"]}
        }
        fig = plot_sobol_workflow(sobol_dict, output_key="Y0", backend="plotly")
        assert fig is not None


class TestPlotSafetyMargins:
    def test_plot_safety_margins_plotly(self):
        pytest.importorskip("plotly")
        from smrforge.visualization.design_study_plots import plot_safety_margins

        report = SafetyMarginReport(
            passed=True,
            margins=[MarginEntry("min_k_eff", 1.02, 1.0, "", 0.02, True)],
            metrics={"k_eff": 1.02},
            violations=[],
        )
        fig = plot_safety_margins(report, backend="plotly")
        assert fig is not None


class TestPlotScenarioComparison:
    def test_plot_scenario_comparison_plotly(self):
        pytest.importorskip("plotly")
        from smrforge.visualization.design_study_plots import plot_scenario_comparison

        results = {
            "s1": ScenarioResult(
                "s1", True, {"k_eff": 1.0, "power_thermal_mw": 50}, [], {}
            ),
            "s2": ScenarioResult(
                "s2", False, {"k_eff": 0.98, "power_thermal_mw": 50}, ["v1"], {}
            ),
        }
        fig = plot_scenario_comparison(results, backend="plotly")
        assert fig is not None


class TestPlotParetoWithKnee:
    def test_plot_pareto_with_knee_plotly(self):
        pytest.importorskip("plotly")
        import numpy as np

        from smrforge.visualization.design_study_plots import plot_pareto_with_knee

        x = np.array([1.0, 2.0, 3.0])
        y = np.array([3.0, 2.0, 1.0])
        mask = np.array([True, True, False])
        fig = plot_pareto_with_knee(
            x, y, mask, knee_index=0, metric_x="m1", metric_y="m2", backend="plotly"
        )
        assert fig is not None


class TestPlotAtlasDesigns:
    def test_plot_atlas_designs_plotly(self):
        pytest.importorskip("plotly")
        from smrforge.visualization.design_study_plots import plot_atlas_designs

        entries = [
            {
                "design_id": "a",
                "power_mw": 50,
                "metrics_summary": {"k_eff": 1.02},
                "passed": True,
            },
            {
                "design_id": "b",
                "power_mw": 100,
                "metrics_summary": {"k_eff": 0.99},
                "passed": False,
            },
        ]
        fig = plot_atlas_designs(
            entries, x_metric="power_mw", y_metric="k_eff", backend="plotly"
        )
        assert fig is not None
