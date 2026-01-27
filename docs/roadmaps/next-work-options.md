# Next Work Options - ENDF-B-VIII.1 Analysis Review

**Date:** January 18, 2026  
**Last Updated:** January 18, 2026  
**Based on:** ENDF_FILE_TYPES_ANALYSIS.md review

---

## ✅ Recently Completed (Status Update)

Based on recent work, the following HIGH and MEDIUM priority items have been **COMPLETED**:

1. ✅ **Thermal Scattering Laws (TSL)** - **COMPLETE**
   - ✅ Full ENDF MF=7 parser implemented (MT=2 and MT=4)
   - ✅ Real S(α,β) data extraction from ENDF files
   - ✅ File discovery and indexing
   - ✅ Integration with scattering matrix calculation
   - ✅ Temperature support with interpolation
   - ✅ Material name mapping

2. ✅ **Neutron Fission Yields** - **COMPLETE**
   - ✅ Fission yield parser implemented (`fission_yield_parser.py`)
   - ✅ File discovery and indexing
   - ✅ Integration with burnup solver
   - ✅ Independent and cumulative yields

3. ✅ **Decay Data** - **COMPLETE**
   - ✅ Decay parser implemented (`decay_parser.py`)
   - ✅ Gamma-ray spectrum parsing (MF=8, MT=460)
   - ✅ Beta spectrum parsing (MF=8, MT=455)
   - ✅ File discovery and indexing
   - ✅ Integration with burnup solver
   - ✅ Half-life and decay chain tracking

4. ✅ **Burnup Solver** - **COMPLETE**
   - ✅ Full burnup solver with Bateman equations
   - ✅ Cross-section updates based on composition
   - ✅ Spatial and energy-dependent flux integration
   - ✅ Complete capture transmutation

5. ✅ **Enhanced Decay Heat** - **COMPLETE**
   - ✅ Time-dependent decay heat calculator
   - ✅ Energy-weighted decay heat from gamma/beta spectra
   - ✅ Nuclide-by-nuclide contribution tracking

6. ✅ **Gamma Transport Solver** - **COMPLETE**
   - ✅ Multi-group gamma transport solver
   - ✅ Dose rate computation
   - ✅ Shielding calculations

---

## 🎯 Recommended Next Work Options

### Option 1: ✅ Enhance TSL Implementation - **COMPLETE** ⭐

**Status:** ✅ **COMPLETE** - Full ENDF MF=7 parser implemented

**What was done:**
- ✅ Implemented full ENDF MF=7 parser for S(α,β) tables
- ✅ Parse coherent elastic scattering (MT=2)
- ✅ Parse incoherent inelastic scattering (MT=4)
- ✅ Extract real temperature-dependent data
- ✅ Automatic fallback to placeholder if parsing fails

**Impact:** 
- **High** - Enables accurate thermal reactor calculations with real data
- Critical for LWR, HWR, and graphite-moderated reactor accuracy

**See `docs/implementation/thermal-scattering.md` and `docs/implementation/options-1-2-4-6.md` for details.**

---

### Option 2: ✅ Enhanced Decay Heat Calculations - **COMPLETE**

**Status:** ✅ **COMPLETE** - Comprehensive decay heat calculator implemented

**What was done:**
- ✅ Parse gamma-ray emission spectra from decay data (MF=8, MT=460)
- ✅ Parse beta spectra (MF=8, MT=455)
- ✅ Integrate energy spectra into decay heat calculation
- ✅ Generate time-dependent decay heat curves
- ✅ Support post-shutdown decay heat analysis
- ✅ Nuclide-by-nuclide contribution tracking

**Impact:**
- **Medium-High** - Enables accurate decay heat predictions
- Important for safety analysis and shutdown cooling

**See `docs/implementation/options-1-2-4-6.md` for details.**

---

### Option 3: Validation and Benchmarking Framework (Medium Impact, Low-Medium Effort)

**What:** Use real ENDF data + standards/reference benchmarks for validation and benchmarking

**Real ENDF available (Windows):** `C:\Users\cmwha\Downloads\ENDF-B-VIII.1`

**Current Status:**
- ✅ Real ENDF-B-VIII.1 parsing + end-to-end workflow validation is runnable
- ✅ “Standards/reference” benchmarking is supported via a benchmark database file (`--benchmarks`) with k-eff comparison implemented (extend with additional reference datasets as they become available)
- ✅ Validation reporting is standardized: `validate run` writes a text report + structured JSON results (beyond test output)

