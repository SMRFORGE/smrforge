# ENDF-B-VIII.1 File Types and Parser Recommendations

**Date:** January 1, 2026  
**Directory Analyzed:** `C:\Users\cmwha\Downloads\ENDF-B-VIII.1`

---

## File Type Analysis

Based on directory scan, the ENDF-B-VIII.1 directory contains the following file types:

### Primary Data Files

| Extension | Count | Description | File Type |
|-----------|-------|-------------|-----------|
| `.endf` | 5,000+ | ENDF-6 format nuclear data files | **Primary Data Format** |
| `.csv` | 1 | Comma-separated values (likely metadata/index) | Metadata |
| `.txt` | 1 | Text documentation/readme | Documentation |

### Supporting Files

| Extension | Count | Description | File Type |
|-----------|-------|-------------|-----------|
| `.py` | 4 | Python utility scripts | Scripts |
| `.md` | 4 | Markdown documentation | Documentation |
| `.yml` | 2 | YAML configuration files | Configuration |
| `.ini` | 1 | INI configuration file | Configuration |
| `.sh` | 1 | Shell script | Scripts |
| (none) | 1 | LICENSE file | Legal |

### ENDF File Categories (by prefix)

Based on actual file analysis, the directory contains:

| Prefix | Count | Description | Example Filename |
|--------|-------|-------------|------------------|
| `dec` | 3,821 | Decay data files | `dec-092_U_235.endf` |
| `n` | 558 | Neutron cross-section data | `n-092_U_235.endf` |
| `g` | 222 | Gamma production data | `g-092_U_235.endf` |
| `tsl` | 114 | Thermal scattering law data | `tsl-HinH2O.endf` |
| `photoat` | 100 | Photon/atomic interaction data | `photoat-002_He_004.endf` |
| `atom` | 100 | Atomic data files | `atom-001_H_000.endf` |
| `e` | 100 | Electron interaction data | `e-001_H_001.endf` |
| `p` | 49 | Proton interaction data | `p-001_H_001.endf` |
| `nfy` | 31 | Neutron-induced fission yields | `nfy-092_U_235.endf` |
| `std` | 11 | Standard reference data | `std-001_H_001.endf` |
| `sfy` | 9 | Spontaneous fission yields | `sfy-098_Cf_252.endf` |
| `d` | 6 | Decay data (alternative format?) | `d-092_U_235.endf` |
| `t` | 5 | Tritium data | `t-001_H_003.endf` |
| `a` | 5 | Alpha particle data | `a-002_He_004.endf` |
| `h` | 4 | Hydrogen/helium data | `h-001_H_001.endf` |

**Total ENDF files:** ~5,135 files

---

## Recommended GitHub Repositories by File Type

### 1. ENDF-6 Format Parsers (`.endf` files - ALL types)

#### **Primary Recommendations:**

**A. endf-parserpy** (IAEA-NDS) ⭐ **RECOMMENDED**
- **Repository:** https://github.com/IAEA-NDS/endf-parserpy
- **Language:** Python
- **Features:**
  - Read, write, verify ENDF-6 files
  - Convert to JSON format
  - Format validation
  - Access to all ENDF sections (MF/MT)
  - Supports all file types: neutron, photon, decay, TSL, fission yields, gamma production
- **Best for:** General ENDF parsing, validation, format conversion
- **Installation:** `pip install endf-parserpy`
- **Status:** ✅ Currently used in SMRForge

**B. ENDFtk** (NJOY Team)
- **Repository:** https://github.com/njoy/ENDFtk
- **Language:** C++ (with Python bindings)
- **Features:**
  - High-performance ENDF-6 parsing
  - Structured data access
  - Part of NJOY nuclear data processing system
- **Best for:** High-performance applications, integration with NJOY
- **Installation:** Requires C++ compilation or pre-built binaries

**C. SANDY** (Nuclear Data Processing) ⭐ **RECOMMENDED**
- **Repository:** https://github.com/luca-fiorito-11/sandy
- **Language:** Python
- **Features:**
  - ENDF file manipulation and processing
  - Uncertainty quantification
  - Covariance data handling
  - Statistical analysis
- **Best for:** Uncertainty propagation, covariance analysis
- **Installation:** `pip install sandy`
- **Status:** ✅ Currently used in SMRForge as fallback

#### **Additional Options:**

**D. OpenMC ENDF Parser**
- **Repository:** https://github.com/openmc-dev/openmc
- **Language:** Python/C++
- **Features:**
  - ENDF parsing for Monte Carlo transport
  - Cross-section processing
  - Part of OpenMC Monte Carlo code
- **Best for:** Monte Carlo transport applications
- **Note:** Parser is part of larger codebase

**E. SERPENT ENDF Parser**
- **Repository:** https://github.com/CORE-GATECH/serpent-tools
- **Language:** Python
- **Features:**
  - ENDF file reading utilities
  - SERPENT output processing
  - Part of SERPENT Monte Carlo tools
- **Best for:** SERPENT users, Monte Carlo applications

