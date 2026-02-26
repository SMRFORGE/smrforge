"""
Tests for parameter sweep and sensitivity analysis workflow.

Tests cover:
- SweepConfig parameter parsing and combination generation
- ParameterSweep single case execution
- Sequential and parallel sweep execution
- Result aggregation and statistics
- Result saving (JSON/Parquet)
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pandas as pd
import pytest

from smrforge.workflows.parameter_sweep import ParameterSweep, SweepConfig, SweepResult


class TestSweepConfig:
    """Tests for SweepConfig class."""

    def test_get_parameter_values_range(self):
        """Test getting parameter values from range tuple."""
        config = SweepConfig(
            parameters={"enrichment": (0.10, 0.25, 0.05)}, analysis_types=["keff"]
        )

        values = config.get_parameter_values("enrichment")
        expected = np.arange(0.10, 0.25 + 0.05 / 2, 0.05)
        np.testing.assert_array_almost_equal(values, expected)

    def test_get_parameter_values_list(self):
        """Test getting parameter values from list."""
        config = SweepConfig(
            parameters={"power": [50, 75, 100]}, analysis_types=["keff"]
        )

        values = config.get_parameter_values("power")
        expected = np.array([50, 75, 100])
        np.testing.assert_array_equal(values, expected)

    def test_get_parameter_values_invalid(self):
        """Test invalid parameter specification raises error (at construction)."""
        from pydantic import ValidationError

        with pytest.raises((ValueError, ValidationError), match="Invalid parameter"):
            SweepConfig(
                parameters={"invalid": "not a tuple or list"}, analysis_types=["keff"]
            )

    def test_get_all_combinations_single_param(self):
        """Test combination generation with single parameter."""
        config = SweepConfig(
            parameters={"enrichment": [0.10, 0.20, 0.30]}, analysis_types=["keff"]
        )

        combinations = config.get_all_combinations()

        assert len(combinations) == 3
        assert combinations[0] == {"enrichment": 0.10}
        assert combinations[1] == {"enrichment": 0.20}
        assert combinations[2] == {"enrichment": 0.30}

    def test_get_all_combinations_multiple_params(self):
        """Test combination generation with multiple parameters."""
        config = SweepConfig(
            parameters={"enrichment": [0.10, 0.20], "power": [50, 100]},
            analysis_types=["keff"],
        )

        combinations = config.get_all_combinations()

        assert len(combinations) == 4
        assert {"enrichment": 0.10, "power": 50} in combinations
        assert {"enrichment": 0.10, "power": 100} in combinations
        assert {"enrichment": 0.20, "power": 50} in combinations
        assert {"enrichment": 0.20, "power": 100} in combinations

    def test_get_all_combinations_range(self):
        """Test combination generation with range parameters."""
        config = SweepConfig(
            parameters={"enrichment": (0.10, 0.20, 0.10), "power": (50, 100, 50)},
            analysis_types=["keff"],
        )

        combinations = config.get_all_combinations()

        assert len(combinations) == 4  # 2 enrichment values × 2 power values
        assert all("enrichment" in c and "power" in c for c in combinations)

    def test_from_file_json(self, tmp_path):
        """Test loading SweepConfig from JSON file."""
        config_file = tmp_path / "sweep_config.json"
        config_file.write_text(
            json.dumps(
                {
                    "parameters": {"enrichment": [0.10, 0.20], "power": [50, 100]},
                    "analysis_types": ["keff"],
                }
            ),
            encoding="utf-8",
        )
        config = SweepConfig.from_file(config_file)
        assert config.parameters["enrichment"] == [0.10, 0.20]
        assert config.parameters["power"] == [50, 100]
        assert config.analysis_types == ["keff"]

    def test_from_file_range_tuple(self, tmp_path):
        """Test from_file normalizes [start, end, step] to range tuple."""
        config_file = tmp_path / "sweep_config.json"
        config_file.write_text(
            json.dumps(
                {
                    "parameters": {"x": [0.0, 1.0, 0.25]},
                    "analysis_types": ["keff"],
                }
            ),
            encoding="utf-8",
        )
        config = SweepConfig.from_file(config_file)
        assert config.parameters["x"] == (0.0, 1.0, 0.25)

    def test_from_file_not_found(self):
        """Test from_file raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError, match="not found"):
            SweepConfig.from_file(Path("/nonexistent/sweep.json"))


