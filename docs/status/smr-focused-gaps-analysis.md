# SMR-Focused Advanced Capabilities Gaps Analysis

**Date:** January 1, 2026  
**Focus:** Missing advanced features in `reactor_core.py` and geometry modules for **SMR development and prototyping**  
**Scope:** Small Modular Reactors (SMRs) - <300 MWe, modular construction, factory fabrication

---

## Executive Summary

SMRForge is scoped for **Small Modular Reactor (SMR) development and prototyping**. Currently, the codebase supports **HTGR-based SMRs** (X-energy Xe-100, NuScale-style HTGR concepts) but is missing critical capabilities for the broader SMR market, particularly **LWR-based SMRs** which represent the majority of near-term SMR deployments.

**Key Findings:**
- ✅ **HTGR SMRs** - Well supported (prismatic, pebble bed)
- ❌ **LWR-based SMRs** - Missing (NuScale, mPower, CAREM, etc.) - **CRITICAL GAP**
- ⚠️ **Advanced nuclear data processing** - Missing features critical for SMR design
- ⚠️ **SMR-specific geometry features** - Missing compact designs, integral systems

---

## SMR Market Context

### SMR Types in Development

1. **LWR-based SMRs** (~70% of SMR market)
   - NuScale (PWR, 77 MWe)
   - mPower (PWR, 180 MWe)
   - CAREM (integral PWR, 25-100 MWe)
   - SMART (integral PWR, 100 MWe)
   - SMR-160 (PWR, 160 MWe)
   - **Status:** ❌ **NOT SUPPORTED**

2. **HTGR SMRs** (~15% of SMR market)
   - X-energy Xe-100 (prismatic, 80 MWe)
   - HTR-PM (pebble bed, 200 MWe)
   - **Status:** ✅ **SUPPORTED**

3. **Fast Reactor SMRs** (~10% of SMR market)
   - Natrium (SFR, 345 MWe)
   - PRISM (SFR, 311 MWe)
   - **Status:** ❌ **NOT SUPPORTED**

4. **Molten Salt SMRs** (~5% of SMR market)
   - Various MSR concepts
   - **Status:** ❌ **NOT SUPPORTED**

---

## Currently Supported SMR Capabilities

### ✅ HTGR SMR Support

**Implemented:**
- Prismatic HTGR cores (`PrismaticCore`)
- Pebble bed HTGR cores (`PebbleBedCore`)
- Reference designs: Valar-10, GT-MHR, HTR-PM, Micro-HTGR
- Helium coolant channels
- Graphite moderator
- Control rod geometry
- Assembly management

**Suitable for:**
- X-energy Xe-100 (prismatic)
- HTR-PM (pebble bed)
- Other HTGR SMR concepts

---

## 🔴 CRITICAL Gaps for SMR Development

### 1. **LWR-based SMR Geometry Support** - **HIGHEST PRIORITY**

**Missing Components:**

#### 1.1 **Square Lattice Fuel Assemblies**
- ❌ **No square lattice** support (17x17, 15x15, 14x14 arrays)
- ❌ **No fuel rod arrays** (cylindrical pins in square grid)
- ❌ **No spacer grids** (support structures for fuel rods)
- ❌ **No top/bottom nozzles** (assembly end fittings)

**Impact:** 🔴 **CRITICAL** - Cannot model LWR-based SMRs (NuScale, mPower, etc.)

**SMR Examples:**
- NuScale: 17x17 fuel assemblies
- mPower: 15x15 fuel assemblies
- CAREM: Compact square assemblies

**Recommendation:** 🔴 **IMMEDIATE PRIORITY** - Required for majority of SMR market

---

#### 1.2 **Integral Reactor Designs**
- ❌ **No in-vessel steam generators** (integral PWR designs)
- ❌ **No compact core layouts** (SMR-specific arrangements)
- ❌ **No integrated primary system** (core + SG + pumps in single vessel)

**Impact:** 🟡 **HIGH** - Many SMRs use integral designs (CAREM, SMART, NuScale)

**SMR Examples:**
- CAREM: Integral PWR with in-vessel steam generators
- SMART: Integral PWR design
- NuScale: Compact integral design

**Recommendation:** 🟡 **HIGH PRIORITY** - Important for SMR-specific designs

---

#### 1.3 **Water Moderator/Coolant Geometry**
- ❌ **No water channels** (currently only helium)
- ❌ **No two-phase flow regions** (BWR SMRs)
- ❌ **No pressurizer geometry** (PWR SMRs)
- ❌ **No steam separator geometry** (BWR SMRs)

**Impact:** 🔴 **CRITICAL** - LWR SMRs require water geometry

