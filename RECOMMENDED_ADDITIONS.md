# Recommended Additions to SMRForge Package

Based on the Production Readiness Assessment, here are the top priorities for improving the package.

---

## 🔴 CRITICAL PRIORITIES (Blocking Production)

### 1. Testing Infrastructure & Coverage ⚠️ **MOST CRITICAL**

**Current State:** 
- Test coverage likely <20%
- Many tests are placeholders/skip tests
- No integration tests

**What to Add:**

#### A. Comprehensive Test Suite
- ✅ **Unit Tests**: Already started in `tests/`, but need expansion
  - Expand `test_neutronics.py` (already has good coverage)
  - Add tests for thermal-hydraulics
  - Add tests for safety/transients
  - Add tests for validation models
  - Add tests for convenience API

#### B. Integration Tests
```python
# tests/integration/test_full_workflow.py
def test_complete_reactor_analysis():
    """Test complete workflow from reactor creation to results"""
    # Create reactor → generate XS → solve → get results
    pass
```

#### C. Test Infrastructure Setup
- Add `pytest.ini` or `pyproject.toml` pytest configuration
- Add `coverage` configuration
- Add test fixtures for common reactor designs
- Add regression test data

#### D. Performance Benchmarking
```python
# tests/benchmarks/performance_tests.py
def test_solver_performance():
    """Ensure solver meets performance targets"""
    pass
```

**Estimated Effort:** 2-3 weeks
**Impact:** Enables CI/CD, ensures reliability

---

### 2. CI/CD Pipeline ⚠️ **CRITICAL**

**Current State:** No automated testing

**What to Add:**

#### A. GitHub Actions Workflow (`.github/workflows/ci.yml`)
```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.8", "3.9", "3.10", "3.11"]
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e ".[dev]"
      - run: pytest --cov=smrforge --cov-report=xml
      - uses: codecov/codecov-action@v3
```

#### B. Pre-commit Hooks (`.pre-commit-config.yaml`)
Already exists! Just needs activation:
```bash
pre-commit install
```

#### C. Automated Releases
- GitHub Actions workflow for PyPI releases
- Version tagging automation
- Changelog generation

**Estimated Effort:** 1 week
**Impact:** Ensures code quality, prevents regressions

---

## 🟡 HIGH PRIORITIES (Strongly Recommended)

### 3. Logging Framework

**Current State:** Basic error handling, no structured logging

**What to Add:**

```python
# smrforge/utils/logging.py
import logging
from pathlib import Path

def setup_logging(level: str = "INFO", log_file: Path = None):
    """Configure SMRForge logging"""
    logger = logging.getLogger("smrforge")
    # ... setup handlers
```

- Add logging throughout core modules
- Log solver iterations, convergence, warnings
- Log nuclear data fetching/caching
- Configurable log levels

**Estimated Effort:** 3-5 days
**Impact:** Better debugging, production monitoring

---

### 4. Complete Core Features

**Current State:** Some incomplete methods (e.g., Arnoldi)

**What to Add:**

#### A. Complete Arnoldi Method (Optional - Low Priority)
The power iteration method works well, but Arnoldi could be added for completeness.

#### B. Enhanced Error Messages
- User-friendly error messages
- Suggestions for fixing common issues
- Clear validation error messages

**Estimated Effort:** 1-2 weeks
**Impact:** Better user experience

---

### 5. API Documentation (Sphinx)

**Current State:** Basic README, no API docs

**What to Add:**

You already have `docs/conf.py` and `docs/index.rst`! Just need to:

1. Generate API documentation:
```bash
cd docs
sphinx-apidoc -o . ../smrforge
sphinx-build -b html . _build/html
```

2. Add docstrings to all public APIs
3. Add examples to docstrings
4. Deploy to Read the Docs or GitHub Pages

**Estimated Effort:** 1 week
**Impact:** Better developer experience

---

## 🟢 MEDIUM PRIORITIES (Nice to Have)

### 6. Visualization Module

**Current State:** Stub module

**What to Add:**

```python
# smrforge/visualization/plots.py
def plot_flux_distribution(flux: np.ndarray, geometry, **kwargs):
    """Plot neutron flux distribution"""
    pass

def plot_power_distribution(power: np.ndarray, geometry, **kwargs):
    """Plot power distribution"""
    pass

def plot_geometry(geometry, **kwargs):
    """Visualize reactor geometry"""
    pass
```

- Matplotlib-based plotting functions
- Plot flux, power, temperature distributions
- Geometry visualization
- Results comparison plots