class TestSweepResult:
    """Tests for SweepResult class."""

    def test_to_dataframe_empty(self):
        """Test DataFrame conversion with empty results."""
        config = SweepConfig(parameters={"x": [1]}, analysis_types=["keff"])
        result = SweepResult(config=config, results=[])

        df = result.to_dataframe()
        assert df.empty
        assert isinstance(df, pd.DataFrame)

    def test_to_dataframe_with_results(self):
        """Test DataFrame conversion with results."""
        config = SweepConfig(parameters={"x": [1, 2]}, analysis_types=["keff"])
        result = SweepResult(
            config=config,
            results=[
                {"parameters": {"x": 1}, "k_eff": 1.0},
                {"parameters": {"x": 2}, "k_eff": 1.1},
            ],
        )

        df = result.to_dataframe()
        assert len(df) == 2
        assert "k_eff" in df.columns

    def test_to_polars_when_available(self):
        """Test to_polars returns Polars DataFrame when polars is installed."""
        import polars as pl

        config = SweepConfig(parameters={"x": [1, 2]}, analysis_types=["keff"])
        result = SweepResult(
            config=config,
            results=[
                {"parameters": {"x": 1}, "k_eff": 1.0},
                {"parameters": {"x": 2}, "k_eff": 1.1},
            ],
        )
        pdf = result.to_polars()
        assert pdf is not None
        assert isinstance(pdf, pl.DataFrame)
        assert len(pdf) == 2

    def test_to_dataframe_engine_polars(self):
        """Test to_dataframe(engine='polars') returns Polars DataFrame."""
        import polars as pl

        config = SweepConfig(parameters={"x": [1]}, analysis_types=["keff"])
        result = SweepResult(
            config=config, results=[{"parameters": {"x": 1}, "k_eff": 1.0}]
        )
        df = result.to_dataframe(engine="polars")
        assert isinstance(df, pl.DataFrame)
        assert len(df) == 1

    def test_save_json(self, tmp_path):
        """Test saving results to JSON."""
        config = SweepConfig(parameters={"x": [1]}, analysis_types=["keff"])
        result = SweepResult(
            config=config,
            results=[{"parameters": {"x": 1}, "k_eff": 1.0}],
            summary_stats={"k_eff": {"mean": 1.0}},
        )

        output_file = tmp_path / "results.json"
        result.save(output_file)

        assert output_file.exists()
        with open(output_file) as f:
            data = json.load(f)
        assert "results" in data
        assert "summary_stats" in data

    def test_save_parquet(self, tmp_path):
        """Test saving results to Parquet."""
        try:
            pd.read_parquet  # Check if parquet support is available
        except AttributeError:
            pytest.skip("Parquet support not available (pyarrow/fastparquet)")

        config = SweepConfig(parameters={"x": [1, 2]}, analysis_types=["keff"])
        result = SweepResult(
            config=config,
            results=[
                {"parameters": {"x": 1}, "k_eff": 1.0},
                {"parameters": {"x": 2}, "k_eff": 1.1},
            ],
        )

        output_file = tmp_path / "results.parquet"
        try:
            result.save(output_file)
            assert output_file.exists()
            # Verify it can be read back
            df = pd.read_parquet(output_file)
            assert len(df) == 2
        except ImportError:
            pytest.skip("Parquet support not available (pyarrow/fastparquet)")


