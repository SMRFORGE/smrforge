# Usage Examples and API Documentation Update

**Date:** 2024-12-28  
**Status:** ✅ Complete

---

## Usage Examples Added

### 1. `examples/visualization_examples.py`
Demonstrates geometry visualization capabilities:
- Prismatic core layout plots (top view, side views)
- Pebble bed core layout plots
- Flux distribution overlays
- Power distribution visualization
- Temperature distribution plots

**Key Functions:**
- `plot_core_layout()` - Core geometry visualization
- `plot_flux_on_geometry()` - Flux overlay
- `plot_power_distribution()` - Power visualization
- `plot_temperature_distribution()` - Temperature plots

### 2. `examples/control_rods_example.py`
Demonstrates control rod management:
- Single control rod creation and manipulation
- Control rod bank operations (insertion, withdrawal, scram)
- Complete control rod system management
- Reactivity worth calculations
- Shutdown margin analysis

**Key Classes:**
- `ControlRod` - Individual control rod
- `ControlRodBank` - Group of rods operated together
- `ControlRodSystem` - Complete control system

### 3. `examples/assembly_refueling_example.py`
Demonstrates assembly management and refueling:
- Single assembly tracking (burnup, age, depletion)
- Refueling pattern creation and validation
- Assembly manager operations
- Shuffle and refueling operations
- Cycle length estimation

**Key Classes:**
- `Assembly` - Fuel assembly with burnup tracking
- `RefuelingPattern` - Multi-batch refueling patterns
- `AssemblyManager` - Complete assembly management

### 4. `examples/geometry_import_example.py`
Demonstrates geometry import/export:
- Export prismatic cores to JSON
- Import geometry from JSON files
- Export pebble bed cores
- Roundtrip import/export testing
- Manual JSON creation and import
- Geometry validation

**Key Classes:**
- `GeometryImporter` - Import geometries from various formats
- `GeometryExporter` - Export geometries to JSON

---

## Documentation Updates

### Updated Files

1. **`docs/examples.rst`**
   - Added new "Geometry Examples" section
   - Organized examples into categories (Basic, Geometry, Advanced)
   - Added entries for all new example scripts

2. **`USAGE.md`**
   - Added new examples to the example list
   - Updated to reflect new capabilities

3. **`docs/api_reference.rst`**
   - Moved `smrforge.visualization` from "Optional/Experimental" to "Core Functionality"
   - Reflects that visualization is now a stable, fully-implemented feature

---

## API Documentation Status

### Current Status
- ✅ API documentation structure exists for all modules
- ✅ New modules are properly indexed
- ✅ Visualization moved to core functionality section

### Note on API Docs Generation
API documentation files (`.rst`) are generated using Sphinx's `sphinx-apidoc` tool. To regenerate:
```bash
cd docs
sphinx-apidoc -o api ../smrforge --separate --module-first
sphinx-build -b html . _build/html
```

The new modules will be automatically included when API docs are regenerated.

---

## Example Scripts Summary

**Total Examples:** 10 (6 existing + 4 new)

**New Examples:**
1. `visualization_examples.py` - Geometry visualization
2. `control_rods_example.py` - Control rod management
3. `assembly_refueling_example.py` - Assembly and refueling
4. `geometry_import_example.py` - Geometry import/export

**Existing Examples:**
1. `basic_neutronics.py` - Basic neutronics calculations
2. `preset_designs.py` - Preset reactor designs
3. `custom_reactor.py` - Custom reactor creation
4. `thermal_analysis.py` - Thermal-hydraulics analysis
5. `complete_integration_example.py` - Complete workflow
6. `integrated_safety_uq.py` - Safety analysis with UQ

---

## Running the Examples

All examples can be run directly:
```bash
# Run a specific example
python examples/visualization_examples.py

# Or run all examples
python examples/*.py
```

Output files (plots, JSON exports) are saved to the `output/` directory.

---

**Conclusion:** All new features now have comprehensive usage examples and are properly documented in the API reference structure.

