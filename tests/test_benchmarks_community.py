"""Tests for smrforge.benchmarks Community benchmark suite."""

import json
from pathlib import Path

import pytest

from smrforge.benchmarks import CommunityBenchmarkRunner
from smrforge.benchmarks.runner import _load_benchmarks, _run_case


class TestCommunityBenchmarkRunner:
    """Test CommunityBenchmarkRunner."""

    def test_list_cases(self):
        """Test list_cases returns case IDs."""
        runner = CommunityBenchmarkRunner()
        cases = runner.list_cases()
        assert isinstance(cases, list)
        assert len(cases) >= 1
        assert all(isinstance(c, str) for c in cases)

    def test_run_all_returns_dict(self):
        """Test run_all returns dict of results."""
        runner = CommunityBenchmarkRunner()
        results = runner.run_all()
        assert isinstance(results, dict)
        for cid, tup in results.items():
            assert isinstance(cid, str)
            assert isinstance(tup, tuple)
            assert len(tup) == 3
            passed, value, err = tup
            assert isinstance(passed, bool)
            assert isinstance(value, (int, float))

    def test_generate_report_without_output(self):
        """Test generate_report returns string when no output_path."""
        runner = CommunityBenchmarkRunner()
        results = runner.run_all()
        report = runner.generate_report(results=results)
        assert isinstance(report, str)
        assert "SMRForge Community Benchmark Report" in report
        assert "| Case |" in report or "Case" in report

    def test_generate_report_with_output(self, tmp_path):
        """Test generate_report writes to file."""
        runner = CommunityBenchmarkRunner()
        results = runner.run_all()
        out = tmp_path / "bench_report.md"
        runner.generate_report(results=results, output_path=out)
        assert out.exists()
        assert "SMRForge Community Benchmark Report" in out.read_text()


class TestCommunityBenchmarkRunnerCustomPath:
    """Test runner with custom benchmarks path."""

    def test_custom_benchmarks_path(self, tmp_path):
        """Test runner with custom benchmarks file."""
        bench_file = tmp_path / "custom_benchmarks.json"
        bench_file.write_text(
            json.dumps(
                {
                    "neutronics_benchmarks": {
                        "quick_keff_default": {
                            "test_case": "quick_keff_default",
                            "call": "quick_keff",
                            "kwargs": {"power_mw": 10.0, "enrichment": 0.195},
                            "expected_key": "k_eff",
                            "reference_value": 0.9,
                            "tolerance_rel": 0.15,
                        }
                    }
                }
            )
        )
        runner = CommunityBenchmarkRunner(benchmarks_path=bench_file)
        cases = runner.list_cases()
        assert "quick_keff_default" in cases

    def test_benchmarks_file_not_found(self):
        """Test FileNotFoundError when benchmarks file missing."""
        runner = CommunityBenchmarkRunner(
            benchmarks_path=Path("/nonexistent/bench.json")
        )
        with pytest.raises(FileNotFoundError, match="not found"):
            runner.run_all()


class TestLoadBenchmarks:
    """Test _load_benchmarks helper."""

    def test_load_benchmarks_default(self):
        """Test loading default benchmarks."""
        data = _load_benchmarks()
        assert "neutronics_benchmarks" in data
        assert isinstance(data["neutronics_benchmarks"], dict)
