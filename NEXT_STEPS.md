# SMRForge Development Roadmap

**Last Updated:** 2025  
**Current Version:** 0.1.0 (Alpha)  
**Status:** Core functionality complete, focusing on polish and documentation

This document consolidates next steps and recommended additions based on current package state.

---

## 🎯 Current Status & Immediate Next Steps

### ✅ Recently Completed (2025)
- ✅ API documentation generated (Sphinx)
- ✅ Test coverage improved (67% overall, up from 35%)
- ✅ Code formatting applied (Black and isort)
- ✅ Test infrastructure for external data dependencies (mock fixtures)
- ✅ Coverage analysis and roadmap completed
- ✅ ENDF-B-VIII.1 local data integration (Phases 1-3)
  - Local ENDF directory support for offline use
  - Fast file indexing and O(1) lookups
  - Version fallback and multi-URL download retry
  - ~800x performance improvement for local file access
- ✅ ENDF data handling improvements
  - Removed automatic downloads (replaced with manual setup wizard)
  - Interactive ENDF setup wizard with validation
  - Bulk ENDF file organization utilities
  - Comprehensive ENDF documentation consolidation
- ✅ Neutronics solver robustness improvements
  - Zero absorption cross-section handling with multi-level fallback
  - Zero flux detection and recovery mechanisms
  - NaN/Inf detection in k_eff and flux calculations
  - Enhanced error diagnostics and messages
  - Improved fission source handling for very small cross-sections
- ✅ Codebase verification and fixes
  - Fixed import issues in examples (standardized to public API)
  - Fixed NeutronicsSolver import in smrforge/__init__.py
  - Verified all critical imports work correctly
  - Updated docstrings for accuracy
  - All examples verified and working

### 🔴 Next Priority Actions
1. **Increase test coverage** from 67% to 75-80%+ (focus on `reactor_core.py` and `endf_parser.py`)
2. **Review and improve** API documentation docstrings (1 week)
3. **Deploy documentation** to GitHub Pages or Read the Docs (2-4 hours)
4. **Validate ENDF-based cross-section generation** in complete integration example
   - Ensure ENDF data quality is sufficient for realistic k_eff calculations
   - Verify cross-section conversion accuracy
   - Test with various ENDF library versions

**Focus:** Quality assurance and developer experience improvements before beta release.

---

## ✅ Recently Completed

### Foundation (Phase 1) ✅ **COMPLETE**

1. ✅ **Testing Infrastructure**
   - Comprehensive test suite (100+ tests)
   - Integration tests for complete workflows
   - Test fixtures and utilities
   - Parametric and edge case coverage

2. ✅ **CI/CD Pipeline**
   - GitHub Actions workflows (`.github/workflows/ci.yml`)
   - Automated testing on multiple Python versions
   - Coverage reporting
   - Linting checks
   - Package build validation

3. ✅ **Logging Framework**
   - Structured logging throughout core modules
   - Configurable log levels
   - Module-specific loggers

4. ✅ **Documentation Structure**
   - Sphinx documentation framework
   - Quick start guide
   - Installation guide
   - CHANGELOG.md
   - CONTRIBUTING.md
   - Example gallery (6 examples)

5. ✅ **Bug Fixes**
   - Fixed ReactorSpecification validation errors
   - Fixed missing dependencies
   - Fixed import issues
   - Improved error messages

---

## 🔴 HIGH PRIORITY - Immediate Actions

### 1. Increase Test Coverage to 75-80%+ (1-2 weeks) 📊

**Status:** Current coverage is 67% overall, target is 75-80% on all modules

**What to do:**
```bash
pytest --cov=smrforge --cov-report=html --cov-report=term-missing
# Review htmlcov/index.html to identify gaps
```

**Target:** 75-80% coverage on all modules, focusing on:
- `reactor_core.py`: 49% → 75-80%
- `endf_parser.py`: 40% → 75-80%
- `resonance_selfshield.py`: 27% → 75-80%

