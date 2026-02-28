"""
Example demonstrating SMRForge discovery and help functions.

Shows system_info(), help_topics(), list_*(), get_example_path(),
check_setup(), get_cheat_sheet(), list_cli_commands(), suggest_next_steps(),
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
    print("  list_endf_libraries:", smr.list_endf_libraries())
    print("  list_geometry_types:", smr.list_geometry_types())
    print("  list_analysis_types:", smr.list_analysis_types())
    print("  list_surrogates:", smr.list_surrogates())

    # 4. Example path
    print("\n4. Example path:")
    print("-" * 70)
    path = smr.get_example_path("reactor")
    print(f"  get_example_path('reactor') -> {path}")

    # 5. Default directories and paths
    print("\n5. Default directories and data paths:")
    print("-" * 70)
    print(f"  get_default_output_dir: {smr.get_default_output_dir()}")
    print(f"  get_default_endf_dir: {smr.get_default_endf_dir()}")
    paths = smr.get_data_paths()
    print(f"  get_data_paths keys: {list(paths.keys())}")
    print(f"  find_endf_directory: {smr.find_endf_directory()}")

    # 5b. Help and setup functions
    print("\n5b. Help and setup:")
    print("-" * 70)
    setup = smr.check_setup()
    print(f"  check_setup ok: {setup.get('ok')}, checks: {[c['name'] for c in setup.get('checks', [])]}")
    print(f"  list_cli_commands (first 3): {[c['command'] for c in smr.list_cli_commands()[:3]]}")
    print(f"  get_quick_start_commands: {len(smr.get_quick_start_commands())} suggestions")
    print(f"  suggest_next_steps('quick_keff'): {smr.suggest_next_steps('quick_keff')}")
    print(f"  get_cheat_sheet (first line): {smr.get_cheat_sheet().split(chr(10))[0]}")

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
        print(
            f"  enrichment={r['parameters']['enrichment']:.2f} -> k_eff={r['k_eff']:.4f}"
        )

    # 8. Quick economics (optional display=True for Rich summary)
    print("\n8. Quick economics:")
    print("-" * 70)
    costs = smr.quick_economics(path)
    print(f"  LCOE: ${costs.get('lcoe', 0):.2f}/kWh")

    # 9. Quick optimize (small run; optional display=True)
    print("\n9. Quick optimize (enrichment bounds):")
    print("-" * 70)
    opt = smr.quick_optimize(path, {"enrichment": (0.18, 0.22)}, max_iter=3)
    print(f"  Best k_eff: {opt.get('best_k_eff', 'N/A')}")

    # 10. Quick UQ (optional display=True)
    print("\n10. Quick UQ (enrichment uncertainty):")
    print("-" * 70)
    uq = smr.quick_uq(
        path,
        [
            {
                "name": "enrichment",
                "nominal": 0.195,
                "distribution": "normal",
                "uncertainty": 0.02,
            }
        ],
        n_samples=20,
    )
    mean_val = uq.get("k_eff_mean")
    if isinstance(mean_val, (int, float)):
        print(f"  k_eff mean: {mean_val:.4f}")
    else:
        print(f"  UQ result keys: {list(uq.keys())}")

    print("\n" + "=" * 70)
    print("Try: smr.help('convenience') for full list")
    print("Try: smr.get_cheat_sheet() for quick reference")
    print("Try: smr.check_setup() to verify environment")
    print("=" * 70)


if __name__ == "__main__":
    main()
