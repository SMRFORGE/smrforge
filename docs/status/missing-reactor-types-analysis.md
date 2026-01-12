# Missing Reactor Types Analysis

**Date:** January 1, 2026  
**Focus:** Reactor types missing from geometry implementation  
**Current Status:** Limited to HTGR (High Temperature Gas-cooled Reactor) designs

---

## Executive Summary

SMRForge currently supports **only HTGR (High Temperature Gas-cooled Reactor) designs**:
- ✅ **Prismatic HTGR** (e.g., GT-MHR, Valar Atomics style) - **FULLY IMPLEMENTED**
- ✅ **Pebble Bed HTGR** (e.g., HTR-PM, PBMR) - **FULLY IMPLEMENTED**
- ⚠️ **Annular HTGR** - Defined in enum but **NOT IMPLEMENTED**
- ⚠️ **Hybrid HTGR** - Defined in enum but **NOT IMPLEMENTED**

**All other major reactor types are missing**, significantly limiting the codebase's applicability to the broader nuclear reactor design community.

---

## Currently Implemented Reactor Types

### ✅ 1. Prismatic HTGR (`PrismaticCore`)

**Status:** Fully implemented  
**Examples:** GT-MHR, X-energy Xe-100, Valar Atomics designs

**Features:**
- Hexagonal graphite fuel blocks
- Fuel channels and coolant channels
- Hexagonal lattice arrangement
- Reflector regions
- Control rod insertion support

**Limitations:**
- Only supports hexagonal lattices
- Hardcoded for graphite moderator
- Helium coolant only

---

### ✅ 2. Pebble Bed HTGR (`PebbleBedCore`)

**Status:** Fully implemented  
**Examples:** HTR-PM, PBMR, HTR-10

**Features:**
- Random and structured pebble packing
- Pebble recirculation simulation
- Annular core geometry (parameter exists)
- Burnup tracking per pebble
- KD-tree for neighbor finding

**Limitations:**
- Simplified packing algorithm (not full DEM)
- Basic recirculation model
- Graphite moderator only

---

## Missing Reactor Types

### 🔴 HIGH PRIORITY Missing Reactor Types

#### 1. **Light Water Reactors (LWR)**

**Subtypes:**
- **Pressurized Water Reactor (PWR)**
- **Boiling Water Reactor (BWR)**
- **Small Modular Reactor (SMR) - LWR variants** (NuScale, AP1000, etc.)

**Key Features Missing:**
- ❌ **Square lattice fuel assemblies** (17x17, 15x15, etc.)
- ❌ **Fuel rod arrays** (cylindrical fuel pins in square/hexagonal arrays)
- ❌ **Control rod clusters** (cruciform, rod cluster control assemblies)
- ❌ **Water moderator/coolant** geometry
- ❌ **Pressurizer and steam generator** components
- ❌ **BWR fuel bundles** (square channels with fuel rods)
- ❌ **BWR control blades** (cross-shaped control rods)

**Why Important:**
- LWRs represent ~90% of global nuclear capacity
- Most common reactor type worldwide
- Critical for SMR market (many SMR designs are LWR-based)

**Impact:** 🔴 **CRITICAL** - Limits applicability to vast majority of nuclear industry

**Effort:** High (requires new geometry classes, different lattice structures)

---

#### 2. **Fast Reactors**

**Subtypes:**
- **Sodium-Cooled Fast Reactor (SFR)** (e.g., PRISM, Natrium, BN-800)
- **Lead-Cooled Fast Reactor (LFR)** (e.g., BREST, ALFRED)
- **Gas-Cooled Fast Reactor (GFR)** (e.g., ALLEGRO)

**Key Features Missing:**
- ❌ **Hexagonal fuel assemblies** (for SFR - different from HTGR hexagons)
- ❌ **Triangular pitch lattices** (common in fast reactors)
- ❌ **Wire-wrap fuel pins** (spiral wire spacers)
- ❌ **Grid spacers** (for fuel rod support)
- ❌ **Sodium/lead coolant channels** (liquid metal flow paths)
- ❌ **No moderator** (fast spectrum - different physics)

**Why Important:**
- Fast reactors are key to advanced fuel cycles
- Important for waste management and resource utilization
- Growing interest in SFR and LFR designs

**Impact:** 🟡 **HIGH** - Important for advanced reactor designs

**Effort:** Medium-High (similar to HTGR but different lattice and coolant)

---

#### 3. **Small Modular Reactors (SMRs) - Non-HTGR**

**Subtypes:**
- **NuScale** (PWR-based SMR)
- **mPower** (PWR-based SMR)
- **CAREM** (integral PWR)
- **SMART** (integral PWR)
- **SMR-160** (PWR-based)
- **Molten Salt SMRs** (see below)

