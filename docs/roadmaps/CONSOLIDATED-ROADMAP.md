# SMRForge Consolidated Roadmap

**Last Updated:** January 2026  
**Status:** Comprehensive view of completed work, pending tasks, and future feature suggestions

---

## 📋 Executive Summary

This document consolidates all roadmap information from multiple sources to provide a unified view of:
- ✅ **Completed Features** - What's done and ready
- ⚠️ **Pending Tasks** - What still needs to be done
- 💡 **Future Features** - Pain point-driven suggestions for reactor development

**Current Status:** SMRForge is **production-ready for alpha** with 79.2% test coverage, comprehensive CLI, and all core functionality implemented. Remaining work focuses on polish, documentation, and addressing workflow pain points.

---

## ✅ Major Completed Features

### Core Functionality (Complete)
- ✅ Comprehensive ENDF data parsing (TSL, fission yields, decay data, photon, gamma production)
- ✅ Burnup solver with adaptive nuclide tracking
- ✅ Decay heat calculator
- ✅ Gamma transport solver
- ✅ Multi-group diffusion neutronics
- ✅ Advanced geometry support (HTGR, LWR SMR, MSR, compact cores)
- ✅ Thermal-hydraulics analysis
- ✅ Safety analysis and transients (LOFC, ATWS, RIA, LOCA)
- ✅ Advanced visualization (3D, animations, comparisons)
- ✅ Validation framework with benchmarking
- ✅ Comprehensive CLI with nested subcommands
- ✅ Web dashboard with dark/gray mode
- ✅ Data downloader with parallel downloads
- ✅ Configuration management
- ✅ Workflow scripts support
- ✅ Interactive shell mode
- ✅ Tab completion (Bash/Zsh/PowerShell)

### Test Coverage
- ✅ **79.2% overall coverage** (target: 75-80% achieved)
- ✅ All priority modules at 75-80%+ coverage
- ✅ Critical modules exceeding targets (reactor_core.py: 86.5%, endf_parser.py: 97.3%)

---

## ⚠️ Pending Tasks - What Still Needs To Be Done

### 🔴 High Priority (Immediate Actions)

#### 1. API Documentation Review (1 week)
**Status:** ⚠️ Partially Complete  
**Progress:** Enhanced convenience functions, CLI docstrings improved

**Remaining Work:**
- Review all public API docstrings for completeness
- Add missing `Raises:` sections to functions that raise exceptions
- Add examples to all public functions
- Ensure consistent docstring formatting (Google/NumPy style)
- Verify API docs generated correctly from docstrings

**Impact:** Essential for developer experience and adoption  
**Effort:** 1 week

---

#### 2. Execute Validation Tests with Real Data (1-2 weeks)
**Status:** ✅ Framework Complete, ⚠️ Execution Pending  
**Progress:** All validation frameworks, scripts, and utilities ready

**Remaining Work:**
- Execute validation test suite with real ENDF-B-VIII.1 files
- Add benchmark reference values from:
  - ANSI/ANS-5.1 standards (decay heat)
  - MCNP comparisons (gamma transport)
  - IAEA benchmarks (burnup, k-eff)
- Generate validation reports with accuracy metrics
- Document validation results and comparison with benchmarks

**Note:** Framework is complete, execution requires ENDF files and benchmark data.  
**Tools Available:**
- `scripts/run_validation.py` - Validation test runner
- `scripts/add_benchmark_values.py` - Add benchmark values interactively
- `scripts/load_benchmark_references.py` - Load benchmarks from files
- `scripts/generate_validation_report.py` - Generate validation reports
- `docs/validation/adding-benchmark-values.md` - Complete guide

**Impact:** Ensures accuracy and reliability of calculations  
**Effort:** 1-2 weeks (depends on benchmark data availability)

---

### 🟡 Medium Priority (Feature Enhancements)

#### 3. Enhanced I/O Utilities (1 week)
**Status:** ⚠️ Partial - Basic JSON via Pydantic exists

**Remaining Work:**
- Enhanced reactor design export (HDF5, YAML)
- Results export (CSV, HDF5, Parquet) via CLI
- Format converters for interoperability:
  - Serpent compatibility (import/export)
  - OpenMC compatibility (import/export)
  - MCNP format conversion

