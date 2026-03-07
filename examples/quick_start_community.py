"""
Quick Start — SMRForge Community (5 lines)

Minimal workflow to get k-eff from a preset reactor. No ENDF data required.
Run: python examples/quick_start_community.py
"""

import smrforge as smr

reactor = smr.create_reactor("valar-10")
core = reactor.build_core()
k_eff, flux = smr.quick_keff_calculation(core=core)
print(f"k-eff: {k_eff:.6f}")
