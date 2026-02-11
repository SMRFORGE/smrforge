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
    MCNPConverter: MCNP format converter
"""

from smrforge.io.converters import MCNPConverter, OpenMCConverter, SerpentConverter
from smrforge.io.readers import InputReader, OutputWriter

__all__ = [
    "InputReader",
    "OutputWriter",
    "SerpentConverter",
    "OpenMCConverter",
    "MCNPConverter",
    "run_serpent",
    "parse_serpent_res",
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


def run_serpent(work_dir, input_file, executable=None, timeout=None):
    """Convenience: run Serpent 2 in work_dir on input_file."""
    from smrforge.io.serpent_run import run_serpent as _run_serpent_fn

    return _run_serpent_fn(work_dir, input_file, executable=executable, timeout=timeout)


def parse_serpent_res(path):
    """Convenience: parse Serpent _res.m file for k-eff and related results."""
    from smrforge.io.serpent_run import parse_res_file

    return parse_res_file(path)