**Impact:** Better interoperability with other nuclear codes  
**Effort:** 1 week

---

#### 4. Pre-Processed Nuclear Data Libraries (1-2 weeks)
**Status:** ⏳ Pending (Phase 2 of data import plan)

**What:** Generate and host pre-processed Zarr libraries for faster first-time access

**Benefits:**
- Faster initial setup (no parsing on first use)
- Reduced disk space (compressed Zarr format)
- Consistent data format across users

**Implementation:**
- Create pre-processing pipeline
- Generate Zarr libraries from ENDF-B-VIII.1
- Host on GitHub Releases or cloud storage
- Add download function to CLI

**Impact:** Significantly improves user experience  
**Effort:** 1-2 weeks

---

### 🟢 Low Priority (Future Enhancements)

#### 5. Complete Type Hints (Ongoing)
**Status:** ⚠️ Partial

**Approach:** Gradual improvement
- Add type hints to new code
- Gradually add to existing code during refactoring
- Use `mypy` to check (already in CI)

**Effort:** Ongoing

---

#### 6. Advanced Optimization Algorithms (2-4 weeks)
**Status:** ⏳ Future work

**Potential Features:**
- Genetic algorithms for design optimization
- Particle swarm optimization
- Bayesian optimization
- Design space exploration tools

**Priority:** Low - scipy.optimize covers most needs  
**Effort:** 2-4 weeks

---

## 💡 Future Features - Addressing Common Pain Points

Based on reactor development, prototyping, and simulation workflows, here are feature suggestions that address real pain points:

### 🔧 Workflow & Productivity Pain Points

#### 1. **Parameter Sweep & Sensitivity Analysis Workflow** ⚡
**Pain Point:** Manually running multiple simulations with different parameters is time-consuming and error-prone.

**Proposed Feature:**
```python
# CLI command
smrforge sweep --reactor reactor.json \
    --params enrichment:0.10:0.25:0.05,power:50:100:10 \
    --analysis keff,burnup \
    --output results/sweep/
```

**Benefits:**
- Automated parameter sweeps
- Parallel execution support
- Results aggregation and visualization
- Statistical analysis (correlation, sensitivity)
- Export to CSV/Parquet for further analysis

**Implementation:**
- Extend existing UQ framework
- Add CLI command for sweeps
- Integration with batch processing
- Result comparison and visualization tools

**Effort:** 2-3 weeks  
**Impact:** High - Saves hours of manual work

---

#### 2. **Design Comparison & Trade Studies** 📊
**Pain Point:** Comparing multiple design variants requires manual data collection and analysis.

**Proposed Feature:**
```python
# Enhanced compare command
smrforge reactor compare \
    --designs design1.json design2.json design3.json \
    --metrics keff,power_density,temperature_peak,cycle_length \
    --output comparison_report.html \
    --visualize
```

**Benefits:**
- Automated multi-design comparison
- Side-by-side metrics comparison
- Visualization of trade-offs
- Export to HTML/PDF reports
- Pareto front analysis

**Implementation:**
- Enhance existing `compare_designs()` function
- Add comprehensive metrics calculation
- Create comparison visualization tools
- Generate formatted reports

**Effort:** 1-2 weeks  
**Impact:** High - Essential for design decisions

---

#### 3. **Template-Based Reactor Design Library** 📚
**Pain Point:** Starting from scratch for each design iteration is inefficient.

**Proposed Feature:**
```python
# Template system
smrforge reactor template create --from preset valar-10 --output template.json
smrforge reactor template modify template.json --param enrichment=0.20
smrforge reactor template validate template.json
```

**Benefits:**
- Reusable design templates
- Parameterized designs
- Template validation
- Template sharing (via GitHub/templates directory)
- Version control for design evolution

**Implementation:**
- Extend preset system
- Add template management CLI commands
- Template validation framework
- Template repository structure

**Effort:** 1 week  
**Impact:** Medium-High - Accelerates design iteration

---

#### 4. **Simulation Checkpointing & Resume** 💾
**Pain Point:** Long-running simulations are lost if interrupted, wasting computational resources.

