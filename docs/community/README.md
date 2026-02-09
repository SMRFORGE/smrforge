# SMRForge Community Edition — Documentation

**Tier:** Community (free, open-source)  
**Scope:** Core reactor physics, multi-group diffusion, burnup, geometry, presets, validation, and visualization.

---

## Community Tier Feature Overview

The Community edition provides a complete toolkit for SMR design and analysis using built-in multi-group diffusion solvers, geometry libraries, and nuclear data handling. No external Monte Carlo codes are required.

| Category | Features |
|----------|----------|
| **Neutronics** | Multi-group diffusion (2–70 groups), power iteration, Arnoldi eigenvalue solver |
| **Nuclear Data** | ENDF parsing (via endf-parserpy/SANDY or built-in), resonance self-shielding, fission yields |
| **Geometry** | PrismaticCore, PebbleBedCore, LWR SMR cores, mesh extraction, 3D meshes |
| **Burnup** | Bateman solver, nuclide inventory, decay chains, power history |
| **Decay Heat** | Post-shutdown decay heat from inventory |
| **Thermal** | Channel thermal-hydraulics, lumped models, two-phase flow |
| **Validation** | Constraint sets, safety margin reports, scenario design |
| **Presets** | Valar-10, GT-MHR, HTR-PM, Micro-HTGR, LWR SMR designs |
| **Workflows** | Design point, parameter sweep, Pareto report, scenario design, atlas |

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
