# SMRForge Community Edition — Documentation

**Tier:** Community (free, open-source)  
**Scope:** Core reactor physics, multi-group diffusion, burnup, decay heat, gamma transport, geometry, presets, validation, economics, fuel cycle, and visualization.

> **Pro:** For Serpent/MCNP export, full benchmark suite, PDF reports with traceability, OpenMC tally visualization, AI/surrogate workflows, and more, see [Community vs Pro](../community_vs_pro.md). Pro lives in [github.com/SMRFORGE/smrforge-pro](https://github.com/SMRFORGE/smrforge-pro). Community includes full OpenMC export/import and Serpent run+parse.

---

## Community Tier Feature Overview

The Community edition provides a complete toolkit for SMR design and analysis using built-in multi-group diffusion solvers, geometry libraries, and nuclear data handling. No external Monte Carlo codes are required.

| Category | Features |
|----------|----------|
| **Neutronics** | Multi-group diffusion (2–70 groups), power iteration, Arnoldi eigenvalue solver; reactivity coefficients (Doppler, temperature-dependent XS); built-in Monte Carlo; Serpent run+parse |
| **Nuclear Data** | ENDF parsing (via endf-parserpy/SANDY or built-in), resonance self-shielding, fission yields, decay parser (half-life, gamma/beta spectra), thermal scattering (MF=7), gamma production |
| **Geometry** | PrismaticCore, PebbleBedCore, LWR SMR cores, mesh extraction, 3D meshes; control rods; assembly management; SMR fuel management; advanced import (OpenMC CSG, Serpent, CAD STEP/IGES/STL) |
| **Burnup** | Bateman solver, nuclide inventory, decay chains, fission yields, composition-dependent XS, parameter sweep burnup |
| **Decay Heat** | Time-dependent decay heat; gamma/beta spectrum integration from ENDF; post-shutdown analysis; `quick_decay_heat`, `smrforge decay calculate` |
| **Gamma Transport** | Multi-group gamma diffusion; dose rate; shielding calculations |
| **Thermal** | Channel thermal-hydraulics, lumped models, two-phase flow (drift flux, two-fluid) |
| **Transients** | Point kinetics; LOFC, ATWS, RIA, LOCA; decay heat removal; reactivity insertion |
| **Validation** | Constraint sets, safety margin reports, scenario design |
| **Economics** | Capital cost, operating cost, LCOE, nth-of-a-kind; `quick_economics` |
| **Fuel Cycle** | FuelCycleOptimizer, RefuelingStrategyOptimizer, MaterialAging, LongTermThermalCoupling |
| **UQ & Optimization** | Parameter sweep (keff, burnup, transient, economics); design optimization; UQ (Monte Carlo, LHS, Sobol); `quick_uq`, `quick_optimize` |
| **Presets** | Valar-10, GT-MHR, HTR-PM, Micro-HTGR; NuScale 77 MWe, SMART 100 MWe, CAREM 32 MWe, BWRX-300 |
| **Workflows** | Design point, parameter sweep, Pareto report, scenario design, atlas; DOE, sensitivity, Sobol |
| **I/O** | Full OpenMC export/import with statepoint HDF5 parsing; Serpent run+parse; basic Markdown reports; 3 community benchmark cases |

---

## Quick Navigation

- [Community Feature Matrix](community-feature-matrix.md) — Feature-by-feature breakdown with workflows and required data
- [Community Workflows Guide](community-workflows.md) — Step-by-step workflows
- [Community API Quick Reference](community-api-quick-reference.md) — Key modules and functions
- [Community Examples Index](../guides/community/community-examples-index.md)

---

## Installation (Community)

```bash
pip install smrforge
```

Optional for ENDF data fetching: `endf-parserpy` or `sandy` (see [Nuclear Data Setup](community-nuclear-data-setup.md)).

---

## Getting Started

1. **Tutorial:** [docs/guides/community/tutorial.md](../guides/community/tutorial.md)
2. **CLI Quickstart:** [docs/guides/cli-guide.md](../guides/cli-guide.md)
3. **Examples:** `examples/community/`
