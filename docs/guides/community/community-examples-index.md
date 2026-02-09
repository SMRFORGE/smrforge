# Community Tier — Examples Index

All Community edition examples with workflow and required data.

---

## Location

**Path:** `examples/community/`

---

## Quick Start

| Example | Workflow | Required Data |
|---------|----------|---------------|
| `basic_neutronics.py` | Multi-group k-eff | None (synthetic XS) |
| `preset_designs.py` | Preset reactors | None |
| `convenience_methods_example.py` | Convenience API | None |

---

## Neutronics

| Example | Description | Data |
|---------|-------------|------|
| `basic_neutronics.py` | Multi-group diffusion, power iteration | Synthetic XS |
| `control_rods_example.py` | Control rod worth | Geometry, XS |

---

## Burnup & Decay

| Example | Description | Data |
|---------|-------------|------|
| `burnup_example.py` | Burnup solver | Time steps, power |
| `decay_heat_example.py` | Decay heat | Inventory, cooling time |

---

## Geometry & Mesh

| Example | Description | Data |
|---------|-------------|------|
| `mesh_3d_example.py` | 3D mesh extraction | Core |
| `geometry_import_example.py` | Geometry import | Geometry file |
| `custom_reactor.py` | Custom reactor creation | Dimensions |

---

## Visualization

| Example | Description | Data |
|---------|-------------|------|
| `visualization_3d_example.py` | 3D mesh plot | Core, mesh |
| `visualization_examples.py` | 2D/3D plots | Core |

---

## Data & Nuclear

| Example | Description | Data |
|---------|-------------|------|
| `data_downloader_example.py` | ENDF download | Network |
| `thermal_scattering_example.py` | Thermal scattering | ENDF (S(α,β)) |
| `tsl_file_discovery_example.py` | TSL discovery | ENDF dir |

---

## Workflows

| Example | Description | Data |
|---------|-------------|------|
| `complete_integration_example.py` | End-to-end Community workflow | Optional ENDF |
| `complete_smr_workflow_example.py` | Full SMR analysis | ENDF, data |
| `integrated_safety_uq.py` | Safety + UQ | Reactor |

---

## Presets & Convenience

| Example | Description | Data |
|---------|-------------|------|
| `preset_designs.py` | List and create presets | None |
| `convenience_methods_example.py` | quick_keff, create_simple_* | None |
| `help_system_example.py` | Interactive help | None |

---

## LWR & Thermal

| Example | Description | Data |
|---------|-------------|------|
| `lwr_smr_example.py` | LWR SMR geometry | Dimensions |
| `thermal_analysis.py` | Thermal-hydraulics | Core, channel geometry |
| `assembly_refueling_example.py` | Assembly refueling | Core |