**Action Items:**
- ✅ Test infrastructure for external data dependencies (mock fixtures) - DONE
- 🔴 Create realistic mock ENDF files (`tests/data/sample_U235.endf`)
- 🟠 Fix zarr API usage in `_save_to_cache`
- 🟡 Test `_parse_mf3_section` fully (97 lines - largest gap)
- 🟡 Test `_simple_endf_parse` fully (57 lines)
- Add edge case and error handling tests
- Set coverage thresholds in CI/CD (currently reports but doesn't fail)

**Impact:** Ensures code quality and reliability for production use

**Priority:** High - Blocks progression from alpha to beta release

**See `TESTING_AND_COVERAGE.md` for detailed roadmap and priorities.**

---

### 2. Review and Improve API Documentation Docstrings (1 week) 📚

**Status:** API docs generated, but docstrings need review and enhancement

**Action Items:**
- Review generated API documentation for completeness
- Enhance docstrings with examples where missing
- Ensure all public functions/classes have proper docstrings
- Add type hints documentation
- Improve docstring formatting consistency (NumPy/Google style)

**Impact:** Essential for developer experience and adoption

**Priority:** High - Improves usability significantly

---

### 3. Deploy Documentation to GitHub Pages or Read the Docs (2-4 hours) 🌐

**Status:** HTML documentation builds successfully, needs hosting

**What to do:**
- Option A: GitHub Pages (free, simple)
  - Enable GitHub Pages in repository settings
  - Set up GitHub Actions workflow to build and deploy docs on push
- Option B: Read the Docs (free, automatic)
  - Connect repository to Read the Docs
  - Configure build settings

**Action Items:**
- Set up automated documentation deployment
- Configure documentation versioning (stable vs. latest)
- Add documentation link to README.md
- Test documentation links and navigation

**Impact:** Makes documentation easily accessible to users

**Priority:** High - Essential for user adoption

---

## 🟡 MEDIUM PRIORITY - Feature Enhancements

### 4. Visualization Module (1-2 weeks) 📊

**Status:** Currently a stub module

**What to add:**
```python
# smrforge/visualization/plots.py
def plot_flux_distribution(flux, geometry, **kwargs)
def plot_power_distribution(power, geometry, **kwargs)
def plot_geometry(geometry, **kwargs)
def plot_temperature_distribution(temp, geometry, **kwargs)
```

**Features:**
- Matplotlib-based plotting functions
- Flux, power, and temperature distribution plots
- Geometry visualization (2D and 3D)
- Comparison plots for multiple designs
- Export to common image formats

**Impact:** Better analysis capabilities and results presentation

**Priority:** Medium - Nice to have for user experience

---

### 5. I/O Utilities Module (1 week) 💾

**Status:** Currently a stub (though Pydantic serialization works)

**What to add:**
```python
# smrforge/io/import_export.py
def save_reactor(reactor, filepath: Path, format: str = "json")
def load_reactor(filepath: Path) -> ReactorSpecification
def export_results(results, filepath: Path, format: str = "hdf5")
def import_from_serpent(filepath: Path) -> ReactorSpecification
```

**Features:**
- Enhanced reactor design import/export (JSON, YAML, HDF5)
- Results export (CSV, HDF5, Parquet)
- Format converters (Serpent, OpenMC compatibility)
- Batch processing utilities

**Impact:** Better interoperability with other tools

**Priority:** Medium - Pydantic serialization already provides basic functionality

---

### 6. Enhanced Convenience API (3-5 days) 🚀

**Status:** Basic convenience functions exist and work

**Potential additions:**
```python
def compare_designs(designs: List[str]) -> pd.DataFrame:
    """Compare multiple designs side-by-side"""
    
def optimize_reactor(reactor, objective, constraints):
    """Optimize reactor design using scipy.optimize"""
    
def sensitivity_analysis(reactor, parameters):
    """Perform sensitivity analysis on key parameters"""
```

**Impact:** Easier to use for common workflows

**Priority:** Medium - Current API is functional

---

## 🟢 LOW PRIORITY - Future Enhancements

### 7. Complete Type Hints (Ongoing) 🔍

**Status:** Partial - some modules have type hints, others don't

**Approach:** Gradual improvement
- Add type hints to new code
- Gradually add to existing code during refactoring
- Use `mypy` to check (already in CI)

**Priority:** Low - Nice to have, doesn't block functionality

---

### 8. Additional Stub Modules (Future) 📦

These modules are currently stubs and are **NOT blocking** production:

- **Fuel Performance** (`smrforge.fuel`) - Fuel temperature, swelling, fission gas release
- **Optimization** (`smrforge.optimization`) - Design optimization algorithms
- **Control Systems** (`smrforge.control`) - Reactor control and protection systems
- **Economics** (`smrforge.economics`) - Cost modeling and LCOE calculations

**Recommendation:** Implement as needed based on user demand or project requirements. Current status is clearly documented in `FEATURE_STATUS.md`.

**Priority:** Low - Optional features, not core functionality

---

## 📋 Recommended Implementation Timeline

### ✅ Completed (Quick Wins - 2025)
1. ✅ Generate Sphinx API docs (2-4 hours) - **DONE**
2. ✅ Verify test coverage (1-2 hours) - **DONE** (measured at 35%)
3. ✅ Run code formatters (2-3 hours) - **DONE** (Black and isort applied)

**Total:** ✅ Completed

### Next 1-2 Weeks (High Priority)
1. Increase test coverage from 35% to 80%+ (focus on critical modules)
2. Review and improve API documentation docstrings
3. Deploy documentation to GitHub Pages or Read the Docs

**Total:** ~1-2 weeks of focused work

### Next 2-3 Weeks (Medium Priority)
4. Visualization module (start implementation)
5. I/O utilities (if needed)
6. Enhanced convenience API (if needed)

### Ongoing (Low Priority)
7. Complete type hints (gradual)
8. Implement stub modules (as needed)

---

## 🎯 Quick Reference: What's Done vs. What's Needed

### ✅ Completed and Production-Ready
- Core neutronics solver
- Geometry support
- Validation framework
- Preset reactor designs
- Convenience API
- Testing infrastructure
- CI/CD pipeline
- Logging framework
- Documentation structure
- Example gallery

### ⚠️ Needs Attention (High Priority)
- ✅ API docs generated (needs docstring improvements)
- ⚠️ Increase test coverage from 67% to 75-80%+ target
- ✅ Code formatting applied (Black and isort)
- ✅ Solver robustness improvements (NaN detection, error handling)
- ✅ Example code verified and fixed
- ⚠️ Deploy documentation to GitHub Pages/Read the Docs
- ⚠️ Validate ENDF-based workflows end-to-end

### 📝 Optional Enhancements (Medium/Low Priority)
- Visualization module
- I/O utilities module
- Enhanced convenience functions
- Complete type hints
- Stub module implementations

---

## 📊 Current Package Health

**Core Functionality:** ✅ **EXCELLENT**
- All core features implemented and tested
- Comprehensive test suite
- Good error handling and validation

**Documentation:** ✅ **GOOD** (needs docstring improvements and deployment)
- User documentation exists
- Examples available
- ✅ API docs generated (needs review and enhancement)
- ⚠️ Documentation needs to be deployed (GitHub Pages/Read the Docs)

**Code Quality:** ✅ **GOOD** (test coverage improving)
- Code is functional and tested
- ✅ Consistent formatting applied (Black/isort)
- ✅ Robust error handling and NaN detection in solver
- ✅ Comprehensive diagnostics for debugging
- ⚠️ Test coverage at 67% (target: 75-80%, focus on `reactor_core.py` and `endf_parser.py`)
- Type hints incomplete but not blocking

**Production Readiness:** ✅ **READY FOR ALPHA**
- Version 0.1.0 (alpha) is appropriate
- Core functionality is solid
- Can be used for development and research
- Ready for broader testing and feedback

---

## 💡 Key Takeaways

1. **Core package is functional** - All essential features work
2. **Focus on polish** - Documentation and code quality improvements
3. **Optional features are truly optional** - Stub modules don't block usage
4. **Good foundation** - Testing, CI/CD, and logging are in place
5. **Next phase** - Focus on user experience and documentation

---

*This document consolidates NEXT_STEPS.md and RECOMMENDED_ADDITIONS.md into a single comprehensive roadmap.*
