"""Tests for execute_and_document_benchmarks."""

from pathlib import Path

import pytest

from smrforge.validation.benchmark_runner import (
    execute_and_document_benchmarks,
    run_validation_suite,
)


class TestExecuteAndDocumentBenchmarks:
    """Tests for execute_and_document_benchmarks."""

    def test_execute_and_document(self, tmp_path):
        """Test execute and document produces files."""
        results, out_dir = execute_and_document_benchmarks(
            output_dir=tmp_path,
        )
        assert out_dir == tmp_path
        assert (tmp_path / "benchmark_results.json").exists()
        assert (tmp_path / "BENCHMARK_SUMMARY.md").exists()
        assert len(results) > 0

    def test_run_validation_suite(self):
        """Test run_validation_suite returns results."""
        results = run_validation_suite()
        assert len(results) > 0
        for r in results:
            assert hasattr(r, "name")
            assert hasattr(r, "passed")