**Proposed Feature:**
```python
# Automatic checkpointing
burnup_options = BurnupOptions(
    time_steps=[0, 365, 730, 1095],
    checkpoint_interval=100,  # Checkpoint every 100 days
    checkpoint_dir="checkpoints/"
)

# Resume from checkpoint
solver = BurnupSolver(reactor, options)
solver.resume_from_checkpoint("checkpoints/checkpoint_365days.h5")
```

**Benefits:**
- Automatic checkpointing during long simulations
- Resume from any checkpoint
- Fault tolerance
- Time travel debugging (inspect intermediate states)
- Distributed computation support

**Implementation:**
- Add checkpointing to BurnupSolver
- HDF5/Zarr checkpoint format
- CLI support for resume
- Checkpoint management utilities

**Effort:** 2 weeks  
**Impact:** High - Critical for production workflows

---

### 📐 Design & Analysis Pain Points

#### 5. **Automated Design Constraints & Validation** ✅
**Pain Point:** Manual checking of design constraints (power limits, temperature limits, etc.) is error-prone.

**Proposed Feature:**
```python
# Design validation
constraints = {
    "max_power_density": 100.0,  # W/cm³
    "max_temperature": 1200.0,   # K
    "min_k_eff": 1.0,
    "max_burnup": 50.0           # MWd/kg
}

validation = reactor.validate(constraints)
if not validation.passed:
    print(validation.violations)
```

**Benefits:**
- Automated constraint checking
- Design rule validation
- Safety margin analysis
- Regulatory compliance checks
- Integration with optimization

**Implementation:**
- Constraint validation framework
- Pre-defined constraint sets (regulatory, safety)
- Integration with reactor analysis
- CLI validation command

**Effort:** 1-2 weeks  
**Impact:** Medium-High - Prevents design errors

---

#### 6. **Real-Time Analysis Monitoring** 📡
**Pain Point:** Long-running analyses provide no feedback, making it unclear if they're progressing or stuck.

**Proposed Feature:**
```python
# Real-time monitoring
smrforge reactor analyze --reactor reactor.json \
    --monitor \
    --update-interval 5 \
    --output progress.json

# In another terminal
smrforge monitor progress.json
```

**Benefits:**
- Real-time progress updates
- Performance metrics (iterations/sec, convergence rate)
- Early detection of convergence issues
- Resource usage monitoring
- Cancel/restart capability

**Implementation:**
- Progress tracking framework
- WebSocket/SSE for real-time updates
- Monitoring CLI command
- Dashboard integration

**Effort:** 2 weeks  
**Impact:** Medium - Improves user experience

---

#### 7. **Cross-Section Library Management** 📚
**Pain Point:** Managing multiple cross-section libraries (ENDF-B-VIII.0, VIII.1, JEFF-3.3, JENDL-5) is complex.

**Proposed Feature:**
```python
# Library management
smrforge data library list
smrforge data library switch ENDF-B-VIII.1
smrforge data library compare ENDF-B-VIII.0 ENDF-B-VIII.1 --nuclide U235
smrforge data library merge --libraries VIII.0 VIII.1 --output merged
```

**Benefits:**
- Easy library switching
- Library comparison tools
- Selective library merging
- Version management
- Library validation

**Implementation:**
- Library management CLI commands
- Comparison utilities
- Merge functionality
- Library metadata system

**Effort:** 1-2 weeks  
**Impact:** Medium - Improves data management

---

### 🔬 Research & Development Pain Points

#### 8. **Reproducibility & Experiment Tracking** 🔬
**Pain Point:** Tracking experiments, parameters, and results for reproducibility is manual and error-prone.

**Proposed Feature:**
```python
# Experiment tracking
smrforge experiment init --name "enrichment_sweep_v2"
smrforge experiment run --reactor reactor.json --params enrichment=0.20
smrforge experiment log --notes "Baseline case"
smrforge experiment compare experiment1 experiment2
```

**Benefits:**
- Automatic experiment tracking
- Parameter versioning
- Result provenance
- Reproducibility guarantees
- Experiment comparison

**Implementation:**
- Experiment tracking framework
- Metadata capture
- SQLite/JSON experiment database
- CLI commands for experiment management

**Effort:** 2 weeks  
**Impact:** Medium-High - Essential for research