**What to do:**
- ✅ Add a reference/standards layer - **DONE**: `standards-version.VIII.1` directory is detected by `scan_endf_directory()` (reports `has_standards: true` and `standards_files` count). Standards files (std-*.endf) are available for validation use.
- ✅ Add benchmark cases with expected outputs - **DONE**: Benchmark database (`benchmarks/validation_benchmarks.json`) includes:
  - k-eff regression benchmark (`simple_neutronics_2g`)
  - Cross-section spot checks (U-235/U-238 thermal fission/capture) with tolerance bands
  - Extensible format for additional benchmarks (decay heat, gamma transport, etc.)
- ✅ Generate a structured validation report (text + JSON) - **DONE**: `scripts/run_validation.py` generates:
  - ✅ Pass/fail summary, runtimes, environment info (in JSON `metadata` + text report)
  - ✅ Discovered ENDF inventory via `scan_endf_directory()` (includes standards detection)
  - ✅ Benchmark deltas vs reference values (in `comparison_data` with relative errors, tolerance checks)
- ✅ Integrate into CI/CD pipeline - **DONE**: `.github/workflows/ci.yml` includes validation job that:
  - Runs validation tests (pytest)
  - Runs validation runner with benchmarks (if `LOCAL_ENDF_DIR` secret is set)
  - Uploads validation artifacts (reports + JSON) as GitHub Actions artifacts

**How to run the real-data validation now (PowerShell):**

```powershell
# Basic validation (no benchmarks)
smrforge validate run --endf-dir "C:\Users\cmwha\Downloads\ENDF-B-VIII.1" --verbose

# With benchmark comparisons
smrforge validate run `
  --endf-dir "C:\Users\cmwha\Downloads\ENDF-B-VIII.1" `
  --benchmarks "benchmarks\validation_benchmarks.json" `
  --output "validation_report.txt" `
  --verbose
```

**Standards data:** The `standards-version.VIII.1` directory is automatically detected. See `docs/validation/standards-data-availability.md` for details.

**Impact:**
- **Medium** - Improves confidence in calculations
- Important for quality assurance
- Enables systematic testing

**Effort:** Low-Medium (1-2 weeks)
- Standards data is relatively simple
- Can leverage existing parser infrastructure
- Testing framework already exists

**Dependencies:** None

---

### Option 4: ✅ Gamma Transport Solver - **COMPLETE**

**Status:** ✅ **COMPLETE** - Gamma transport solver implemented

**What was done:**
- ✅ Created gamma transport solver (multi-group diffusion)
- ✅ Integrate with decay heat for gamma source terms
- ✅ Support shielding calculations
- ✅ Dose rate computation
- ⚠️ Photon cross-sections use placeholder data (ready for real data)

**Future Enhancements:**
- Implement photon atomic data parser (`photoat-version.VIII.1`)
- Implement gamma production parser (`gammas-version.VIII.1`)
- Load real photon cross-sections

**Impact:**
- **Low-Medium** - Enables gamma shielding and transport
- Useful for radiation protection and shielding design

**See `docs/implementation/options-1-2-4-6.md` for details.**

---

### Option 5: Enhanced Burnup Capabilities (Medium Impact, Medium Effort)

**What:** Add advanced burnup features and optimizations

**Current Status:**
- ✅ Basic burnup solver complete
- ✅ Cross-section updates working
- ✅ Cross-section updates based on composition - **DONE**: Implemented `_update_cross_sections()` that weights nuclide-specific cross-sections by concentration
- ✅ Performance optimizations - **DONE**: Added cross-section caching, decay matrix caching, and vectorized flux integration
- ✅ Enhanced calculations - **DONE**: 
  - Fission rate now uses actual flux distribution instead of placeholder
  - Decay heat uses real gamma/beta spectra from decay data
  - Capture matrix uses cached cross-sections with proper energy mapping

**What to do:**
- ✅ Implement adaptive nuclide tracking - **DONE**: Full implementation with array resizing in `_add_nuclides()` and `_remove_nuclides()` methods. Nuclides are dynamically added/removed based on concentration thresholds and importance.
- ✅ Add refueling simulation capabilities - **DONE**: Enhanced `BurnupFuelManagerIntegration` with `run_multi_cycle_burnup()` supporting multiple cycles with refueling operations.
- ✅ Implement multiple fuel batch tracking - **DONE**: Enhanced batch tracking with flux distribution integration in `_update_assembly_burnup_values()`. Batch burnup summary via `get_batch_burnup_summary()`.
- ✅ Optimize ODE solver performance - **DONE**: Enhanced ODE solver with sparse matrix support, Jacobian computation for BDF/Radau methods, and adaptive time stepping control via `max_step` option.
- ✅ Add burnup visualization tools - **DONE**: New `smrforge/burnup/visualization.py` module with:
  - `plot_batch_comparison()` - Compare burnup across batches
  - `plot_refueling_cycles()` - Visualize multi-cycle evolution
  - `plot_control_rod_effects()` - Compare with/without control rods
  - `plot_burnup_dashboard_enhanced()` - Enhanced dashboard with batch comparison