**Key Features Missing:**
- ❌ **Integral reactor designs** (core + steam generator in single vessel)
- ❌ **Compact fuel assemblies** (smaller than full-scale PWR)
- ❌ **In-vessel components** (steam generators, pumps, etc.)
- ❌ **SMR-specific control systems**

**Why Important:**
- SMRs are major focus of current nuclear industry
- Many designs are PWR-based (not HTGR)
- Growing market segment

**Impact:** 🟡 **HIGH** - Important for SMR market

**Effort:** Medium (can leverage PWR geometry once implemented)

---

### 🟡 MEDIUM PRIORITY Missing Reactor Types

#### 4. **Molten Salt Reactors (MSR)**

**Subtypes:**
- **Molten Salt Fast Reactor (MSFR)**
- **Molten Salt Thermal Reactor (MSTR)**
- **Liquid Fuel MSR** (fuel dissolved in salt)
- **Solid Fuel MSR** (fuel in graphite, salt coolant)

**Key Features Missing:**
- ❌ **Molten salt channels** (flow paths for liquid fuel/coolant)
- ❌ **Graphite moderator blocks** (for thermal MSRs)
- ❌ **Fuel salt circulation** (pump loops, heat exchangers)
- ❌ **Freeze plugs** (safety systems)
- ❌ **Salt chemistry** (material properties different from solid fuel)

**Why Important:**
- Growing interest in MSR designs
- Unique geometry requirements (liquid fuel)
- Different from solid fuel reactors

**Impact:** 🟡 **MEDIUM** - Specialized but growing interest

**Effort:** High (unique geometry and physics)

---

#### 5. **Heavy Water Reactors (HWR)**

**Subtypes:**
- **CANDU** (Canadian Deuterium Uranium)
- **PHWR** (Pressurized Heavy Water Reactor)
- **AHWR** (Advanced Heavy Water Reactor)

**Key Features Missing:**
- ❌ **Horizontal pressure tubes** (CANDU-specific)
- ❌ **Calandria vessel** (large moderator tank)
- ❌ **Fuel bundles** (cylindrical bundles, not assemblies)
- ❌ **On-power refueling** geometry
- ❌ **Heavy water moderator** (D2O)

**Why Important:**
- CANDU is significant reactor type (~5% global capacity)
- Unique horizontal fuel channel design
- On-power refueling capability

**Impact:** 🟡 **MEDIUM** - Important for CANDU community

**Effort:** High (very different geometry from LWR/HTGR)

---

#### 6. **Research Reactors**

**Subtypes:**
- **Pool-type research reactors**
- **Tank-type research reactors**
- **TRIGA** (Training, Research, Isotopes, General Atomics)
- **Material Test Reactors (MTR)**

**Key Features Missing:**
- ❌ **Plate-type fuel elements** (common in research reactors)
- ❌ **Open pool geometry** (water pool, not pressurized)
- ❌ **Beam ports** (for neutron scattering experiments)
- ❌ **Irradiation positions** (for material testing)
- ❌ **Low power density** geometries

**Why Important:**
- Research reactors have different geometry requirements
- Important for education and training
- Material testing applications

**Impact:** 🟢 **LOW-MEDIUM** - Specialized application

**Effort:** Medium (simpler than power reactors but unique features)

---

### 🟢 LOW PRIORITY / Specialized Reactor Types

#### 7. **Gas-Cooled Reactors (Non-HTGR)**

**Subtypes:**
- **Advanced Gas-Cooled Reactor (AGR)** (UK)
- **Magnox Reactors** (UK, legacy)
- **Gas-Cooled Fast Reactor (GFR)**

**Key Features Missing:**
- ❌ **CO2 coolant** (AGR, Magnox)
- ❌ **Steel pressure vessel** (not graphite)
- ❌ **Different fuel geometry** (AGR uses oxide fuel in steel)

**Impact:** 🟢 **LOW** - Legacy/specialized designs

**Effort:** Medium (similar to HTGR but different materials)

---

#### 8. **Advanced Reactor Concepts**

**Subtypes:**
- **Microreactors** (very small, <10 MWe)
- **Space Reactors** (Kilopower, etc.)
- **Fusion-Fission Hybrids**
- **Accelerator-Driven Systems (ADS)**

**Key Features Missing:**
- ❌ **Very compact geometries** (microreactors)
- ❌ **Unique cooling systems** (heat pipes, etc.)
- ❌ **Fusion blanket geometry** (for hybrids)
- ❌ **Accelerator beam targets** (for ADS)

**Impact:** 🟢 **LOW** - Specialized/future concepts

**Effort:** High (very different from current designs)

