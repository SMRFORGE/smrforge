#!/usr/bin/env python3
"""
Validation test runner script.

This script runs comprehensive validation tests with real ENDF files and
generates validation reports with timing and benchmarking results.

Usage:
    python scripts/run_validation.py [--endf-dir PATH] [--benchmarks benchmarks.json] [--output REPORT.txt] [--json-output RESULTS.json] [--verbose]
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import platform
import pytest
import json
from datetime import datetime


def _to_jsonable(obj):
    """Best-effort JSON conversion for common types."""
    try:
        import numpy as np
    except Exception:  # pragma: no cover
        np = None

    if np is not None:
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.generic):
            return obj.item()
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, dict):
        return {str(k): _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_to_jsonable(v) for v in obj]
    return obj


def _result_to_dict(result):
    timing = None
    if getattr(result, "timing", None) is not None:
        timing = {
            "name": getattr(result.timing, "name", None),
            "elapsed_time": getattr(result.timing, "elapsed_time", None),
            "iterations": getattr(result.timing, "iterations", None),
            "average_time": getattr(result.timing, "average_time", None),
            "metadata": getattr(result.timing, "metadata", None),
        }
    return {
        "test_name": getattr(result, "test_name", None),
        "passed": bool(getattr(result, "passed", False)),
        "message": getattr(result, "message", ""),
        "timing": timing,
        "metrics": _to_jsonable(getattr(result, "metrics", {}) or {}),
        "comparison_data": _to_jsonable(getattr(result, "comparison_data", None)),
    }

def main():
    parser = argparse.ArgumentParser(
        description="Run validation tests with ENDF files and generate reports"
    )
    parser.add_argument(
        "--endf-dir",
        type=Path,
        help="Path to ENDF-B-VIII.1 directory",
        default=None
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file for validation report (default: validation_report_YYYYMMDD_HHMMSS.txt)",
        default=None
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        help="Output file for JSON results (optional)",
        default=None
    )
    parser.add_argument(
        "--benchmarks",
        type=Path,
        help="Benchmark database JSON file (optional)",
        default=None,
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--tests",
        nargs="+",
        help="Specific test files or patterns to run (default: all validation tests)",
        default=None
    )
    
    args = parser.parse_args()
    
    # Set ENDF directory if provided
    if args.endf_dir:
        endf_abs = str(args.endf_dir.absolute())
        # Keep both env vars for compatibility (tests/scripts vs core auto-detection)
        os.environ["LOCAL_ENDF_DIR"] = endf_abs
        os.environ["SMRFORGE_ENDF_DIR"] = endf_abs
        print(f"Using ENDF directory: {args.endf_dir}")
    
    # Determine output file
    if args.output is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = Path(f"validation_report_{timestamp}.txt")

    # Determine JSON output file
    if args.json_output is None:
        try:
            args.json_output = args.output.with_suffix(".json")
        except Exception:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            args.json_output = Path(f"validation_results_{timestamp}.json")
    
    # Determine which tests to run
    if args.tests is None:
        test_files = [
            "tests/test_validation_comprehensive.py",
            "tests/test_endf_workflows_e2e.py",
        ]
    else:
        test_files = args.tests
    
    print("=" * 80)
    print("SMRForge Validation Test Runner")
    print("=" * 80)
    print(f"Output file: {args.output}")
    print(f"Test files: {', '.join(test_files)}")
    print()
    
    # Build pytest command
    pytest_args = [
        *test_files,
        "-v",
        "--tb=short",
    ]
    
    if args.verbose:
        pytest_args.append("-s")
    
    # Run tests
    print("Running validation tests...")
    exit_code = pytest.main(pytest_args)

    # Generate standardized JSON + report (independent of captured pytest output)
    print("\nGenerating validation report artifacts...")
    results_payload = {
        "metadata": {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "platform": platform.platform(),
            "python": sys.version,
            "cwd": str(Path.cwd()),
            "endf_dir": os.environ.get("SMRFORGE_ENDF_DIR") or os.environ.get("LOCAL_ENDF_DIR"),
            "benchmarks_file": str(args.benchmarks) if args.benchmarks else None,
        },
        "pytest_exit_code": int(exit_code),
        "results": [],
    }

    # Attach ENDF inventory (best-effort)
    try:
        from smrforge.core.reactor_core import scan_endf_directory

        endf_dir = os.environ.get("SMRFORGE_ENDF_DIR") or os.environ.get("LOCAL_ENDF_DIR")
        if endf_dir:
            results_payload["metadata"]["endf_inventory"] = scan_endf_directory(Path(endf_dir))
    except Exception as e:
        results_payload["metadata"]["endf_inventory_error"] = str(e)

    # Run structured validations/benchmarks (best-effort; does not affect pytest exit code)
    try:
        from smrforge.core.reactor_core import NuclearDataCache
        from smrforge.geometry import PrismaticCore
        from smrforge.validation.models import CrossSectionData, SolverOptions
        from smrforge.neutronics.solver import MultiGroupDiffusion
        from smrforge.burnup import BurnupOptions
        from smrforge.core.reactor_core import Nuclide
        from tests.validation_benchmarks import ValidationBenchmarker
        from tests.validation_benchmark_data import BenchmarkDatabase
        import numpy as np

        endf_dir = os.environ.get("SMRFORGE_ENDF_DIR") or os.environ.get("LOCAL_ENDF_DIR")
        cache = NuclearDataCache(local_endf_dir=Path(endf_dir)) if endf_dir else NuclearDataCache()
        benchmark_db = None
        if args.benchmarks and args.benchmarks.exists():
            benchmark_db = BenchmarkDatabase(args.benchmarks)

        bench = ValidationBenchmarker(cache, benchmark_database=benchmark_db)

        # TSL
        try:
            materials = cache.list_available_tsl_materials()
            for material in (materials[:3] if materials else []):
                bench.results.append(
                    bench.validate_tsl_interpolation_accuracy(
                        material, temperatures=[293.6, 400.0, 600.0, 900.0]
                    )
                )
        except Exception as e:
            results_payload["metadata"]["tsl_validation_error"] = str(e)

        # Fission yields
        for nuclide in [Nuclide(Z=92, A=235), Nuclide(Z=92, A=238), Nuclide(Z=94, A=239)]:
            try:
                bench.results.append(bench.validate_fission_yield_parser(nuclide))
            except Exception as e:
                results_payload["metadata"][f"fission_yield_validation_error_{nuclide}"] = str(e)

        # Decay heat
        try:
            nuclides = {
                Nuclide(Z=92, A=235): 1e20,
                Nuclide(Z=55, A=137): 1e19,
                Nuclide(Z=38, A=90): 1e19,
            }
            times = np.array([0, 3600, 86400, 604800, 2592000], dtype=float)
            bench.results.append(bench.validate_decay_heat_ans_standard(nuclides, times))
        except Exception as e:
            results_payload["metadata"]["decay_heat_validation_error"] = str(e)

        # Gamma transport
        try:
            geometry = PrismaticCore(name="ValidationShielding")
            geometry.core_height = 200.0
            geometry.core_diameter = 100.0
            geometry.generate_mesh(n_radial=5, n_axial=3)
            bench.results.append(bench.benchmark_gamma_transport(geometry, n_groups=20))
        except Exception as e:
            results_payload["metadata"]["gamma_transport_validation_error"] = str(e)

        # Burnup reference (structure)
        try:
            geometry = PrismaticCore(name="ValidationBurnup")
            geometry.core_height = 100.0
            geometry.core_diameter = 50.0
            geometry.generate_mesh(n_radial=3, n_axial=2)
            burnup_options = BurnupOptions(time_steps=[0, 30, 60, 90], initial_enrichment=0.195)
            bench.results.append(bench.validate_burnup_reference(geometry, burnup_options))
        except Exception as e:
            results_payload["metadata"]["burnup_validation_error"] = str(e)

        # k_eff benchmark against benchmark database (if provided)
        if benchmark_db and benchmark_db.burnup_benchmarks:
            try:
                # Deterministic, simple 2-group benchmark (regression-style reference)
                geometry = PrismaticCore(name="BenchmarkCore")
                geometry.core_height = 100.0
                geometry.core_diameter = 50.0
                geometry.generate_mesh(n_radial=5, n_axial=3)

                xs_data = CrossSectionData(
                    n_groups=2,
                    n_materials=1,
                    sigma_t=np.array([[0.5, 0.8]]),
                    sigma_a=np.array([[0.1, 0.2]]),
                    sigma_f=np.array([[0.05, 0.15]]),
                    nu_sigma_f=np.array([[0.125, 0.375]]),
                    sigma_s=np.array([[[0.39, 0.01], [0.0, 0.58]]]),
                    chi=np.array([[1.0, 0.0]]),
                    D=np.array([[1.5, 0.4]]),
                )
                solver = MultiGroupDiffusion(geometry, xs_data, SolverOptions(max_iterations=50, tolerance=1e-5))
                k_eff, _ = solver.solve_steady_state()

                # Prefer a specifically named benchmark if present, else first entry
                benchmark_key = "simple_neutronics_2g"
                if benchmark_key in benchmark_db.burnup_benchmarks:
                    bm = benchmark_db.burnup_benchmarks[benchmark_key]
                else:
                    bm = next(iter(benchmark_db.burnup_benchmarks.values()))

                bench.results.append(bench.benchmark_k_eff([float(k_eff)], bm, tolerance=0.01))
            except Exception as e:
                results_payload["metadata"]["k_eff_benchmark_error"] = str(e)

        # Write artifacts
        results_payload["results"] = [_result_to_dict(r) for r in getattr(bench, "results", [])]
        args.json_output.write_text(json.dumps(_to_jsonable(results_payload), indent=2))
        bench.generate_report(output_file=args.output)
        print(f"JSON results saved to: {args.json_output}")
        print(f"Text report saved to: {args.output}")
    except Exception as e:
        # If structured reporting fails, still emit minimal JSON
        results_payload["metadata"]["report_generation_error"] = str(e)
        args.json_output.write_text(json.dumps(_to_jsonable(results_payload), indent=2))
        print(f"WARNING: Structured reporting failed: {e}")
        print(f"Minimal JSON results saved to: {args.json_output}")
    
    print()
    print("=" * 80)
    print(f"Validation tests completed. Exit code: {exit_code}")
    print(f"Check test output above for results.")
    print(f"Artifacts: report={args.output} json={args.json_output}")
    print("=" * 80)
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
