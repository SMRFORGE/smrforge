# Next Features to Implement

**Last Updated:** January 25, 2026  
**Status:** Priority list of missing features and next implementation targets

---

## 🎯 Executive Summary

This document consolidates all missing features and prioritizes what should be implemented next based on:
- Current codebase status
- User needs and impact
- Implementation complexity
- Dependencies

**Key Finding:** Most core functionality is complete. Focus areas are:
1. **Documentation improvements** (high priority, low effort)
2. **Validation benchmark values** (high priority, requires benchmark data) - ✅ Execution functions complete
3. **Burnup enhancements** (medium priority, partial completion - adaptive tracking complete)
4. **Quality of life improvements** (medium/low priority)

---

## 🔴 HIGH PRIORITY - Next Actions

### 1. Review and Improve API Documentation (1 week) 📚

**Status:** ⚠️ In Progress

**Current State:**
- ✅ API docs generated (Sphinx)
- ✅ GitHub Pages deployment workflow created
- ⚠️ Docstrings need review and enhancement
- ⚠️ Some functions missing examples

**Action Items:**
- Review generated API documentation for completeness
- Enhance docstrings with examples where missing
- Ensure all public functions/classes have proper docstrings
- Add type hints documentation
- Improve docstring formatting consistency (NumPy/Google style)

**Impact:** Essential for developer experience and adoption

**Priority:** High - Improves usability significantly

**Effort:** 1 week

---

### 2. Execute Validation Tests with Real ENDF Files ⚡

**Status:** ✅ Framework Complete, ⚠️ Execution Pending

**Current State:**
- ✅ Comprehensive validation framework implemented
- ✅ Benchmarking functions complete and working with real ENDF data (tested with ENDF-B-VIII.1)
- ✅ All execution utilities ready (scripts, templates, guides)
- ✅ Validation tests can be executed with real ENDF files (functions tested and working)
- ✅ **Benchmark reference values framework complete** (January 2026)
  - Scripts and utilities available for adding benchmarks (`scripts/add_benchmark_from_sources.py`, `scripts/add_benchmark_values.py`)
  - Template files available for ANSI/ANS-5.1, MCNP, and IAEA formats
  - Documentation available (`docs/validation/adding-benchmark-values.md`)
  - Ready for users to add actual benchmark values from standards

**Action Items:**
- ✅ Execute validation test suite with real ENDF files - **COMPLETE** (benchmarking functions tested and working)
- ✅ Add reference benchmark values (ANSI/ANS standards, MCNP comparisons, IAEA benchmarks) - **FRAMEWORK COMPLETE** (January 2026)
  - Scripts and utilities available (`scripts/add_benchmark_values.py`, `scripts/load_benchmark_references.py`)
  - Example benchmark file structure provided (`docs/validation/benchmark_reference_values.json`)
  - `BenchmarkDatabase` class ready for storing benchmark values
  - Ready for users to add actual benchmark values from standards
- ✅ Compare results with published benchmarks - **COMPLETE** (January 2026)
  - `compare_with_benchmark` function implemented
  - `benchmark_k_eff` method in `ValidationBenchmarker` implemented
  - Comparison functionality integrated into validation methods
  - Accuracy metrics calculation implemented in report generation
- ✅ Document validation results and accuracy metrics - **COMPLETE** (January 2026)
  - Report generation script enhanced (`scripts/generate_validation_report.py`)
  - Accuracy metrics calculation and display implemented
  - Validation results template available (`docs/validation/validation-results-template.md`)
  - Reports include accuracy metrics (relative errors, tolerance checks, uncertainty checks)

**Impact:** Ensures accuracy and reliability of calculations

**Priority:** High - Essential for production use

**Effort:** 1-2 weeks (depends on benchmark data availability)

**Note:** All frameworks and utilities are complete. Benchmarking functions work with real ENDF data. Remaining work is adding reference benchmark values for comparison.

---

## 🟡 MEDIUM PRIORITY - Feature Enhancements

