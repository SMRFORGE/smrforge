"""
SMRForge Pro — Code-to-Code Verification Example

Run the same reactor through SMRForge diffusion, built-in MC, OpenMC, Serpent,
MCNP and produce a unified comparison report.

Workflow:
  1. Create reactor (preset or custom)
  2. Call run_code_verification()
  3. Inspect VerificationReport, save JSON

Required: Pro license, smrforge
Output: verification_report.json, per-code exports
"""


def main():
    try:
        from smrforge_pro.workflows.code_verification import run_code_verification
    except ImportError:
        print("SMRForge Pro is required for code verification.")
        print("Install: pip install smrforge-pro")
        return 1

    from pathlib import Path

    print("=" * 60)
    print("SMRForge Pro — Code-to-Code Verification Example")
    print("=" * 60)

    output_dir = Path("code_verification_output")
    print(f"\n1. Running verification (output: {output_dir})...")
    report = run_code_verification("valar-10", output_dir=output_dir)

    print(f"\n2. Reactor: {report.reactor_name}")
    print("   Results:")
    for r in report.results:
        status = "OK" if r.k_eff is not None else ("N/A" if r.available else "skipped")
        k = r.k_eff if r.k_eff is not None else "—"
        print(f"     {r.code}: k_eff={k} ({status})")

    jf = output_dir / "verification_report.json"
    report.save_json(jf)
    print(f"\n3. Report saved to {jf}")

    print("=" * 60)
    return 0


if __name__ == "__main__":
    exit(main())
