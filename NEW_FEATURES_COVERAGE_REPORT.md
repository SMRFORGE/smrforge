# New Features Coverage Report

**Date:** 2024-12-28  
**Status:** New features implemented, tests needed

---

## Coverage Summary

| Module | Statements | Missing | Coverage | Status |
|--------|-----------|---------|----------|--------|
| `geometry/control_rods.py` | 71 | 29 | 59.2% | 🟡 Needs tests |
| `geometry/assembly.py` | 101 | 54 | 46.5% | 🟡 Needs tests |
| `geometry/importers.py` | 62 | 47 | 24.2% | 🔴 Needs tests |
| `geometry/mesh_generation.py` | 89 | 64 | 28.1% | 🔴 Needs tests |
| `visualization/geometry.py` | ~200 | ~200 | ~0% | 🔴 Needs tests |
| **Total** | **323** | **194** | **39.9%** | 🟡 **Below target** |

**Target Coverage:** 75-80%  
**Current:** 39.9%  
**Gap:** -35-40 percentage points

---

## Coverage Details

### 1. `geometry/control_rods.py` (59.2% coverage)

**Covered:**
- Basic class definitions
- Simple property methods

**Missing Coverage (29 lines):**
- Lines 49, 53, 57, 61: Helper methods (`volume()`, `inserted_length()`, etc.)
- Lines 85, 94-96: Bank operations (`add_rod()`, `set_insertion()`)
- Lines 100, 104, 108-111: Scram and withdrawal methods
- Lines 125-127, 131: System-level methods
- Lines 135-138, 142-143: Reactivity worth calculations
- Lines 147, 160-171: Shutdown margin calculations

**Priority Tests Needed:**
- ✅ ControlRod creation and properties
- ❌ ControlRodBank operations (add_rod, set_insertion, scram, withdraw)
- ❌ ControlRodSystem management (add_bank, scram_all, total_worth)
- ❌ Shutdown margin calculations
- ❌ Reactivity worth calculations

---

### 2. `geometry/assembly.py` (46.5% coverage)

**Covered:**
- Basic class definitions
- Simple property methods

**Missing Coverage (54 lines):**
- Lines 69-71, 75, 79: Burnup fraction and depletion checks
- Lines 109-119: RefuelingPattern validation
- Lines 123-125: Batch size calculations
- Lines 139-142, 146, 150, 154: AssemblyManager methods
- Lines 163-181: Shuffle operations
- Lines 198-219: Refueling operations
- Lines 231-236: Average burnup calculations
- Lines 250-261: Cycle length estimation

**Priority Tests Needed:**
- ✅ Assembly creation
- ❌ Burnup tracking (burnup_fraction, is_depleted, age_cycles)
- ❌ RefuelingPattern validation and batch calculations
- ❌ AssemblyManager operations (get_assemblies_by_batch, get_depleted)
- ❌ Shuffle and refueling operations
- ❌ Cycle length estimation

---

### 3. `geometry/importers.py` (24.2% coverage)

**Covered:**
- Basic class structure

**Missing Coverage (47 lines):**
- Lines 35-71: `from_json()` method (entire implementation)
- Lines 87-102: `from_openmc_xml()` and `from_serpent()` placeholders
- Lines 117, 135-172: `validate_imported_geometry()` method

**Priority Tests Needed:**
- ❌ JSON import functionality (roundtrip with exporter)
- ❌ Geometry validation (overlap checking, dimension validation)
- ❌ Error handling for invalid JSON
- ❌ Warning generation for potential issues

---

### 4. `geometry/mesh_generation.py` (28.1% coverage)

**Covered:**
- Basic class definitions
- Enum definitions

**Missing Coverage (64 lines):**
- Lines 33, 47: Mesh generator initialization
- Lines 66-82: Radial mesh generation with refinement
- Lines 101-112: Axial mesh generation with refinement
- Lines 129-139: 2D unstructured mesh generation
- Lines 154-194: Mesh quality evaluation
- Lines 219-232: Mesh refinement operations
- Lines 249-260: Gradient computation