---

## Implementation Status Summary

| Reactor Type | Status | Priority | Impact | Effort | Notes |
|--------------|--------|----------|--------|--------|-------|
| **Prismatic HTGR** | ✅ Implemented | - | - | - | Fully functional |
| **Pebble Bed HTGR** | ✅ Implemented | - | - | - | Fully functional |
| **Annular HTGR** | ⚠️ Enum only | 🟡 Medium | Medium | Low | Parameter exists in PebbleBedCore |
| **Hybrid HTGR** | ⚠️ Enum only | 🟡 Medium | Medium | Medium | Not implemented |
| **PWR** | ❌ Missing | 🔴 High | Critical | High | Most common reactor type |
| **BWR** | ❌ Missing | 🔴 High | Critical | High | Second most common |
| **SMR (LWR-based)** | ❌ Missing | 🔴 High | High | Medium | Growing market |
| **Sodium Fast Reactor** | ❌ Missing | 🔴 High | High | Medium-High | Advanced reactors |
| **Lead Fast Reactor** | ❌ Missing | 🔴 High | High | Medium-High | Advanced reactors |
| **Molten Salt Reactor** | ❌ Missing | 🟡 Medium | Medium | High | Unique geometry |
| **CANDU/HWR** | ❌ Missing | 🟡 Medium | Medium | High | Horizontal channels |
| **Research Reactors** | ❌ Missing | 🟢 Low | Low | Medium | Specialized |
| **AGR/Magnox** | ❌ Missing | 🟢 Low | Low | Medium | Legacy |
| **Microreactors** | ❌ Missing | 🟢 Low | Low | High | Specialized |

---

## Detailed Missing Features by Reactor Type

### Light Water Reactors (PWR/BWR)

#### Missing Geometry Components:

1. **Fuel Assemblies**
   - Square lattice arrays (17x17, 15x15, 14x14, etc.)
   - Hexagonal assemblies (some BWR designs)
   - Fuel rod positioning within assembly
   - Spacer grids (support structures)
   - Top and bottom nozzles

2. **Fuel Rods**
   - Cylindrical fuel pellets
   - Cladding (Zircaloy, stainless steel)
   - Gap between fuel and cladding
   - Plenum regions (for fission gas)
   - End caps

3. **Control Systems**
   - **PWR:** Control rod cluster assemblies (RCCA)
   - **BWR:** Control blades (cruciform cross-section)
   - Burnable poison rods
   - Instrumentation tubes

4. **Core Structure**
   - Core barrel (PWR)
   - Lower core support plate
   - Upper core plate
   - Flow distribution structures

5. **Coolant/Moderator**
   - Water channels (not helium)
   - Two-phase flow regions (BWR)
   - Pressurizer (PWR)
   - Steam separators (BWR)

---

### Fast Reactors (SFR/LFR)

#### Missing Geometry Components:

1. **Fuel Assemblies**
   - Hexagonal ducts (different from HTGR hexagons)
   - Triangular pitch lattices
   - Wire-wrap spacers (spiral wires around fuel pins)
   - Grid spacers (alternative to wire-wrap)

2. **Fuel Pins**
   - Metallic fuel (U-Pu-Zr) or oxide fuel
   - Sodium/lead bond (gap filler)
   - Cladding (HT9, T91, etc.)
   - Gas plenum

3. **Core Structure**
   - Core support structure
   - Radial reflectors (steel, not graphite)
   - Radial blankets (breeding regions)
   - Axial blankets

4. **Coolant**
   - Sodium/lead flow channels
   - No moderator (fast spectrum)
   - Primary and secondary loops

---

### Molten Salt Reactors

#### Missing Geometry Components:

1. **Core Vessel**
   - Graphite moderator blocks (for thermal MSRs)
   - Fuel salt channels (for liquid fuel MSRs)
   - Reflector regions

2. **Fuel Salt System**
   - Primary loop (fuel salt circulation)
   - Heat exchangers
   - Pumps
   - Freeze plugs (safety systems)

3. **Unique Features**
   - Liquid fuel geometry (not solid fuel)
   - Salt chemistry considerations
   - Graphite replacement mechanisms

---

### CANDU/Heavy Water Reactors

#### Missing Geometry Components:

1. **Pressure Tubes**
   - Horizontal orientation (unique to CANDU)
   - Calandria tube (outer)
   - Pressure tube (inner, contains fuel)
   - Annulus (gas gap between tubes)

2. **Fuel Bundles**
   - Cylindrical bundles (not assemblies)
   - 37 or 43 fuel elements per bundle
   - End plates
   - Spacer pads

3. **Calandria**
   - Large moderator tank
   - Horizontal tube sheets
   - Heavy water moderator (D2O)

