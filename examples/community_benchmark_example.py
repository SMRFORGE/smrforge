"""
Community Benchmark Example

Runs SMRForge Community benchmark cases and generates a report.
Demonstrates validation against regression baselines.

For a full benchmark suite (10+ cases) with automated comparison,
see SMRForge Pro.
"""

from pathlib import Path

import smrforge as smr
from smrforge.benchmarks import CommunityBenchmarkRunner


def main():
    print("SMRForge Community Benchmark Suite")
    print("=" * 50)

    runner = CommunityBenchmarkRunner()
    cases = runner.list_cases()
    print(f"Available cases: {cases}")

    print("\nRunning benchmarks...")
    results = runner.run_all()

    for case_id, (passed, value, err) in results.items():
        status = "PASS" if passed else "FAIL"
        msg = f"  {err}" if err else ""
        print(f"  {case_id}: {status} (k_eff={value:.6f}){msg}")

    # Generate report (output/ keeps root clean)
    out_dir = Path("output")
    out_dir.mkdir(exist_ok=True)
    report_path = out_dir / "community_benchmark_report.md"
    runner.generate_report(results=results, output_path=report_path)
    print(f"\nReport saved to {report_path}")

    # Also demonstrate report generator
    print("\n--- Design Report Example ---")
    design_results = smr.analyze_preset("valar-10")
    from smrforge.reporting import generate_markdown_report

    generate_markdown_report(
        design_results,
        title="Valar-10 Design Summary",
        output_path=out_dir / "design_summary_example.md",
    )
    print(f"Design summary saved to {out_dir / 'design_summary_example.md'}")


if __name__ == "__main__":
    main()