**Estimated Effort:** 1-2 weeks
**Impact:** Better analysis capabilities

---

### 7. I/O Utilities

**Current State:** Stub module (though Pydantic serialization exists)

**What to Add:**

```python
# smrforge/io/import_export.py
def save_reactor(reactor, filepath: Path, format: str = "json"):
    """Save reactor design to file"""
    pass

def load_reactor(filepath: Path) -> ReactorSpecification:
    """Load reactor design from file"""
    pass

def export_results(results, filepath: Path, format: str = "hdf5"):
    """Export analysis results"""
    pass
```

- Reactor design import/export (JSON, YAML, HDF5)
- Results export (CSV, HDF5, Parquet)
- Import from other formats (OpenMC XML, etc.)

**Estimated Effort:** 1 week
**Impact:** Better interoperability

---

### 8. Enhanced Convenience API

**Current State:** Basic convenience functions exist

**What to Add (see USAGE.md for current convenience API):**

```python
# Already partially implemented, but could expand:
def compare_designs(designs: List[str]) -> pd.DataFrame:
    """Compare multiple designs side-by-side"""
    pass

def optimize_reactor(reactor, objective, constraints):
    """Optimize reactor design"""
    pass
```

**Estimated Effort:** 3-5 days
**Impact:** Easier to use

---

### 9. Example Gallery

**Current State:** One example exists (`examples/complete_integration_example.py`)

**What to Add:**

- More examples in `examples/`:
  - `basic_neutronics.py` - Simple k-eff calculation
  - `thermal_analysis.py` - Coupled neutronics-thermal
  - `safety_analysis.py` - Transient analysis
  - `optimization_example.py` - Design optimization
  - `custom_reactor.py` - Creating custom designs

**Estimated Effort:** 1 week
**Impact:** Better onboarding

---

### 10. Contributing Guide

**What to Add:**

`CONTRIBUTING.md` with:
- Development setup instructions
- Code style guidelines
- Testing requirements
- PR process
- Issue templates

**Estimated Effort:** 1-2 days
**Impact:** Better open-source collaboration

---

## 🔵 LOW PRIORITIES (Future Enhancements)

### 11. Optimization Module
- Design optimization algorithms
- Loading pattern optimization
- Parameter sweeps

### 12. Fuel Performance Module
- Fuel temperature calculations
- Swelling models
- Fission gas release

### 13. Control Systems Module
- Reactor control algorithms
- Protection systems
- Control rod worth

### 14. Economics Module
- Cost modeling
- LCOE calculations
- Economic analysis

---

## Recommended Implementation Order

### Phase 1: Foundation (3-4 weeks) - **DO THIS FIRST**
1. ✅ Testing Infrastructure (expand test suite, add fixtures)
2. ✅ CI/CD Pipeline (GitHub Actions)
3. ✅ Logging Framework

### Phase 2: Completeness (2-3 weeks)
4. ✅ API Documentation (Sphinx)
5. ✅ Enhanced Error Messages
6. ✅ Contributing Guide
7. ✅ Example Gallery

### Phase 3: Features (2-4 weeks)
8. ✅ Visualization Module
9. ✅ I/O Utilities
10. ✅ Enhanced Convenience API

### Phase 4: Advanced (as needed)
11. ✅ Optimization Module
12. ✅ Fuel Performance
13. ✅ Control Systems
14. ✅ Economics

---

## Quick Wins (Can Do Now)

These can be implemented quickly with high impact:

1. **Add CHANGELOG.md** - Track version history (30 min)
2. **Add CONTRIBUTING.md** - Help contributors (2 hours)
3. **Expand test coverage** - Add 10-20 more test cases (1 day)
4. **Add more examples** - 2-3 more example scripts (1 day)
5. **Set up GitHub Actions CI** - Basic CI pipeline (2 hours)

---

## Summary

**Top 3 Critical Items:**
1. 🔴 **Testing Infrastructure** (expand test suite, add fixtures)
2. 🔴 **CI/CD Pipeline** (GitHub Actions for automated testing)
3. 🟡 **Logging Framework** (structured logging throughout)

**Top 3 High-Impact Additions:**
1. 🟡 **API Documentation** (Sphinx - you already have the setup!)
2. 🟢 **Visualization Module** (plotting functions)
3. 🟢 **Example Gallery** (more usage examples)

Focus on Phase 1 first to establish a solid foundation, then move to Phase 2 for completeness.

