"""
Unit tests for I/O readers and writers module.
"""

import json
import tempfile
from pathlib import Path

import numpy as np
import pytest

from smrforge.io.readers import InputReader, OutputWriter


class TestInputReader:
    """Tests for InputReader class."""

    def test_read_json(self):
        """Test reading JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"key": "value", "number": 42}, f)
            temp_path = Path(f.name)

        try:
            data = InputReader.read_json(temp_path)

            assert data["key"] == "value"
            assert data["number"] == 42
        finally:
            temp_path.unlink()

    def test_read_json_file_not_found(self):
        """Test reading non-existent JSON file."""
        with pytest.raises(FileNotFoundError):
            InputReader.read_json(Path("nonexistent.json"))

    def test_read_json_invalid(self):
        """Test reading invalid JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{ invalid json }")
            temp_path = Path(f.name)

        try:
            with pytest.raises(json.JSONDecodeError):
                InputReader.read_json(temp_path)
        finally:
            temp_path.unlink()

    def test_read_yaml(self):
        """Test reading YAML file (if yaml available)."""
        try:
            import yaml

            yaml_available = True
        except ImportError:
            yaml_available = False

        if not yaml_available:
            pytest.skip("yaml not available")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("key: value\nnumber: 42\n")
            temp_path = Path(f.name)

        try:
            data = InputReader.read_yaml(temp_path)

            assert data["key"] == "value"
            assert data["number"] == 42
        finally:
            temp_path.unlink()

    def test_read_yaml_not_available(self):
        """Test reading YAML when yaml module not available."""
        # Mock yaml not available
        import smrforge.io.readers as readers_module

        original_yaml = getattr(readers_module, "_YAML_AVAILABLE", None)
        readers_module._YAML_AVAILABLE = False

        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".yaml", delete=False
            ) as f:
                f.write("key: value\n")
                temp_path = Path(f.name)

            try:
                with pytest.raises(ImportError):
                    InputReader.read_yaml(temp_path)
            finally:
                temp_path.unlink()
        finally:
            if original_yaml is not None:
                readers_module._YAML_AVAILABLE = original_yaml

    def test_read_legacy_input(self):
        """Test reading legacy card-based input format."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".inp", delete=False) as f:
            f.write("# Comment line\n")
            f.write("KEY1 = value1\n")
            f.write("KEY2 = 42\n")
            f.write("KEY3 = 3.14\n")
            f.write("  KEY4 = spaced_value  \n")
            temp_path = Path(f.name)

        try:
            data = InputReader.read_legacy_input(temp_path)

            assert data["KEY1"] == "value1"
            assert data["KEY2"] == 42
            assert data["KEY3"] == 3.14
            assert data["KEY4"] == "spaced_value"
        finally:
            temp_path.unlink()

    def test_read_legacy_input_with_comments(self):
        """Test reading legacy input with comments."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".inp", delete=False) as f:
            f.write("# Comment line\n")
            f.write("KEY = value\n")
            f.write("  # Another comment\n")
            f.write("KEY2 = value2\n")
            temp_path = Path(f.name)

        try:
            data = InputReader.read_legacy_input(temp_path)

            assert "KEY" in data
            assert "KEY2" in data
            assert "# Comment" not in data
        finally:
            temp_path.unlink()


class TestOutputWriter:
    """Tests for OutputWriter class."""

    def test_write_json(self):
        """Test writing JSON file."""
        data = {"key": "value", "number": 42, "list": [1, 2, 3]}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = Path(f.name)

        try:
            OutputWriter.write_json(data, temp_path)

            # Read back and verify
            with open(temp_path, "r") as f:
                loaded = json.load(f)

            assert loaded == data
        finally:
            temp_path.unlink()

    def test_write_json_with_indent(self):
        """Test writing JSON file with custom indent."""
        data = {"key": "value"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = Path(f.name)

        try:
            OutputWriter.write_json(data, temp_path, indent=4)

            # Verify file was written
            assert temp_path.exists()
            with open(temp_path, "r") as f:
                content = f.read()
                # Should have indentation
                assert "    " in content
        finally:
            temp_path.unlink()

    def test_write_csv(self):
        """Test writing CSV file."""
        data = {
            "column1": [1, 2, 3],
            "column2": ["a", "b", "c"],
            "column3": [1.1, 2.2, 3.3],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            temp_path = Path(f.name)

        try:
            OutputWriter.write_csv(data, temp_path)

            # Verify file was written
            assert temp_path.exists()
            with open(temp_path, "r") as f:
                lines = f.readlines()
                # Should have header and data rows
                assert len(lines) >= 2
                assert "column1" in lines[0]
        finally:
            temp_path.unlink()

    def test_write_csv_empty(self):
        """Test writing empty CSV file."""
        data = {}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            temp_path = Path(f.name)

        try:
            OutputWriter.write_csv(data, temp_path)

            # File should exist but be empty or minimal
            assert temp_path.exists()
        finally:
            temp_path.unlink()

    def test_write_yaml(self):
        """Test writing YAML file (if yaml available)."""
        try:
            import yaml

            yaml_available = True
        except ImportError:
            yaml_available = False

        if not yaml_available:
            pytest.skip("yaml not available")

        data = {"key": "value", "number": 42}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            temp_path = Path(f.name)

        try:
            OutputWriter.write_yaml(data, temp_path)

            # Verify file was written
            assert temp_path.exists()
            # Read back and verify
            with open(temp_path, "r") as f:
                loaded = yaml.safe_load(f)

            assert loaded == data
        finally:
            temp_path.unlink()

    def test_write_yaml_not_available(self):
        """Test writing YAML when yaml module not available."""
        # Mock yaml not available
        import smrforge.io.readers as readers_module

        original_yaml = getattr(readers_module, "_YAML_AVAILABLE", None)
        readers_module._YAML_AVAILABLE = False

        try:
            data = {"key": "value"}

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".yaml", delete=False
            ) as f:
                temp_path = Path(f.name)

            try:
                with pytest.raises(ImportError):
                    OutputWriter.write_yaml(data, temp_path)
            finally:
                if temp_path.exists():
                    temp_path.unlink()
        finally:
            if original_yaml is not None:
                readers_module._YAML_AVAILABLE = original_yaml
