"""
Integration tests for k-eff benchmarking with ValidationBenchmarker.

Tests the complete workflow of benchmarking k-eff calculations against
reference values from BenchmarkDatabase.
"""

import json
import tempfile
from pathlib import Path

import numpy as np
import pytest

from smrforge.core.reactor_core import Nuclide, NuclearDataCache
from tests.validation_benchmarks import ValidationBenchmarker
from tests.validation_benchmark_data import BenchmarkDatabase, BurnupBenchmark, BenchmarkValue


class TestKEffBenchmarkingIntegration:
    """Integration tests for k-eff benchmarking."""
    
    def test_benchmark_k_eff_with_validation_benchmarker(self):
        """Test benchmarking k-eff using ValidationBenchmarker."""
        cache = NuclearDataCache()
        database = BenchmarkDatabase()
        
        # Create benchmark with k-eff values
        benchmark_k_eff = [
            BenchmarkValue(value=1.0, uncertainty=0.001, source="IAEA"),
            BenchmarkValue(value=0.995, uncertainty=0.001, source="IAEA"),
            BenchmarkValue(value=0.990, uncertainty=0.001, source="IAEA"),
        ]
        
        burnup_bm = BurnupBenchmark(
            test_case="test_burnup_k_eff",
            problem_description="Test burnup problem",
            initial_composition={"U235": 0.02, "U238": 0.98},
            time_steps=[0, 30, 60],
            benchmark_compositions=[{"U235": 0.02}, {"U235": 0.0195}, {"U235": 0.019}],
            benchmark_k_eff=benchmark_k_eff,
            reference_source="IAEA",
        )
        
        database.add_burnup_benchmark(burnup_bm)
        
        # Create ValidationBenchmarker with database
        benchmarker = ValidationBenchmarker(cache, benchmark_database=database)
        
        # Simulated calculated k-eff values (in real usage, these would come from burnup solver)
        calculated_k_eff = [0.998, 0.994, 0.989]
        
        # Benchmark the calculated values
        result = benchmarker.benchmark_k_eff(calculated_k_eff, burnup_bm, tolerance=0.01)
        
        assert result.passed
        assert result.metrics["total_comparisons"] == 3
        assert result.metrics["within_tolerance_count"] == 3
        assert result.comparison_data is not None
        assert result.comparison_data["benchmark_test_case"] == "test_burnup_k_eff"
        assert len(result.comparison_data["comparisons"]) == 3
    
    def test_benchmark_k_eff_with_database_lookup(self):
        """Test benchmarking k-eff by looking up benchmark from database."""
        cache = NuclearDataCache()
        database = BenchmarkDatabase()
        
        # Add benchmark to database
        benchmark_k_eff = [
            BenchmarkValue(value=1.0, uncertainty=0.001, source="IAEA"),
            BenchmarkValue(value=0.995, uncertainty=0.001, source="IAEA"),
        ]
        
        burnup_bm = BurnupBenchmark(
            test_case="test_lookup",
            problem_description="Test lookup",
            initial_composition={"U235": 0.02},
            time_steps=[0, 30],
            benchmark_compositions=[{"U235": 0.02}, {"U235": 0.0195}],
            benchmark_k_eff=benchmark_k_eff,
            reference_source="IAEA",
        )
        
        database.add_burnup_benchmark(burnup_bm)
        
        benchmarker = ValidationBenchmarker(cache, benchmark_database=database)
        
        # Look up benchmark from database
        test_case = "test_lookup"
        if test_case in database.burnup_benchmarks:
            benchmark = database.burnup_benchmarks[test_case]
            
            # Simulated calculated k-eff
            calculated_k_eff = [0.999, 0.994]
            
            # Benchmark
            result = benchmarker.benchmark_k_eff(calculated_k_eff, benchmark, tolerance=0.01)
            
            assert result.passed
            assert result.metrics["total_comparisons"] == 2
    
    def test_benchmark_k_eff_outside_tolerance(self):
        """Test benchmarking k-eff when values are outside tolerance."""
        cache = NuclearDataCache()
        database = BenchmarkDatabase()
        
        benchmark_k_eff = [
            BenchmarkValue(value=1.0, uncertainty=0.001, source="IAEA"),
        ]
        
        burnup_bm = BurnupBenchmark(
            test_case="test_outside_tolerance",
            problem_description="Test",
            initial_composition={"U235": 0.02},
            time_steps=[0],
            benchmark_compositions=[{"U235": 0.02}],
            benchmark_k_eff=benchmark_k_eff,
            reference_source="IAEA",
        )
        
        database.add_burnup_benchmark(burnup_bm)
        benchmarker = ValidationBenchmarker(cache, benchmark_database=database)
        
        # Calculated value outside tolerance (2% error, tolerance is 1%)
        calculated_k_eff = [1.02]
        
        result = benchmarker.benchmark_k_eff(calculated_k_eff, burnup_bm, tolerance=0.01)
        
        assert not result.passed  # Should fail because outside tolerance
        assert result.metrics["within_tolerance_count"] == 0
        assert result.metrics["max_relative_error"] > 0.01
