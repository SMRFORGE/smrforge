#!/usr/bin/env python3
"""
Run V&V (Verification & Validation) benchmarks and generate a report.

Produces a markdown report comparing SMRForge results against reference
benchmarks. Used for safety-critical V&V documentation (SC-1).

Usage:
    python scripts/run_vv_benchmarks.py
    python scripts/run_vv_benchmarks.py --output vv_report.md
"""

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run V&V benchmarks and generate report (SC-1)"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("vv_benchmark_report.md"),
        help="Output report path",
    )
    args = parser.parse_args()

    try:
        from smrforge.benchmarks import CommunityBenchmarkRunner
    except ImportError:
        print("ERROR: smrforge.benchmarks not found. Install SMRForge.")
        return 1

    runner = CommunityBenchmarkRunner()
    cases = runner.list_cases()
    if not cases:
        print("No benchmark cases found.")
        return 1

    print(f"Running {len(cases)} V&V benchmark cases...")
    results = runner.run_all()

    passed = sum(1 for p, _, _ in results.values() if p)
    total = len(results)
    runner.generate_report(results=results, output_path=args.output)

    print(f"V&V complete: {passed}/{total} passed")
    print(f"Report saved to {args.output}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
