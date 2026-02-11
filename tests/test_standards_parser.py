"""
Tests for standards data parser.

Tests the StandardsParser class for parsing ANSI/ANS-5.1, IAEA, and MCNP
benchmark data.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from smrforge.validation.standards_parser import (
    StandardsBenchmarkData,
    StandardsParser,
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
                    ],
                }
            ],
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
                    "standard": "ANSI/ANS-5.1",
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
            ],
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
            "benchmark_flux": [{"value": 1e10, "unit": "photons/cm²/s"}],
            "benchmark_dose_rate": {"value": 1e-3, "unit": "Sv/h"},
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
            "standard": "ANSI/ANS-5.1",
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
                    "decay_heat_values": [{"time": 3600, "value": 0.07, "unit": "MW"}],
                }
            ],
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


class TestStandardsBenchmarkData:
    """Tests for StandardsBenchmarkData dataclass."""

    def test_to_dict(self):
        """Test converting StandardsBenchmarkData to dictionary."""
        benchmark = StandardsBenchmarkData(
            standard_type=StandardType.ANSI_ANS_5_1,
            test_case="test_case",
            data={"key": "value"},
            metadata={"meta": "data"},
        )

        result = benchmark.to_dict()

        assert result["standard_type"] == "ANSI/ANS-5.1"
        assert result["test_case"] == "test_case"
        assert result["data"] == {"key": "value"}
        assert result["metadata"] == {"meta": "data"}


class TestStandardsParserExtended:
    """Extended tests for StandardsParser to improve coverage."""

    def test_parse_ansi_ans_5_1_json_decode_error(self):
        """Test parsing ANSI/ANS-5.1 with invalid JSON."""
        parser = StandardsParser()

        # Create file with invalid JSON
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json content {")
            temp_file = Path(f.name)

        try:
            result = parser.parse_ansi_ans_5_1(temp_file)
            # Should return empty list on JSON decode error
            assert result == []
        finally:
            temp_file.unlink()

    def test_parse_ansi_ans_5_1_exception_handling(self):
        """Test parsing ANSI/ANS-5.1 with exception during file read."""
        parser = StandardsParser()

        # Create a file that will cause an exception
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"standard": "ANSI/ANS-5.1", "benchmarks": []}, f)
            temp_file = Path(f.name)

        try:
            # Mock open to raise an exception
            from unittest.mock import mock_open, patch

            with patch("builtins.open", side_effect=PermissionError("Access denied")):
                result = parser.parse_ansi_ans_5_1(temp_file)
                assert result == []
        finally:
            temp_file.unlink()

    def test_parse_iaea_benchmark_yaml(self):
        """Test parsing IAEA benchmark from YAML file."""
        parser = StandardsParser()

        try:
            import yaml
        except ImportError:
            pytest.skip("yaml not available")

        test_data = {
            "test_case": "iaea_yaml_test",
            "benchmark_id": "IAEA-BM-002",
            "problem_description": "YAML test problem",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(test_data, f)
            temp_file = Path(f.name)

        try:
            benchmark = parser.parse_iaea_benchmark(temp_file)

            assert benchmark is not None
            assert benchmark.standard_type == StandardType.IAEA_BENCHMARK
            assert benchmark.test_case == "iaea_yaml_test"
        finally:
            temp_file.unlink()

    def test_parse_iaea_benchmark_yaml_no_pyyaml(self):
        """Test parsing IAEA benchmark YAML when pyyaml is not available."""
        parser = StandardsParser()

        test_data = {"test_case": "test"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("test_case: test\n")  # Simple YAML
            temp_file = Path(f.name)

        try:
            # Test the ImportError path by mocking the import inside the function
            # The code does: import yaml inside the try block
            # We can't easily test this without actually removing yaml, so skip if available
            try:
                import yaml

                pytest.skip("yaml is available, cannot test ImportError path")
            except ImportError:
                # If yaml is not available, test the error path
                result = parser.parse_iaea_benchmark(temp_file)
                # Should return None when yaml is not available
                assert result is None
        finally:
            temp_file.unlink()

    def test_parse_iaea_benchmark_exception(self):
        """Test parsing IAEA benchmark with exception."""
        parser = StandardsParser()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json")
            temp_file = Path(f.name)

        try:
            result = parser.parse_iaea_benchmark(temp_file)
            # Should return None on exception
            assert result is None
        finally:
            temp_file.unlink()

    def test_parse_iaea_benchmark_problem_name_fallback(self):
        """Test parsing IAEA benchmark with problem_name fallback."""
        parser = StandardsParser()

        test_data = {
            "problem_name": "iaea_problem",  # No test_case, use problem_name
            "benchmark_id": "IAEA-BM-003",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_data, f)
            temp_file = Path(f.name)

        try:
            benchmark = parser.parse_iaea_benchmark(temp_file)

            assert benchmark is not None
            assert benchmark.test_case == "iaea_problem"
        finally:
            temp_file.unlink()

    def test_parse_iaea_benchmark_stem_fallback(self):
        """Test parsing IAEA benchmark with filename stem fallback."""
        parser = StandardsParser()

        test_data = {}  # No test_case or problem_name

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, prefix="iaea_test_"
        ) as f:
            json.dump(test_data, f)
            temp_file = Path(f.name)

        try:
            benchmark = parser.parse_iaea_benchmark(temp_file)

            assert benchmark is not None
            # Should use filename stem
            assert benchmark.test_case == temp_file.stem
        finally:
            temp_file.unlink()

    def test_parse_mcnp_reference_file_not_found(self):
        """Test parsing MCNP reference with non-existent file."""
        parser = StandardsParser()

        result = parser.parse_mcnp_reference("nonexistent_mcnp.json")

        assert result is None

    def test_parse_mcnp_reference_exception(self):
        """Test parsing MCNP reference with exception."""
        parser = StandardsParser()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json")
            temp_file = Path(f.name)

        try:
            result = parser.parse_mcnp_reference(temp_file)
            # Should return None on exception
            assert result is None
        finally:
            temp_file.unlink()

    def test_parse_mcnp_reference_problem_name_fallback(self):
        """Test parsing MCNP reference with problem_name fallback."""
        parser = StandardsParser()

        test_data = {
            "problem_name": "mcnp_problem",  # No test_case
            "mcnp_version": "6.2",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_data, f)
            temp_file = Path(f.name)

        try:
            benchmark = parser.parse_mcnp_reference(temp_file)

            assert benchmark is not None
            assert benchmark.test_case == "mcnp_problem"
        finally:
            temp_file.unlink()

    def test_parse_custom_benchmark(self):
        """Test parsing custom benchmark data."""
        parser = StandardsParser()

        test_data = {
            "test_case": "custom_test",
            "custom_field": "custom_value",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_data, f)
            temp_file = Path(f.name)

        try:
            benchmark = parser.parse_custom_benchmark(
                temp_file, standard_name="CUSTOM_STANDARD"
            )

            assert benchmark is not None
            assert benchmark.standard_type == StandardType.CUSTOM
            assert benchmark.test_case == "custom_test"
            assert benchmark.metadata["standard"] == "CUSTOM_STANDARD"
        finally:
            temp_file.unlink()

    def test_parse_custom_benchmark_file_not_found(self):
        """Test parsing custom benchmark with non-existent file."""
        parser = StandardsParser()

        result = parser.parse_custom_benchmark("nonexistent_custom.json")

        assert result is None

    def test_parse_custom_benchmark_exception(self):
        """Test parsing custom benchmark with exception."""
        parser = StandardsParser()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json")
            temp_file = Path(f.name)

        try:
            result = parser.parse_custom_benchmark(temp_file)
            # Should return None on exception
            assert result is None
        finally:
            temp_file.unlink()

    def test_parse_custom_benchmark_stem_fallback(self):
        """Test parsing custom benchmark with filename stem fallback."""
        parser = StandardsParser()

        test_data = {}  # No test_case

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, prefix="custom_"
        ) as f:
            json.dump(test_data, f)
            temp_file = Path(f.name)

        try:
            benchmark = parser.parse_custom_benchmark(temp_file)

            assert benchmark is not None
            # Should use filename stem
            assert benchmark.test_case == temp_file.stem
        finally:
            temp_file.unlink()

    def test_load_into_database_decay_heat_values(self):
        """Test loading benchmarks with decay_heat_values format."""
        from tests.validation_benchmark_data import BenchmarkDatabase

        parser = StandardsParser()
        database = BenchmarkDatabase()

        # Create benchmark with decay_heat_values format (not benchmark_values)
        test_data = {
            "test_case": "test_decay_heat_values",
            "nuclides": {"U235": 1e20},
            "initial_power": 100.0,
            "shutdown_time": 0.0,
            "time_points": [3600, 86400],
            "decay_heat_values": [  # Different format
                {"time": 3600, "value": 0.07, "unit": "MW"},
                {"time": 86400, "value": 0.04, "unit": "MW"},
            ],
        }

        benchmark = StandardsBenchmarkData(
            standard_type=StandardType.ANSI_ANS_5_1,
            test_case="test_decay_heat_values",
            data=test_data,
            metadata={"standard": "ANSI/ANS-5.1"},
        )

        loaded_count = parser.load_into_database([benchmark], database)

        assert loaded_count == 1
        assert "test_decay_heat_values" in database.decay_heat_benchmarks

    def test_load_into_database_iaea_benchmark(self):
        """Test loading IAEA benchmark into database."""
        from tests.validation_benchmark_data import BenchmarkDatabase

        parser = StandardsParser()
        database = BenchmarkDatabase()

        test_data = {
            "test_case": "iaea_burnup_test",
            "problem_description": "IAEA burnup problem",
            "initial_composition": {"U235": 0.02, "U238": 0.98},
            "time_steps": [0, 30, 60],
            "benchmark_k_eff": [
                {"value": 1.0, "uncertainty": 0.001},
                {"value": 0.99, "uncertainty": 0.001},
            ],
        }

        benchmark = StandardsBenchmarkData(
            standard_type=StandardType.IAEA_BENCHMARK,
            test_case="iaea_burnup_test",
            data=test_data,
            metadata={"standard": "IAEA"},
        )

        loaded_count = parser.load_into_database([benchmark], database)

        assert loaded_count == 1
        assert "iaea_burnup_test" in database.burnup_benchmarks

    def test_load_into_database_mcnp_gamma_transport(self):
        """Test loading MCNP gamma transport benchmark into database."""
        from tests.validation_benchmark_data import BenchmarkDatabase

        parser = StandardsParser()
        database = BenchmarkDatabase()

        test_data = {
            "test_case": "mcnp_gamma_test",
            "mcnp_version": "6.2",
            "geometry_description": "Test geometry",
            "benchmark_flux": [
                {"value": 1e10, "unit": "photons/cm²/s"},
            ],
            "benchmark_dose_rate": {
                "value": 1e-3,
                "unit": "Sv/h",
            },
        }

        benchmark = StandardsBenchmarkData(
            standard_type=StandardType.MCNP_REFERENCE,
            test_case="mcnp_gamma_test",
            data=test_data,
            metadata={"standard": "MCNP"},
        )

        loaded_count = parser.load_into_database([benchmark], database)

        assert loaded_count == 1
        assert "mcnp_gamma_test" in database.gamma_transport_benchmarks

    def test_load_into_database_exception_handling(self):
        """Test loading benchmarks with exception handling."""
        from tests.validation_benchmark_data import BenchmarkDatabase

        parser = StandardsParser()
        database = BenchmarkDatabase()

        # Create benchmark that will cause exception during conversion
        # Use a benchmark type that requires specific fields
        benchmark = StandardsBenchmarkData(
            standard_type=StandardType.ANSI_ANS_5_1,
            test_case="invalid_test",
            data={
                "invalid": "data"
            },  # Missing required fields like nuclides, initial_power
            metadata={},
        )

        # Mock add_decay_heat_benchmark to raise exception
        with patch.object(
            database, "add_decay_heat_benchmark", side_effect=ValueError("Invalid data")
        ):
            loaded_count = parser.load_into_database([benchmark], database)

            # Should skip invalid benchmark
            assert loaded_count == 0

    def test_parse_directory(self):
        """Test parsing all files in a directory."""
        parser = StandardsParser()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create multiple test files
            ansi_data = {
                "standard": "ANSI/ANS-5.1",
                "benchmarks": [{"test_case": "ansi_test", "nuclides": {"U235": 1.0}}],
            }
            ansi_file = tmp_path / "ansi_test.json"
            with open(ansi_file, "w") as f:
                json.dump(ansi_data, f)

            iaea_data = {
                "test_case": "iaea_test",
                "benchmark_id": "IAEA-BM-001",
            }
            iaea_file = tmp_path / "iaea_test.json"
            with open(iaea_file, "w") as f:
                json.dump(iaea_data, f)

            benchmarks = parser.parse_directory(tmp_path)

            assert len(benchmarks) >= 2

    def test_parse_directory_not_dir(self):
        """Test parsing directory when path is not a directory."""
        parser = StandardsParser()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_file = Path(f.name)

        try:
            result = parser.parse_directory(temp_file)  # File, not directory
            assert result == []
        finally:
            temp_file.unlink()

    def test_parse_directory_custom_pattern(self):
        """Test parsing directory with custom pattern."""
        parser = StandardsParser()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create test file
            test_data = {
                "standard": "ANSI/ANS-5.1",
                "benchmarks": [{"test_case": "test", "nuclides": {"U235": 1.0}}],
            }
            test_file = tmp_path / "test.json"
            with open(test_file, "w") as f:
                json.dump(test_data, f)

            benchmarks = parser.parse_directory(tmp_path, pattern="*.json")

            assert len(benchmarks) >= 1

    def test_parse_directory_exception_handling(self):
        """Test parsing directory with exception handling."""
        parser = StandardsParser()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create invalid file
            invalid_file = tmp_path / "invalid.json"
            with open(invalid_file, "w") as f:
                f.write("invalid json")

            # Should handle exceptions gracefully
            benchmarks = parser.parse_directory(tmp_path)

            # Should skip invalid files
            assert isinstance(benchmarks, list)

    def test_parse_standards_data_auto_detect_ansi(self):
        """Test parse_standards_data auto-detection for ANSI."""
        test_data = {
            "standard": "ANSI/ANS-5.1",
            "benchmarks": [{"test_case": "auto_test", "nuclides": {"U235": 1.0}}],
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, prefix="ansi_"
        ) as f:
            json.dump(test_data, f)
            temp_file = Path(f.name)

        try:
            benchmarks = parse_standards_data(temp_file)
            assert len(benchmarks) > 0
            assert benchmarks[0].standard_type == StandardType.ANSI_ANS_5_1
        finally:
            temp_file.unlink()

    def test_parse_standards_data_auto_detect_decay_heat_benchmarks(self):
        """Test parse_standards_data auto-detection from decay_heat_benchmarks."""
        test_data = {
            "decay_heat_benchmarks": {
                "test_case_1": {
                    "test_case": "test_case_1",
                    "standard": "ANSI/ANS-5.1",
                    "nuclides": {"U235": 1e20},
                }
            }
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

    def test_parse_standards_data_auto_detect_iaea(self):
        """Test parse_standards_data auto-detection for IAEA."""
        test_data = {
            "test_case": "iaea_auto_test",
            "benchmark_id": "IAEA-BM-001",
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, prefix="iaea_"
        ) as f:
            json.dump(test_data, f)
            temp_file = Path(f.name)

        try:
            benchmarks = parse_standards_data(temp_file)
            assert len(benchmarks) > 0
            assert benchmarks[0].standard_type == StandardType.IAEA_BENCHMARK
        finally:
            temp_file.unlink()

    def test_parse_standards_data_auto_detect_mcnp(self):
        """Test parse_standards_data auto-detection for MCNP."""
        test_data = {
            "test_case": "mcnp_auto_test",
            "mcnp_version": "6.2",
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, prefix="mcnp_"
        ) as f:
            json.dump(test_data, f)
            temp_file = Path(f.name)

        try:
            benchmarks = parse_standards_data(temp_file)
            assert len(benchmarks) > 0
            assert benchmarks[0].standard_type == StandardType.MCNP_REFERENCE
        finally:
            temp_file.unlink()

    def test_parse_standards_data_auto_detect_custom(self):
        """Test parse_standards_data auto-detection for custom."""
        test_data = {
            "test_case": "custom_auto_test",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_data, f)
            temp_file = Path(f.name)

        try:
            benchmarks = parse_standards_data(temp_file)
            assert len(benchmarks) > 0
            assert benchmarks[0].standard_type == StandardType.CUSTOM
        finally:
            temp_file.unlink()

    def test_parse_standards_data_specified_type_ansi(self):
        """Test parse_standards_data with specified ANSI type."""
        test_data = {
            "standard": "ANSI/ANS-5.1",
            "benchmarks": [{"test_case": "specified_test", "nuclides": {"U235": 1.0}}],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_data, f)
            temp_file = Path(f.name)

        try:
            benchmarks = parse_standards_data(
                temp_file, standard_type=StandardType.ANSI_ANS_5_1
            )
            assert len(benchmarks) > 0
            assert benchmarks[0].standard_type == StandardType.ANSI_ANS_5_1
        finally:
            temp_file.unlink()

    def test_parse_standards_data_specified_type_iaea(self):
        """Test parse_standards_data with specified IAEA type."""
        test_data = {
            "test_case": "iaea_specified_test",
            "benchmark_id": "IAEA-BM-001",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_data, f)
            temp_file = Path(f.name)

        try:
            benchmarks = parse_standards_data(
                temp_file, standard_type=StandardType.IAEA_BENCHMARK
            )
            assert len(benchmarks) > 0
            assert benchmarks[0].standard_type == StandardType.IAEA_BENCHMARK
        finally:
            temp_file.unlink()

    def test_parse_standards_data_specified_type_mcnp(self):
        """Test parse_standards_data with specified MCNP type."""
        test_data = {
            "test_case": "mcnp_specified_test",
            "mcnp_version": "6.2",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_data, f)
            temp_file = Path(f.name)

        try:
            benchmarks = parse_standards_data(
                temp_file, standard_type=StandardType.MCNP_REFERENCE
            )
            assert len(benchmarks) > 0
            assert benchmarks[0].standard_type == StandardType.MCNP_REFERENCE
        finally:
            temp_file.unlink()

    def test_parse_standards_data_specified_type_custom(self):
        """Test parse_standards_data with specified CUSTOM type."""
        test_data = {
            "test_case": "custom_specified_test",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_data, f)
            temp_file = Path(f.name)

        try:
            benchmarks = parse_standards_data(
                temp_file, standard_type=StandardType.CUSTOM
            )
            assert len(benchmarks) > 0
            assert benchmarks[0].standard_type == StandardType.CUSTOM
        finally:
            temp_file.unlink()

    def test_parse_standards_data_json_decode_error(self):
        """Test parse_standards_data with JSON decode error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json")
            temp_file = Path(f.name)

        try:
            benchmarks = parse_standards_data(temp_file)
            # Should return empty list or handle gracefully
            assert isinstance(benchmarks, list)
        finally:
            temp_file.unlink()
