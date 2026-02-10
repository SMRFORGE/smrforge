"""
Input/output utilities.

This module provides I/O utilities for:
- Import/export reactor designs
- Results export formats
- Data format converters
- File format readers/writers

Classes:
    InputReader: Input file readers (JSON, YAML, legacy formats)
    OutputWriter: Output file writers (JSON, CSV, YAML)
    SerpentConverter: Serpent format converter
    OpenMCConverter: OpenMC format converter
"""

from smrforge.io.converters import OpenMCConverter, SerpentConverter
from smrforge.io.readers import InputReader, OutputWriter

__all__ = [
    "InputReader",
    "OutputWriter",
    "SerpentConverter",
    "OpenMCConverter",
]


def export_to_openmc(reactor, output_dir, particles=1000, batches=20):
    """Convenience: export reactor to OpenMC format."""
    from pathlib import Path

    return OpenMCConverter.export_reactor(
        reactor, Path(output_dir), particles=particles, batches=batches
    )


def run_openmc(work_dir, executable=None, timeout=None):
    """Convenience: run OpenMC in work_dir."""
    from smrforge.io.openmc_run import run_openmc as _run_openmc

    return _run_openmc(work_dir, executable=executable, timeout=timeout)


def parse_openmc_statepoint(path):
    """Convenience: parse OpenMC statepoint HDF5."""
    from smrforge.io.openmc_run import parse_statepoint

    return parse_statepoint(path)
