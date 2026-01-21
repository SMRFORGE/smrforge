#!/usr/bin/env python3
"""
Quick coverage analysis script.

Analyzes a coverage JSON file and provides summary statistics.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def analyze_coverage_file(coverage_file: str) -> None:
    """Analyze a coverage JSON file and print summary."""
    coverage_path = Path(coverage_file)
    
    if not coverage_path.exists():
        print(f"Error: Coverage file not found: {coverage_file}")
        sys.exit(1)
    
    print(f"Analyzing: {coverage_file}")
    print(f"Last modified: {coverage_path.stat().st_mtime}")
    print("=" * 70)
    
    try:
        with open(coverage_path, 'r') as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading coverage file: {e}")
        sys.exit(1)
    
    # Overall statistics
    totals = data.get('totals', {})
    if not totals:
        print("Error: No totals found in coverage file")
        sys.exit(1)
    
    coverage = totals.get('percent_covered', 0)
    covered = totals.get('covered_lines', 0)
    total = totals.get('num_statements', 0)
    missing = totals.get('missing_lines', 0)
    excluded = totals.get('excluded_lines', 0)
    
    print("\nOVERALL COVERAGE STATISTICS")
    print("=" * 70)
    print(f"Coverage:     {coverage:.2f}%")
    print(f"Covered:      {covered:,} lines")
    print(f"Total:        {total:,} statements")
    print(f"Missing:      {missing:,} lines")
    print(f"Excluded:     {excluded:,} lines")
    
    # Calculate gap to 80%
    if coverage < 80:
        gap = 80 - coverage
        # Estimate statements needed (assuming similar ratio)
        if total > 0:
            statements_needed = int((gap / 100) * total)
            print(f"\nGap to 80%:    {gap:.2f}% ({statements_needed:,} statements)")
    
    # Per-file statistics
    files = data.get('files', {})
    if files:
        print("\n" + "=" * 70)
        print("MODULE COVERAGE (Top 20 Lowest)")
        print("=" * 70)
        
        # Collect modules with coverage data
        module_stats = []
        for filepath, file_data in files.items():
            if 'summary' in file_data:
                summary = file_data['summary']
                # Extract module name from path
                path_parts = filepath.replace('\\', '/').split('/')
                if 'smrforge' in path_parts:
                    idx = path_parts.index('smrforge')
                    module = '/'.join(path_parts[idx+1:])
                    if module.endswith('.py'):
                        module = module[:-3]
                    
                    # Skip excluded modules (per pytest.ini)
                    excluded_modules = [
                        'cli', 'gui', 'visualization', 'examples',
                        'convenience/transients', 'safety/transients', 'uncertainty/uq',
                        'core/endf_parser', 'core/endf_extractors',
                        'core/thermal_scattering_parser', 'core/photon_parser',
                        'core/gamma_production_parser', 'core/energy_angle_parser',
                        'core/fission_yield_parser', 'core/decay_parser',
                        'core/temperature_interpolation'
                    ]
                    
                    # Check if module should be excluded
                    should_exclude = False
                    for excluded in excluded_modules:
                        if module.startswith(excluded) or excluded in module:
                            should_exclude = True
                            break
                    
                    if not should_exclude:
                        module_stats.append((
                            summary.get('percent_covered', 0),
                            summary.get('missing_lines', 0),
                            summary.get('num_statements', 0),
                            module
                        ))
        
        # Sort by coverage (lowest first)
        module_stats.sort(key=lambda x: x[0])
        
        print(f"\n{'Module':<50} {'Coverage':<10} {'Missing':<10} {'Total':<10}")
        print("-" * 70)
        for coverage_pct, missing, total_statements, module in module_stats[:20]:
            print(f"{module:<50} {coverage_pct:>6.2f}%   {missing:>8}   {total_statements:>8}")
    
    print("\n" + "=" * 70)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        coverage_file = sys.argv[1]
    else:
        # Default to most recent coverage file
        coverage_file = 'coverage.json'
    
    analyze_coverage_file(coverage_file)
