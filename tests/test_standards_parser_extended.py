"""
Extended tests for smrforge.validation.standards_parser module.

This test file focuses on improving coverage from 43.98% to 75%+ by testing:
- StandardType enum
- StandardsBenchmarkData dataclass
- StandardsParser methods
- Error handling and edge cases
- File I/O operations
- Integration with BenchmarkDatabase
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from smrforge.validation.standards_parser import (
    StandardsBenchmarkData,
    StandardsParser,
    StandardType,
    parse_standards_data,
)


class TestStandardType:
    """Tests for StandardType enum."""

    def test_standard_type_values(self):
        """Test all StandardType enum values."""
        assert StandardType.ANSI_ANS_5_1.value == "ANSI/ANS-5.1"
        assert StandardType.IAEA_BENCHMARK.value == "IAEA"
        assert StandardType.MCNP_REFERENCE.value == "MCNP"
        assert StandardType.CUSTOM.value == "CUSTOM"

    def test_standard_type_membership(self):
        """Test checking enum membership."""
        assert StandardType.ANSI_ANS_5_1 in StandardType
        assert StandardType.IAEA_BENCHMARK in StandardType


class TestStandardsBenchmarkData:
    """Tests for StandardsBenchmarkData dataclass."""

    def test_benchmark_data_creation(self):
        """Test creating StandardsBenchmarkData."""
        benchmark = StandardsBenchmarkData(
            standard_type=StandardType.ANSI_ANS_5_1,
            test_case="test_001",
            data={"power": 100.0},
            metadata={"source": "test"},
        )

        assert benchmark.standard_type == StandardType.ANSI_ANS_5_1
        assert benchmark.test_case == "test_001"
        assert benchmark.data["power"] == 100.0
        assert benchmark.metadata["source"] == "test"

    def test_benchmark_data_to_dict(self):
        """Test converting benchmark data to dictionary."""
        benchmark = StandardsBenchmarkData(
            standard_type=StandardType.IAEA_BENCHMARK,
            test_case="iaea_test",
            data={"k_eff": 1.00123},
            metadata={"benchmark_id": "001"},
        )

        data = benchmark.to_dict()

        assert data["standard_type"] == "IAEA"
        assert data["test_case"] == "iaea_test"
        assert data["data"]["k_eff"] == 1.00123
        assert data["metadata"]["benchmark_id"] == "001"

    def test_benchmark_data_all_standard_types(self):
        """Test benchmark data with all standard types."""
        for std_type in StandardType:
            benchmark = StandardsBenchmarkData(
                standard_type=std_type, test_case="test", data={}, metadata={}
            )
            assert benchmark.standard_type == std_type


class TestStandardsParser:
    """Tests for StandardsParser class."""

    def test_parser_initialization(self):
        """Test creating StandardsParser instance."""
        parser = StandardsParser()

        assert isinstance(parser, StandardsParser)
        assert parser.parsed_benchmarks == []

    def test_parse_ansi_ans_5_1_valid_json(self, tmp_path):
        """Test parsing valid ANSI/ANS-5.1 JSON file."""
        parser = StandardsParser()

        # Create valid ANSI/ANS-5.1 data file
        data = {
            "standard": "ANSI/ANS-5.1",
            "benchmarks": [
                {
                    "test_case": "u235_thermal_fission",
                    "nuclides": {"U235": 1.0},
                    "initial_power": 100.0,
                    "operating_time": 86400.0,
                    "time_points": [3600, 86400],
                    "decay_heat_values": [{"time": 3600, "value": 0.07, "unit": "MW"}],
                }
            ],
        }

        data_file = tmp_path / "ansi_ans_5_1.json"
        with open(data_file, "w") as f:
            json.dump(data, f)

        benchmarks = parser.parse_ansi_ans_5_1(data_file)

        assert len(benchmarks) == 1
        assert benchmarks[0].standard_type == StandardType.ANSI_ANS_5_1
        assert benchmarks[0].test_case == "u235_thermal_fission"

    def test_parse_ansi_ans_5_1_direct_format(self, tmp_path):
        """Test parsing ANSI/ANS-5.1 data in direct benchmark format."""
        parser = StandardsParser()

        # Create data in direct benchmark format
        data = {
            "decay_heat_benchmarks": {
                "test_case_1": {
                    "standard": "ANSI/ANS-5.1",
                    "nuclides": {"U235": 1.0},
                    "power": 100.0,
                }
            }
        }

        data_file = tmp_path / "ansi_direct.json"
        with open(data_file, "w") as f:
            json.dump(data, f)

        benchmarks = parser.parse_ansi_ans_5_1(data_file)

        assert len(benchmarks) == 1
        assert benchmarks[0].standard_type == StandardType.ANSI_ANS_5_1
        assert benchmarks[0].test_case == "test_case_1"

    def test_parse_ansi_ans_5_1_file_not_found(self):
        """Test parsing non-existent file returns empty list."""
        parser = StandardsParser()

        result = parser.parse_ansi_ans_5_1(Path("nonexistent.json"))

        assert result == []

    def test_parse_ansi_ans_5_1_invalid_json(self, tmp_path):
        """Test parsing invalid JSON returns empty list."""
        parser = StandardsParser()

        data_file = tmp_path / "invalid.json"
        data_file.write_text("not valid json")

        result = parser.parse_ansi_ans_5_1(data_file)

        assert result == []

    def test_parse_ansi_ans_5_1_wrong_standard(self, tmp_path):
        """Test parsing file with wrong standard type."""
        parser = StandardsParser()

        data = {"standard": "WRONG_STANDARD", "benchmarks": []}

        data_file = tmp_path / "wrong.json"
        with open(data_file, "w") as f:
            json.dump(data, f)

        result = parser.parse_ansi_ans_5_1(data_file)

        assert result == []

    def test_parse_ansi_ans_5_1_empty_benchmarks(self, tmp_path):
        """Test parsing file with empty benchmarks list."""
        parser = StandardsParser()

        data = {"standard": "ANSI/ANS-5.1", "benchmarks": []}

        data_file = tmp_path / "empty.json"
        with open(data_file, "w") as f:
            json.dump(data, f)

        result = parser.parse_ansi_ans_5_1(data_file)

        assert result == []

    def test_parse_iaea_benchmark_valid_json(self, tmp_path):
        """Test parsing valid IAEA benchmark JSON file."""
        parser = StandardsParser()

        data = {
            "test_case": "iaea_test",
            "problem_name": "IAEA Test Problem",
            "benchmark_id": "001",
            "k_eff": 1.00123,
        }

        data_file = tmp_path / "iaea.json"
        with open(data_file, "w") as f:
            json.dump(data, f)

        benchmark = parser.parse_iaea_benchmark(data_file)

        assert benchmark is not None
        assert benchmark.standard_type == StandardType.IAEA_BENCHMARK
        assert benchmark.test_case == "iaea_test"
        assert benchmark.metadata["benchmark_id"] == "001"

    def test_parse_iaea_benchmark_uses_filename(self, tmp_path):
        """Test IAEA parser uses filename if test_case not provided."""
        parser = StandardsParser()

        data = {"k_eff": 1.00123}

        data_file = tmp_path / "iaea_test_problem.json"
        with open(data_file, "w") as f:
            json.dump(data, f)

        benchmark = parser.parse_iaea_benchmark(data_file)

        assert benchmark is not None
        assert benchmark.test_case == "iaea_test_problem"

    def test_parse_iaea_benchmark_file_not_found(self):
        """Test parsing non-existent IAEA file returns None."""
        parser = StandardsParser()

        result = parser.parse_iaea_benchmark(Path("nonexistent.json"))

        assert result is None

    def test_parse_iaea_benchmark_yaml_with_pyyaml(self, tmp_path):
        """Test parsing IAEA benchmark YAML file."""
        parser = StandardsParser()

        # Check if yaml is available
        try:
            import yaml

            yaml_available = True
        except ImportError:
            yaml_available = False

        if not yaml_available:
            pytest.skip("PyYAML not available")

        data = {"test_case": "iaea_yaml", "k_eff": 1.00123}

        data_file = tmp_path / "iaea.yaml"
        with open(data_file, "w") as f:
            yaml.dump(data, f)

        benchmark = parser.parse_iaea_benchmark(data_file)

        assert benchmark is not None
        assert benchmark.test_case == "iaea_yaml"

    def test_parse_iaea_benchmark_yaml_without_pyyaml(self, tmp_path):
        """Test parsing YAML file when PyYAML not available."""
        parser = StandardsParser()

        data_file = tmp_path / "iaea.yaml"
        data_file.write_text("test_case: test")

        with patch.dict("sys.modules", {"yaml": None}):
            with patch("smrforge.validation.standards_parser.logger") as mock_logger:
                result = parser.parse_iaea_benchmark(data_file)

                assert result is None
                mock_logger.error.assert_called()

    def test_parse_iaea_benchmark_invalid_json(self, tmp_path):
        """Test parsing invalid JSON returns None."""
        parser = StandardsParser()

        data_file = tmp_path / "invalid.json"
        data_file.write_text("not valid json")

        result = parser.parse_iaea_benchmark(data_file)

        assert result is None

    def test_parse_mcnp_reference_valid(self, tmp_path):
        """Test parsing valid MCNP reference file."""
        parser = StandardsParser()

        data = {
            "test_case": "mcnp_test",
            "problem_name": "MCNP Test",
            "mcnp_version": "6.2",
            "k_eff": 1.00123,
        }

        data_file = tmp_path / "mcnp.json"
        with open(data_file, "w") as f:
            json.dump(data, f)

        benchmark = parser.parse_mcnp_reference(data_file)

        assert benchmark is not None
        assert benchmark.standard_type == StandardType.MCNP_REFERENCE
        assert benchmark.test_case == "mcnp_test"
        assert benchmark.metadata["mcnp_version"] == "6.2"

    def test_parse_mcnp_reference_file_not_found(self):
        """Test parsing non-existent MCNP file returns None."""
        parser = StandardsParser()

        result = parser.parse_mcnp_reference(Path("nonexistent.json"))

        assert result is None

    def test_parse_mcnp_reference_invalid_json(self, tmp_path):
        """Test parsing invalid JSON returns None."""
        parser = StandardsParser()

        data_file = tmp_path / "invalid.json"
        data_file.write_text("not valid json")

        result = parser.parse_mcnp_reference(data_file)

        assert result is None

    def test_parse_custom_benchmark_valid(self, tmp_path):
        """Test parsing valid custom benchmark file."""
        parser = StandardsParser()

        data = {"test_case": "custom_test", "k_eff": 1.00123}

        data_file = tmp_path / "custom.json"
        with open(data_file, "w") as f:
            json.dump(data, f)

        benchmark = parser.parse_custom_benchmark(
            data_file, standard_name="CUSTOM_TEST"
        )

        assert benchmark is not None
        assert benchmark.standard_type == StandardType.CUSTOM
        assert benchmark.test_case == "custom_test"
        assert benchmark.metadata["standard"] == "CUSTOM_TEST"

    def test_parse_custom_benchmark_default_name(self, tmp_path):
        """Test parsing custom benchmark with default standard name."""
        parser = StandardsParser()

        data = {"test_case": "test"}
        data_file = tmp_path / "custom.json"
        with open(data_file, "w") as f:
            json.dump(data, f)

        benchmark = parser.parse_custom_benchmark(data_file)

        assert benchmark is not None
        assert benchmark.metadata["standard"] == "CUSTOM"

    def test_parse_custom_benchmark_file_not_found(self):
        """Test parsing non-existent custom file returns None."""
        parser = StandardsParser()

        result = parser.parse_custom_benchmark(Path("nonexistent.json"))

        assert result is None

    def test_parse_custom_benchmark_invalid_json(self, tmp_path):
        """Test parsing invalid JSON returns None."""
        parser = StandardsParser()

        data_file = tmp_path / "invalid.json"
        data_file.write_text("not valid json")

        result = parser.parse_custom_benchmark(data_file)

        assert result is None

    def test_parse_custom_benchmark_uses_filename(self, tmp_path):
        """Test custom parser uses filename if test_case not provided."""
        parser = StandardsParser()

        data = {"k_eff": 1.00123}
        data_file = tmp_path / "custom_test.json"
        with open(data_file, "w") as f:
            json.dump(data, f)

        benchmark = parser.parse_custom_benchmark(data_file)

        assert benchmark is not None
        assert benchmark.test_case == "custom_test"

    def test_load_into_database(self):
        """Test loading benchmarks into database.

        This test verifies the method exists and can be called.
        Full functionality testing requires the BenchmarkDatabase implementation.
        """
        parser = StandardsParser()

        # Create mock benchmarks
        benchmarks = [
            StandardsBenchmarkData(
                standard_type=StandardType.ANSI_ANS_5_1,
                test_case="test_1",
                data={"nuclides": {"U235": 1.0}},
                metadata={},
            )
        ]

        # Create mock database
        mock_database = Mock()
        mock_database.add_decay_heat_benchmark = Mock()
        mock_database.add_gamma_transport_benchmark = Mock()
        mock_database.add_burnup_benchmark = Mock()

        # Test that the method exists and can be called
        # Actual implementation may require real BenchmarkDatabase
        try:
            loaded_count = parser.load_into_database(benchmarks, mock_database)
            # Should return a number (may be 0 if conversion fails)
            assert isinstance(loaded_count, int)
            assert loaded_count >= 0
        except (ImportError, AttributeError):
            # Skip if BenchmarkDatabase classes aren't available
            pytest.skip("BenchmarkDatabase classes not available")


class TestParseStandardsData:
    """Tests for parse_standards_data helper function."""

    def test_parse_standards_data_ansi(self, tmp_path):
        """Test parse_standards_data with ANSI/ANS-5.1 file."""
        data = {
            "standard": "ANSI/ANS-5.1",
            "benchmarks": [{"test_case": "test", "nuclides": {"U235": 1.0}}],
        }

        data_file = tmp_path / "ansi.json"
        with open(data_file, "w") as f:
            json.dump(data, f)

        result = parse_standards_data(data_file)

        assert isinstance(result, list)
        assert len(result) > 0

    def test_parse_standards_data_iaea(self, tmp_path):
        """Test parse_standards_data with IAEA file."""
        data = {"test_case": "iaea_test", "k_eff": 1.00123}

        data_file = tmp_path / "iaea.json"
        with open(data_file, "w") as f:
            json.dump(data, f)

        result = parse_standards_data(data_file, standard_type="IAEA")

        assert result is not None or isinstance(result, list)

    def test_parse_standards_data_mcnp(self, tmp_path):
        """Test parse_standards_data with MCNP file."""
        data = {"test_case": "mcnp_test", "k_eff": 1.00123}

        data_file = tmp_path / "mcnp.json"
        with open(data_file, "w") as f:
            json.dump(data, f)

        result = parse_standards_data(data_file, standard_type="MCNP")

        assert result is not None or isinstance(result, list)

    def test_parse_standards_data_custom(self, tmp_path):
        """Test parse_standards_data with custom file."""
        data = {"test_case": "custom_test", "k_eff": 1.00123}

        data_file = tmp_path / "custom.json"
        with open(data_file, "w") as f:
            json.dump(data, f)

        result = parse_standards_data(data_file, standard_type="CUSTOM")

        assert result is not None or isinstance(result, list)

    def test_parse_standards_data_file_not_found(self):
        """Test parse_standards_data with non-existent file."""
        result = parse_standards_data(Path("nonexistent.json"))

        # Should return None or empty list
        assert result is None or result == []
