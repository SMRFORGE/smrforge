# SMRForge Development Roadmap

**Last Updated:** 2024-12-23  
**Current Version:** 0.1.0 (Alpha)  
**Status:** Core functionality complete, focusing on polish and documentation

This document consolidates next steps and recommended additions based on current package state.

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

### 1. Generate Sphinx API Documentation ⚡ **QUICK WIN** (2-4 hours)

**Status:** Infrastructure exists, just needs execution

**What to do:**
```bash
cd docs
sphinx-apidoc -o . ../smrforge --separate
sphinx-build -b html . _build/html
```

**Action Items:**
- Run `sphinx-apidoc` to generate API docs
- Review and improve docstrings where needed
- Deploy to GitHub Pages or Read the Docs
- Add to CI/CD for automatic generation

**Impact:** Essential for developer experience

---

### 2. Verify Test Coverage (1-2 hours) 📊

**Status:** Tests exist, coverage not yet verified

**What to do:**
```bash
pytest --cov=smrforge --cov-report=html --cov-report=term-missing
# Review htmlcov/index.html
```

**Target:** 80%+ coverage on critical modules

**Action Items:**
- Measure current coverage
- Identify gaps in test coverage
- Add tests for uncovered critical paths
- Set coverage thresholds in CI/CD

**Impact:** Ensures code quality and reliability

---

### 3. Code Formatting and Style (2-3 hours) 🎨

**Status:** Formatters configured but not consistently applied

**What to do:**
```bash
# Run Black formatter
black smrforge/ tests/

# Run isort
isort smrforge/ tests/

# Verify formatting in CI (already configured)
```

**Action Items:**
- Run Black on entire codebase
- Run isort for import organization
- Fix any formatting inconsistencies
- Ensure CI passes formatting checks

**Impact:** Code consistency and maintainability

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

### This Week (High Priority)
1. ✅ Generate Sphinx API docs (2-4 hours)
2. ✅ Verify test coverage (1-2 hours)
3. ✅ Run code formatters (2-3 hours)

**Total:** ~1 day of focused work

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
- Generate actual API docs from Sphinx structure
- Verify test coverage meets 80%+ target
- Apply code formatting consistently

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

**Documentation:** ✅ **GOOD** (needs API docs generation)
- User documentation exists
- Examples available
- API docs structure ready (needs execution)

**Code Quality:** ⚠️ **GOOD** (needs formatting pass)
- Code is functional and tested
- Needs consistent formatting
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
