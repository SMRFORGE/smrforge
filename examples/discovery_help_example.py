"""
Example demonstrating SMRForge discovery and help functions.

Shows system_info(), help_topics(), list_*(), get_example_path(),
quick_sweep, quick_economics, quick_optimize, quick_uq, etc.
"""

import smrforge as smr


def main():
    """Demonstrate discovery and help functions."""
    print("=" * 70)
    print("SMRForge Discovery & Help Functions")
    print("=" * 70)

    # 1. System info (with optional Rich display)
    print("\n1. System info (version and available features):")
    print("-" * 70)
    info = smr.system_info(display=True)
    for k, v in sorted(info.items()):
        print(f"  {k}: {v}")

    # 2. Help topics
    print("\n2. Help topics (smr.help('topic')):")
    print("-" * 70)
    topics = smr.help_topics()
    print(f"  {topics[:6]}...")

    # 3. Discovery functions
    print("\n3. Discovery functions:")
    print("-" * 70)
    print("  list_presets:", smr.list_presets()[:4], "...")
    print("  list_reactor_types:", smr.list_reactor_types())
    print("  list_fuel_types:", smr.list_fuel_types())
    print("  list_constraint_sets:", smr.list_constraint_sets())
    print("  list_sweepable_params (first 5):", smr.list_sweepable_params()[:5])
    print("  list_nuclides (first 5):", smr.list_nuclides()[:5])
    print("  list_examples (first 5):", smr.list_examples()[:5])

    # 4. Example path
    print("\n4. Example path:")
    print("-" * 70)
    path = smr.get_example_path("reactor")
    print(f"  get_example_path('reactor') -> {path}")

    # 5. Default output dir
    print("\n5. Default output directory:")
    print("-" * 70)
    print(f"  {smr.get_default_output_dir()}")

    # 6. Load and run from example
    print("\n6. Load reactor from example and solve k-eff:")
    print("-" * 70)
    reactor = smr.load_reactor(path)
    k = reactor.solve_keff()
    print(f"  k_eff = {k:.6f}")

    # 7. Quick sweep (small)
    print("\n7. Quick sweep (2 enrichment points):")
    print("-" * 70)
    out = smr.quick_sweep(path, {"enrichment": [0.18, 0.20]}, analysis="keff")
    for r in out["results"]:
        print(f"  enrichment={r['parameters']['enrichment']:.2f} -> k_eff={r['k_eff']:.4f}")

    # 8. Quick economics
    print("\n8. Quick economics:")
    print("-" * 70)
    costs = smr.quick_economics(path)
    print(f"  LCOE: ${costs.get('lcoe', 0):.2f}/kWh")

    print("\n" + "=" * 70)
    print("Try: smr.help('convenience') for full list")
    print("=" * 70)


if __name__ == "__main__":
    main()