**Recommendation:** 🔴 **IMMEDIATE PRIORITY** - Required for LWR SMRs

---

### 2. **Advanced Nuclear Data Processing for SMRs** - **HIGH PRIORITY**

**Missing in `reactor_core.py`:**

#### 2.1 **Resonance Self-Shielding** - **CRITICAL FOR SMRs**
- ❌ **No Bondarenko factors** (f-factors) for heterogeneous fuel assemblies
- ❌ **No subgroup method** for resonance treatment
- ❌ **No equivalence theory** (Bell-Wigner) for fuel pin homogenization

**Why Critical for SMRs:**
- SMRs use compact fuel assemblies with heterogeneous fuel/moderator
- Fuel pins in water moderator require self-shielding corrections
- Without self-shielding, cross-sections are inaccurate → wrong k-eff, power distributions

**Impact:** 🔴 **CRITICAL** - Essential for accurate SMR neutronics

**Recommendation:** 🔴 **IMMEDIATE PRIORITY** - Required for accurate SMR design

**Location:** `smrforge/core/reactor_core.py` - `NuclearDataCache` class

---

#### 2.2 **Advanced Fission Data** - **CRITICAL FOR SMR BURNUP**
- ⚠️ Basic chi (fission spectrum) exists
- ❌ **No MF=5 (fission product yields)** parsing
- ❌ **No delayed neutron data** (MF=1, MT=455)
- ❌ **No prompt/delayed chi separation**
- ❌ **No nu-bar energy dependence**

**Why Critical for SMRs:**
- SMRs need long fuel cycles (3-5 years) → requires burnup analysis
- Delayed neutrons critical for SMR safety analysis
- Fission yields needed for burnup calculations

**Impact:** 🔴 **CRITICAL** - Required for SMR fuel cycle analysis

**Recommendation:** 🔴 **HIGH PRIORITY** - Essential for SMR burnup and safety

**Location:** `smrforge/core/reactor_core.py` - `NuclearDataCache` class

---

#### 2.3 **Advanced Scattering Matrix** - **IMPORTANT FOR SMRs**
- ✅ TSL parser exists (`thermal_scattering_parser.py`)
- ⚠️ TSL integration with neutronics unclear
- ❌ **No MF=6 (energy-angle distributions)** parsing
- ❌ **No anisotropic scattering** (P0, P1, P2 Legendre moments)
- ❌ **No thermal upscattering** in scattering matrix

**Why Important for SMRs:**
- LWR SMRs are thermal reactors → need accurate thermal scattering
- Anisotropic scattering important for accurate flux distributions
- TSL data exists but may not be fully utilized

**Impact:** 🟡 **HIGH** - Important for accurate thermal SMR calculations

**Recommendation:** 🟡 **MEDIUM PRIORITY** - Verify TSL integration, add anisotropic scattering

**Location:** `smrforge/core/reactor_core.py` - `NuclearDataCache` class

---

#### 2.4 **Advanced Multi-Group Processing** - **IMPORTANT FOR SMRs**
- ✅ Basic multi-group collapse exists
- ❌ **No superhomogenization (SPH)** method
- ❌ **No equivalence theory** for group collapse
- ❌ **No adjoint flux weighting** for importance-weighted collapse

**Why Important for SMRs:**
- SMRs need accurate multi-group cross-sections for diffusion solver
- SPH method improves accuracy for heterogeneous assemblies
- Important for SMR design optimization

**Impact:** 🟡 **MEDIUM** - Improves accuracy but not critical

**Recommendation:** 🟡 **MEDIUM PRIORITY** - Enhancement for better accuracy

**Location:** `smrforge/core/reactor_core.py` - `CrossSectionTable` class

---

### 3. **SMR-Specific Geometry Features** - **HIGH PRIORITY**

**Missing in Geometry Modules:**

#### 3.1 **Compact Core Layouts**
- ❌ **No SMR-specific core arrangements** (smaller, more compact than full-scale)
- ❌ **No reduced assembly counts** (SMRs have fewer assemblies)
- ❌ **No compact reflector** designs

**Impact:** 🟡 **HIGH** - SMRs have unique compact geometries

**Recommendation:** 🟡 **MEDIUM PRIORITY** - Important for SMR-specific designs

---

#### 3.2 **Control Rod Systems for SMRs**
- ✅ Basic control rod geometry exists
- ⚠️ **May not support SMR-specific control systems**
- ❌ **No control rod cluster assemblies** (PWR SMRs)
- ❌ **No control blades** (BWR SMRs)
- ❌ **No SMR-specific scram systems**

**Impact:** 🟡 **MEDIUM** - SMRs may have different control systems

