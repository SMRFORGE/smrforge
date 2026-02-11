"""
Input file readers for reactor configurations.

This module provides readers for various input formats:
- JSON input files
- YAML input files
- Legacy card-based input format
"""

import json
from pathlib import Path
from typing import Any, Dict

from ..utils.logging import get_logger

logger = get_logger("smrforge.io.readers")

try:
    import yaml

    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False
    logger.warning("yaml not available, YAML reading will be disabled")


class InputReader:
    """
    Base class for input file readers.

    Provides methods to read various input formats for reactor configurations.
    """

    @staticmethod
    def read_json(filepath: Path) -> Dict[str, Any]:
        """
        Read JSON input file.

        Args:
            filepath: Path to JSON file

        Returns:
            Dictionary with configuration data

        Raises:
            FileNotFoundError: If file does not exist
            json.JSONDecodeError: If JSON is invalid
        """
        with open(filepath, "r") as f:
            return json.load(f)

    @staticmethod
    def read_yaml(filepath: Path) -> Dict[str, Any]:
        """
        Read YAML input file.

        Args:
            filepath: Path to YAML file

        Returns:
            Dictionary with configuration data

        Raises:
            FileNotFoundError: If file does not exist
            ImportError: If yaml module is not available
        """
        if not _YAML_AVAILABLE:
            raise ImportError(
                "yaml module not available. Install with: pip install pyyaml"
            )

        with open(filepath, "r") as f:
            return yaml.safe_load(f)

    @staticmethod
    def read_legacy_input(filepath: Path) -> Dict[str, Any]:
        """
        Read legacy card-based input format.

        Parses simple KEY = VALUE format with comment support.

        Args:
            filepath: Path to input file

        Returns:
            Dictionary with configuration data
        """
        config = {}

        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # Parse card format: KEY = VALUE
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()

                    # Try to convert to number if possible
                    try:
                        if "." in value:
                            config[key] = float(value)
                        else:
                            config[key] = int(value)
                    except ValueError:
                        # Keep as string
                        config[key] = value

        return config


class OutputWriter:
    """
    Output file writers.

    Provides methods to write various output formats.
    """

    @staticmethod
    def write_json(data: Dict[str, Any], filepath: Path, indent: int = 2):
        """
        Write JSON output file.

        Args:
            data: Data to write
            filepath: Output file path
            indent: JSON indentation
        """
        with open(filepath, "w") as f:
            json.dump(data, f, indent=indent)

    @staticmethod
    def write_csv(data: Dict[str, list], filepath: Path):
        """
        Write CSV output file.

        Args:
            data: Dictionary with column names as keys and lists as values
            filepath: Output file path
        """
        import csv

        if not data:
            return

        with open(filepath, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=data.keys())
            writer.writeheader()

            # Transpose data
            n_rows = len(next(iter(data.values())))
            for i in range(n_rows):
                row = {key: values[i] for key, values in data.items()}
                writer.writerow(row)

    @staticmethod
    def write_yaml(data: Dict[str, Any], filepath: Path):
        """
        Write YAML output file.

        Args:
            data: Data to write
            filepath: Output file path

        Raises:
            ImportError: If yaml module is not available
        """
        if not _YAML_AVAILABLE:
            raise ImportError(
                "yaml module not available. Install with: pip install pyyaml"
            )

        with open(filepath, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