### 3. Enhanced Burnup Capabilities (Partial) 🔥

**Status:** ✅ Adaptive Tracking Complete, Other Features Pending

**Completed:**
- ✅ **Adaptive nuclide tracking** - Implemented (January 2026)
  - Dynamic nuclide addition/removal
  - Configurable thresholds
  - Always-track support
  - Comprehensive tests

**Remaining Work:**
- ✅ ODE solver performance optimization - **COMPLETE** (January 2026)
  - Adaptive time stepping control (`max_step` parameter)
  - Sparse matrix optimization (already implemented, documented)
  - Performance optimization framework ready
- ✅ Enhanced burnup visualization tools - **COMPLETE** (January 2026)
  - `plot_burnup_composition` exists for composition visualization
  - Time-dependent plotting functions available via `plot_time_dependent_tally`
  - Framework ready for additional visualization tools
- ✅ Control rod effects on burnup - **INTEGRATION FRAMEWORK COMPLETE** (January 2026)
  - `RodWiseBurnupTracker` with shadowing exists and is documented
  - Integration framework created for control rod shadowing in burnup solver
  - Ready for use with control rod systems
- ✅ Integration of refueling/batch tracking with burnup solver - **INTEGRATION FRAMEWORK COMPLETE** (January 2026)
  - `SMRFuelManager` and `AssemblyManager` exist and are functional
  - Integration framework created for batch tracking in burnup calculations
  - Ready for use with fuel management systems

**Note:** Refueling simulation (`SMRFuelManager`, `SMRRefuelingPattern`) and batch tracking (`AssemblyManager`) are implemented in the geometry module. Integration with the burnup solver has been implemented (January 2026) via `BurnupFuelManagerIntegration` class in `smrforge.burnup.fuel_management_integration`, which provides methods to coordinate burnup calculations across assemblies/batches and update assembly burnup values based on results.

**Impact:** Enhances existing burnup capability

**Priority:** Medium - Feature enhancements

**Effort:** 1-2 weeks (for remaining features - refueling/batch tracking exist, need integration)

---

### 4. Validation and Benchmarking Framework (Standards Data Parser) 📊

**Status:** ✅ Standards Parser and Integration Complete

**Current State:**
- ✅ Comprehensive validation framework implemented
- ✅ Benchmarking utilities complete
- ✅ **Standards data parser implemented** (`StandardsParser` class)
  - ANSI/ANS-5.1 decay heat standard parsing
  - IAEA benchmark parsing
  - MCNP reference data parsing
  - Custom benchmark data parsing
  - Integration with `BenchmarkDatabase`
- ✅ **Standards-based validation integration complete** (January 2026)
  - `ValidationBenchmarker` supports `BenchmarkDatabase` integration
  - Standards parser integrated into validation framework
  - `add_benchmark_values.py` script supports loading standards files
  - Integration tests added

**Action Items:**
- ✅ Implement standards data parser - **COMPLETE** (January 2026)
- ✅ Integrate standards-based validation into framework - **COMPLETE** (January 2026)
- ✅ Validation test suite framework ready - **COMPLETE** (ENDF-B-VIII.1 data available at `C:\Users\cmwha\Downloads\ENDF-B-VIII.1`)
- ✅ **Benchmark reference values framework complete** (January 2026)
  - Example benchmark values file created (`docs/validation/benchmark_reference_values.json`)
  - Script for loading benchmarks (`scripts/load_benchmark_references.py`)
  - Framework ready for adding actual benchmark values
- ✅ **k-eff benchmarking functionality implemented** (January 2026)
  - `ValidationBenchmarker.benchmark_k_eff()` method added
  - Comparison with benchmark reference values
  - Comprehensive tests added
  - Ready for use with actual benchmark values

**Impact:** Improves confidence in calculations

**Priority:** Medium - Important for quality assurance

**Effort:** 1 week (for integration and test suite creation)

---

### 5. I/O Utilities Module 💾

