"""
Tests for standards data parser.

Tests the StandardsParser class for parsing ANSI/ANS-5.1, IAEA, and MCNP
benchmark data.
"""

import json
import tempfile
from pathlib import Path

import pytest

from smrforge.validation.standards_parser import (
    StandardsParser,
    StandardsBenchmarkData,
    StandardType,
    parse_standards_data,
)


class TestStandardsParser:
    """Tests for StandardsParser class."""
    
    def test_parse_ansi_ans_5_1_json(self):
        """Test parsing ANSI/ANS-5.1 data from JSON."""
        parser = StandardsParser()
        
        # Create temporary JSON file
        test_data = {
            "standard": "ANSI/ANS-5.1",
            "benchmarks": [
                {
                    "test_case": "u235_thermal_fission",
                    "nuclides": {"U235": 1.0},
                    "initial_power": 100.0,
                    "operating_time": 86400.0,
                    "time_points": [3600, 86400, 604800],
                    "decay_heat_values": [
                        {"time": 3600, "value": 0.07, "unit": "MW"},
                        {"time": 86400, "value": 0.04, "unit": "MW"},
                    ]
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_data, f)
            temp_file = Path(f.name)
        
        try:
            benchmarks = parser.parse_ansi_ans_5_1(temp_file)
            
            assert len(benchmarks) == 1
            assert benchmarks[0].standard_type == StandardType.ANSI_ANS_5_1
            assert benchmarks[0].test_case == "u235_thermal_fission"
            assert benchmarks[0].data["nuclides"] == {"U235": 1.0}
        finally:
            temp_file.unlink()
    
    def test_parse_ansi_ans_5_1_benchmark_format(self):
        """Test parsing ANSI/ANS-5.1 data in BenchmarkDatabase format."""
        parser = StandardsParser()
        
        # Create temporary JSON file in BenchmarkDatabase format
        test_data = {
            "decay_heat_benchmarks": {
                "test_case_1": {
                    "test_case": "test_case_1",
                    "nuclides": {"U235": 1e20},
                    "initial_power": 100.0,
                    "shutdown_time": 0.0,
                    "time_points": [3600, 86400],
                    "benchmark_values": [
                        {
                            "value": 0.07,
                            "uncertainty": 0.01,
                            "unit": "MW",
                            "source": "ANSI/ANS-5.1",
                        }
                    ],
                    "standard": "ANSI/ANS-5.1"
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_data, f)
            temp_file = Path(f.name)
        
        try:
            benchmarks = parser.parse_ansi_ans_5_1(temp_file)
            
            assert len(benchmarks) == 1
            assert benchmarks[0].standard_type == StandardType.ANSI_ANS_5_1
            assert benchmarks[0].test_case == "test_case_1"
        finally:
            temp_file.unlink()
    
    def test_parse_iaea_benchmark(self):
        """Test parsing IAEA benchmark data."""
        parser = StandardsParser()
        
        test_data = {
            "test_case": "iaea_test_1",
            "benchmark_id": "IAEA-BM-001",
            "problem_description": "Test problem",
            "initial_composition": {"U235": 0.02, "U238": 0.98},
            "time_steps": [0, 30, 60],
            "benchmark_k_eff": [
                {"value": 1.0, "uncertainty": 0.001},
                {"value": 0.99, "uncertainty": 0.001},
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_data, f)
            temp_file = Path(f.name)
        
        try:
            benchmark = parser.parse_iaea_benchmark(temp_file)
            
            assert benchmark is not None
            assert benchmark.standard_type == StandardType.IAEA_BENCHMARK
            assert benchmark.test_case == "iaea_test_1"
            assert benchmark.data["benchmark_id"] == "IAEA-BM-001"
        finally:
            temp_file.unlink()
    
    def test_parse_mcnp_reference(self):
        """Test parsing MCNP reference data."""
        parser = StandardsParser()
        
        test_data = {
            "test_case": "mcnp_test_1",
            "mcnp_version": "6.2",
            "geometry_description": "Test geometry",
            "benchmark_flux": [
                {"value": 1e10, "unit": "photons/cm²/s"}
            ],
            "benchmark_dose_rate": {
                "value": 1e-3,
                "unit": "Sv/h"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_data, f)
            temp_file = Path(f.name)
        
        try:
            benchmark = parser.parse_mcnp_reference(temp_file)
            
            assert benchmark is not None
            assert benchmark.standard_type == StandardType.MCNP_REFERENCE
            assert benchmark.test_case == "mcnp_test_1"
        finally:
            temp_file.unlink()
    
    def test_load_into_database(self):
        """Test loading benchmarks into BenchmarkDatabase."""
        from tests.validation_benchmark_data import BenchmarkDatabase
        
        parser = StandardsParser()
        database = BenchmarkDatabase()
        
        # Create ANSI/ANS-5.1 benchmark
        test_data = {
            "test_case": "test_decay_heat",
            "nuclides": {"U235": 1e20},
            "initial_power": 100.0,
            "shutdown_time": 0.0,
            "time_points": [3600, 86400],
            "benchmark_values": [
                {
                    "value": 0.07,
                    "uncertainty": 0.01,
                    "unit": "MW",
                    "source": "ANSI/ANS-5.1",
                }
            ],
            "standard": "ANSI/ANS-5.1"
        }
        
        benchmark = StandardsBenchmarkData(
            standard_type=StandardType.ANSI_ANS_5_1,
            test_case="test_decay_heat",
            data=test_data,
            metadata={"standard": "ANSI/ANS-5.1"},
        )
        
        loaded_count = parser.load_into_database([benchmark], database)
        
        assert loaded_count == 1
        assert "test_decay_heat" in database.decay_heat_benchmarks
    
    def test_parse_nonexistent_file(self):
        """Test parsing nonexistent file."""
        parser = StandardsParser()
        
        result = parser.parse_ansi_ans_5_1("nonexistent_file.json")
        assert result == []
        
        result = parser.parse_iaea_benchmark("nonexistent_file.json")
        assert result is None
    
    def test_parse_standards_data_convenience(self):
        """Test parse_standards_data convenience function."""
        test_data = {
            "standard": "ANSI/ANS-5.1",
            "benchmarks": [
                {
                    "test_case": "test_case",
                    "nuclides": {"U235": 1.0},
                    "initial_power": 100.0,
                    "time_points": [3600],
                    "decay_heat_values": [{"time": 3600, "value": 0.07, "unit": "MW"}]
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_data, f)
            temp_file = Path(f.name)
        
        try:
            benchmarks = parse_standards_data(temp_file)
            assert len(benchmarks) > 0
            assert benchmarks[0].standard_type == StandardType.ANSI_ANS_5_1
        finally:
            temp_file.unlink()
