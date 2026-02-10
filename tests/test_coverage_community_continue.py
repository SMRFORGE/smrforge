"""
Continue coverage for Community tier modules.

Adds tests for: workflows/pareto_report, decay_heat cache path, fuel_cycle optimization.
"""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pytest

from smrforge.core.reactor_core import NuclearDataCache, Nuclide


class TestParetoReportCoverage:
    """Cover workflows/pareto_report edge cases."""

    def test_pareto_knee_point_empty_returns_none(self):
        from smrforge.workflows.pareto_report import pareto_knee_point

        assert pareto_knee_point(np.array([]), np.array([])) is None

    def test_pareto_knee_point_length_mismatch_returns_none(self):
        from smrforge.workflows.pareto_report import pareto_knee_point

        assert pareto_knee_point(np.array([1.0]), np.array([1.0, 2.0])) is None

    def test_pareto_knee_point_xmax_eq_xmin(self):
        from smrforge.workflows.pareto_report import pareto_knee_point

        x = np.array([5.0, 5.0, 5.0])
        y = np.array([1.0, 2.0, 3.0])
        idx = pareto_knee_point(x, y)
        assert idx in (0, 1, 2)

    def test_pareto_knee_point_maximize_x_false(self):
        from smrforge.workflows.pareto_report import pareto_knee_point

        x = np.array([3.0, 2.0, 1.0])  # Lower is better
        y = np.array([1.0, 2.0, 3.0])
        idx = pareto_knee_point(x, y, maximize_x=False, maximize_y=True)
        assert idx in (0, 1, 2)

    def test_pareto_summary_report_empty(self):
        from smrforge.workflows.pareto_report import pareto_summary_report

        out = pareto_summary_report([], "cost", "performance")
        assert out["n_pareto"] == 0
        assert out["knee_point"] is None
        assert "No Pareto points" in out["trade_off_summary"]

    def test_pareto_summary_report_with_knee_index(self):
        from smrforge.workflows.pareto_report import pareto_summary_report

        points = [
            {"cost": 10.0, "performance": 1.0},
            {"cost": 5.0, "performance": 2.0},
            {"cost": 2.0, "performance": 1.5},
        ]
        out = pareto_summary_report(points, "cost", "performance", knee_index=1)
        assert out["n_pareto"] == 3
        assert out["knee_point"] is not None
        assert out["knee_point"]["cost"] == 5.0

    def test_pareto_summary_report_get_v_from_parameters(self):
        """Cover get_v when metric in parameters dict."""
        from smrforge.workflows.pareto_report import pareto_summary_report

        points = [
            {"parameters": {"cost": 1.0, "perf": 2.0}},
            {"parameters": {"cost": 3.0, "perf": 4.0}},
        ]
        out = pareto_summary_report(points, "cost", "perf")
        assert out["n_pareto"] == 2
        assert "range" in out["trade_off_summary"]

    def test_pareto_summary_report_single_point_no_range(self):
        """Cover len(x_arr) < 2 branch - no range in trade summary."""
        from smrforge.workflows.pareto_report import pareto_summary_report

        points = [{"cost": 1.0, "performance": 2.0}]
        out = pareto_summary_report(points, "cost", "performance")
        assert out["n_pareto"] == 1
        assert "range" not in out["trade_off_summary"]

    def test_pareto_summary_report_nan_triggers_refetch(self):
        """Cover len(x_vals) != len branch when some values are nan."""
        from smrforge.workflows.pareto_report import pareto_summary_report

        points = [
            {"cost": 1.0, "perf": 2.0},
            {"cost": "bad", "perf": 4.0},  # triggers get_v -> nan
        ]
        out = pareto_summary_report(points, "cost", "perf")
        assert out["n_pareto"] == 2

    def test_pareto_summary_report_extremes_maximize_false(self):
        """Cover extremes with maximize_x=False, maximize_y=False."""
        from smrforge.workflows.pareto_report import pareto_summary_report

        points = [
            {"cost": 10.0, "perf": 1.0},
            {"cost": 2.0, "perf": 5.0},
        ]
        out = pareto_summary_report(
            points, "cost", "perf", maximize_x=False, maximize_y=False
        )
        assert "extremes" in out
        assert "best_x" in out["extremes"] and "best_y" in out["extremes"]


class TestDecayHeatCachePath:
    """Cover decay_heat _get_decay_data cache hit path."""

    def test_calculate_decay_heat_populates_cache_on_second_nuclide(self):
        from smrforge.decay_heat import DecayHeatCalculator

        u235 = Nuclide(Z=92, A=235)
        mock_cache = Mock(spec=NuclearDataCache)
        mock_cache._find_local_decay_file.return_value = None
        concentrations = {u235: 1e20}
        times = np.array([0.0, 3600.0])
        calc = DecayHeatCalculator(cache=mock_cache)
        result = calc.calculate_decay_heat(concentrations, times)
        assert u235 in calc._decay_data_cache
        assert np.any(result.total_decay_heat >= 0)


