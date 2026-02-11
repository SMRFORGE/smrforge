"""
Integration tests for standards parser with validation framework.

Tests the integration between StandardsParser and ValidationBenchmarker
for standards-based validation.
"""

import json
import tempfile
from pathlib import Path

import numpy as np
import pytest

from smrforge.core.reactor_core import NuclearDataCache, Nuclide
from smrforge.validation.standards_parser import StandardsParser, StandardType
from tests.validation_benchmark_data import BenchmarkDatabase
from tests.validation_benchmarks import ValidationBenchmarker


class TestStandardsIntegration:
    """Tests for standards parser integration with validation framework."""

    def test_load_standards_into_benchmarker(self):
        """Test loading standards data into ValidationBenchmarker."""
        cache = NuclearDataCache()
        database = BenchmarkDatabase()

        # Create ANSI/ANS-5.1 benchmark data
        test_data = {
            "standard": "ANSI/ANS-5.1",
            "benchmarks": [
                {
                    "test_case": "test_u235_shutdown",
                    "nuclides": {"U235": 1e20},
                    "initial_power": 100.0,
                    "operating_time": 86400.0,
                    "time_points": [3600, 86400],
                    "decay_heat_values": [
                        {"time": 3600, "value": 0.07, "unit": "MW"},
                        {"time": 86400, "value": 0.04, "unit": "MW"},
                    ],
                }
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_data, f)
            temp_file = Path(f.name)

        try:
            # Parse standards data
            parser = StandardsParser()
            benchmarks = parser.parse_ansi_ans_5_1(temp_file)

            # Load into database
            loaded_count = parser.load_into_database(benchmarks, database)
            assert loaded_count == 1

            # Create ValidationBenchmarker with database
            benchmarker = ValidationBenchmarker(cache, benchmark_database=database)

            # Verify database is accessible
            assert benchmarker.benchmark_database is not None
            assert (
                "test_u235_shutdown"
                in benchmarker.benchmark_database.decay_heat_benchmarks
            )

        finally:
            temp_file.unlink()

    def test_validation_with_standards_benchmark(self):
        """Test validation using standards benchmark values."""
        cache = NuclearDataCache()
        database = BenchmarkDatabase()

        # Add a benchmark to database
        from tests.validation_benchmark_data import BenchmarkValue, DecayHeatBenchmark

        benchmark_values = [
            BenchmarkValue(
                value=0.07,
                uncertainty=0.01,
                unit="MW",
                source="ANSI/ANS-5.1",
            ),
            BenchmarkValue(
                value=0.04,
                uncertainty=0.01,
                unit="MW",
                source="ANSI/ANS-5.1",
            ),
        ]

        decay_heat_bm = DecayHeatBenchmark(
            test_case="test_u235",
            nuclides={"U235": 1e20},
            initial_power=100.0,
            shutdown_time=0.0,
            time_points=[3600, 86400],
            benchmark_values=benchmark_values,
            standard="ANSI/ANS-5.1",
        )

        database.add_decay_heat_benchmark(decay_heat_bm)

        # Create ValidationBenchmarker with database
        benchmarker = ValidationBenchmarker(cache, benchmark_database=database)

        # Verify benchmark is accessible
        assert "test_u235" in benchmarker.benchmark_database.decay_heat_benchmarks
        benchmark = benchmarker.benchmark_database.decay_heat_benchmarks["test_u235"]
        assert benchmark.standard == "ANSI/ANS-5.1"
        assert len(benchmark.benchmark_values) == 2

    def test_standards_parser_available(self):
        """Test that standards parser is available in ValidationBenchmarker."""
        cache = NuclearDataCache()
        benchmarker = ValidationBenchmarker(cache)

        # Standards parser should be available if module is installed
        # (it may be None if standards_parser module is not available)
        assert hasattr(benchmarker, "standards_parser")

        if benchmarker.standards_parser is not None:
            assert isinstance(benchmarker.standards_parser, StandardsParser)
