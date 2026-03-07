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
            reactor_template=None,
        )
        config.reactor_template = []  # invalid type; bypasses Pydantic, exercises else branch
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

    @patch("smrforge.convenience.create_reactor", create=True)
    def test_parameter_sweep_burnup_analysis(self, mock_create_reactor, tmp_path):
        """Test parameter sweep with burnup analysis type (no longer returns None)."""
        import numpy as np

        from smrforge.geometry import PrismaticCore
        from smrforge.neutronics.solver import MultiGroupDiffusion
        from smrforge.validation.models import (
            CrossSectionData,
            SolverOptions,
        )
        from smrforge.workflows.parameter_sweep import ParameterSweep, SweepConfig

        geom = PrismaticCore(name="T")
        geom.core_height = 100.0
        geom.core_diameter = 50.0
        geom.generate_mesh(n_radial=3, n_axial=2)

        xs = CrossSectionData(
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
        solver = MultiGroupDiffusion(geom, xs, SolverOptions(tolerance=1e-5))
        solver.k_eff = 1.0

        mock_reactor = Mock()
        mock_reactor._get_solver.return_value = solver

        mock_create_reactor.return_value = mock_reactor
        out = tmp_path / "out"
        out.mkdir()
        config = SweepConfig(
            parameters={"x": [1.0]},
            analysis_types=["burnup"],
            output_dir=out,
            reactor_template={"name": "test"},
            parallel=False,
            save_intermediate=False,
        )
        sweep = ParameterSweep(config)
        result = sweep.run(resume=False, show_progress=False)
        assert len(result.results) == 1
        r = result.results[0]
        assert "burnup" in r
        assert r["burnup"] is not None
        assert "final_burnup_mwd_kg" in r["burnup"]
        assert "n_nuclides" in r["burnup"]


class TestOpenMCRunCoverage:
    """Cover io/openmc_run: run_openmc, parse_statepoint, run_and_parse."""

    def test_run_openmc_raises_when_geometry_missing(self, tmp_path):
        """Cover FileNotFoundError when geometry.xml not found."""
        from smrforge.io.openmc_run import run_openmc

        with pytest.raises(FileNotFoundError, match="geometry.xml not found"):
            run_openmc(tmp_path)

    @patch("subprocess.run")
    def test_run_openmc_success_with_mock(self, mock_run, tmp_path):
        """Cover successful run_openmc path."""
        from smrforge.io.openmc_run import run_openmc

        (tmp_path / "geometry.xml").write_text("<geometry/>")
        mock_run.return_value = Mock(returncode=0, stdout="ok", stderr="")
        result = run_openmc(tmp_path)
        assert result.returncode == 0
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_run_openmc_with_env_override(self, mock_run, tmp_path):
        """Cover run_openmc env parameter (line 46)."""
        from smrforge.io.openmc_run import run_openmc

        (tmp_path / "geometry.xml").write_text("<geometry/>")
        mock_run.return_value = Mock(returncode=0, stdout="ok", stderr="")
        run_openmc(tmp_path, env={"OPENMC_CROSS_SECTIONS": "/path/to/xs"})
        call_kw = mock_run.call_args[1]
        assert "env" in call_kw
        assert call_kw["env"].get("OPENMC_CROSS_SECTIONS") == "/path/to/xs"

    @patch("subprocess.run")
    def test_run_openmc_nonzero_returncode_logs_warning(self, mock_run, tmp_path):
        """Cover returncode != 0 warning path."""
        from smrforge.io.openmc_run import run_openmc

        (tmp_path / "geometry.xml").write_text("<geometry/>")
        mock_run.return_value = Mock(returncode=1, stdout="", stderr="error msg")
        result = run_openmc(tmp_path)
        assert result.returncode == 1

    def test_parse_statepoint_file_not_found(self):
        """Cover FileNotFoundError when statepoint does not exist."""
        from smrforge.io.openmc_run import parse_statepoint

        with pytest.raises(FileNotFoundError, match="Statepoint not found"):
            parse_statepoint("/nonexistent/statepoint.10.h5")

    def test_parse_statepoint_h5py_import_error(self, tmp_path):
        """Cover ImportError when h5py not available."""
        from smrforge.io.openmc_run import parse_statepoint

        sp = tmp_path / "statepoint.10.h5"
        sp.write_bytes(b"fake")
        with patch.dict("sys.modules", {"h5py": None}):
            with pytest.raises(ImportError, match="h5py required"):
                parse_statepoint(sp)

    def test_parse_statepoint_extracts_k_eff_and_tallies(self, tmp_path):
        """Cover parse_statepoint with k_combined and tallies."""
        pytest.importorskip("h5py")
        import h5py

        from smrforge.io.openmc_run import parse_statepoint

        sp = tmp_path / "statepoint.10.h5"
        with h5py.File(sp, "w") as f:
            f.create_dataset("k_combined", data=[1.05, 0.002])
            f.create_dataset("k_generation", data=[[1.0]] * 20)
            tallies = f.create_group("tallies")
            t1 = tallies.create_group("1")
            t1.create_dataset("mean", data=1.0)
            t1.create_dataset("std_dev", data=0.1)

        parsed = parse_statepoint(sp)
        assert parsed["k_eff"] == 1.05
        assert parsed["k_eff_std"] == 0.002
        assert parsed["batches"] == 20
        assert "tallies" in parsed
        assert 1 in parsed["tallies"]
        assert parsed["tallies"][1]["mean"] == 1.0
        assert parsed["tallies"][1]["std_dev"] == 0.1

    def test_parse_statepoint_k_combined_scalar(self, tmp_path):
        """Cover k_combined as scalar (len < 2)."""
        pytest.importorskip("h5py")
        import h5py

        from smrforge.io.openmc_run import parse_statepoint

        sp = tmp_path / "statepoint.10.h5"
        with h5py.File(sp, "w") as f:
            f.create_dataset("k_combined", data=1.04)

        parsed = parse_statepoint(sp)
        assert parsed["k_eff"] == 1.04
        assert "k_eff_std" not in parsed

    def test_parse_statepoint_tally_scalar_mean_std_dev(self, tmp_path):
        """Cover tally mean/std_dev scalar path (else float() when not __iter__)."""
        pytest.importorskip("h5py")
        import h5py

        from smrforge.io.openmc_run import parse_statepoint

        sp = tmp_path / "statepoint.10.h5"
        with h5py.File(sp, "w") as f:
            tallies = f.create_group("tallies")
            t1 = tallies.create_group("1")
            t1.create_dataset("mean", data=2.5)
            t1.create_dataset("std_dev", data=0.05)

        orig = h5py.Dataset.__getitem__

        def scalar_on_read(self, key):
            r = orig(self, key)
            if key == () or (isinstance(key, tuple) and len(key) == 0):
                return float(r)
            return r

        with patch.object(h5py.Dataset, "__getitem__", scalar_on_read):
            parsed = parse_statepoint(sp)
        assert "tallies" in parsed
        assert parsed["tallies"][1]["mean"] == 2.5
        assert parsed["tallies"][1]["std_dev"] == 0.05

    def test_parse_statepoint_tally_keyerror_typeerror_suppressed(self, tmp_path):
        """Cover except (KeyError, TypeError): pass (lines 127-128)."""
        pytest.importorskip("h5py")
        import h5py

        from smrforge.io.openmc_run import parse_statepoint

        sp = tmp_path / "statepoint.10.h5"
        with h5py.File(sp, "w") as f:
            tallies = f.create_group("tallies")
            t1 = tallies.create_group("1")
            t1.create_dataset("mean", data=1.0)
            t1.create_dataset("std_dev", data=0.1)
            t2 = tallies.create_group("2")
            t2.create_dataset("mean", data=1.0)
            # Missing std_dev -> KeyError when accessing t["std_dev"]
        parsed = parse_statepoint(sp)
        assert "tallies" in parsed
        assert 1 in parsed["tallies"]
        assert 2 not in parsed["tallies"]

    @patch("subprocess.run")
    def test_run_and_parse_success(self, mock_run, tmp_path):
        """Cover run_and_parse when OpenMC succeeds and statepoint exists."""
        pytest.importorskip("h5py")
        import h5py

        from smrforge.io.openmc_run import run_and_parse

        (tmp_path / "geometry.xml").write_text("<geometry/>")
        mock_run.return_value = Mock(returncode=0, stdout="ok", stderr="")
        sp = tmp_path / "statepoint.10.h5"
        with h5py.File(sp, "w") as f:
            f.create_dataset("k_combined", data=[1.05, 0.001])

        out = run_and_parse(tmp_path)
        assert out["returncode"] == 0
        assert out["k_eff"] == 1.05
        assert "k_eff_std" in out

    @patch("subprocess.run")
    def test_run_and_parse_no_statepoint(self, mock_run, tmp_path):
        """Cover run_and_parse when no statepoint files (still returns returncode)."""
        from smrforge.io.openmc_run import run_and_parse

        (tmp_path / "geometry.xml").write_text("<geometry/>")
        mock_run.return_value = Mock(returncode=0, stdout="ok", stderr="")
        out = run_and_parse(tmp_path)
        assert out["returncode"] == 0
        assert "k_eff" not in out

    @patch("subprocess.run")
    def test_run_and_parse_statepoint_parse_raises_logs_warning(
        self, mock_run, tmp_path
    ):
        """Cover run_and_parse when parse_statepoint raises (lines 167-168)."""
        from smrforge.io.openmc_run import run_and_parse

        (tmp_path / "geometry.xml").write_text("<geometry/>")
        mock_run.return_value = Mock(returncode=0, stdout="ok", stderr="")
        corrupt = tmp_path / "statepoint.10.h5"
        corrupt.write_bytes(b"not valid hdf5")
        out = run_and_parse(tmp_path)
        assert out["returncode"] == 0
        assert "k_eff" not in out


class TestOpenMCExportExtended:
    """Extended coverage for io/openmc_export: PebbleBedCore, fallbacks, errors."""

    def test_export_pebble_bed_core_writes_xml(self, tmp_path):
        """Cover PebbleBedCore branch in _collect_materials and _write_geometry_xml_pebble."""
        from smrforge.geometry.core_geometry import (
            MaterialRegion,
            Pebble,
            PebbleBedCore,
            Point3D,
        )
        from smrforge.io.openmc_export import export_reactor_to_openmc

        core = PebbleBedCore(name="TestPebble")
        core.core_diameter = 300.0
        core.core_height = 1100.0
        mr = MaterialRegion(
            material_id="pebble_fuel",
            composition={"U235": 0.0005, "U238": 0.002, "C0": 0.08},
            temperature=1100.0,
            density=1.74,
        )
        core.pebbles = [
            Pebble(id=0, position=Point3D(0, 0, 50), material_region=mr),
        ]
        out = tmp_path / "pebble_out"
        export_reactor_to_openmc(core, out)
        assert (out / "geometry.xml").exists()
        assert (out / "materials.xml").exists()
        assert "PebbleBedCore" in (out / "geometry.xml").read_text()

    def test_export_reactor_with_core_attribute(self, tmp_path):
        """Cover _get_core_from_reactor via reactor.core."""
        from smrforge.geometry.core_geometry import PrismaticCore
        from smrforge.io.openmc_export import export_reactor_to_openmc

        core = PrismaticCore(name="Inner")
        core.build_hexagonal_lattice(
            n_rings=1, pitch=40.0, block_height=50.0, n_axial=2
        )
        reactor = Mock(core=core)
        out = tmp_path / "out"
        export_reactor_to_openmc(reactor, out)
        assert (out / "geometry.xml").exists()

    def test_export_reactor_with_get_core_method(self, tmp_path):
        """Cover _get_core_from_reactor via _get_core()."""
        from smrforge.geometry.core_geometry import PrismaticCore
        from smrforge.io.openmc_export import export_reactor_to_openmc

        core = PrismaticCore(name="Inner")
        core.build_hexagonal_lattice(
            n_rings=1, pitch=40.0, block_height=50.0, n_axial=2
        )
        reactor = Mock(spec=["_get_core"])
        reactor._get_core = Mock(return_value=core)
        out = tmp_path / "out"
        export_reactor_to_openmc(reactor, out)
        assert (out / "geometry.xml").exists()

    def test_export_reactor_with_core_attr(self, tmp_path):
        """Cover _get_core_from_reactor via _core."""
        from smrforge.geometry.core_geometry import PrismaticCore
        from smrforge.io.openmc_export import export_reactor_to_openmc

        core = PrismaticCore(name="Inner")
        core.build_hexagonal_lattice(
            n_rings=1, pitch=40.0, block_height=50.0, n_axial=2
        )
        reactor = Mock(spec=["_core"])
        reactor._core = core
        out = tmp_path / "out"
        export_reactor_to_openmc(reactor, out)
        assert (out / "geometry.xml").exists()

    def test_export_empty_core_uses_default_materials(self, tmp_path):
        """Cover empty materials fallback (default fuel and graphite)."""
        from smrforge.geometry.core_geometry import PrismaticCore
        from smrforge.io.openmc_export import export_reactor_to_openmc

        core = PrismaticCore(name="Empty")
        core.build_hexagonal_lattice(
            n_rings=1, pitch=40.0, block_height=50.0, n_axial=2
        )
        core.blocks = []
        out = tmp_path / "out"
        export_reactor_to_openmc(core, out)
        mat_xml = (out / "materials.xml").read_text()
        assert "fuel" in mat_xml or "1" in mat_xml
        assert "graphite" in mat_xml or "2" in mat_xml

    def test_export_unsupported_core_raises(self, tmp_path):
        """Cover TypeError for unsupported core type."""
        from smrforge.io.openmc_export import export_reactor_to_openmc

        reactor = Mock()
        reactor.core = Mock()  # not PrismaticCore or PebbleBedCore
        with pytest.raises(TypeError, match="Unsupported core type"):
            export_reactor_to_openmc(reactor, tmp_path / "out")

    def test_export_prismatic_with_moderator_material(self, tmp_path):
        """Cover moderator_material branch in _collect_materials (lines 66-67)."""
        from smrforge.geometry.core_geometry import (
            MaterialRegion,
            Point3D,
            PrismaticCore,
        )
        from smrforge.io.openmc_export import export_reactor_to_openmc

        core = PrismaticCore(name="Test")
        core.build_hexagonal_lattice(
            n_rings=1, pitch=40.0, block_height=50.0, n_axial=2
        )
        mod = MaterialRegion(
            material_id="graphite_mod",
            composition={"C0": 0.08},
            temperature=700.0,
            density=1.7,
        )
        core.blocks[0].moderator_material = mod
        out = tmp_path / "out"
        export_reactor_to_openmc(core, out)
        mat_xml = (out / "materials.xml").read_text()
        assert "graphite_mod" in mat_xml or "2" in mat_xml

    def test_export_material_region_empty_composition_fallback(self, tmp_path):
        """Cover _write_materials_xml when composition is empty (U235/U238/C0 fallback)."""
        from smrforge.geometry.core_geometry import (
            FuelChannel,
            GraphiteBlock,
            MaterialRegion,
            Point3D,
            PrismaticCore,
        )
        from smrforge.io.openmc_export import export_reactor_to_openmc

        mr = MaterialRegion(
            material_id="fuel",
            composition={},
            temperature=900.0,
            density=1.74,
        )
        ch = FuelChannel(
            id=0, position=Point3D(0, 0, 0), radius=2.0, height=50.0, material_region=mr
        )
        block = GraphiteBlock(
            id=0, position=Point3D(0, 0, 0), flat_to_flat=20.0, height=50.0
        )
        block.fuel_channels = [ch]
        core = PrismaticCore(name="Test")
        core.blocks = [block]
        core.core_diameter = 100.0
        core.core_height = 200.0
        core.reflector_thickness = 30.0
        out = tmp_path / "out"
        export_reactor_to_openmc(core, out)
        assert "U235" in (out / "materials.xml").read_text()


class TestOpenMCImportExtended:
    """Extended coverage for io/openmc_import."""

    def test_import_geometry_file_not_found(self):
        """Cover FileNotFoundError when geometry file does not exist."""
        from smrforge.io.openmc_import import import_reactor_from_openmc

        with pytest.raises(FileNotFoundError, match="Geometry file not found"):
            import_reactor_from_openmc(Path("/nonexistent/geometry.xml"))

    def test_import_geometry_parse_fails_raises_value_error(self, tmp_path):
        """Cover ValueError when core is None (parse failed)."""
        from smrforge.io.openmc_import import import_reactor_from_openmc

        geom = tmp_path / "geometry.xml"
        geom.write_text("<geometry/>")
        with patch(
            "smrforge.geometry.advanced_import.AdvancedGeometryImporter._from_openmc_xml_csg",
            return_value=None,
        ):
            with pytest.raises(ValueError, match="Could not parse"):
                import_reactor_from_openmc(geom)

    def test_import_with_materials_file(self, tmp_path):
        """Cover materials_file path and _parse_materials_xml."""
        from smrforge.geometry.core_geometry import PrismaticCore
        from smrforge.io.openmc_export import export_reactor_to_openmc
        from smrforge.io.openmc_import import import_reactor_from_openmc

        core = PrismaticCore(name="Test")
        core.build_hexagonal_lattice(
            n_rings=1, pitch=40.0, block_height=50.0, n_axial=2
        )
        out = tmp_path / "export"
        export_reactor_to_openmc(core, out)
        result = import_reactor_from_openmc(
            out / "geometry.xml", materials_file=out / "materials.xml"
        )
        assert "core" in result
        assert "materials" in result
        assert result["format"] == "openmc"

    def test_import_materials_file_parse_exception(self, tmp_path):
        """Cover Exception path in _parse_materials_xml (lines 81-82)."""
        from smrforge.geometry.core_geometry import PrismaticCore
        from smrforge.io.openmc_export import export_reactor_to_openmc
        from smrforge.io.openmc_import import import_reactor_from_openmc

        core = PrismaticCore(name="Test")
        core.build_hexagonal_lattice(
            n_rings=1, pitch=40.0, block_height=50.0, n_axial=2
        )
        out = tmp_path / "export"
        export_reactor_to_openmc(core, out)
        bad_mats = tmp_path / "bad_materials.xml"
        bad_mats.write_text("<materials><material id='1'")  # malformed XML
        result = import_reactor_from_openmc(
            out / "geometry.xml", materials_file=bad_mats
        )
        assert "core" in result
        assert "materials" not in result or result.get("materials") == {}
