"""
SMRForge Pro — Natural-Language Reactor Design Example

Parse natural-language design intent (e.g., "10 MW HTGR with k-eff 1.0-1.05,
enrichment <20%") and produce a reactor spec with optional analysis.

Workflow:
  1. Parse text with parse_nl_design()
  2. Create reactor with design_from_nl()
  3. Optionally run neutronics analysis

Required: Pro license
Output: Reactor spec, intent dict, optional analysis results
"""


def main():
    try:
        from smrforge_pro.ai.nl_design import design_from_nl, parse_nl_design
    except ImportError:
        print("SMRForge Pro is required for natural-language design.")
        print("Install: pip install smrforge-pro")
        return 1

    print("=" * 60)
    print("SMRForge Pro — Natural-Language Design Example")
    print("=" * 60)

    # 1. Parse intent from text
    text = "10 MW HTGR with k-eff 1.0-1.05, enrichment <20%"
    print(f"\n1. Parsing: '{text}'")
    intent = parse_nl_design(text)
    print(f"   Power (MW): {intent.get('power_mw')}")
    print(f"   Enrichment: {intent.get('enrichment')}")
    print(f"   k-eff range: {intent.get('keff_range')}")
    print(f"   Preset: {intent.get('preset')}")

    # 2. Create reactor from natural language
    print("\n2. Creating reactor from NL (run_analysis=True)...")
    result = design_from_nl("valar-10 preset", run_analysis=True)
    print(f"   Spec: {result.spec.name if hasattr(result.spec, 'name') else 'reactor'}")
    if result.analysis:
        k = result.analysis.get("k_eff")
        print(f"   k_eff: {k}")

    # 3. Create without running analysis
    print("\n3. Create without analysis (run_analysis=False)...")
    result2 = design_from_nl("10 MW HTGR", run_analysis=False)
    assert result2.analysis is None
    print("   OK (spec only)")

    print("\n" + "=" * 60)
    return 0


if __name__ == "__main__":
    exit(main())
