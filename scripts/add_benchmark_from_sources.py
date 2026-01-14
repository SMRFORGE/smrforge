#!/usr/bin/env python3
"""
Utility script to add benchmark values from various sources.

Helps users add benchmark values from:
- ANSI/ANS-5.1 standards (decay heat)
- MCNP calculations (gamma transport)
- IAEA benchmark problems (burnup)

Usage:
    python scripts/add_benchmark_from_sources.py --help
    python scripts/add_benchmark_from_sources.py --ansi-ans --file ansi_data.json --output benchmarks.json
    python scripts/add_benchmark_from_sources.py --mcnp --file mcnp_results.txt --output benchmarks.json
    python scripts/add_benchmark_from_sources.py --iaea --file iaea_benchmark.json --output benchmarks.json
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.validation_benchmark_data import (
    BenchmarkDatabase,
    DecayHeatBenchmark,
    GammaTransportBenchmark,
    BurnupBenchmark,
    BenchmarkValue,
)


def parse_ansi_ans_format(data: Dict[str, Any]) -> List[DecayHeatBenchmark]:
    """
    Parse ANSI/ANS-5.1 standard format data.
    
    Expected format:
    {
        "test_cases": [
            {
                "test_case": "u235_thermal_100mw",
                "nuclides": {"U235": 1e20},
                "initial_power": 100.0,
                "shutdown_time": 0.0,
                "time_points": [3600, 86400, 604800],
                "benchmark_values": [
                    {"value": 7.0, "uncertainty": 0.5, "unit": "MW", "source": "ANSI/ANS-5.1"},
                    ...
                ]
            }
        ]
    }
    """
    benchmarks = []
    
    for test_data in data.get("test_cases", []):
        benchmark_values = [
            BenchmarkValue(
                value=bv["value"],
                uncertainty=bv.get("uncertainty"),
                unit=bv.get("unit", "MW"),
                source=bv.get("source", "ANSI/ANS-5.1"),
                notes=bv.get("notes", ""),
            )
            for bv in test_data["benchmark_values"]
        ]
        
        benchmark = DecayHeatBenchmark(
            test_case=test_data["test_case"],
            nuclides=test_data["nuclides"],
            initial_power=test_data["initial_power"],
            shutdown_time=test_data.get("shutdown_time", 0.0),
            time_points=test_data["time_points"],
            benchmark_values=benchmark_values,
            standard="ANSI/ANS-5.1",
        )
        benchmarks.append(benchmark)
    
    return benchmarks


def parse_mcnp_format(data: Dict[str, Any]) -> List[GammaTransportBenchmark]:
    """
    Parse MCNP calculation results format.
    
    Expected format:
    {
        "test_cases": [
            {
                "test_case": "simple_shielding",
                "geometry_description": "...",
                "source_description": "...",
                "energy_groups": [0.1, 1.0, 10.0],
                "benchmark_flux": [
                    {"value": 1e10, "uncertainty": 1e8, "unit": "photons/cm²/s", "source": "MCNP 6.2"},
                    ...
                ],
                "benchmark_dose_rate": {"value": 1.23, "uncertainty": 0.01, "unit": "Sv/h", "source": "MCNP 6.2"}
            }
        ]
    }
    """
    benchmarks = []
    
    for test_data in data.get("test_cases", []):
        benchmark_flux = [
            BenchmarkValue(
                value=bv["value"],
                uncertainty=bv.get("uncertainty"),
                unit=bv.get("unit", "photons/cm²/s"),
                source=bv.get("source", "MCNP"),
            )
            for bv in test_data["benchmark_flux"]
        ]
        
        dose_rate_data = test_data["benchmark_dose_rate"]
        benchmark_dose_rate = BenchmarkValue(
            value=dose_rate_data["value"],
            uncertainty=dose_rate_data.get("uncertainty"),
            unit=dose_rate_data.get("unit", "Sv/h"),
            source=dose_rate_data.get("source", "MCNP"),
        )
        
        benchmark = GammaTransportBenchmark(
            test_case=test_data["test_case"],
            geometry_description=test_data["geometry_description"],
            source_description=test_data["source_description"],
            energy_groups=test_data["energy_groups"],
            benchmark_flux=benchmark_flux,
            benchmark_dose_rate=benchmark_dose_rate,
            reference_code="MCNP",
            reference_version=test_data.get("reference_version", ""),
        )
        benchmarks.append(benchmark)
    
    return benchmarks


def parse_iaea_format(data: Dict[str, Any]) -> List[BurnupBenchmark]:
    """
    Parse IAEA benchmark format data.
    
    Expected format:
    {
        "test_cases": [
            {
                "test_case": "u235_pin_30days",
                "problem_description": "...",
                "initial_composition": {"U235": 0.02, "U238": 0.98},
                "time_steps": [0, 30, 60, 90],
                "benchmark_k_eff": [
                    {"value": 1.0, "uncertainty": 0.001, "unit": "", "source": "IAEA Benchmark"},
                    ...
                ],
                "benchmark_compositions": [...]
            }
        ]
    }
    """
    benchmarks = []
    
    for test_data in data.get("test_cases", []):
        benchmark_k_eff = [
            BenchmarkValue(
                value=bv["value"],
                uncertainty=bv.get("uncertainty"),
                unit=bv.get("unit", ""),
                source=bv.get("source", "IAEA Benchmark"),
            )
            for bv in test_data["benchmark_k_eff"]
        ]
        
        benchmark = BurnupBenchmark(
            test_case=test_data["test_case"],
            problem_description=test_data["problem_description"],
            initial_composition=test_data["initial_composition"],
            time_steps=test_data["time_steps"],
            benchmark_compositions=test_data.get("benchmark_compositions", []),
            benchmark_k_eff=benchmark_k_eff,
            reference_source="IAEA",
        )
        benchmarks.append(benchmark)
    
    return benchmarks


def add_from_ansi_ans(input_file: Path, output_file: Path, append: bool = False):
    """Add benchmark values from ANSI/ANS-5.1 format file."""
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)
    
    # Load database
    if append and output_file.exists():
        db = BenchmarkDatabase(output_file)
        print(f"Appending to existing database: {output_file}")
    else:
        db = BenchmarkDatabase()
        print(f"Creating new database: {output_file}")
    
    # Parse input file
    data = json.loads(input_file.read_text())
    benchmarks = parse_ansi_ans_format(data)
    
    # Add benchmarks
    for benchmark in benchmarks:
        db.add_decay_heat_benchmark(benchmark)
        print(f"Added decay heat benchmark: {benchmark.test_case}")
    
    # Save database
    db.save(output_file)
    print(f"\nSuccessfully added {len(benchmarks)} ANSI/ANS-5.1 benchmarks to {output_file}")


def add_from_mcnp(input_file: Path, output_file: Path, append: bool = False):
    """Add benchmark values from MCNP format file."""
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)
    
    # Load database
    if append and output_file.exists():
        db = BenchmarkDatabase(output_file)
        print(f"Appending to existing database: {output_file}")
    else:
        db = BenchmarkDatabase()
        print(f"Creating new database: {output_file}")
    
    # Parse input file
    data = json.loads(input_file.read_text())
    benchmarks = parse_mcnp_format(data)
    
    # Add benchmarks
    for benchmark in benchmarks:
        db.add_gamma_transport_benchmark(benchmark)
        print(f"Added gamma transport benchmark: {benchmark.test_case}")
    
    # Save database
    db.save(output_file)
    print(f"\nSuccessfully added {len(benchmarks)} MCNP benchmarks to {output_file}")


def add_from_iaea(input_file: Path, output_file: Path, append: bool = False):
    """Add benchmark values from IAEA format file."""
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)
    
    # Load database
    if append and output_file.exists():
        db = BenchmarkDatabase(output_file)
        print(f"Appending to existing database: {output_file}")
    else:
        db = BenchmarkDatabase()
        print(f"Creating new database: {output_file}")
    
    # Parse input file
    data = json.loads(input_file.read_text())
    benchmarks = parse_iaea_format(data)
    
    # Add benchmarks
    for benchmark in benchmarks:
        db.add_burnup_benchmark(benchmark)
        print(f"Added burnup benchmark: {benchmark.test_case}")
    
    # Save database
    db.save(output_file)
    print(f"\nSuccessfully added {len(benchmarks)} IAEA benchmarks to {output_file}")


def create_template_files(output_dir: Path):
    """Create template files for each benchmark source format."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # ANSI/ANS-5.1 template
    ansi_template = {
        "test_cases": [
            {
                "test_case": "u235_thermal_100mw",
                "nuclides": {"U235": 1e20},
                "initial_power": 100.0,
                "shutdown_time": 0.0,
                "time_points": [3600, 86400, 604800, 2592000],
                "benchmark_values": [
                    {
                        "value": 0.0,  # Replace with actual ANSI/ANS-5.1 value
                        "uncertainty": 0.0,  # Replace with actual uncertainty
                        "unit": "MW",
                        "source": "ANSI/ANS-5.1",
                        "notes": "Replace with actual benchmark value from ANSI/ANS-5.1 standard"
                    }
                ]
            }
        ]
    }
    ansi_file = output_dir / "ansi_ans_template.json"
    ansi_file.write_text(json.dumps(ansi_template, indent=2))
    print(f"Created ANSI/ANS-5.1 template: {ansi_file}")
    
    # MCNP template
    mcnp_template = {
        "test_cases": [
            {
                "test_case": "simple_shielding",
                "geometry_description": "Describe geometry (replace with actual description)",
                "source_description": "Describe source (replace with actual description)",
                "energy_groups": [0.1, 1.0, 10.0],
                "benchmark_flux": [
                    {
                        "value": 0.0,  # Replace with actual MCNP value
                        "uncertainty": 0.0,  # Replace with actual uncertainty
                        "unit": "photons/cm²/s",
                        "source": "MCNP 6.2"
                    }
                ],
                "benchmark_dose_rate": {
                    "value": 0.0,  # Replace with actual MCNP value
                    "uncertainty": 0.0,  # Replace with actual uncertainty
                    "unit": "Sv/h",
                    "source": "MCNP 6.2"
                },
                "reference_version": "6.2"
            }
        ]
    }
    mcnp_file = output_dir / "mcnp_template.json"
    mcnp_file.write_text(json.dumps(mcnp_template, indent=2))
    print(f"Created MCNP template: {mcnp_file}")
    
    # IAEA template
    iaea_template = {
        "test_cases": [
            {
                "test_case": "u235_pin_30days",
                "problem_description": "Describe problem (replace with actual IAEA benchmark description)",
                "initial_composition": {"U235": 0.02, "U238": 0.98},
                "time_steps": [0, 30, 60, 90],
                "benchmark_k_eff": [
                    {
                        "value": 0.0,  # Replace with actual IAEA benchmark value
                        "uncertainty": 0.0,  # Replace with actual uncertainty
                        "unit": "",
                        "source": "IAEA Benchmark"
                    }
                ],
                "benchmark_compositions": []
            }
        ]
    }
    iaea_file = output_dir / "iaea_template.json"
    iaea_file.write_text(json.dumps(iaea_template, indent=2))
    print(f"Created IAEA template: {iaea_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Add benchmark values from various sources (ANSI/ANS, MCNP, IAEA)"
    )
    parser.add_argument(
        "--ansi-ans",
        action="store_true",
        help="Add benchmarks from ANSI/ANS-5.1 format file"
    )
    parser.add_argument(
        "--mcnp",
        action="store_true",
        help="Add benchmarks from MCNP format file"
    )
    parser.add_argument(
        "--iaea",
        action="store_true",
        help="Add benchmarks from IAEA format file"
    )
    parser.add_argument(
        "--file",
        type=Path,
        help="Input file with benchmark data"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmarks.json"),
        help="Output benchmark database file (default: benchmarks.json)"
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append to existing database (default: create new)"
    )
    parser.add_argument(
        "--create-templates",
        type=Path,
        help="Create template files for benchmark formats in specified directory"
    )
    
    args = parser.parse_args()
    
    # Create templates
    if args.create_templates:
        create_template_files(args.create_templates)
        return 0
    
    # Validate inputs
    if not (args.ansi_ans or args.mcnp or args.iaea):
        parser.print_help()
        print("\nError: Must specify --ansi-ans, --mcnp, or --iaea")
        sys.exit(1)
    
    if not args.file:
        parser.print_help()
        print("\nError: Must specify --file")
        sys.exit(1)
    
    # Add benchmarks based on source type
    if args.ansi_ans:
        add_from_ansi_ans(args.file, args.output, args.append)
    elif args.mcnp:
        add_from_mcnp(args.file, args.output, args.append)
    elif args.iaea:
        add_from_iaea(args.file, args.output, args.append)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
