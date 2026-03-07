"""
Serpent Run+Parse Example (Community)

Demonstrates SMRForge Community's Serpent round-trip:
- run_serpent(): Run Serpent 2 as subprocess
- parse_serpent_res(): Parse k-eff from _res.m file

Works with Pro-exported Serpent input. Full Serpent export is Pro tier.
Requires: Serpent 2 installed and in PATH.

Run: python examples/serpent_run_example.py
"""

from pathlib import Path

from smrforge.io import run_serpent, parse_serpent_res


def main():
    print("SMRForge Community — Serpent Run+Parse Example")
    print("=" * 50)

    # Create a minimal Serpent input for demo (or use Pro-exported input)
    work_dir = Path("output/serpent_run_demo")
    work_dir.mkdir(parents=True, exist_ok=True)

    # Minimal Serpent 2 input (pin cell)
    input_file = work_dir / "demo.sss"
    input_file.write_text("""
% --- Minimal Serpent 2 pin cell ---
set title "SMRForge demo"
set acel "sss_endfb71"
set bc 1
pin 1
fuel 1 1.0
cell 1 0 fuel -1
cell 2 0 moder 1 -2
cell 3 0 outside 2
surf 1 cyl 0.4
surf 2 cyl 1.26
""")

    print(f"\n1. Running Serpent 2: {input_file.name}")
    proc = run_serpent(work_dir, input_file.name, timeout=120)
    if proc.returncode != 0:
        print(f"   Serpent exited with code {proc.returncode}")
        print("   (Install Serpent 2 and set cross-section path to run)")
        return

    res_file = work_dir / "demo_res.m"
    if not res_file.exists():
        print(f"   No _res.m file found at {res_file}")
        return

    print("\n2. Parsing results")
    parsed = parse_serpent_res(res_file)
    k = parsed.get("k_eff")
    if isinstance(k, (int, float)):
        print(f"   k_eff: {k:.6f}")
    else:
        print(f"   k_eff: {k}")
    if "k_eff_std" in parsed:
        print(f"   k_eff_std: {parsed['k_eff_std']:.6f}")
    print("\nDone.")


if __name__ == "__main__":
    main()