---

#### 9. **Surrogate Model Generation** 🤖
**Pain Point:** Full physics simulations are too slow for optimization and uncertainty quantification.

**Proposed Feature:**
```python
# Surrogate model generation
smrforge surrogate train \
    --design-space enrichment:0.10:0.25,power:50:100 \
    --samples 100 \
    --output surrogate_model.pkl \
    --method gaussian_process

# Fast surrogate evaluation
results = surrogate_model.predict(enrichment=0.20, power=75)
```

**Benefits:**
- Fast approximate calculations
- Enables global optimization
- Uncertainty propagation
- Sensitivity analysis
- Design space exploration

**Implementation:**
- Integration with scikit-learn
- Sample generation (Latin Hypercube, etc.)
- Model training pipeline
- Surrogate solver wrapper

**Effort:** 3-4 weeks  
**Impact:** High - Enables new analysis capabilities

---

#### 10. **Multi-Physics Coupling Framework** 🔗
**Pain Point:** Neutronics, thermal-hydraulics, and burnup are analyzed separately, missing important feedback.

**Proposed Feature:**
```python
# Coupled analysis
coupling = MultiPhysicsCoupling(
    neutronics_solver=neutronics_solver,
    thermal_solver=thermal_solver,
    burnup_solver=burnup_solver,
    coupling_scheme="iterative",
    convergence_tolerance=1e-4
)

results = coupling.solve(time_steps=[0, 365, 730])
```

**Benefits:**
- Physically consistent results
- Temperature feedback effects
- Doppler feedback
- Density feedback
- Realistic reactor behavior

**Implementation:**
- Coupling framework design
- Iterative coupling algorithms
- Convergence monitoring
- CLI support

**Effort:** 4-6 weeks  
**Impact:** Very High - Enables realistic simulations

---

### 🚀 Advanced Capabilities

#### 11. **GPU Acceleration for Large Problems** ⚡
**Pain Point:** Large 3D problems are computationally expensive on CPU.

**Proposed Feature:**
```python
# GPU-accelerated solver
solver = MultiGroupDiffusion(
    geometry=geometry,
    cross_sections=xs_data,
    device="cuda"  # or "cpu"
)
```

**Benefits:**
- 10-100x speedup for large problems
- Enables 3D full-core simulations
- Faster parameter sweeps
- Real-time visualization updates

**Implementation:**
- CuPy/CLArray integration
- GPU-optimized matrix operations
- Memory management
- Fallback to CPU

**Effort:** 4-6 weeks  
**Impact:** High - Enables new problem sizes

---

#### 12. **Distributed Computing Support** 🌐
**Pain Point:** Parameter sweeps and large analyses require more computational resources than available locally.

**Proposed Feature:**
```python
# Distributed execution
smrforge sweep --reactor reactor.json \
    --params enrichment:0.10:0.25:0.05 \
    --backend dask \
    --cluster tcp://scheduler:8786 \
    --workers 8
```

**Benefits:**
- Scale to available resources
- Cloud deployment support
- Cluster/HPC integration
- Automatic load balancing

**Implementation:**
- Dask/Ray integration
- Task distribution framework
- Result aggregation
- Cloud deployment guides

**Effort:** 3-4 weeks  
**Impact:** Medium - Enables larger analyses

---

#### 13. **Interactive Design Exploration** 🎨
**Pain Point:** Exploring design space interactively requires writing scripts.

**Proposed Feature:**
```python
# Jupyter widget for interactive design
from smrforge.widgets import ReactorDesigner

designer = ReactorDesigner()
designer.show()  # Interactive sliders, live updates
```

**Benefits:**
- Interactive parameter adjustment
- Real-time visualization
- Intuitive design exploration
- Teaching/learning tool

**Implementation:**
- Jupyter widgets (ipywidgets)
- Live solver integration
- Visualization updates
- Notebook templates

**Effort:** 2-3 weeks  
**Impact:** Medium - Improves user experience

---

## 📊 Priority Matrix for Future Features