**Recommendation:** 🟡 **MEDIUM PRIORITY** - Verify SMR compatibility

---

#### 3.3 **SMR Fuel Management**
- ✅ Basic assembly management exists
- ⚠️ **May not support SMR-specific refueling**
- ❌ **No long-cycle fuel management** (3-5 year cycles)
- ❌ **No batch refueling patterns** for SMRs
- ❌ **No fuel shuffling** for SMR compact cores

**Impact:** 🟡 **MEDIUM** - SMRs have different fuel cycle requirements

**Recommendation:** 🟡 **MEDIUM PRIORITY** - Enhance for SMR fuel cycles

---

### 4. **Advanced Data Structures for SMRs** - **MEDIUM PRIORITY**

**Missing in `reactor_core.py`:**

#### 4.1 **Nuclide Inventory Tracking**
- ❌ **No nuclide inventory tracking** (atom densities, concentrations)
- ❌ **No decay chain representation**
- ❌ **No burnup-dependent composition** tracking

**Why Important for SMRs:**
- SMRs need long fuel cycles → requires burnup tracking
- Need to track isotope evolution during operation

**Impact:** 🟡 **MEDIUM** - Required for SMR burnup analysis

**Recommendation:** 🟡 **MEDIUM PRIORITY** - Required for burnup calculations

**Location:** `smrforge/core/reactor_core.py` - `Nuclide` class, `NuclearDataCache` class

---

#### 4.2 **Cross-Section Interpolation**
- ⚠️ Basic Doppler broadening exists
- ❌ **No temperature interpolation** (only Doppler broadening)
- ❌ **No interpolation methods** (linear, log-log, spline)
- ❌ **No multi-temperature libraries**

**Why Important for SMRs:**
- SMRs operate at different temperatures than full-scale
- Need accurate cross-sections across temperature range

**Impact:** 🟢 **LOW** - Enhancement opportunity

**Recommendation:** 🟢 **LOW PRIORITY** - Nice to have

---

## 🟡 MEDIUM PRIORITY Gaps for SMRs

### 5. **Fast Reactor SMR Support** - **MEDIUM PRIORITY**

**Missing:**
- ❌ **No sodium-cooled fast reactor** geometry (Natrium, PRISM)
- ❌ **No hexagonal fuel assemblies** (different from HTGR hexagons)
- ❌ **No wire-wrap spacers**
- ❌ **No liquid metal coolant** channels

**Impact:** 🟡 **MEDIUM** - Important for advanced SMR concepts

**Recommendation:** 🟡 **MEDIUM PRIORITY** - For advanced SMR market segment

---

### 6. **SMR-Specific Mesh Generation** - **MEDIUM PRIORITY**

**Missing:**
- ⚠️ Basic mesh generation exists
- ❌ **No SMR-optimized mesh** (compact geometries)
- ❌ **No adaptive refinement** for SMR-specific features
- ❌ **No mesh optimization** for small cores

**Impact:** 🟢 **LOW-MEDIUM** - Enhancement opportunity

**Recommendation:** 🟢 **LOW PRIORITY** - Optimization opportunity

---

## Priority Recommendations for SMR Development

### 🔴 Phase 1: Critical SMR Capabilities (0-6 months)

**Goal:** Enable LWR-based SMR development

1. **Square Lattice Fuel Assemblies** (Geometry)
   - Implement square lattice support
   - Fuel rod arrays
   - Spacer grids
   - **Effort:** High
   - **Impact:** 🔴 **CRITICAL** - Enables LWR SMR modeling

2. **Water Moderator/Coolant Geometry** (Geometry)
   - Water channels
   - Two-phase flow regions
   - **Effort:** Medium
   - **Impact:** 🔴 **CRITICAL** - Required for LWR SMRs

3. **Resonance Self-Shielding** (`reactor_core.py`)
   - Bondarenko factors
   - Subgroup method
   - Equivalence theory
   - **Effort:** High
   - **Impact:** 🔴 **CRITICAL** - Essential for accurate SMR neutronics

4. **Advanced Fission Data** (`reactor_core.py`)
   - MF=5 parsing (fission yields)
   - Delayed neutron data
   - **Effort:** Medium
   - **Impact:** 🔴 **CRITICAL** - Required for SMR burnup analysis

---

### 🟡 Phase 2: Enhanced SMR Capabilities (6-12 months)

5. **Integral Reactor Designs** (Geometry)
   - In-vessel steam generators
   - Compact core layouts
   - **Effort:** Medium
   - **Impact:** 🟡 **HIGH** - Important for many SMR designs

