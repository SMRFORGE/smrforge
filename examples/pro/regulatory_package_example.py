"""
SMRForge Pro — Regulatory Submission Package Example

Generate an NRC/IAEA-ready submission package:
  - Inputs and outputs in required formats
  - Traceability matrices
  - Uncertainty and margin documentation

Workflow:
  1. Create or load reactor
  2. Call generate_regulatory_package()
  3. Use package for regulatory submission

Required: Pro license, smrforge
Output: inputs.json, outputs.json, traceability_matrix.json, README.md
"""


def main():
    try:
        from smrforge.convenience import create_reactor
        from smrforge_pro.workflows.regulatory_package import (
            RegulatoryPackageConfig,
            generate_regulatory_package,
        )
    except ImportError as e:
        print("SMRForge Pro and smrforge required for regulatory package.")
        print("Install: pip install smrforge smrforge-pro")
        print(f"Error: {e}")
        return 1

    from pathlib import Path

    print("=" * 60)
    print("SMRForge Pro — Regulatory Package Example")
    print("=" * 60)

    reactor = create_reactor("valar-10")
    output_dir = Path("regulatory_package_output")
    config = RegulatoryPackageConfig(framework="NRC", include_uncertainty=True)

    print(f"\n1. Generating package (output: {output_dir})...")
    path = generate_regulatory_package(
        reactor, output_dir=output_dir, config=config
    )

    print("\n2. Package contents:")
    for f in sorted(path.iterdir()):
        print(f"   {f.name}")

    print("\n" + "=" * 60)
    return 0


if __name__ == "__main__":
    exit(main())