class TestFuelCycleOptimizationCoverage:
    """Cover fuel_cycle/optimization paths."""

    def test_fuel_cycle_optimizer_optimize_cycle_length(self):
        from smrforge.fuel_cycle.optimization import FuelCycleOptimizer

        def mock_burnup(cycle_length):
            keff = 1.0 + 0.001 * (cycle_length - 1000)
            burnup = cycle_length * 0.01
            return (keff, burnup)

        opt = FuelCycleOptimizer(
            power_thermal=1e9, max_cycle_length=1500.0, min_cycle_length=500.0
        )
        result = opt.optimize_cycle_length(mock_burnup, initial_guess=1000.0)
        assert "optimal_cycle_length" in result
        assert "k_eff" in result


class TestConvertersCommunityPath:
    """Cover io/converters Community-only path (when Pro not available)."""

    def test_serpent_export_writes_valid_file(self, tmp_path):
        from smrforge.io.converters import SerpentConverter

        mock_reactor = Mock()
        out = tmp_path / "reactor.serp"
        SerpentConverter.export_reactor(mock_reactor, out)
        assert out.exists()
        content = out.read_text()
        assert "Serpent" in content

    def test_openmc_export_writes_xml_files(self, tmp_path):
        from smrforge.geometry.core_geometry import PrismaticCore
        from smrforge.io.converters import OpenMCConverter

        core = PrismaticCore(name="Test")
        core.build_hexagonal_lattice(
            n_rings=1, pitch=40.0, block_height=50.0, n_axial=2
        )
        out = tmp_path / "openmc_out"
        OpenMCConverter.export_reactor(core, out)
        assert (out / "geometry.xml").exists()
        assert (out / "materials.xml").exists()

    def test_converters_pro_delegation_when_mocked(self, tmp_path):
        """Cover Pro delegation paths when _PRO_AVAILABLE is True (mock)."""
        from unittest.mock import MagicMock

        import smrforge.io.converters as conv

        mock_serpent = MagicMock()
        mock_openmc = MagicMock()
        with patch.object(conv, "_PRO_AVAILABLE", True), patch.object(
            conv, "_ProSerpentConverter", mock_serpent
        ), patch.object(conv, "_ProOpenMCConverter", mock_openmc):
            conv.SerpentConverter.export_reactor(Mock(), tmp_path / "a.serp")
            mock_serpent.export_reactor.assert_called_once()
            conv.SerpentConverter.import_reactor(tmp_path / "b.serp")
            mock_serpent.import_reactor.assert_called_once()
            conv.OpenMCConverter.export_reactor(Mock(), tmp_path / "openmc")
            mock_openmc.export_reactor.assert_called_once()
            conv.OpenMCConverter.import_reactor(tmp_path / "openmc")
            mock_openmc.import_reactor.assert_called_once()


