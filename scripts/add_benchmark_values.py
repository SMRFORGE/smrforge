#!/usr/bin/env python3
"""
Script for adding benchmark values to the validation benchmark database.

This script provides utilities for adding benchmark values from various sources
(ANSI/ANS standards, MCNP comparisons, IAEA benchmarks) to the benchmark database.

Usage:
    python scripts/add_benchmark_values.py --help
    python scripts/add_benchmark_values.py --create-template --output benchmarks_template.json
    python scripts/add_benchmark_values.py --add-decay-heat --file benchmarks.json --test-case U235_shutdown
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.validation_benchmark_data import (
    BenchmarkDatabase,
    DecayHeatBenchmark,
    GammaTransportBenchmark,
    BurnupBenchmark,
    BenchmarkValue,
)


def create_template(output_file: Path):
    """Create a template benchmark data file."""
    template = {
        "decay_heat_benchmarks": {
            "example_u235_shutdown": {
                "test_case": "example_u235_shutdown",
                "nuclides": {"U235": 1e20},
                "initial_power": 100.0,
                "shutdown_time": 0.0,
                "time_points": [3600, 86400, 604800],
                "benchmark_values": [
                    {
                        "value": 0.0,  # Replace with actual ANSI/ANS-5.1 value
                        "uncertainty": 0.01,  # Replace with actual uncertainty
                        "unit": "MW",
                        "source": "ANSI/ANS-5.1",
                        "notes": "Replace with actual benchmark value"
                    }
                ],
                "standard": "ANSI/ANS-5.1"
            }
        },
        "gamma_transport_benchmarks": {
            "example_simple_shielding": {
                "test_case": "example_simple_shielding",
                "geometry_description": "Describe geometry",
                "source_description": "Describe source",
                "energy_groups": [0.1, 1.0, 10.0],
                "benchmark_flux": [
                    {
                        "value": 0.0,  # Replace with actual MCNP value
                        "uncertainty": 0.0,
                        "unit": "photons/cm²/s",
                        "source": "MCNP 6.2"
                    }
                ],
                "benchmark_dose_rate": {
                    "value": 0.0,  # Replace with actual MCNP value
                    "uncertainty": 0.0,
                    "unit": "Sv/h",
                    "source": "MCNP 6.2"
                },
                "reference_code": "MCNP",
                "reference_version": "6.2"
            }
        },
        "burnup_benchmarks": {
            "example_simple_burnup": {
                "test_case": "example_simple_burnup",
                "problem_description": "Describe problem",
                "initial_composition": {"U235": 0.02, "U238": 0.98},
                "time_steps": [0, 30, 60, 90],
                "benchmark_compositions": [
                    {"U235": 0.02, "U238": 0.98}
                ],
                "benchmark_k_eff": [
                    {
                        "value": 0.0,  # Replace with actual IAEA benchmark value
                        "uncertainty": 0.0,
                        "unit": "",
                        "source": "IAEA Benchmark"
                    }
                ],
                "reference_source": "IAEA"
            }
        }
    }
    
    output_file.write_text(json.dumps(template, indent=2))
    print(f"Template created: {output_file}")


def add_decay_heat_interactive(db_file: Path):
    """Interactive function to add decay heat benchmark."""
    print("Adding Decay Heat Benchmark (ANSI/ANS-5.1)")
    print("-" * 60)
    
    test_case = input("Test case name: ")
    nuclides_input = input("Nuclides (format: U235:1e20,U238:1e19): ")
    nuclides = {}
    for pair in nuclides_input.split(","):
        key, value = pair.split(":")
        nuclides[key.strip()] = float(value.strip())
    
    initial_power = float(input("Initial power (MW): "))
    shutdown_time = float(input("Shutdown time (seconds): "))
    
    time_points_input = input("Time points (comma-separated, seconds): ")
    time_points = [float(t.strip()) for t in time_points_input.split(",")]
    
    benchmark_values = []
    for time_point in time_points:
        print(f"\nTime point: {time_point} seconds")
        value = float(input("  Benchmark value (MW): "))
        uncertainty = input("  Uncertainty (MW, optional): ")
        uncertainty = float(uncertainty) if uncertainty else None
        source = input("  Source (e.g., ANSI/ANS-5.1): ")
        notes = input("  Notes (optional): ")
        
        benchmark_values.append(
            BenchmarkValue(
                value=value,
                uncertainty=uncertainty,
                unit="MW",
                source=source,
                notes=notes
            )
        )
    
    benchmark = DecayHeatBenchmark(
        test_case=test_case,
        nuclides=nuclides,
        initial_power=initial_power,
        shutdown_time=shutdown_time,
        time_points=time_points,
        benchmark_values=benchmark_values,
        standard="ANSI/ANS-5.1"
    )
    
    # Load existing database or create new
    db = BenchmarkDatabase(db_file) if db_file.exists() else BenchmarkDatabase()
    db.add_decay_heat_benchmark(benchmark)
    db.save(db_file)
    
    print(f"\nBenchmark added to {db_file}")


def validate_benchmark_file(file_path: Path):
    """Validate benchmark data file structure."""
    try:
        data = json.loads(file_path.read_text())
        
        print(f"Validating {file_path}...")
        errors = []
        
        # Check structure
        if "decay_heat_benchmarks" not in data:
            errors.append("Missing 'decay_heat_benchmarks' section")
        if "gamma_transport_benchmarks" not in data:
            errors.append("Missing 'gamma_transport_benchmarks' section")
        if "burnup_benchmarks" not in data:
            errors.append("Missing 'burnup_benchmarks' section")
        
        # Try to load as BenchmarkDatabase to validate structure
        try:
            db = BenchmarkDatabase(file_path)
            print("✓ File structure is valid")
            print(f"  Decay heat benchmarks: {len(db.decay_heat_benchmarks)}")
            print(f"  Gamma transport benchmarks: {len(db.gamma_transport_benchmarks)}")
            print(f"  Burnup benchmarks: {len(db.burnup_benchmarks)}")
        except Exception as e:
            errors.append(f"Failed to load as BenchmarkDatabase: {e}")
        
        if errors:
            print("✗ Validation errors:")
            for error in errors:
                print(f"  - {error}")
            return False
        else:
            print("✓ All validations passed")
            return True
            
    except json.JSONDecodeError as e:
        print(f"✗ JSON parse error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Utilities for managing validation benchmark data"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Create template
    parser_template = subparsers.add_parser(
        "create-template",
        help="Create a template benchmark data file"
    )
    parser_template.add_argument(
        "--output",
        type=Path,
        default=Path("validation_benchmarks_template.json"),
        help="Output file path"
    )
    
    # Add decay heat benchmark (interactive)
    parser_decay = subparsers.add_parser(
        "add-decay-heat",
        help="Interactively add a decay heat benchmark"
    )
    parser_decay.add_argument(
        "--file",
        type=Path,
        default=Path("validation_benchmarks.json"),
        help="Benchmark database file"
    )
    
    # Validate file
    parser_validate = subparsers.add_parser(
        "validate",
        help="Validate a benchmark data file"
    )
    parser_validate.add_argument(
        "file",
        type=Path,
        help="Benchmark data file to validate"
    )
    
    args = parser.parse_args()
    
    if args.command == "create-template":
        create_template(args.output)
    elif args.command == "add-decay-heat":
        add_decay_heat_interactive(args.file)
    elif args.command == "validate":
        success = validate_benchmark_file(args.file)
        sys.exit(0 if success else 1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
