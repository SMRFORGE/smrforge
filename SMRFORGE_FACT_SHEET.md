# SMRForge Fact Sheet
**Small Modular Reactor Design and Analysis Toolkit**

---

## 🚀 Overview

SMRForge is a comprehensive Python toolkit for nuclear reactor design, analysis, and optimization with a focus on Small Modular Reactors (SMRs). Built with modern Python standards, it provides both high-level convenience APIs and low-level physics solvers for researchers and engineers.

---

## ✨ Key Features

### ✅ Production-Ready Core

| Feature | Description | Status |
|---------|-------------|--------|
| **Multi-Group Diffusion Solver** | Power iteration & Arnoldi eigenvalue methods | ✅ Stable (100% tested) |
| **Geometry Engine** | Prismatic & pebble bed cores, mesh generation | ✅ Stable (100% tested) |
| **Control Rod Geometry** | Positioning, reactivity worth, shutdown margin | ✅ Stable (100% tested) |
| **Assembly Management** | Fuel tracking, refueling patterns, cycle analysis | ✅ Stable (97% tested) |
| **Visualization** | 2D core layouts, flux/power distributions | ✅ Stable (83.5% tested) |
| **Validation Framework** | Pydantic-based input validation | ✅ Stable |
| **Preset Designs** | 4 reference HTGR designs (Valar-10, GT-MHR, HTR-PM, Micro-HTGR) | ✅ Stable |

### 🔬 Experimental (Well-Tested, API May Change)

| Feature | Test Coverage | Capabilities |
|---------|---------------|--------------|
| **Monte Carlo Transport** | 97.7% | Particle transport, k-eff calculations, tallies |
| **Thermal-Hydraulics** | 45+ tests | 1D channel models, fluid properties, heat transfer |
| **Safety Analysis** | 40+ tests | Transient simulations (LOFC, ATWS, RIA), point kinetics |
| **Uncertainty Quantification** | 55+ tests | Monte Carlo sampling, Sobol indices, sensitivity analysis |

---

## 📊 Test Coverage & Quality

- **Total Tests**: 200+ comprehensive test cases
- **Core Modules**: 90-100% test coverage
- **Experimental Modules**: 97%+ test coverage
- **Input Validation**: Pydantic-based validation throughout
- **Error Handling**: Comprehensive error messages and logging
- **Documentation**: Full API documentation with examples

---

## 🎯 Performance Highlights

### Rust-Powered Performance
SMRForge leverages **Rust-powered libraries** for critical performance gains:

| Library | Rust Implementation | Performance Benefit |
|---------|---------------------|---------------------|
| **Pydantic 2.0** | Rust core for validation | 5-50x faster validation than v1 |
| **Polars** | Rust-based DataFrame engine | 10-100x faster than pandas for data operations |
| **Rich** | Rust terminal library | Fast, beautiful console output |
| **uv** (installer) | Rust-based package manager | 10-100x faster package installation |

**Benefits:**
- ⚡ **Ultra-fast validation**: Pydantic's Rust core validates complex reactor specifications in microseconds
- 🚀 **Fast data processing**: Polars enables rapid cross-section data manipulation and analysis
- 💨 **Quick installation**: uv installs dependencies 10-100x faster than traditional pip
- 🎨 **Efficient I/O**: Rich provides fast, feature-rich terminal output without performance overhead

### Computational Efficiency
- **Sparse Matrix Operations**: Optimized using `scipy.sparse` for memory efficiency
- **Numba JIT Compilation**: Critical functions compiled for speed
- **Vectorized Operations**: NumPy-based for fast array operations
- **Efficient Algorithms**: Power iteration with convergence acceleration
- **Rust-Powered Libraries**: Leverage Rust for validation, data processing, and I/O operations

### Scalability
- Supports large core geometries (1000+ fuel blocks)
- Efficient memory usage with sparse matrices
- Parallel-ready architecture (NumPy/NumPy-based parallelism)
- Optimized for multi-group neutronics (up to 30+ energy groups)

### Accuracy
- Validated against reference reactor designs
- Physics-based models (diffusion theory, point kinetics)
- Conservation laws enforced (neutron balance, energy balance)
- Extensive validation test suite

---

## 💻 Technology Stack

| Category | Technologies |
|----------|--------------|
| **Core Language** | Python 3.8+ |
| **Scientific Computing** | NumPy, SciPy, Numba |
| **Data Handling** | Pandas, **Polars** (Rust), HDF5, Zarr |
| **Validation** | **Pydantic 2.0** (Rust core) |
| **Terminal I/O** | **Rich** (Rust) |
| **Package Manager** | pip, **uv** (Rust - recommended) |
| **Visualization** | Matplotlib, Plotly (optional) |
| **Testing** | pytest, pytest-cov |
| **Documentation** | Sphinx, ReadTheDocs |

**Note**: Rust-powered libraries (Pydantic, Polars, Rich, uv) provide significant performance improvements while maintaining Python's ease of use.

---

## 📦 Installation & Usage

### Quick Install
```bash
pip install smrforge
```

### One-Liner Usage
```python
import smrforge as smr

# Quick k-eff calculation
k = smr.quick_keff(power_mw=10, enrichment=0.195)

# Analyze preset design
results = smr.analyze_preset("valar-10")
```

### Advanced Usage
```python
from smrforge.neutronics.solver import MultiGroupDiffusion
from smrforge.presets.htgr import ValarAtomicsReactor

reactor = ValarAtomicsReactor()
solver = MultiGroupDiffusion(geometry, xs_data, options)
k_eff, flux = solver.solve_steady_state()
```