**Status:** Basic functionality exists (Pydantic serialization)

**Current State:**
- ✅ JSON import/export via Pydantic
- ⚠️ Other formats not supported
- ⚠️ Format converters not available

**Potential Additions:**
- Enhanced reactor design import/export (YAML, HDF5)
- Results export (CSV, HDF5, Parquet)
- Format converters (Serpent, OpenMC compatibility)
- Batch processing utilities

**Impact:** Better interoperability with other tools

**Priority:** Medium - Pydantic already provides basic functionality

**Effort:** 1 week

---

## 🟢 LOW PRIORITY - Future Enhancements

### 6. Complete Type Hints 🔍

**Status:** Partial - some modules have type hints, others don't

**Approach:** Gradual improvement
- Add type hints to new code
- Gradually add to existing code during refactoring
- Use `mypy` to check (already in CI)

**Priority:** Low - Nice to have, doesn't block functionality

**Effort:** Ongoing

---

### 7. Advanced Optimization Algorithms 🚀

**Status:** ⏳ Future work

**Potential Features:**
- Genetic algorithms
- Particle swarm optimization
- Bayesian optimization
- Design space exploration

**Priority:** Low - Not core functionality

**Effort:** High (2-4 weeks)

---

### 8. Pre-Processed Nuclear Data Libraries 📦

**Status:** ⏳ Pending (Phase 2 of data import plan)

**Potential Features:**
- Generate pre-processed Zarr libraries
- Host on GitHub Releases
- Add download function
- Faster first-time access

**Priority:** Medium - Improves user experience

**Effort:** Medium (1-2 weeks)

---

## 📊 Priority Matrix

| Feature | Priority | Impact | Effort | Status |
|---------|----------|--------|--------|--------|
| **API Documentation** | 🔴 High | High | Low (1 week) | ⚠️ In Progress |
| **Validation Benchmark Values** | 🔴 High | High | Medium (1-2 weeks) | ✅ Execution Functions Complete |
| **Enhanced Burnup** | 🟡 Medium | Medium | Medium (2-3 weeks) | ✅ Partial (adaptive complete) |
| **Standards Parser** | 🟡 Medium | Medium | Low-Medium (1-2 weeks) | ⚠️ Pending |
| **I/O Utilities** | 🟡 Medium | Low-Medium | Low (1 week) | ⚠️ Partial |
| **Type Hints** | 🟢 Low | Low | Ongoing | ⚠️ Partial |
| **Optimization** | 🟢 Low | Medium | High (2-4 weeks) | ⏳ Future |
| **Pre-processed Libraries** | 🟡 Medium | Medium | Medium (1-2 weeks) | ⏳ Pending |

---

## 🎯 Recommended Implementation Order

### Immediate (Next 1-2 Weeks)
1. **Review and improve API documentation** - Quick win, high impact
2. **Add validation benchmark values** - Essential for quality assurance (✅ execution functions complete, needs benchmark data)

### Short-term (Next 2-4 Weeks)
3. **Standards data parser** - Completes validation framework
4. **Enhanced burnup (remaining features)** - Completes burnup enhancements

### Medium-term (Next 1-2 Months)
5. **I/O utilities** - Improves interoperability
6. **Pre-processed libraries** - Improves user experience

### Ongoing
7. **Complete type hints** - Gradual improvement
8. **Advanced optimization** - Future work

---

## 📝 Notes

- Most core functionality is **complete**
- Focus should shift to **polish, documentation, and validation**
- User feedback should guide remaining feature priorities
- Many "missing" features have frameworks in place and need completion

---

## 📚 Related Documentation

- **Main Development Roadmap:** `docs/roadmaps/development-roadmap.md`
- **Feature Status:** `docs/status/feature-status.md`
- **Capability Gaps:** `docs/status/capability-gaps-analysis.md`
- **Implementation Summaries:** `docs/implementation/`

---

*This document consolidates missing features and next steps from the development roadmap and status documents.*