4. **Refueling**
   - On-power refueling machines
   - Fuel handling system geometry

---

## Priority Recommendations

### 🔴 Immediate Focus (Next 6-12 months)

1. **Light Water Reactor (PWR) Support**
   - **Why:** Most common reactor type (~65% of global capacity)
   - **Impact:** Critical for broad applicability
   - **Effort:** High (new geometry classes, square lattices)
   - **Key Components:**
     - Square lattice fuel assemblies
     - Fuel rod arrays
     - Control rod clusters
     - Water moderator/coolant

2. **Annular HTGR Implementation**
   - **Why:** Already defined in enum, parameter exists
   - **Impact:** Completes HTGR family
   - **Effort:** Low-Medium (extend existing PebbleBedCore)
   - **Key Components:**
     - Inner/outer diameter parameters
     - Annular pebble bed packing

### 🟡 Medium-term (12-24 months)

3. **Boiling Water Reactor (BWR) Support**
   - **Why:** Second most common reactor type (~20% of global capacity)
   - **Impact:** High for industry applicability
   - **Effort:** High (similar to PWR but different control systems)

4. **Sodium Fast Reactor (SFR) Support**
   - **Why:** Important for advanced reactors, growing interest
   - **Impact:** High for advanced reactor community
   - **Effort:** Medium-High (hexagonal assemblies, different from HTGR)

5. **SMR (LWR-based) Support**
   - **Why:** Growing market, can leverage PWR geometry
   - **Impact:** High for SMR market
   - **Effort:** Medium (once PWR is implemented)

### 🟢 Long-term (24+ months)

6. **Molten Salt Reactor Support**
   - **Why:** Growing interest, unique geometry
   - **Impact:** Medium for MSR community
   - **Effort:** High (unique requirements)

7. **CANDU/Heavy Water Reactor Support**
   - **Why:** Significant reactor type, unique geometry
   - **Impact:** Medium for CANDU community
   - **Effort:** High (very different from other types)

8. **Research Reactor Support**
   - **Why:** Education and training applications
   - **Impact:** Low-Medium
   - **Effort:** Medium

---

## Implementation Strategy

### Phase 1: Extend HTGR Support (Low Effort)
1. Implement `AnnularCore` class (extend `PebbleBedCore`)
2. Implement `HybridCore` class (combine prismatic + pebble bed)

### Phase 2: Add LWR Support (High Impact)
1. Create `LWRCore` base class
2. Implement `PWRCore` class
   - Square lattice fuel assemblies
   - Fuel rod arrays
   - Control rod clusters
3. Implement `BWRCore` class
   - Fuel bundles
   - Control blades
   - Two-phase flow regions

### Phase 3: Add Fast Reactor Support
1. Create `FastReactorCore` base class
2. Implement `SFRCore` class
   - Hexagonal fuel assemblies
   - Wire-wrap spacers
3. Implement `LFRCore` class
   - Similar to SFR but lead coolant

### Phase 4: Specialized Reactors
1. Molten Salt Reactors
2. CANDU/HWR
3. Research Reactors

---

## Key Design Considerations

### Common Patterns Across Reactor Types

1. **Lattice Structures**
   - Square (PWR, BWR)
   - Hexagonal (HTGR, SFR)
   - Triangular (some fast reactors)
   - Custom (research reactors)

2. **Fuel Elements**
   - Rods (LWR, fast reactors)
   - Pebbles (pebble bed HTGR)
   - Blocks (prismatic HTGR)
   - Plates (research reactors)
   - Liquid (MSR)

3. **Coolant Types**
   - Water (LWR, HWR)
   - Helium (HTGR)
   - Sodium (SFR)
   - Lead (LFR)
   - Molten salt (MSR)

4. **Moderator Types**
   - Water (LWR)
   - Heavy water (HWR)
   - Graphite (HTGR, MSR)
   - None (fast reactors)

---

## Conclusion

SMRForge currently supports **only HTGR designs** (prismatic and pebble bed), which represents a small fraction of the global nuclear reactor fleet. The **most critical missing reactor types are Light Water Reactors (PWR and BWR)**, which together represent ~85% of global nuclear capacity.

**Recommended Priority Order:**
1. 🔴 **PWR support** (highest impact, most common)
2. 🔴 **BWR support** (second most common)
3. 🟡 **Annular HTGR** (complete HTGR family, low effort)
4. 🟡 **SFR support** (advanced reactors, growing interest)
5. 🟡 **SMR (LWR-based)** (growing market)

Adding LWR support would dramatically expand SMRForge's applicability to the broader nuclear industry, while maintaining the existing HTGR capabilities for the advanced reactor community.