class TestParameterSweep:
    """Tests for ParameterSweep class."""

    def test_init(self, tmp_path):
        """Test ParameterSweep initialization."""
        config = SweepConfig(
            parameters={"enrichment": [0.10, 0.20]},
            analysis_types=["keff"],
            output_dir=tmp_path / "sweep_output",
        )

        sweep = ParameterSweep(config)
        assert sweep.config == config
        assert (tmp_path / "sweep_output").exists()

    def test_get_reactor_template_from_dict(self):
        """Test getting reactor template from dictionary."""
        config = SweepConfig(
            parameters={"enrichment": [0.10]},
            analysis_types=["keff"],
            reactor_template={"preset": "valar-10", "power_mw": 10.0},
        )

        sweep = ParameterSweep(config)
        template = sweep._get_reactor_template()

        assert template == {"preset": "valar-10", "power_mw": 10.0}

    def test_get_reactor_template_from_file(self, tmp_path):
        """Test getting reactor template from JSON file."""
        template_file = tmp_path / "template.json"
        template_data = {"preset": "valar-10", "power_mw": 10.0}
        with open(template_file, "w") as f:
            json.dump(template_data, f)

        config = SweepConfig(
            parameters={"enrichment": [0.10]},
            analysis_types=["keff"],
            reactor_template=str(template_file),
        )

        sweep = ParameterSweep(config)
        template = sweep._get_reactor_template()

        assert template == template_data

    def test_get_reactor_template_preset_name(self):
        """Test getting reactor template from preset name string."""
        config = SweepConfig(
            parameters={"enrichment": [0.10]},
            analysis_types=["keff"],
            reactor_template="valar-10",
        )

        sweep = ParameterSweep(config)
        template = sweep._get_reactor_template()

        assert template == {"name": "valar-10"}

    def test_get_reactor_template_nonexistent_path(self):
        """Test getting reactor template when path does not exist (falls back to preset)."""
        config = SweepConfig(
            parameters={"enrichment": [0.10]},
            analysis_types=["keff"],
            reactor_template="/nonexistent/path/to/template.json",
        )

        sweep = ParameterSweep(config)
        template = sweep._get_reactor_template()

        assert template == {"name": "/nonexistent/path/to/template.json"}

    def test_get_reactor_template_none(self):
        """Test getting reactor template when None."""
        config = SweepConfig(
            parameters={"enrichment": [0.10]},
            analysis_types=["keff"],
            reactor_template=None,
        )

        sweep = ParameterSweep(config)
        template = sweep._get_reactor_template()

        assert template == {}

    @patch("smrforge.convenience.create_reactor", create=True)
    def test_run_single_case_keff(self, mock_create_reactor):
        """Test running single case with k-eff analysis."""
        mock_reactor = Mock()
        mock_reactor.solve_keff.return_value = 1.05
        mock_create_reactor.return_value = mock_reactor

        config = SweepConfig(
            parameters={"enrichment": [0.10]},
            analysis_types=["keff"],
            reactor_template={"preset": "valar-10"},
        )

        sweep = ParameterSweep(config)
        result = sweep._run_single_case({"enrichment": 0.15})

        assert "parameters" in result
        assert result["parameters"]["enrichment"] == 0.15
        assert result["k_eff"] == 1.05
        # Note: _run_single_case doesn't add 'success' key, it's added by the run() method
        mock_create_reactor.assert_called_once()

    @patch("smrforge.convenience.create_reactor", create=True)
    def test_run_single_case_error(self, mock_create_reactor):
        """Test single case execution with error."""
        mock_create_reactor.side_effect = ValueError("Test error")

        config = SweepConfig(parameters={"enrichment": [0.10]}, analysis_types=["keff"])

        sweep = ParameterSweep(config)
        result = sweep._run_single_case({"enrichment": 0.15})

        assert "error" in result
        assert result["success"] is False
        assert "Test error" in result["error"]

    @patch("smrforge.convenience.create_reactor", create=True)
    def test_run_single_case_neutronics(self, mock_create_reactor):
        """Test running single case with neutronics analysis."""
        mock_reactor = Mock()
        mock_reactor.solve.return_value = {"k_eff": 1.05, "flux": np.array([1.0, 2.0])}
        mock_create_reactor.return_value = mock_reactor

        config = SweepConfig(
            parameters={"enrichment": [0.10]},
            analysis_types=["neutronics"],
            reactor_template={"preset": "valar-10"},
        )

        sweep = ParameterSweep(config)
        result = sweep._run_single_case({"enrichment": 0.15})

        assert "k_eff" in result
        assert result["k_eff"] == 1.05
        mock_reactor.solve.assert_called_once()

    @patch("smrforge.convenience.create_reactor", create=True)
    def test_run_single_case_burnup(self, mock_create_reactor):
        """Test running single case with burnup analysis (placeholder path)."""
        mock_reactor = Mock()
        mock_create_reactor.return_value = mock_reactor

        config = SweepConfig(
            parameters={"enrichment": [0.10]},
            analysis_types=["burnup"],
            reactor_template={"preset": "valar-10"},
        )

        sweep = ParameterSweep(config)
        result = sweep._run_single_case({"enrichment": 0.15})

        assert "burnup" in result
        # Mock reactor cannot run real burnup; expect None or error dict
        assert result["burnup"] is None or isinstance(result["burnup"], dict)

    @patch("smrforge.convenience.create_reactor", create=True)
    def test_run_sequential(self, mock_create_reactor, tmp_path):
        """Test sequential sweep execution."""
        mock_reactor = Mock()
        mock_reactor.solve_keff.return_value = 1.05
        mock_create_reactor.return_value = mock_reactor

        config = SweepConfig(
            parameters={"enrichment": [0.10, 0.20]},
            analysis_types=["keff"],
            output_dir=tmp_path / "sweep_output",
            parallel=False,
        )

        sweep = ParameterSweep(config)
        result = sweep.run()

        assert len(result.results) == 2
        assert len(result.failed_cases) == 0
        assert all("k_eff" in r for r in result.results)
        assert mock_create_reactor.call_count == 2

    @patch("smrforge.convenience.create_reactor", create=True)
    def test_run_parallel(self, mock_create_reactor, tmp_path):
        """Test parallel sweep execution."""
        mock_reactor = Mock()
        mock_reactor.solve_keff.return_value = 1.05
        mock_create_reactor.return_value = mock_reactor

        config = SweepConfig(
            parameters={"enrichment": [0.10, 0.20, 0.30]},
            analysis_types=["keff"],
            output_dir=tmp_path / "sweep_output",
            parallel=True,
            max_workers=2,
        )

        sweep = ParameterSweep(config)
        result = sweep.run()

        assert len(result.results) == 3
        assert len(result.failed_cases) == 0
        assert mock_create_reactor.call_count == 3

    @patch("smrforge.convenience.create_reactor", create=True)
    def test_run_parallel_with_save_intermediate(self, mock_create_reactor, tmp_path):
        """Test parallel sweep with save_intermediate (10+ cases to trigger)."""
        mock_reactor = Mock()
        mock_reactor.solve_keff.return_value = 1.05
        mock_create_reactor.return_value = mock_reactor

        config = SweepConfig(
            parameters={"enrichment": [0.10 + i * 0.01 for i in range(12)]},
            analysis_types=["keff"],
            output_dir=tmp_path / "sweep_output",
            parallel=True,
            max_workers=2,
            save_intermediate=True,
        )

        sweep = ParameterSweep(config)
        result = sweep.run()

        assert len(result.results) == 12
        # Check intermediate file was saved (at i=10)
        intermediate = tmp_path / "sweep_output" / "sweep_intermediate_10.json"
        assert intermediate.exists()

    @patch("smrforge.convenience.create_reactor", create=True)
    def test_run_with_failures(self, mock_create_reactor, tmp_path):
        """Test sweep execution with some failures."""
        mock_reactor = Mock()
        mock_reactor.solve_keff.side_effect = [1.05, ValueError("Error"), 1.06]
        mock_create_reactor.return_value = mock_reactor

        config = SweepConfig(
            parameters={"enrichment": [0.10, 0.20, 0.30]},
            analysis_types=["keff"],
            output_dir=tmp_path / "sweep_output",
            parallel=False,
        )

        sweep = ParameterSweep(config)
        result = sweep.run()

        assert len(result.results) == 2  # 2 successes
        assert len(result.failed_cases) == 1  # 1 failure

    def test_calculate_summary_stats_empty_results(self):
        """Test summary statistics with no results returns empty dict."""
        config = SweepConfig(parameters={"x": [1]}, analysis_types=["keff"])
        sweep = ParameterSweep(config)
        stats = sweep._calculate_summary_stats([])
        assert stats == {}

    def test_calculate_summary_stats(self, tmp_path):
        """Test summary statistics calculation."""
        config = SweepConfig(
            parameters={"enrichment": [0.10, 0.20, 0.30]}, analysis_types=["keff"]
        )

        results = [
            {"parameters": {"enrichment": 0.10}, "k_eff": 1.00},
            {"parameters": {"enrichment": 0.20}, "k_eff": 1.05},
            {"parameters": {"enrichment": 0.30}, "k_eff": 1.10},
        ]

        sweep = ParameterSweep(config)
        stats = sweep._calculate_summary_stats(results)

        assert "k_eff" in stats
        assert stats["k_eff"]["mean"] == pytest.approx(1.05)
        assert stats["k_eff"]["min"] == 1.00
        assert stats["k_eff"]["max"] == 1.10
        assert stats["k_eff"]["std"] > 0
        assert "median" in stats["k_eff"]
        assert stats["k_eff"]["median"] == pytest.approx(1.05)

    def test_calculate_summary_stats_with_correlations(self):
        """Test summary stats including parameter-result correlations."""
        config = SweepConfig(
            parameters={"enrichment": [0.10, 0.20, 0.30]}, analysis_types=["keff"]
        )

        results = [
            {"parameters": {"enrichment": 0.10}, "enrichment": 0.10, "k_eff": 1.00},
            {"parameters": {"enrichment": 0.20}, "enrichment": 0.20, "k_eff": 1.05},
            {"parameters": {"enrichment": 0.30}, "enrichment": 0.30, "k_eff": 1.10},
        ]

        sweep = ParameterSweep(config)
        stats = sweep._calculate_summary_stats(results)

        assert "k_eff" in stats
        assert "correlations" in stats
        assert "enrichment" in stats
        assert stats["k_eff"]["mean"] == pytest.approx(1.05)
        assert stats["k_eff"]["median"] == pytest.approx(1.05)
        assert stats["k_eff"]["std"] >= 0
        assert stats["k_eff"]["min"] == 1.0
        assert stats["k_eff"]["max"] == 1.1

    def test_save_intermediate(self, tmp_path):
        """Test intermediate result saving."""
        config = SweepConfig(
            parameters={"enrichment": [0.10]},
            analysis_types=["keff"],
            output_dir=tmp_path / "sweep_output",
        )

        sweep = ParameterSweep(config)
        results = [{"k_eff": 1.05}]
        failed = []

        sweep._save_intermediate(results, failed, 10)

        intermediate_file = tmp_path / "sweep_output" / "sweep_intermediate_10.json"
        assert intermediate_file.exists()

        with open(intermediate_file) as f:
            data = json.load(f)
        assert data["case_num"] == 10
        assert "results" in data


class TestParameterSweepIntegration:
    """Integration tests for parameter sweep."""

    @patch("smrforge.convenience.create_reactor", create=True)
    def test_full_sweep_workflow(self, mock_create_reactor, tmp_path):
        """Test complete parameter sweep workflow."""

        # Mock reactor that returns different k-eff based on enrichment
        def create_mock_reactor(**kwargs):
            mock_reactor = Mock()
            enrichment = kwargs.get("enrichment", 0.10)
            mock_reactor.solve_keff.return_value = 0.95 + enrichment * 0.5
            return mock_reactor

        mock_create_reactor.side_effect = create_mock_reactor

        config = SweepConfig(
            parameters={"enrichment": [0.10, 0.15, 0.20], "power_mw": [50, 100]},
            analysis_types=["keff"],
            reactor_template={"preset": "valar-10"},
            output_dir=tmp_path / "sweep_output",
            parallel=False,
        )

        sweep = ParameterSweep(config)
        result = sweep.run()

        # Should have 3 × 2 = 6 combinations
        assert len(result.results) == 6
        assert len(result.summary_stats) > 0
        assert "k_eff" in result.summary_stats

        # Save results
        output_file = tmp_path / "final_results.json"
        result.save(output_file)
        assert output_file.exists()
