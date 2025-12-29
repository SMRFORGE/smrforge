# Missing Features Analysis for Reactor Design & Simulation

**Date:** 2024-12-28  
**Focus:** Geometry and reactor design capabilities

---

## 📊 Current State Summary

### ✅ Well Implemented
- **Core Geometry**: Prismatic and pebble bed geometries with mesh generation
- **Basic Geometry Export**: VTK (ParaView), JSON
- **Geometry Data Structures**: Blocks, channels, pebbles, regions
- **Neutronics**: Multi-group diffusion solver
- **Validation**: Pydantic models for reactor specifications

### ⚠️ Partially Implemented
- **Thermal-Hydraulics**: Channel models exist but need more testing
- **Safety Analysis**: Transient simulations implemented but need validation
- **Monte Carlo**: Basic implementation, needs validation

### ❌ Missing/Stub Modules
- **Visualization**: Stub (no implementation)
- **Optimization**: Stub (no implementation)
- **I/O Utilities**: Stub (basic Pydantic serialization works)
- **Fuel Performance**: Stub
- **Control Systems**: Stub
- **Economics**: Stub

---

## 🔴 HIGH PRIORITY Missing Features

### 1. **Geometry Visualization** 📐

**Status**: ❌ Not implemented (stub module exists)

**What's Missing:**
- 2D cross-section visualization (axial, radial views)
- 3D geometry visualization (interactive)
- Flux/power mapping to geometry
- Temperature distribution overlay on geometry
- Assembly/block layout visualization
- Control rod positions visualization

**Why Important:**
- Essential for understanding reactor design
- Needed for validation and debugging
- Important for presentations and documentation
- Helps identify geometry issues before simulation

**Implementation Priority**: 🔴 **HIGH** - Critical for usability

**Suggested Implementation:**
```python
# smrforge/visualization/geometry.py
def plot_core_layout(core: PrismaticCore, view='xy', **kwargs)
def plot_flux_on_geometry(flux, geometry, **kwargs)
def plot_power_distribution(power, geometry, **kwargs)
def plot_temperature_map(temp, geometry, **kwargs)
def plot_3d_core(core: PrismaticCore, interactive=True, **kwargs)
```

**Dependencies:**
- matplotlib (2D plots)
- plotly or pyvista (3D/interactive)
- Existing geometry structures

**Estimated Effort**: 1-2 weeks

---

### 2. **Geometry Analysis & Validation Tools** 🔍

**Status**: ⚠️ Limited - basic volume calculations exist

**What's Missing:**
- Geometry consistency checking (overlaps, gaps, boundaries)
- Material region validation (completeness, connectivity)
- Mesh quality metrics
- Distance/clearance checking
- Assembly placement validation
- Control rod insertion validation
- Fuel loading pattern validation

**Why Important:**
- Prevents geometry errors before simulation
- Ensures physical feasibility
- Validates design constraints
- Critical for safety analysis

**Implementation Priority**: 🔴 **HIGH** - Prevents errors

**Suggested Implementation:**
```python
# smrforge/geometry/validation.py
def validate_geometry(core: PrismaticCore) -> ValidationReport
def check_overlaps(blocks: List[GraphiteBlock]) -> List[Overlap]
def validate_material_regions(core: PrismaticCore) -> ValidationReport
def check_mesh_quality(mesh) -> MeshQualityReport
def validate_assembly_placement(core: PrismaticCore) -> bool
```

**Estimated Effort**: 1 week

---

### 3. **Assembly-Level & Refueling Geometry** 🔄

**Status**: ❌ Not implemented (core-level only)

**What's Missing:**
- Assembly definition and management
- Refueling pattern support
- Burnup-dependent geometry (fuel shuffling)
- Multiple batch fuel management
- Assembly positioning/orientation
- Fuel cycle geometry tracking

**Why Important:**
- Essential for realistic reactor operations
- Needed for fuel cycle analysis
- Required for optimization studies
- Important for operational planning

**Implementation Priority**: 🟡 **MEDIUM** - Important for advanced use cases

**Suggested Implementation:**
```python
# smrforge/geometry/assembly.py
class Assembly:
    """Represents a fuel assembly with burnup tracking"""
    id: int
    position: Point3D
    burnup: float
    batch: int
    refueling_history: List[RefuelingEvent]
    
def create_refueling_pattern(core: PrismaticCore, batches: int) -> RefuelingPattern
def shuffle_assemblies(core: PrismaticCore, pattern: RefuelingPattern)
```

**Estimated Effort**: 2-3 weeks

---

## 🟡 MEDIUM PRIORITY Missing Features

### 4. **Control Rod Geometry & Positioning** 🎛️

**Status**: ⚠️ Mentioned but not fully implemented

**What's Missing:**
- Control rod geometry definition
- Control rod bank definitions
- Insertion/withdrawal positions
- Worth calculations per position
- Control rod sequencing
- Scram geometry (full insertion)

**Why Important:**
- Critical for reactor control
- Needed for safety analysis
- Important for operational scenarios

**Implementation Priority**: 🟡 **MEDIUM**

**Suggested Implementation:**
```python
# smrforge/geometry/control_rods.py
class ControlRod:
    """Control rod geometry and properties"""
    id: int
    position: Point3D
    length: float
    material: str
    insertion: float  # 0.0 = fully inserted, 1.0 = fully withdrawn
    
class ControlRodBank:
    """Group of control rods operated together"""
    rods: List[ControlRod]
    insertion: float
```

