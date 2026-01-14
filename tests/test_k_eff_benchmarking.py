"""
Tests for k-eff benchmarking functionality.

Tests the comparison of calculated k-eff values against benchmark reference values.
"""

import json
import tempfile
from pathlib import Path

import numpy as np
import pytest

from smrforge.core.reactor_core import Nuclide, NuclearDataCache
from smrforge.geometry import PrismaticCore
from smrforge.burnup import BurnupOptions
from tests.validation_benchmarks import ValidationBenchmarker
from tests.validation_benchmark_data import BenchmarkDatabase, BurnupBenchmark, BenchmarkValue, compare_with_benchmark


class TestKEffBenchmarking:
    """Tests for k-eff benchmarking functionality."""
    
    def test_compare_k_eff_with_benchmark(self):
        """Test comparing calculated k-eff with benchmark value."""
        benchmark_value = BenchmarkValue(
            value=1.0,
            uncertainty=0.001,
            unit="",
            source="IAEA Benchmark",
            notes="Example benchmark"
        )
        
        calculated_k_eff = 0.998
        
        comparison = compare_with_benchmark(calculated_k_eff, benchmark_value, tolerance=0.01)
        
        assert comparison["calculated"] == calculated_k_eff
        assert comparison["benchmark"] == benchmark_value.value
        assert "relative_error" in comparison
        assert "within_tolerance" in comparison
        assert comparison["relative_error"] < 0.01  # Within 1% tolerance
    
    def test_k_eff_within_uncertainty(self):
        """Test checking if k-eff is within benchmark uncertainty."""
        benchmark_value = BenchmarkValue(
            value=1.0,
            uncertainty=0.001,
            unit="",
            source="IAEA Benchmark"
        )
        
        # Value within 2-sigma uncertainty
        calculated_k_eff = 1.0005
        assert benchmark_value.within_uncertainty(calculated_k_eff, n_sigma=2.0)
        
        # Value outside 2-sigma uncertainty
        calculated_k_eff = 1.003
        assert not benchmark_value.within_uncertainty(calculated_k_eff, n_sigma=2.0)
    
    def test_load_burnup_benchmark_from_database(self):
        """Test loading burnup benchmark with k-eff values from database."""
        database = BenchmarkDatabase()
        
        # Create burnup benchmark with k-eff values
        benchmark_k_eff = [
            BenchmarkValue(value=1.0, uncertainty=0.001, source="IAEA"),
            BenchmarkValue(value=0.995, uncertainty=0.001, source="IAEA"),
        ]
        
        burnup_bm = BurnupBenchmark(
            test_case="test_burnup",
            problem_description="Test problem",
            initial_composition={"U235": 0.02, "U238": 0.98},
            time_steps=[0, 30],
            benchmark_compositions=[{"U235": 0.02}, {"U235": 0.0195}],
            benchmark_k_eff=benchmark_k_eff,
            reference_source="IAEA",
        )
        
        database.add_burnup_benchmark(burnup_bm)
        
        assert "test_burnup" in database.burnup_benchmarks
        benchmark = database.burnup_benchmarks["test_burnup"]
        assert len(benchmark.benchmark_k_eff) == 2
        assert benchmark.benchmark_k_eff[0].value == 1.0
        assert benchmark.benchmark_k_eff[1].value == 0.995
    
    def test_compare_multiple_k_eff_values(self):
        """Test comparing multiple k-eff values with benchmark."""
        benchmark_k_eff = [
            BenchmarkValue(value=1.0, uncertainty=0.001, source="IAEA"),
            BenchmarkValue(value=0.995, uncertainty=0.001, source="IAEA"),
            BenchmarkValue(value=0.990, uncertainty=0.001, source="IAEA"),
        ]
        
        calculated_k_eff = [0.998, 0.994, 0.989]
        
        comparisons = []
        for calc, bench in zip(calculated_k_eff, benchmark_k_eff):
            comparison = compare_with_benchmark(calc, bench, tolerance=0.01)
            comparisons.append(comparison)
        
        assert len(comparisons) == 3
        assert all(c["within_tolerance"] for c in comparisons)
        assert all(c["relative_error"] < 0.01 for c in comparisons)
    
    def test_load_benchmark_from_json_file(self):
        """Test loading benchmark database from JSON file."""
        # Create temporary benchmark file
        test_data = {
            "burnup_benchmarks": {
                "test_case_1": {
                    "test_case": "test_case_1",
                    "problem_description": "Test problem",
                    "initial_composition": {"U235": 0.02, "U238": 0.98},
                    "time_steps": [0, 30],
                    "benchmark_compositions": [{"U235": 0.02}, {"U235": 0.0195}],
                    "benchmark_k_eff": [
                        {"value": 1.0, "uncertainty": 0.001, "unit": "", "source": "IAEA"},
                        {"value": 0.995, "uncertainty": 0.001, "unit": "", "source": "IAEA"}
                    ],
                    "reference_source": "IAEA"
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_data, f)
            temp_file = Path(f.name)
        
        try:
            database = BenchmarkDatabase(temp_file)
            
            assert "test_case_1" in database.burnup_benchmarks
            benchmark = database.burnup_benchmarks["test_case_1"]
            assert len(benchmark.benchmark_k_eff) == 2
            assert benchmark.benchmark_k_eff[0].value == 1.0
        finally:
            temp_file.unlink()
