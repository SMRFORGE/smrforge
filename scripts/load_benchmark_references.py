#!/usr/bin/env python3
"""
Script to load benchmark reference values into the validation database.

Loads benchmark values from JSON files (including standards data files)
into the BenchmarkDatabase for use in validation testing.

Usage:
    python scripts/load_benchmark_references.py --file docs/validation/benchmark_reference_values.json --output benchmarks.json
    python scripts/load_benchmark_references.py --dir docs/validation --output benchmarks.json
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.validation_benchmark_data import BenchmarkDatabase

# Import standards parser
try:
    from smrforge.validation.standards_parser import StandardsParser, parse_standards_data
    _STANDARDS_PARSER_AVAILABLE = True
except ImportError:
    _STANDARDS_PARSER_AVAILABLE = False


def load_benchmark_file(input_file: Path, database: BenchmarkDatabase) -> int:
    """
    Load benchmark values from a JSON file into database.
    
    Args:
        input_file: Path to benchmark data file (JSON format)
        database: BenchmarkDatabase instance to load into
    
    Returns:
        Number of benchmarks loaded
    """
    if not input_file.exists():
        print(f"Error: File not found: {input_file}")
        return 0
    
    try:
        # Try loading as BenchmarkDatabase format
        database.load(input_file)
        count = (
            len(database.decay_heat_benchmarks) +
            len(database.gamma_transport_benchmarks) +
            len(database.burnup_benchmarks)
        )
        print(f"Loaded {count} benchmarks from {input_file}")
        return count
    except Exception as e:
        # Try using standards parser if available
        if _STANDARDS_PARSER_AVAILABLE:
            try:
                parser = StandardsParser()
                benchmarks = parse_standards_data(input_file)
                if benchmarks:
                    loaded_count = parser.load_into_database(benchmarks, database)
                    print(f"Loaded {loaded_count} benchmarks from {input_file} (via standards parser)")
                    return loaded_count
            except Exception as e2:
                print(f"Error loading with standards parser: {e2}")
        
        print(f"Error loading benchmark file: {e}")
        return 0


def main():
    parser = argparse.ArgumentParser(
        description="Load benchmark reference values into validation database"
    )
    parser.add_argument(
        "--file",
        type=Path,
        help="Benchmark data file to load (JSON format)"
    )
    parser.add_argument(
        "--dir",
        type=Path,
        help="Directory containing benchmark data files"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmarks.json"),
        help="Output database file (default: benchmarks.json)"
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append to existing database (default: create new)"
    )
    
    args = parser.parse_args()
    
    # Create or load database
    if args.append and args.output.exists():
        database = BenchmarkDatabase(args.output)
        print(f"Loading into existing database: {args.output}")
    else:
        database = BenchmarkDatabase()
        print(f"Creating new database: {args.output}")
    
    total_loaded = 0
    
    # Load from file
    if args.file:
        loaded = load_benchmark_file(args.file, database)
        total_loaded += loaded
    
    # Load from directory
    if args.dir:
        if not args.dir.is_dir():
            print(f"Error: Directory not found: {args.dir}")
            sys.exit(1)
        
        json_files = list(args.dir.glob("*.json"))
        print(f"Found {len(json_files)} JSON files in {args.dir}")
        
        for json_file in json_files:
            if json_file.name.startswith("_"):
                continue  # Skip files starting with underscore
            
            loaded = load_benchmark_file(json_file, database)
            total_loaded += loaded
    
    if not args.file and not args.dir:
        parser.print_help()
        print("\nError: Must specify --file or --dir")
        sys.exit(1)
    
    # Save database
    if total_loaded > 0:
        database.save(args.output)
        print(f"\nDatabase saved to {args.output}")
        print(f"Total benchmarks: {total_loaded}")
        print(f"  - Decay heat: {len(database.decay_heat_benchmarks)}")
        print(f"  - Gamma transport: {len(database.gamma_transport_benchmarks)}")
        print(f"  - Burnup: {len(database.burnup_benchmarks)}")
    else:
        print("\nNo benchmarks loaded")
        sys.exit(1)


if __name__ == "__main__":
    main()