**Estimated Effort**: 1-2 weeks

---

### 5. **Geometry Import/Conversion** 📥

**Status**: ⚠️ Only export exists (VTK, JSON)

**What's Missing:**
- Import from CAD formats (STEP, IGES, STL)
- Import from OpenMC XML
- Import from Serpent geometry
- Import from MCNP geometry
- Geometry conversion utilities
- Format validation on import

**Why Important:**
- Enables use of existing designs
- Improves interoperability
- Reduces manual geometry creation
- Facilitates validation against other codes

**Implementation Priority**: 🟡 **MEDIUM**

**Estimated Effort**: 2-3 weeks (depends on formats)

---

### 6. **Advanced Mesh Generation** 🕸️

**Status**: ⚠️ Basic mesh generation exists

**What's Missing:**
- Adaptive mesh refinement
- Mesh generation for complex geometries
- Multiple mesh types (structured, unstructured, hybrid)
- Mesh quality optimization
- Parallel mesh generation
- Mesh conversion utilities

**Why Important:**
- Better solution accuracy
- Handles complex geometries
- Optimizes computational efficiency

**Implementation Priority**: 🟡 **MEDIUM** (nice to have)

**Estimated Effort**: 2-3 weeks

---

## 🟢 LOW PRIORITY / Future Features

### 7. **Optimization Module** 🎯

**Status**: ❌ Stub module

**What's Missing:**
- Design parameter optimization
- Fuel loading pattern optimization
- Control rod optimization
- Multi-objective optimization
- Constraint handling

**Note**: Users can use `scipy.optimize` directly, but a dedicated module would be convenient.

**Priority**: 🟢 **LOW** - Can be done externally

---

### 8. **Visualization Enhancements** 📊

**Status**: ❌ Not implemented

**Beyond basic geometry visualization:**
- Interactive 3D visualization (web-based)
- Animation of transients
- Comparison views (multiple designs)
- Export to video/GIF
- Web dashboard

**Priority**: 🟢 **LOW** - Nice to have

---

### 9. **Fuel Performance Integration** ⛽

**Status**: ❌ Stub module

**What's Missing:**
- Fuel temperature feedback to geometry
- Fuel swelling effects on geometry
- Fission gas release
- Fuel rod deformation

**Note**: Could integrate with external fuel performance codes.

**Priority**: 🟢 **LOW** - Can use external tools

---

## 📋 Recommended Implementation Order

### Phase 1: Critical for Usability (2-3 weeks)
1. ✅ **Geometry Visualization** (HIGH PRIORITY)
   - 2D cross-section plots
   - Flux/power overlay
   - Basic 3D visualization

2. ✅ **Geometry Validation Tools** (HIGH PRIORITY)
   - Overlap checking
   - Material region validation
   - Basic consistency checks

### Phase 2: Enhanced Capabilities (3-4 weeks)
3. **Assembly-Level Geometry**
   - Assembly definitions
   - Basic refueling patterns

4. **Control Rod Geometry**
   - Control rod definitions
   - Positioning and sequencing

### Phase 3: Advanced Features (4-6 weeks)
5. **Geometry Import/Conversion**
   - OpenMC, Serpent import
   - Format conversion utilities

6. **Advanced Mesh Generation**
   - Adaptive refinement
   - Quality optimization

---

## 🎯 Key Gaps Summary

| Feature | Priority | Status | Effort | Impact |
|---------|----------|--------|--------|--------|
| Geometry Visualization | 🔴 HIGH | ❌ Missing | 1-2 weeks | Very High |
| Geometry Validation | 🔴 HIGH | ⚠️ Limited | 1 week | Very High |
| Assembly/Refueling | 🟡 MEDIUM | ❌ Missing | 2-3 weeks | High |
| Control Rod Geometry | 🟡 MEDIUM | ⚠️ Partial | 1-2 weeks | High |
| Geometry Import | 🟡 MEDIUM | ⚠️ Export only | 2-3 weeks | Medium |
| Advanced Mesh | 🟡 MEDIUM | ⚠️ Basic | 2-3 weeks | Medium |
| Optimization | 🟢 LOW | ❌ Stub | 2-3 weeks | Low |
| Fuel Performance | 🟢 LOW | ❌ Stub | Variable | Low |

---

## 💡 Recommendations

### Immediate Focus (Next 1-2 months)
1. **Implement basic geometry visualization** - Biggest usability gap
2. **Add geometry validation tools** - Prevents errors, improves reliability
3. **Document existing geometry capabilities** - Help users understand what's available

### Medium-term (3-6 months)
4. Assembly-level geometry and refueling patterns
5. Control rod geometry and positioning
6. Geometry import from common formats

### Long-term (6+ months)
7. Advanced mesh generation
8. Optimization module (if demand exists)
9. Enhanced visualization (web-based, interactive)

---

## 🔗 Integration Points

When implementing these features, consider integration with:
- **Neutronics Solver**: Flux/power mapping requires solver results
- **Thermal-Hydraulics**: Temperature distributions need TH results
- **Validation Framework**: Geometry validation should use existing validators
- **Preset Designs**: New features should work with existing presets

---

**Conclusion**: The biggest gap is **geometry visualization**, which is essential for usability and validation. Geometry validation tools are also critical to prevent errors. These should be the highest priority additions.