---

## 🏗️ Architecture Highlights

### Modular Design
- **Core Module**: Constants, materials database, resonance self-shielding
- **Neutronics**: Multi-group diffusion, Monte Carlo, transport solvers
- **Thermal-Hydraulics**: Channel models, fluid properties, heat transfer
- **Safety**: Transient analysis, point kinetics, decay heat
- **Geometry**: Core geometries, mesh generation, assembly management
- **Uncertainty**: Monte Carlo sampling, sensitivity analysis

### Design Principles
- ✅ **Type Safety**: Type hints throughout, Pydantic validation
- ✅ **Modularity**: Independent modules with clear interfaces
- ✅ **Extensibility**: Easy to add new features and solvers
- ✅ **Documentation**: Comprehensive docstrings and examples
- ✅ **Testing**: Extensive test coverage with edge cases

---

## 📈 Use Cases

### Research & Development
- Reactor design optimization
- Sensitivity studies
- Uncertainty quantification
- Benchmark comparisons

### Education & Training
- Teaching reactor physics
- Code validation exercises
- Design studies

### Industry Applications
- Pre-design studies
- Parameter sensitivity analysis
- Concept evaluation
- Design iteration

---

## 🔧 Key Capabilities

### Neutronics
- Multi-group neutron diffusion (power iteration, Arnoldi)
- Monte Carlo particle transport (3D geometry)
- Eigenvalue (k-eff) calculations
- Flux and power distribution
- Reaction rate tallies

### Thermal-Hydraulics
- 1D channel flow models
- Porous media flow (pebble beds)
- Fuel rod thermal conduction
- Fluid properties (helium, water, etc.)
- Conjugate heat transfer

### Safety Analysis
- Point kinetics with temperature feedback
- Transient scenarios (LOFC, ATWS, RIA)
- Decay heat calculations (ANS standard)
- Temperature-dependent reactivity feedback

### Uncertainty Quantification
- Monte Carlo sampling
- Latin Hypercube sampling
- Sobol sequence (quasi-Monte Carlo)
- Global sensitivity analysis (Sobol indices, Morris screening)
- Visualization tools

### Geometry & Mesh
- Prismatic core geometries
- Pebble bed core geometries
- Adaptive mesh refinement
- Mesh quality evaluation
- Import/export (JSON, OpenMC XML, Serpent)

---

## 📚 Documentation & Support

- **Online Documentation**: [smrforge.readthedocs.io](https://smrforge.readthedocs.io)
- **API Reference**: Complete with examples
- **Example Scripts**: 11+ working examples
- **Quick Start Guide**: Get started in minutes
- **GitHub Repository**: [github.com/cmwhalen/smrforge](https://github.com/cmwhalen/smrforge)

---

## 🌟 Why SMRForge?

### ✅ Advantages

1. **Easy to Use**: One-liner convenience functions + powerful low-level APIs
2. **Well-Tested**: 200+ tests with high coverage
3. **Modern Python**: Type hints, Pydantic validation, clean code
4. **Rust-Powered Performance**: Leverages Rust implementations for validation, data processing, and I/O (5-100x speedups)
5. **Comprehensive**: Neutronics, thermal-hydraulics, safety, UQ in one toolkit
6. **Open Source**: MIT License, actively developed
7. **Well-Documented**: Full API docs, examples, tutorials
8. **Validated**: Tested against reference designs
9. **Extensible**: Modular design, easy to extend
10. **Fast Installation**: uv package manager for 10-100x faster dependency installation

### 🎯 Target Users

- Nuclear engineering researchers
- Reactor design engineers
- Graduate students
- Code developers
- Educators

---

## 📊 Project Statistics

| Metric | Value |
|--------|-------|
| **Python Version** | 3.8+ |
| **License** | MIT |
| **Development Status** | Alpha (0.1.0) |
| **Test Coverage** | 90-100% (core modules) |
| **Total Tests** | 200+ |
| **Example Scripts** | 11+ |
| **Preset Designs** | 4 |
| **Lines of Code** | ~15,000+ |
| **Modules** | 15+ |
| **Dependencies** | 15 core, 5+ optional |

---

## 🚀 Getting Started

```bash
# Install
pip install smrforge

# Run example
python -c "import smrforge as smr; print(smr.__version__)"

# Analyze preset
python -c "import smrforge as smr; results = smr.analyze_preset('valar-10'); print(results['k_eff'])"
```

---

## 📞 Contact & Links

- **GitHub**: [github.com/cmwhalen/smrforge](https://github.com/cmwhalen/smrforge)
- **Documentation**: [smrforge.readthedocs.io](https://smrforge.readthedocs.io)
- **Issues**: [github.com/cmwhalen/smrforge/issues](https://github.com/cmwhalen/smrforge/issues)
- **License**: MIT

---

## 🎨 Quick Reference

### Stable Features
- Multi-group diffusion solver
- Geometry engine (prismatic & pebble bed)
- Control rod geometry
- Assembly management
- Visualization
- Validation framework
- Preset reactor designs

### Experimental Features (API may change)
- Monte Carlo transport (97.7% tested)
- Thermal-hydraulics (45+ tests)
- Safety analysis (40+ tests)
- Uncertainty quantification (55+ tests)

---

**Version**: 0.1.0 | **Last Updated**: 2024 | **Status**: Active Development

*SMRForge - Empowering SMR Design and Analysis*

