"""
SMRForge Pro — One-Click Benchmark Reproduction Example

Reproduce built-in benchmarks: run, compare to reference, produce report.

Workflow:
  1. List benchmarks with list_benchmarks()
  2. Reproduce with reproduce_benchmark(id)
  3. Check report.json for differences

Required: Pro license, smrforge
Output: report.json, calculated vs reference
"""


def main():
    try:
        from smrforge_pro.workflows.benchmark_reproduction import (
            list_benchmarks,
            reproduce_benchmark,
        )
    except ImportError:
        print("SMRForge Pro is required for benchmark reproduction.")
        print("Install: pip install smrforge-pro")
        return 1

    from pathlib import Path

    print("=" * 60)
    print("SMRForge Pro — Benchmark Reproduction Example")
    print("=" * 60)

    print("\n1. Available benchmarks:")
    ids = list_benchmarks()
    for bid in ids:
        print(f"   {bid}")

    output_dir = Path("benchmark_reproduction_output")
    bid = ids[0]
    print(f"\n2. Reproducing '{bid}'...")
    result = reproduce_benchmark(bid, output_dir=output_dir)

    print(f"   Reference: {result.reference}")
    print(f"   Calculated: {result.calculated}")
    print(f"   Passed: {result.passed}")
    print(f"   Output: {result.output_dir / 'report.json'}")

    print("\n" + "=" * 60)
    return 0


if __name__ == "__main__":
    exit(main())