**F. PyNE (Python Nuclear Engineering)**
- **Repository:** https://github.com/pyne/pyne
- **Language:** Python
- **Features:**
  - ENDF file reading
  - Nuclear data manipulation
  - Part of comprehensive nuclear engineering toolkit
- **Best for:** General nuclear engineering applications
- **Installation:** `pip install pyne`

---

### 2. Specialized Parsers by Data Type

#### **Decay Data (`dec-*`, `d-*` files - 3,827 files)**

**Primary:** endf-parserpy (supports MF=8 decay data)
- **Repository:** https://github.com/IAEA-NDS/endf-parserpy
- **Features:** Half-lives, decay modes, decay chains, branching ratios

**Alternative:** PyNE decay module
- **Repository:** https://github.com/pyne/pyne
- **Features:** Decay chain calculations, activity calculations

#### **Neutron Data (`n-*` files - 558 files)**

**Primary:** endf-parserpy (supports MF=1-6 neutron data)
- **Repository:** https://github.com/IAEA-NDS/endf-parserpy
- **Features:** Cross-sections, resonance parameters, angular distributions

**Alternative:** ENDFtk, OpenMC, SERPENT parsers

#### **Gamma Production Data (`g-*` files - 222 files)**

**Primary:** endf-parserpy (supports MF=12/13/14)
- **Repository:** https://github.com/IAEA-NDS/endf-parserpy
- **Features:** Prompt and delayed gamma spectra, gamma production cross-sections

#### **Thermal Scattering Data (`tsl-*` files - 114 files)**

**Primary:** endf-parserpy (supports MF=7 thermal scattering)
- **Repository:** https://github.com/IAEA-NDS/endf-parserpy
- **Features:** Thermal scattering law data, S(α,β) tables

**Alternative:** NJOY21
- **Repository:** https://github.com/njoy/NJOY21
- **Features:** TSL processing, ACE format generation

#### **Photon/Atomic Data (`photoat-*`, `atom-*`, `a-*` files - 205 files)**

**Primary:** endf-parserpy (supports MF=23 photon atomic data)
- **Repository:** https://github.com/IAEA-NDS/endf-parserpy
- **Features:** Photoelectric, Compton, pair production cross-sections

#### **Fission Yield Data (`nfy-*`, `sfy-*` files - 40 files)**

**Primary:** endf-parserpy (supports MF=8, MT=454/459)
- **Repository:** https://github.com/IAEA-NDS/endf-parserpy
- **Features:** Independent and cumulative fission yields

**Alternative:** PyNE
- **Repository:** https://github.com/pyne/pyne
- **Features:** Fission yield data handling

#### **Charged Particle Data (`e-*`, `p-*`, `a-*`, `t-*` files - 259 files)**

**Primary:** endf-parserpy (supports charged particle data)
- **Repository:** https://github.com/IAEA-NDS/endf-parserpy
- **Features:** Electron, proton, alpha, tritium interaction data

**Note:** Charged particle data is less common but supported by ENDF-6 format

---

### 3. GNDS Format Parsers (if present)

**GNDStk**
- **Repository:** https://github.com/njoy/GNDStk
- **Language:** C++ (with Python bindings)
- **Features:**
  - Read/write GNDS-2.0 format
  - XML-based nuclear data structure
  - Modern alternative to ENDF-6
- **Best for:** GNDS format files (if ENDF-B-VIII.1 includes GNDS distribution)

---

### 4. Configuration and Metadata Files

#### **YAML Files (`.yml`)**
- **Parser:** Built-in Python `yaml` module or `ruamel.yaml`
- **Repository:** https://github.com/yaml/pyyaml
- **Best for:** Configuration file parsing

#### **CSV Files (`.csv`)**
- **Parser:** Built-in Python `csv` module or `pandas`
- **Repository:** https://github.com/pandas-dev/pandas
- **Best for:** Metadata/index file parsing

#### **INI Files (`.ini`)**
- **Parser:** Built-in Python `configparser` module
- **Best for:** Configuration file parsing

---

## Recommended Parser Selection Guide

### For SMRForge Integration:

1. **Primary Choice: endf-parserpy** ✅ **CURRENTLY USED**
   - ✅ Pure Python (easy integration)
   - ✅ Comprehensive ENDF-6 support
   - ✅ Actively maintained by IAEA
   - ✅ Supports ALL file types found (decay, neutron, gamma, TSL, photon, charged particles, fission yields)
   - ✅ Good documentation
   - ✅ Handles 5,000+ files efficiently

2. **Secondary Choice: SANDY** ✅ **CURRENTLY USED AS FALLBACK**
   - ✅ Python-based
   - ✅ Good for uncertainty quantification
   - ✅ ENDF manipulation capabilities
   - ⚠️ May have different API than endf-parserpy

3. **For High Performance: ENDFtk**
   - ✅ Very fast (C++ backend)
   - ✅ Part of NJOY ecosystem
   - ⚠️ Requires compilation or binary installation
   - ⚠️ May be overkill for SMRForge needs

