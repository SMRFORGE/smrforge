# Photon and Gamma Production Integration Summary

**Date:** January 2025  
**Status:** ✅ Complete

---

## ✅ Implementation Complete

### 1. Photon File Discovery in NuclearDataCache

**File:** `smrforge/core/reactor_core.py`

**Methods Added:**
- `_find_local_photon_file()` - Find photon atomic data file for an element
- `_build_photon_file_index()` - Build index of available photon files
- `list_available_photon_elements()` - List all available elements
- `get_photon_file()` - Get photon file path (fast lookup via index)
- `get_photon_cross_section()` - Get parsed photon cross-section data

**Features:**
- Scans `photoat-version.VIII.1/` directory
- Indexes files by element symbol (case-insensitive)
- Fast O(1) lookup via cached index
- Automatic file validation
- Supports standard ENDF filename patterns: `p-ZZZ_Element.endf`

**Usage:**
```python
from smrforge.core.reactor_core import NuclearDataCache

cache = NuclearDataCache(local_endf_dir=Path("path/to/ENDF-B-VIII.1"))

# List available elements
elements = cache.list_available_photon_elements()
print(f"Available photon data: {elements}")

# Get photon cross-section data
photon_data = cache.get_photon_cross_section("H")  # Hydrogen
if photon_data:
    sigma_pe, sigma_comp, sigma_pair, sigma_tot = photon_data.interpolate(1.0)  # 1 MeV
```

---

### 2. Photon Parser Integration with Gamma Transport Solver

**File:** `smrforge/gamma_transport/solver.py`

**Enhancements:**
- Updated `_initialize_cross_sections()` to load real photon data
- Material-to-element mapping (H2O → H, steel → Fe, etc.)
- Automatic fallback to placeholder if data not available
- Energy group interpolation from ENDF data
- Cross-section unit conversion (barn → 1/cm)

**Features:**
- Loads photon cross-sections from ENDF files via `NuclearDataCache`
- Interpolates to solver energy groups
- Converts units appropriately (with material density)
- Falls back gracefully if data not available
- Logs data source (real vs placeholder)

**Usage:**
```python
from smrforge.gamma_transport import GammaTransportSolver, GammaTransportOptions
from smrforge.geometry import PrismaticCore
from smrforge.core.reactor_core import NuclearDataCache

# Create cache with ENDF directory
cache = NuclearDataCache(local_endf_dir=Path("path/to/ENDF-B-VIII.1"))

# Create geometry
geometry = PrismaticCore(name="Shielding")
geometry.build_mesh(n_radial=10, n_axial=5)

# Create solver (will use real photon data if available)
options = GammaTransportOptions(n_groups=20)
solver = GammaTransportSolver(geometry, options, cache=cache)

# Solver automatically loads photon cross-sections for material
# (defaults to H2O, can be customized in _initialize_cross_sections)
```

---

### 3. Gamma Production Parser

**File:** `smrforge/core/gamma_production_parser.py`

**Classes:**
- `GammaProductionSpectrum` - Gamma spectrum for a reaction
- `GammaProductionData` - Complete gamma production data for a nuclide
- `ENDFGammaProductionParser` - Parser for ENDF gamma production files

**Features:**
- Parses MF=12 (prompt gamma production)
- Parses MF=13, 14 (delayed gamma production)
- Extracts gamma energy spectra
- Computes total gamma yields per reaction
- Supports multiple reactions (fission, capture, etc.)

**Methods:**
- `parse_file()` - Parse gamma production file
- `get_total_gamma_yield()` - Get total yield for a reaction
- `get_gamma_spectrum()` - Get energy spectrum for a reaction

**Usage:**
```python
from smrforge.core.gamma_production_parser import ENDFGammaProductionParser
from pathlib import Path

parser = ENDFGammaProductionParser()
gamma_data = parser.parse_file(Path("gammas-092_U_235.endf"))

# Get prompt gamma yield per fission
yield_fission = gamma_data.get_total_gamma_yield("fission", prompt=True)
print(f"Prompt gamma yield per fission: {yield_fission:.2f}")

# Get gamma spectrum
spectrum = gamma_data.get_gamma_spectrum("fission", prompt=True)
if spectrum:
    print(f"Gamma energies: {spectrum.energy} MeV")
    print(f"Intensities: {spectrum.intensity} gammas/fission")
```

---

### 4. Gamma Production File Discovery in NuclearDataCache

**File:** `smrforge/core/reactor_core.py`

**Methods Added:**
- `_find_local_gamma_production_file()` - Find gamma production file for a nuclide
- `get_gamma_production_data()` - Get parsed gamma production data

**Features:**
- Scans `gammas-version.VIII.1/` directory
- Supports standard filename pattern: `gammas-ZZZ_Element_AAA.endf`
- Automatic file validation
- Returns parsed `GammaProductionData` object

**Usage:**
```python
from smrforge.core.reactor_core import NuclearDataCache, Nuclide

cache = NuclearDataCache(local_endf_dir=Path("path/to/ENDF-B-VIII.1"))
u235 = Nuclide(Z=92, A=235)

# Get gamma production data
gamma_data = cache.get_gamma_production_data(u235)
if gamma_data:
    yield_fission = gamma_data.get_total_gamma_yield("fission", prompt=True)
    print(f"U-235 prompt gamma yield per fission: {yield_fission:.2f}")
```

---

## 🔗 Integration Points

### Gamma Transport ↔ Photon Data
- Gamma transport solver automatically loads photon cross-sections
- Uses material name to determine which element's data to load
- Interpolates ENDF data to solver energy groups
- Converts units appropriately

### Decay Heat ↔ Gamma Production
- Gamma production data can be used to compute accurate gamma source terms
- Prompt and delayed gamma spectra available
- Can integrate with decay heat calculator for comprehensive gamma source

### NuclearDataCache ↔ All Parsers
- Unified file discovery interface
- Consistent indexing and caching
- Fast O(1) lookups
- Automatic validation

---

## 📊 File Structure

```
smrforge/
├── core/
│   ├── photon_parser.py          # NEW: Photon atomic data parser
│   ├── gamma_production_parser.py # NEW: Gamma production parser
│   └── reactor_core.py            # UPDATED: Added photon/gamma file discovery
└── gamma_transport/
    └── solver.py                   # UPDATED: Integrated photon data loading
```

---

## ✅ Testing Status

- ✅ All modules import successfully
- ✅ No linting errors
- ✅ Type hints included
- ✅ Comprehensive docstrings
- ⚠️ Integration tests needed (when ENDF files available)

---

## 🎯 Next Steps

1. **Add Integration Tests**
   - Test photon file discovery with real ENDF files
   - Test gamma production file discovery
   - Test gamma transport solver with real photon data

2. **Enhance Material Mapping**
   - More sophisticated material-to-element mapping
   - Support for compound materials (e.g., H2O → H + O)
   - Material density database integration

3. **Gamma Source Integration**
   - Integrate gamma production data with decay heat calculator
   - Use prompt/delayed gamma spectra for accurate source terms
   - Support time-dependent gamma sources

---

## 📝 Notes

- Photon parser follows same patterns as other ENDF parsers
- Gamma production parser supports both prompt and delayed gammas
- File discovery uses same indexing strategy as TSL/decay/fission yields
- All parsers have graceful fallbacks if files not found
- Ready for integration with real ENDF files

---

*Implementation completed January 2025*