**Priority Tests Needed:**
- ❌ Radial mesh generation (uniform and with refinement)
- ❌ Axial mesh generation (uniform and with refinement)
- ❌ 2D unstructured mesh generation (Delaunay triangulation)
- ❌ Mesh quality evaluation (angles, aspect ratio, skewness)
- ❌ Mesh refinement based on criteria
- ❌ Gradient computation

---

### 5. `visualization/geometry.py` (~0% coverage)

**Status:** No tests exist

**Missing Coverage (entire module):**
- `plot_core_layout()` - Main plotting function
- `_plot_prismatic_layout()` - Helper for prismatic cores
- `_plot_pebble_bed_layout()` - Helper for pebble bed cores
- `plot_flux_on_geometry()` - Flux overlay visualization
- `plot_power_distribution()` - Power distribution plots
- `plot_temperature_distribution()` - Temperature plots

**Priority Tests Needed:**
- ❌ Basic plot creation (fig, ax returned)
- ❌ Prismatic core layout plotting (xy, xz, yz views)
- ❌ Pebble bed layout plotting
- ❌ Flux overlay visualization
- ❌ Power distribution plotting
- ❌ Temperature distribution plotting
- ❌ Label and color options
- ❌ Integration with matplotlib

---

## Recommended Test Implementation Plan

### Phase 1: High Priority (Basic Functionality)
1. **Control Rods** (1-2 days)
   - ControlRod basic operations
   - ControlRodBank operations
   - ControlRodSystem management
   - Shutdown margin calculations

2. **Assembly Management** (1-2 days)
   - Assembly burnup tracking
   - RefuelingPattern validation
   - AssemblyManager operations
   - Shuffle and refueling

### Phase 2: Medium Priority (Import/Export)
3. **Geometry Import** (1 day)
   - JSON import roundtrip
   - Validation functionality
   - Error handling

4. **Visualization** (1-2 days)
   - Basic plot creation
   - Core layout plotting
   - Overlay visualizations

### Phase 3: Lower Priority (Advanced Features)
5. **Mesh Generation** (2-3 days)
   - Mesh generation with refinement
   - Quality evaluation
   - Unstructured mesh generation

---

## Test File Structure Recommended

```
tests/
├── test_control_rods.py          # Control rod tests
├── test_assembly.py              # Assembly management tests
├── test_geometry_importers.py    # Import functionality tests
├── test_visualization_geometry.py # Visualization tests
└── test_mesh_generation.py       # Mesh generation tests
```

---

## Quick Start Test Examples

### Control Rods
```python
def test_control_rod_creation():
    rod = ControlRod(id=1, position=Point3D(0,0,0), length=400.0, diameter=5.0)
    assert rod.insertion == 1.0
    assert rod.is_fully_withdrawn()
    assert rod.volume() > 0

def test_control_rod_bank():
    bank = ControlRodBank(id=1, name="A")
    rod = ControlRod(...)
    bank.add_rod(rod)
    bank.set_insertion(0.5)
    assert rod.insertion == 0.5
```

### Assembly Management
```python
def test_assembly_burnup():
    assembly = Assembly(id=1, position=Point3D(0,0,0), burnup=50.0)
    assert not assembly.is_depleted(target_burnup=120.0)
    assembly.burnup = 150.0
    assert assembly.is_depleted(target_burnup=120.0)
```

### Visualization
```python
def test_plot_core_layout():
    core = PrismaticCore()
    core.build_hexagonal_lattice(...)
    fig, ax = plot_core_layout(core, view='xy')
    assert fig is not None
    assert ax is not None
```

---

## Next Steps

1. **Create test files** for each new module
2. **Write basic functionality tests** (Phase 1)
3. **Add integration tests** for complex workflows
4. **Aim for 75-80% coverage** on each module
5. **Update CI/CD** to include new modules in coverage reporting

---

**Note:** These are new features that were just implemented. Tests should be added to ensure reliability and maintainability. The modules are functional but need test coverage to meet production standards.