### For Specific Use Cases:

- **Monte Carlo Transport:** OpenMC or SERPENT parsers
- **Uncertainty Analysis:** SANDY
- **Thermal Scattering:** NJOY21
- **General Purpose:** endf-parserpy or PyNE
- **Large-Scale Processing:** ENDFtk

---

## Integration Recommendations for SMRForge

### Current Status:
SMRForge already uses:
- ✅ `endf-parserpy` (as primary backend)
- ✅ `SANDY` (as fallback backend)
- ✅ Built-in simple parser (as final fallback)

### Recommendations:

1. **Continue using endf-parserpy as primary** ✅
   - Most comprehensive
   - Best maintained
   - Supports all file types found (decay, neutron, gamma, TSL, photon, charged particles, fission yields)

2. **Enhance SANDY integration** ✅
   - Useful for uncertainty quantification features
   - Good for advanced ENDF manipulation
   - Already integrated as fallback

3. **Consider ENDFtk for performance-critical paths** (Future)
   - If parsing speed becomes bottleneck
   - For large-scale batch processing of 5,000+ files

4. **Add GNDStk support** (Future)
   - If ENDF-B-VIII.1 includes GNDS format
   - Modern XML-based format
   - Better structured data access

5. **Add specialized parsers for specific data types** (Optional)
   - PyNE for decay chain calculations
   - NJOY21 for advanced TSL processing

---

## File Type Summary Table

| File Type | Prefix | Count | Recommended Parser | GitHub Repository |
|-----------|--------|-------|-------------------|-------------------|
| Decay Data | `dec-*`, `d-*` | 3,827 | endf-parserpy | https://github.com/IAEA-NDS/endf-parserpy |
| Neutron Data | `n-*` | 558 | endf-parserpy | https://github.com/IAEA-NDS/endf-parserpy |
| Gamma Production | `g-*` | 222 | endf-parserpy | https://github.com/IAEA-NDS/endf-parserpy |
| Charged Particles | `e-*`, `p-*`, `a-*`, `t-*` | 259 | endf-parserpy | https://github.com/IAEA-NDS/endf-parserpy |
| Photon/Atomic | `photoat-*`, `atom-*` | 200 | endf-parserpy | https://github.com/IAEA-NDS/endf-parserpy |
| Thermal Scattering | `tsl-*` | 114 | endf-parserpy / NJOY21 | https://github.com/IAEA-NDS/endf-parserpy |
| Fission Yields | `nfy-*`, `sfy-*` | 40 | endf-parserpy | https://github.com/IAEA-NDS/endf-parserpy |
| Standard Data | `std-*` | 11 | endf-parserpy | https://github.com/IAEA-NDS/endf-parserpy |
| GNDS Format | `.xml` | ? | GNDStk | https://github.com/njoy/GNDStk |
| YAML Config | `.yml` | 2 | pyyaml | https://github.com/yaml/pyyaml |
| CSV Metadata | `.csv` | 1 | pandas | https://github.com/pandas-dev/pandas |
| INI Config | `.ini` | 1 | configparser (built-in) | N/A |

---

## Quick Reference Links

### Primary Parsers:
- **endf-parserpy:** https://github.com/IAEA-NDS/endf-parserpy ⭐ **RECOMMENDED**
- **ENDFtk:** https://github.com/njoy/ENDFtk
- **SANDY:** https://github.com/luca-fiorito-11/sandy ⭐ **RECOMMENDED**

### Alternative Parsers:
- **OpenMC:** https://github.com/openmc-dev/openmc
- **PyNE:** https://github.com/pyne/pyne
- **NJOY21:** https://github.com/njoy/NJOY21
- **GNDStk:** https://github.com/njoy/GNDStk

### Supporting Libraries:
- **pandas:** https://github.com/pandas-dev/pandas
- **pyyaml:** https://github.com/yaml/pyyaml

---

## Notes

1. **ENDF-6 Format:** All `.endf` files follow the ENDF-6 format standard, regardless of data type (neutron, photon, decay, charged particles, etc.)

2. **File Naming Convention:** ENDF files use prefixes to indicate data type:
   - `dec-*` or `d-*` for decay data (most common - 3,827 files)
   - `n-*` for neutron data (558 files)
   - `g-*` for gamma production (222 files)
   - `tsl-*` for thermal scattering (114 files)
   - `photoat-*` or `atom-*` for photon/atomic data (200 files)
   - `e-*`, `p-*`, `a-*`, `t-*` for charged particle data (259 files)
   - `nfy-*`, `sfy-*` for fission yields (40 files)
   - `std-*` for standard reference data (11 files)

3. **Directory Structure:** ENDF-B-VIII.1 organizes files by data type and nuclide

4. **Current SMRForge Support:** ✅ SMRForge already integrates multiple parsers with fallback mechanisms, providing robust ENDF file handling for all file types

5. **File Count:** The directory contains ~5,135 ENDF files, making comprehensive parser support essential

