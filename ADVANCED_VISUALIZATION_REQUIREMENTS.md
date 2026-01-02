# Advanced Visualization Requirements Analysis

**Date:** January 2025  
**Question:** What geometry features need to be added before implementing advanced visualizations?

---

## Current State

### ✅ What Exists

**Geometry:**
- ✅ PrismaticCore and PebbleBedCore classes
- ✅ 2D mesh generation (radial-axial)
- ✅ Block-based geometry (hexagonal blocks)
- ✅ Control rod geometry (positioning, insertion)
- ✅ Assembly management
- ✅ Point3D, MaterialRegion, FuelChannel, CoolantChannel
- ✅ Basic mesh quality evaluation

**Visualization:**
- ✅ 2D core layout plots (xy, xz, yz views)
- ✅ Flux/power/temperature distribution overlays
- ✅ Matplotlib-based static plots
- ✅ Support for prismatic and pebble bed cores

---

## What Advanced Visualizations Need

### 1. **3D Geometry Representation** 🔴 HIGH PRIORITY

**Status:** ⚠️ **MISSING** - Critical for 3D visualization

**What's Needed:**
- 3D mesh data structures (vertices, faces, cells)
- Surface mesh extraction from geometry
- Volume mesh representation
- Boundary surface identification

**Why Important:**
- 3D interactive visualization (plotly, pyvista) requires 3D mesh data
- Volume rendering needs cell/volume data
- Surface plots need face/edge data

**Suggested Implementation:**
```python
# smrforge/geometry/mesh_3d.py
class Mesh3D:
    """3D unstructured mesh representation."""
    vertices: np.ndarray  # [n_vertices, 3]
    faces: np.ndarray    # [n_faces, 3] (triangles) or [n_faces, 4] (quads)
    cells: np.ndarray    # [n_cells, 4] (tetrahedra) or [n_cells, 8] (hexahedra)
    cell_materials: np.ndarray  # [n_cells] material IDs
    cell_data: Dict[str, np.ndarray]  # Scalar fields (flux, power, etc.)

def extract_surface_mesh(core: PrismaticCore) -> Mesh3D:
    """Extract surface mesh from core geometry."""
    # Extract outer surfaces, block boundaries, etc.
    pass

def extract_volume_mesh(core: PrismaticCore) -> Mesh3D:
    """Extract volume mesh from core geometry."""
    # Full 3D mesh with material regions
    pass
```

**Estimated Effort:** 1-2 weeks

---

### 2. **Geometry Query Methods** 🟡 MEDIUM PRIORITY

**Status:** ⚠️ **PARTIALLY MISSING** - Some methods exist, but not comprehensive

**What's Needed:**
- Get all surfaces/boundaries
- Get material boundaries
- Get control rod surfaces
- Get assembly boundaries
- Get fuel channel surfaces
- Query geometry at specific points/regions

**Why Important:**
- Visualizations need to identify what to render
- Different materials need different colors/styles
- Boundaries need to be highlighted

**Suggested Implementation:**
```python
# Enhancements to PrismaticCore
class PrismaticCore:
    def get_surfaces(self) -> List[Surface]:
        """Get all surfaces in the geometry."""
        pass
    
    def get_material_boundaries(self) -> List[Boundary]:
        """Get boundaries between different materials."""
        pass
    
    def get_control_rod_surfaces(self) -> List[Surface]:
        """Get control rod surfaces."""
        pass
    
    def query_point(self, point: Point3D) -> MaterialRegion:
        """Get material at a specific point."""
        pass
    
    def get_region_geometry(self, material_id: str) -> Mesh3D:
        """Get geometry for a specific material region."""
        pass
```

**Estimated Effort:** 1 week

---

### 3. **Surface/Volume Data Extraction** 🟡 MEDIUM PRIORITY

**Status:** ⚠️ **MISSING** - Needed for volume rendering

**What's Needed:**
- Extract surfaces from blocks
- Extract volume regions
- Material region boundaries
- Control rod surfaces
- Fuel channel surfaces
- Coolant channel surfaces

**Why Important:**
- Volume rendering requires cell data
- Surface plots need surface data
- Material boundaries need to be visualized

**Suggested Implementation:**
```python
# smrforge/geometry/surface_extraction.py
def extract_block_surfaces(block: GraphiteBlock) -> List[Surface]:
    """Extract surfaces from a block."""
    pass

def extract_material_region(blocks: List[GraphiteBlock], material_id: str) -> Mesh3D:
    """Extract geometry for a material region."""
    pass

def extract_control_rod_surfaces(rod: ControlRod) -> List[Surface]:
    """Extract control rod surfaces."""
    pass
```

**Estimated Effort:** 1 week

---