class TestParameterSweepCoverage:
    """Cover workflows/parameter_sweep branches."""

    def test_sweep_config_from_file_yaml_import_error(self, tmp_path):
        """Cover YAML config when yaml import fails."""
        import builtins

        yaml_file = tmp_path / "sweep.yaml"
        yaml_file.write_text("parameters: {}\nanalysis_types: [keff]\n")
        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "yaml":
                raise ImportError("PyYAML required for YAML config: pip install pyyaml")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=fake_import):
            from smrforge.workflows.parameter_sweep import SweepConfig

            with pytest.raises(ImportError, match="PyYAML"):
                SweepConfig.from_file(yaml_file)

    def test_parameter_sweep_run_resume_all_done(self, tmp_path):
        """Cover run(resume=True) when intermediate has all combinations (no remaining cases)."""
        from smrforge.workflows.parameter_sweep import (
            ParameterSweep,
            SweepConfig,
            SweepResult,
        )

        out = tmp_path / "out"
        out.mkdir()
        config = SweepConfig(
            parameters={"x": (0.0, 1.0, 1.0)},
            analysis_types=["keff"],
            output_dir=out,
            reactor_template={"name": "test"},
            save_intermediate=True,
        )
        inter_file = out / "sweep_intermediate_1.json"
        inter_file.write_text(
            json.dumps(
                {
                    "results": [
                        {"parameters": {"x": 0.0}, "k_eff": 1.0},
                        {"parameters": {"x": 1.0}, "k_eff": 1.0},
                    ],
                    "failed": [],
                }
            )
        )
        sweep = ParameterSweep(config)
        result = sweep.run(resume=True)
        assert len(result.results) == 2
        assert result.summary_stats is not None

    def test_get_reactor_template_dict(self):
        """Cover _get_reactor_template when reactor_template is a dict."""
        from smrforge.workflows.parameter_sweep import ParameterSweep, SweepConfig

        config = SweepConfig(
            parameters={"x": [1.0]},
            analysis_types=["keff"],
            output_dir=Path("."),
            reactor_template={"name": "custom", "power_thermal": 1e9},
        )
        sweep = ParameterSweep(config)
        cfg = sweep._get_reactor_template()
        assert cfg == {"name": "custom", "power_thermal": 1e9}

    def test_get_reactor_template_other_returns_empty(self):
        """Cover _get_reactor_template when reactor_template is not None/str/Path/dict."""
        from smrforge.workflows.parameter_sweep import ParameterSweep, SweepConfig

        config = SweepConfig(
            parameters={"x": [1.0]},
            analysis_types=["keff"],
            output_dir=Path("."),
            reactor_template=[],  # not a valid type; falls through to else
        )
        sweep = ParameterSweep(config)
        cfg = sweep._get_reactor_template()
        assert cfg == {}

    def test_sweep_config_from_file_json_and_param_list(self, tmp_path):
        """Cover from_file with JSON and param as list (not 3-tuple)."""
        cfg_file = tmp_path / "sweep.json"
        cfg_file.write_text(
            json.dumps(
                {
                    "parameters": {"x": [1.0, 2.0, 3.0, 4.0]},
                    "analysis_types": ["keff"],
                    "output_dir": str(tmp_path / "out"),
                }
            )
        )
        from smrforge.workflows.parameter_sweep import SweepConfig

        config = SweepConfig.from_file(cfg_file)
        assert config.parameters["x"] == [1.0, 2.0, 3.0, 4.0]

    @patch("smrforge.convenience.create_reactor", create=True)
    def test_parameter_sweep_run_env_max_workers(self, mock_create_reactor, tmp_path):
        """Cover run() when SMRFORGE_MAX_BATCH_WORKERS is set."""
        from smrforge.workflows.parameter_sweep import ParameterSweep, SweepConfig

        mock_reactor = Mock()
        mock_reactor.solve_keff.return_value = 1.05
        mock_create_reactor.return_value = mock_reactor
        out = tmp_path / "out"
        out.mkdir()
        config = SweepConfig(
            parameters={"x": (0.0, 1.0, 1.0)},
            analysis_types=["keff"],
            output_dir=out,
            reactor_template={"name": "test"},
            parallel=True,
            save_intermediate=False,
        )
        sweep = ParameterSweep(config)
        with patch.dict("os.environ", {"SMRFORGE_MAX_BATCH_WORKERS": "2"}, clear=False):
            result = sweep.run(resume=False, show_progress=False)
        assert len(result.results) == 2
        assert result.summary_stats is not None

    @patch("smrforge.convenience.create_reactor", create=True)
    def test_parameter_sweep_run_sequential_single_case(
        self, mock_create_reactor, tmp_path
    ):
        """Cover run() sequential path (n_cases=1 or parallel=False)."""
        from smrforge.workflows.parameter_sweep import ParameterSweep, SweepConfig

        mock_reactor = Mock()
        mock_reactor.solve_keff.return_value = 1.05
        mock_create_reactor.return_value = mock_reactor
        out = tmp_path / "out"
        out.mkdir()
        config = SweepConfig(
            parameters={"x": [1.0]},
            analysis_types=["keff"],
            output_dir=out,
            reactor_template={"name": "test"},
            parallel=False,
            save_intermediate=False,
        )
        sweep = ParameterSweep(config)
        result = sweep.run(resume=False, show_progress=False)
        assert len(result.results) == 1
        assert result.summary_stats is not None

    @patch("smrforge.convenience.create_reactor", create=True)
    def test_parameter_sweep_run_with_progress(self, mock_create_reactor, tmp_path):
        """Cover run() with show_progress=True (Rich progress bar path when available)."""
        from smrforge.workflows.parameter_sweep import ParameterSweep, SweepConfig

        mock_reactor = Mock()
        mock_reactor.solve_keff.return_value = 1.05
        mock_create_reactor.return_value = mock_reactor
        out = tmp_path / "out"
        out.mkdir()
        config = SweepConfig(
            parameters={"x": [1.0, 2.0]},
            analysis_types=["keff"],
            output_dir=out,
            reactor_template={"name": "test"},
            parallel=False,
            save_intermediate=False,
        )
        sweep = ParameterSweep(config)
        result = sweep.run(resume=False, show_progress=True)
        assert len(result.results) == 2
        assert result.summary_stats is not None
