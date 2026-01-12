"""
SMRForge Dashboard Example

Demonstrates how to use the SMRForge web dashboard programmatically
while maintaining CLI compatibility.
"""

import smrforge as smr

print("=" * 70)
print("SMRFORGE DASHBOARD EXAMPLE")
print("=" * 70)
print("\nThis example demonstrates:")
print("  1. Launching the dashboard")
print("  2. Using CLI/Python API (same features)")
print("  3. Integration between dashboard and CLI")
print("\n" + "=" * 70 + "\n")

# Option 1: Launch Dashboard
print("OPTION 1: Launch Dashboard")
print("-" * 70)
print("\nTo launch the dashboard, run:")
print("  smrforge serve")
print("\nOr from Python:")
print("  from smrforge.gui import run_server")
print("  run_server()")
print("\nDashboard will be available at: http://127.0.0.1:8050")
print("\n" + "=" * 70 + "\n")

# Option 2: Use CLI/Python API (same features)
print("OPTION 2: Use CLI/Python API (Same Features)")
print("-" * 70)

# Create reactor (same as dashboard)
print("\n1. Create Reactor (CLI equivalent of dashboard):")
reactor = smr.create_reactor("valar-10")
print(f"   ✓ Created reactor: {reactor.spec.name}")
print(f"   Power: {reactor.spec.power_thermal / 1e6:.1f} MWth")

# Run analysis (same as dashboard)
print("\n2. Run Neutronics Analysis (CLI equivalent of dashboard):")
k_eff = reactor.solve_keff()
print(f"   ✓ k-effective: {k_eff:.6f}")

# Complete analysis
print("\n3. Run Complete Analysis:")
results = reactor.solve()
print(f"   ✓ Analysis complete")
print(f"   k-eff: {results['k_eff']:.6f}")
print(f"   Power: {results['power_thermal_mw']:.1f} MWth")

# Data download (same as dashboard)
print("\n4. Download ENDF Data (CLI equivalent of dashboard):")
try:
    from smrforge.data_downloader import download_endf_data
    print("   (Skipping actual download in example)")
    print("   CLI command:")
    print("   from smrforge.data_downloader import download_endf_data")
    print("   stats = download_endf_data(library='ENDF/B-VIII.1', nuclide_set='common_smr')")
except ImportError:
    print("   ⚠ Data downloader not available")

# Visualization (same as dashboard)
print("\n5. Visualize Results (CLI equivalent of dashboard):")
try:
    from smrforge.visualization import plot_core_layout_2d
    import matplotlib.pyplot as plt
    print("   ✓ Visualization available")
    print("   CLI command:")
    print("   from smrforge.visualization import plot_core_layout_2d")
    print("   plot_core_layout_2d(reactor.core)")
except ImportError:
    print("   ⚠ Visualization not available")

print("\n" + "=" * 70)
print("KEY POINT: Dashboard and CLI use the SAME functions!")
print("=" * 70)
print("\nAll features available in dashboard are also available via:")
print("  - Python API: import smrforge as smr")
print("  - CLI commands: smrforge serve")
print("  - Direct function calls")
print("\nChoose the interface that works best for your workflow!")
print("\n" + "=" * 70)