### 4. **3D Coordinate System Methods** 🟢 LOW PRIORITY

**Status:** ✅ **EXISTS** - Point3D exists, but may need enhancements

**What's Needed:**
- Better coordinate transformation methods
- View direction helpers
- Camera position helpers
- Coordinate system conversions

**Why Important:**
- 3D visualizations need proper coordinate systems
- Different views need coordinate transformations

**Current State:**
- ✅ Point3D exists with basic operations
- ⚠️ May need view transformation helpers

**Estimated Effort:** 2-3 days

---

### 5. **Time-Dependent Geometry Support** 🟡 MEDIUM PRIORITY

**Status:** ⚠️ **PARTIALLY MISSING** - Control rods have insertion, but not full time-dependence

**What's Needed:**
- Time-dependent geometry snapshots
- Control rod position over time
- Fuel shuffling geometry changes
- Burnup-dependent geometry

**Why Important:**
- Animations need geometry at different times
- Transient visualizations need time-dependent geometry

**Current State:**
- ✅ Control rods have insertion parameter
- ⚠️ No time-dependent geometry snapshots
- ⚠️ No animation-ready geometry data

**Suggested Implementation:**
```python
# smrforge/geometry/temporal.py
class TemporalGeometry:
    """Time-dependent geometry representation."""
    def get_geometry_at_time(self, time: float) -> PrismaticCore:
        """Get geometry snapshot at specific time."""
        pass
    
    def get_control_rod_positions_at_time(self, time: float) -> Dict[int, float]:
        """Get control rod positions at time."""
        pass
```

**Estimated Effort:** 1 week

---

## Recommendations

### 🔴 **MUST HAVE** Before Advanced Visualizations

1. **3D Mesh Data Structures** (1-2 weeks)
   - Essential for any 3D visualization
   - Required for plotly, pyvista, or other 3D libraries
   - Foundation for all advanced visualizations

2. **Surface Extraction Methods** (1 week)
   - Needed to identify what to render
   - Required for material boundaries
   - Needed for control rod visualization

### 🟡 **SHOULD HAVE** for Full-Featured Visualizations

3. **Geometry Query Methods** (1 week)
   - Makes visualization code cleaner
   - Enables interactive features
   - Better separation of concerns

4. **Time-Dependent Geometry Support** (1 week)
   - Needed for animations
   - Required for transient visualizations
   - Enables time-series plots

### 🟢 **NICE TO HAVE** (Can be added later)

5. **3D Coordinate System Helpers** (2-3 days)
   - Convenience methods
   - Can be added incrementally

---

## Implementation Priority

### Phase 1: Essential for 3D Visualization (2-3 weeks)
1. ✅ 3D mesh data structures
2. ✅ Surface extraction from geometry
3. ✅ Basic geometry query methods

### Phase 2: Enhanced Features (1-2 weeks)
4. ✅ Time-dependent geometry support
5. ✅ Material boundary extraction
6. ✅ Control rod surface extraction

### Phase 3: Polish (Optional)
7. ✅ Coordinate system helpers
8. ✅ Advanced query methods
9. ✅ Performance optimizations

---

## Alternative Approach

**Option:** Start with basic 3D visualization using existing geometry

**What You Can Do Now:**
- Use existing Point3D, blocks, and basic geometry
- Create simple 3D scatter plots
- Visualize control rod positions
- Create basic 3D layouts

**Limitations:**
- No volume rendering
- No surface plots
- Limited material visualization
- No advanced interactions

**Recommendation:** This is acceptable for initial 3D visualizations, but you'll hit limitations quickly. Better to add 3D mesh support first.

---

## Summary

### Critical Gaps for Advanced Visualizations:

1. **3D Mesh Representation** 🔴
   - **Status:** Missing
   - **Impact:** High - Blocks all 3D visualizations
   - **Effort:** 1-2 weeks

2. **Surface Extraction** 🔴
   - **Status:** Missing
   - **Impact:** High - Needed for material boundaries
   - **Effort:** 1 week

3. **Geometry Query Methods** 🟡
   - **Status:** Partially missing
   - **Impact:** Medium - Makes code cleaner
   - **Effort:** 1 week

4. **Time-Dependent Geometry** 🟡
   - **Status:** Partially missing
   - **Impact:** Medium - Needed for animations
   - **Effort:** 1 week

### Recommendation:

**Add 3D mesh support and surface extraction BEFORE implementing advanced visualizations.**

This will:
- Enable proper 3D visualizations
- Support volume rendering
- Allow material boundary visualization
- Provide foundation for animations
- Make visualization code cleaner and more maintainable

**Total Estimated Effort:** 3-4 weeks for essential features

---

*Analysis completed January 2025*