| Feature | Pain Point Severity | Impact | Effort | Priority | Suggested Timeline |
|---------|-------------------|--------|--------|----------|-------------------|
| **Parameter Sweep Workflow** | High | High | Medium (2-3w) | 🔴 High | Next 1-2 months |
| **Design Comparison & Trade Studies** | High | High | Low (1-2w) | 🔴 High | Next 1 month |
| **Checkpointing & Resume** | High | High | Medium (2w) | 🔴 High | Next 1-2 months |
| **Design Constraints & Validation** | Medium | Medium-High | Low-Med (1-2w) | 🟡 Medium | Next 2-3 months |
| **Real-Time Monitoring** | Medium | Medium | Medium (2w) | 🟡 Medium | Next 2-3 months |
| **Template Library** | Medium | Medium-High | Low (1w) | 🟡 Medium | Next 1-2 months |
| **Experiment Tracking** | Medium | Medium-High | Medium (2w) | 🟡 Medium | Next 2-3 months |
| **Cross-Section Library Management** | Medium | Medium | Low-Med (1-2w) | 🟡 Medium | Next 2-3 months |
| **Surrogate Models** | Low-Medium | High | High (3-4w) | 🟢 Low | Future (6+ months) |
| **Multi-Physics Coupling** | Low-Medium | Very High | Very High (4-6w) | 🟢 Low | Future (6+ months) |
| **GPU Acceleration** | Low | High | Very High (4-6w) | 🟢 Low | Future (6+ months) |
| **Distributed Computing** | Low | Medium | High (3-4w) | 🟢 Low | Future (6+ months) |
| **Interactive Design Exploration** | Low | Medium | Medium (2-3w) | 🟢 Low | Future (6+ months) |

---

## 🎯 Recommended Implementation Roadmap

### Phase 1: Immediate (Next 1 Month)
1. ✅ Complete API documentation review
2. ✅ Execute validation tests with real data
3. 🆕 **Parameter Sweep Workflow** - Addresses common workflow pain point
4. 🆕 **Design Comparison & Trade Studies** - Essential for design decisions

### Phase 2: Short-term (Next 2-3 Months)
5. 🆕 **Checkpointing & Resume** - Critical for production workflows
6. 🆕 **Template Library** - Accelerates design iteration
7. 🆕 **Design Constraints & Validation** - Prevents design errors
8. Enhanced I/O utilities (Serpent/OpenMC converters)

### Phase 3: Medium-term (Next 3-6 Months)
9. 🆕 **Real-Time Monitoring** - Improves user experience
10. 🆕 **Experiment Tracking** - Essential for research
11. 🆕 **Cross-Section Library Management** - Improves data management
12. Pre-processed nuclear data libraries

### Phase 4: Long-term (6+ Months)
13. 🆕 **Surrogate Model Generation** - Enables new analysis capabilities
14. 🆕 **Multi-Physics Coupling** - Enables realistic simulations
15. GPU acceleration
16. Distributed computing support
17. Interactive design exploration

---

## 📝 Notes

- **User Feedback Priority:** Features should be prioritized based on actual user needs. This roadmap is a starting point.
- **Incremental Delivery:** Many features can be delivered incrementally (e.g., basic parameter sweep first, advanced analysis later).
- **Community Contributions:** Some features (GPU acceleration, distributed computing) may benefit from community contributions.
- **Research Needs:** Surrogate models and multi-physics coupling are research-oriented features that may require academic collaboration.

---

## 📚 Related Documentation

- **Development Roadmap:** `docs/roadmaps/development-roadmap.md` - Detailed status of all features
- **Next Features:** `docs/roadmaps/NEXT-FEATURES.md` - Immediate next steps
- **CLI Enhancement Plan:** `docs/roadmaps/cli-enhancement-plan.md` - CLI feature status
- **Feature Status:** `docs/status/feature-status.md` - Comprehensive feature tracking
- **Capability Gaps:** `docs/status/capability-gaps-analysis.md` - Missing capabilities analysis

---

*This consolidated roadmap merges information from:*
- `docs/roadmaps/development-roadmap.md`
- `docs/roadmaps/NEXT-FEATURES.md`
- `docs/roadmaps/next-steps.md`
- `docs/roadmaps/cli-enhancement-plan.md`
- `docs/status/smr-focused-gaps-analysis.md`
- `docs/status/capability-gaps-analysis.md`
