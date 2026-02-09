# SMRForge Community — Examples

Examples for the **Community edition**. Each example lists workflow and required data.

---

## Quick Start (No Data Required)

| Example | Path | Description |
|---------|------|-------------|
| Quick k-eff | `../convenience_methods_example.py` | `quick_keff()`, `quick_keff_calculation()` |
| Preset designs | `../preset_designs.py` | `list_presets()`, `create_reactor()` |
| Help system | `../help_system_example.py` | Interactive help |

---

## Community Examples (by category)

### Neutronics
- `../basic_neutronics.py` — Multi-group diffusion, synthetic XS
- `../control_rods_example.py` — Control rod worth

### Burnup & Decay
- `../burnup_example.py` — Burnup solver, nuclide inventory
- `../decay_heat_example.py` — Decay heat from inventory

### Geometry & Mesh
- `../mesh_3d_example.py` — 3D mesh extraction
- `../geometry_import_example.py` — Geometry import
- `../custom_reactor.py` — Custom reactor creation

### Visualization
- `../visualization_3d_example.py` — 3D mesh plot
- `../visualization_examples.py` — 2D/3D plots
- `../openmc_visualization_examples.py` — Mesh tally, voxel, material viz (Community visualization APIs)

### Data & Nuclear
- `../data_downloader_example.py` — ENDF download
- `../thermal_scattering_example.py` — Thermal scattering
- `../tsl_file_discovery_example.py` — TSL discovery

### Workflows
- `../complete_integration_example.py` — End-to-end Community workflow
- `../complete_smr_workflow_example.py` — Full SMR analysis
- `../integrated_safety_uq.py` — Safety + UQ

### LWR & Thermal
- `../lwr_smr_example.py` — LWR SMR geometry
- `../thermal_analysis.py` — Thermal-hydraulics
- `../assembly_refueling_example.py` — Assembly refueling

### Convenience
- `../convenience_methods_example.py` — quick_keff, create_simple_*, get_nuclide
- `../preset_designs.py` — Presets
- `../help_system_example.py` — Help

---

## Required Data Summary

| Example | ENDF | Geometry | Other |
|---------|------|----------|-------|
| basic_neutronics | No | Synthetic | — |
| burnup_example | Optional | Yes | Time steps, power |
| preset_designs | No | Built-in | — |
| convenience_methods | No | Optional | — |
| data_downloader | No | No | Network |
| complete_smr_workflow | Yes | Yes | Full setup |

---

## Documentation

- [Community Feature Matrix](../../docs/community/community-feature-matrix.md)
- [Community Workflows](../../docs/community/community-workflows.md)
- [Community Examples Index](../../docs/guides/community/community-examples-index.md)