6. **Advanced Scattering Matrix** (`reactor_core.py`)
   - Verify TSL integration
   - Add anisotropic scattering (P0, P1, P2)
   - **Effort:** Medium
   - **Impact:** 🟡 **HIGH** - Improves accuracy

7. **Nuclide Inventory Tracking** (`reactor_core.py`)
   - Atom density tracking
   - Decay chain representation
   - **Effort:** Medium
   - **Impact:** 🟡 **MEDIUM** - Required for burnup

8. **SMR Control Systems** (Geometry)
   - Control rod clusters (PWR)
   - Control blades (BWR)
   - **Effort:** Low-Medium
   - **Impact:** 🟡 **MEDIUM** - SMR-specific features

---

### 🟢 Phase 3: Advanced SMR Features (12+ months)

9. **Fast Reactor SMR Support** (Geometry)
   - Sodium-cooled fast reactor geometry
   - Wire-wrap spacers
   - **Effort:** Medium-High
   - **Impact:** 🟢 **MEDIUM** - Advanced SMR concepts

10. **Advanced Multi-Group Processing** (`reactor_core.py`)
    - SPH method
    - Equivalence theory
    - **Effort:** Medium
    - **Impact:** 🟢 **LOW-MEDIUM** - Enhancement

11. **SMR-Specific Mesh Optimization** (Geometry)
    - Compact geometry meshing
    - SMR-optimized refinement
    - **Effort:** Low
    - **Impact:** 🟢 **LOW** - Optimization

---

## Summary Table: SMR-Focused Gaps

| Feature | Priority | Impact | Effort | Location | SMR Market Relevance |
|---------|----------|--------|--------|----------|---------------------|
| **Square Lattice Assemblies** | 🔴 Critical | Critical | High | Geometry | ~70% of SMR market |
| **Water Geometry** | 🔴 Critical | Critical | Medium | Geometry | ~70% of SMR market |
| **Resonance Self-Shielding** | 🔴 Critical | Critical | High | `reactor_core.py` | All SMRs |
| **Fission Yields/Delayed Neutrons** | 🔴 Critical | Critical | Medium | `reactor_core.py` | All SMRs (burnup) |
| **Integral Reactor Designs** | 🟡 High | High | Medium | Geometry | Many SMRs |
| **Anisotropic Scattering** | 🟡 High | High | Medium | `reactor_core.py` | Thermal SMRs |
| **Nuclide Inventory Tracking** | 🟡 Medium | Medium | Medium | `reactor_core.py` | All SMRs (burnup) |
| **SMR Control Systems** | 🟡 Medium | Medium | Low-Medium | Geometry | LWR SMRs |
| **Fast Reactor SMR** | 🟢 Medium | Medium | Medium-High | Geometry | ~10% of SMR market |
| **Advanced Multi-Group** | 🟢 Low | Low-Medium | Medium | `reactor_core.py` | Enhancement |

---

## Implementation Strategy for SMR Focus

### Immediate Actions (Next 3 months)

1. **Add LWR SMR Geometry Support**
   - Create `LWRCore` base class
   - Implement `PWRSMRCore` class
   - Square lattice fuel assemblies
   - Fuel rod arrays
   - Water moderator/coolant

2. **Add Resonance Self-Shielding**
   - Implement Bondarenko factor calculation
   - Add to `NuclearDataCache` class
   - Integrate with multi-group collapse

3. **Add Fission Data Parsing**
   - Parse MF=5 (fission yields)
   - Parse delayed neutron data
   - Add to `NuclearDataCache` class

### Medium-term (3-6 months)

4. **Integral Reactor Designs**
   - In-vessel components
   - Compact layouts

5. **Verify TSL Integration**
   - Ensure thermal scattering used in calculations
   - Add anisotropic scattering support

6. **Nuclide Inventory Tracking**
   - Add inventory tracking classes
   - Decay chain representation

---

## Conclusion

For **SMR development and prototyping**, the most critical gaps are:

1. 🔴 **LWR-based SMR geometry** (square lattices, water geometry) - **CRITICAL**
2. 🔴 **Resonance self-shielding** - **CRITICAL** for accurate neutronics
3. 🔴 **Advanced fission data** (yields, delayed neutrons) - **CRITICAL** for burnup

**Current Status:**
- ✅ HTGR SMRs well supported
- ❌ LWR SMRs not supported (70% of SMR market)
- ⚠️ Advanced nuclear data processing missing

**Recommendation:** Focus Phase 1 on enabling LWR-based SMR development, as this represents the majority of near-term SMR deployments. This will dramatically expand SMRForge's applicability to the SMR market while maintaining existing HTGR SMR capabilities.