- ✅ Support control rod effects on burnup - **DONE**: Added `set_control_rod_effects()` method to `BurnupSolver` with automatic shadowing calculation. Integrated into burnup calculation via `_apply_control_rod_effects()`.

**Impact:**
- **Medium** - Enhances existing burnup capability
- Enables more realistic reactor operation simulations
- Improves performance for large problems

**Effort:** Medium (2-3 weeks)
- Builds on existing burnup solver
- Requires careful design for nuclide tracking
- Performance optimization needed

**Dependencies:** Burnup solver (already complete)

---

### Option 6: ✅ Documentation and Testing Improvements - **COMPLETE**

**Status:** ✅ **COMPLETE** - Tests and examples added

**What was done:**
- ✅ Add unit tests for TSL parser
- ✅ Add unit tests for fission yield parser
- ✅ Add unit tests for decay parser
- ✅ Add integration tests for burnup solver
- ✅ Create usage examples for decay heat and gamma transport
- ✅ Comprehensive docstrings throughout

**Impact:**
- **High** - Improves code quality and usability
- Essential for beta release
- Reduces bugs and improves maintainability

**See `docs/implementation/options-1-2-4-6.md` for details.**

---

## 📊 Comparison Matrix

| Option | Impact | Effort | Priority | Dependencies | Timeline |
|--------|--------|--------|----------|--------------|----------|
| **1. Full TSL Parsing** | High | Medium | ⭐⭐⭐ | None | 2-3 weeks |
| **2. Decay Heat Enhancement** | Medium-High | Medium | ⭐⭐ | Decay parser | 1-2 weeks |
| **3. Validation Framework** | Medium | Low-Medium | ⭐⭐ | None | 1-2 weeks |
| **4. Gamma Transport** | Low-Medium | High | ⭐ | None | 4-6 weeks |
| **5. Enhanced Burnup** | Medium | Medium | ⭐⭐ | Burnup solver | 2-3 weeks |
| **6. Docs & Testing** | High | Low-Medium | ⭐⭐⭐ | None | 1-2 weeks |

---

## 🎯 Recommended Priority Order

### Immediate (Next 1-2 weeks)
1. **Option 6: Documentation and Testing** - Quick wins, high impact
2. **Option 1: Full TSL Parsing** - Complete the high-priority feature

### Short-term (Next 2-4 weeks)
3. **Option 2: Decay Heat Enhancement** - Builds on existing work
4. **Option 3: Validation Framework** - Quality assurance

### Medium-term (Next 1-2 months)
5. **Option 5: Enhanced Burnup** - Feature enhancements
6. **Option 4: Gamma Transport** - New capability (if needed)

---

## 💡 My Recommendation

**Start with Option 6 (Documentation & Testing) + Option 1 (Full TSL Parsing) in parallel:**

- **Option 6** provides immediate quality improvements with low effort
- **Option 1** completes the high-priority TSL feature with real data
- Both can be done simultaneously (different people or sequential)
- Sets up good foundation for beta release

**Then move to Option 2 (Decay Heat)** to enhance the burnup capabilities.

---

## 📝 Notes

- ✅ All HIGH and MEDIUM priority items from ENDF_FILE_TYPES_ANALYSIS.md are now **COMPLETE**
- ✅ Options 1, 2, 4, and 6 from this document are now **COMPLETE**
- Remaining items are either LOW priority or enhancements to existing features:
  - Photon cross-section parser (for real gamma transport data)
  - Gamma production parser (for accurate source terms)
  - Validation framework (using ENDF standards)
  - Enhanced burnup capabilities (adaptive nuclide tracking, refueling)
- Focus should shift to **validation, testing with real ENDF files, and performance optimization**
- Consider user feedback to prioritize remaining work

---

**Note:** This document is historical. Most items listed here are now complete. See `docs/roadmaps/next-steps.md` for current next steps.

---

*This analysis is based on ENDF_FILE_TYPES_ANALYSIS.md and current codebase status as of January 2025.  
Status updated January 2026 - Most high/medium priority items completed.*

