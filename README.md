<div align="center">
  <img src="docs/logo/nukepy-logo.png" alt="SMRForge Logo" width="400"/>
  
  # SMRForge
  
  **Small Modular Reactor Design and Analysis Toolkit**
</div>

SMRForge is a comprehensive Python toolkit for nuclear reactor design, analysis, and optimization with a focus on Small Modular Reactors (SMRs).

## Features

### ✅ Stable & Production Ready
- **Neutronics**: Multi-group diffusion solver with power iteration and Arnoldi methods
- **Nuclear Data**: ENDF file parsing with manual setup and bulk storage
  - **Interactive setup wizard** - step-by-step guide for setting up ENDF files
  - **Manual file placement** - easy directory-based setup with validation
  - **Bulk storage support** - organize and index bulk-downloaded files from NNDC/IAEA
  - **Flexible file discovery** - automatically finds files regardless of directory structure
  - Supports ENDF/B-VIII.0, ENDF/B-VIII.1, JEFF-3.3, JENDL-5.0
  - Local ENDF directory integration for offline use and faster access
  - Automatic version fallback (e.g., VIII.1 → VIII.0)
  - **Setup required**: Run `python -m smrforge.core.endf_setup` to configure ENDF files
  - **NEW: Advanced Nuclear Data Features** (January 2026):
    - **Resonance self-shielding**: Bondarenko, Subgroup, and Equivalence theory methods
    - **Fission yield data**: MF=5 parsing for independent and cumulative yields
    - **Delayed neutron data**: MT=455 parsing for transient analysis
    - **Prompt/delayed chi**: Separate prompt and delayed fission spectra
    - **Thermal scattering laws (TSL)**: MF=7 parsing for H2O, graphite, D2O, BeO
    - **Nuclide inventory tracking**: Atom density tracking for burnup calculations
    - **Decay chain utilities**: Bateman equation solver, chain visualization
- **Geometry**: Prismatic and pebble bed core geometries with mesh generation
  - **NEW: LWR SMR Support** (January 2026):
    - PWR SMR cores (NuScale, mPower, CAREM, SMR-160)
    - BWR SMR cores
    - Square lattice fuel assemblies (17x17, 15x15, 10x10)
    - Fuel rod arrays with cladding and gap
    - Water moderator/coolant channels
    - Control rod clusters (PWR) and control blades (BWR)
    - Compact SMR core layouts (reduced assembly counts)
    - Integral reactor designs (in-vessel steam generators, integrated primary systems)
- **Geometry Tools**: 
  - Import/export (JSON, OpenMC XML, Serpent)
  - **Advanced geometry import**: Full OpenMC CSG parsing, complex Serpent geometry, CAD formats (STEP, IGES, STL), MCNP import
  - **Enhanced geometry validation**: Comprehensive validation tools (gaps, connectivity, clearances, assembly placement, control rod insertion)
  - Control rod geometry with advanced features (bank priorities, sequencing, scram geometry)
  - Assembly management with fuel shuffling, multi-batch support, position tracking
- **Mesh Generation**: 
  - Adaptive mesh refinement
  - **Advanced 3D mesh generation**: Structured/unstructured/hybrid meshes
  - **Parallel mesh generation** support
  - **Mesh conversion utilities**: VTK, STL, XDMF, OBJ, PLY, MSH, MED formats
- **Visualization**: 
  - 2D core layouts, flux/power distribution plots
  - **Advanced visualization**: Animations (matplotlib, plotly), comparison views, video/GIF export
  - 3D transient visualization
  - **NEW: Advanced 3D visualization** (January 2026):
    - Ray-traced solid geometry plots (inspired by OpenMC)
    - Interactive cross-section slicing
    - Material boundary visualization
    - Isosurface rendering
    - Vector field visualization (neutron currents)
    - Multi-view dashboard layouts
    - Interactive 3D exploration
    - Export to HTML, PNG, PDF, SVG, VTK, STL formats
- **Validation**: Pydantic-based input validation with physics checks
- **Presets**: Reference HTGR designs (Valar-10, GT-MHR, HTR-PM, Micro-HTGR)
- **Convenience API**: One-liner functions for quick analysis
- **Quality Assurance**: 70-73% test coverage overall, 75-80%+ on priority modules

### 🟡 Experimental (API May Change)
These features are **functionally complete and well-tested**, but their APIs may change in future versions:
- **Monte Carlo Transport**: Particle transport solver (97.7% test coverage, 51+ tests)
- **Thermal-Hydraulics**: 1D channel models with fluid properties (45+ tests)
- **Safety Analysis**: Transient simulations (LOFC, ATWS, RIA, LOCA, air/water ingress) with point kinetics (40+ tests)
- **Uncertainty Quantification**: Monte Carlo sampling, sensitivity analysis (Sobol indices, Morris screening) (55+ tests)

### ⚡ Performance: Rust-Powered Dependencies
SMRForge leverages **Rust-powered libraries** for critical performance:
- **Pydantic 2.0**: Rust core for ultra-fast data validation (5-50x faster than v1)
- **Polars**: Rust-based DataFrame library for fast data processing (10-100x faster than pandas)
- **Rich**: Rust terminal library for beautiful, performant console output
- **uv** (recommended installer): Rust-based package installer (10-100x faster than pip)

These Rust implementations provide significant performance improvements without requiring Rust knowledge from users.

### ❌ Not Yet Implemented
- **Fuel Performance**: Stub module (use external tools)
- **Optimization**: Stub module (use scipy.optimize)
- **General I/O Utilities**: Stub module (geometry I/O available via `geometry.importers`)
- **Control Systems**: Stub module (control rod geometry available via `geometry.control_rods`)
- **Economics**: Stub module

**See `docs/status/feature-status.md` for detailed status of all features.**

## Installation

### Requirements
- **Python 3.8 or higher** (works with standard Python, no conda required!)
- Standard pip installation

### Install from PyPI

```bash
# Basic installation
pip install smrforge

# With optional dependencies
pip install smrforge[uq,viz]  # Uncertainty quantification and visualization
pip install smrforge[all]     # All optional dependencies
```

### Install from Source

#### Using pip (Standard)

```bash
# Clone repository
git clone https://github.com/cmwhalen/smrforge.git
cd smrforge

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .

# Or install with all dependencies
pip install -e ".[dev,docs,viz]"
```

#### Using uv (Fast Alternative - Recommended!)

```bash
# Install uv: https://github.com/astral-sh/uv

# Clone repository
git clone https://github.com/cmwhalen/smrforge.git
cd smrforge

# Install with uv (much faster!)
uv pip install -e . --python 3.10
```

**Note**: This library works with standard Python installations using pip, uv, or conda. See [`docs/guides/installation.md`](docs/guides/installation.md) for more details.

#### Using Docker

```bash
# Clone repository
git clone https://github.com/cmwhalen/smrforge.git
cd smrforge

# Build and run with Docker Compose
docker compose up -d smrforge

# Run commands
docker compose exec smrforge python -c "import smrforge as smr; print(smr.__version__)"
```

For detailed Docker usage and troubleshooting, see [`docs/guides/docker.md`](docs/guides/docker.md).

## Quick Start

### Basic Usage

```python
import smrforge as smr

# Quick k-eff calculation
k = smr.quick_keff(power_mw=10, enrichment=0.195)
print(f"k-effective: {k:.6f}")

# Analyze a preset design
results = smr.analyze_preset("valar-10")
print(f"k-eff: {results['k_eff']:.6f}")
print(f"Power: {results['power_thermal_mw']:.1f} MWth")
```

### Setting Up ENDF Data

**IMPORTANT**: ENDF files must be downloaded and set up manually before use.

**📖 See [`docs/technical/endf-documentation.md`](docs/technical/endf-documentation.md) for complete documentation:**
- Quick start guide
- Downloading ENDF files from NNDC/IAEA
- Setting up files for local Python scripts
- Mounting files in Docker containers
- Bulk storage and organization
- Codebase improvements and extractors
- Verification and troubleshooting

**Quick start options:**

1. **Interactive setup wizard** (recommended for first-time setup):
   ```bash
   python -m smrforge.core.endf_setup
   ```
   Or: `smrforge-setup-endf`

2. **Manual setup** (see [`docs/technical/endf-documentation.md`](docs/technical/endf-documentation.md)):
   - Download ENDF/B-VIII.1 from https://www.nndc.bnl.gov/endf/
   - Extract to a directory
   - Point `NuclearDataCache` to the directory

### Advanced Usage

```python
import smrforge as smr
from smrforge.neutronics.solver import MultiGroupDiffusion
from smrforge.presets.htgr import ValarAtomicsReactor
from pathlib import Path

# Set up ENDF data (required)
from smrforge.core.reactor_core import NuclearDataCache
cache = NuclearDataCache(
    local_endf_dir=Path("C:/path/to/ENDF-B-VIII.1")  # Your ENDF directory
)

# Create reactor from preset
reactor = ValarAtomicsReactor()

# Run neutronics analysis
solver = MultiGroupDiffusion(geometry, xs_data, options)
k_eff, flux = solver.solve_steady_state()

# Compute power distribution
power_dist = solver.compute_power_distribution(total_power=10e6)
```

### New Features Examples (January 2026)

```python
# LWR SMR Geometry
from smrforge.geometry.lwr_smr import PWRSMRCore
core = PWRSMRCore(name="NuScale")
core.build_square_lattice_core(
    n_assemblies_x=4, n_assemblies_y=4,
    lattice_size=17, rod_pitch=1.26
)

# Resonance Self-Shielding
from smrforge.core.reactor_core import get_cross_section_with_self_shielding, Nuclide
u238 = Nuclide(Z=92, A=238)
energy, xs = get_cross_section_with_self_shielding(
    cache, u238, "capture", temperature=900.0, sigma_0=1000.0
)

# Advanced Visualization
from smrforge.visualization.advanced import plot_ray_traced_geometry, create_dashboard
fig = plot_ray_traced_geometry(core, backend='plotly')
dashboard = create_dashboard(core, flux=flux, power=power, views=['xy', 'xz', '3d'])

# Decay Chain Utilities
from smrforge.core.decay_chain_utils import build_fission_product_chain, solve_bateman_equations
chain = build_fission_product_chain(cache, u235, target_nuclide=cs137)
concentrations = solve_bateman_equations(nuclides, initial, time=365*24*3600)

# Nuclide Inventory Tracking
from smrforge.core.reactor_core import NuclideInventoryTracker
tracker = NuclideInventoryTracker()
tracker.add_nuclide(u235, atom_density=0.0005)
tracker.burnup = 10.0  # MWd/kgU
```

See [`docs/guides/usage.md`](docs/guides/usage.md) for more examples and the [`examples/`](examples/) directory for complete scripts.

**New to SMRForge?** Start with the **[Tutorial](docs/guides/tutorial.md)** - a step-by-step guide for beginners!

## Documentation

📚 **Full documentation available at:**
- **GitHub Pages**: [https://cmwhalen.github.io/smrforge/](https://cmwhalen.github.io/smrforge/) (automatically deployed from main branch)
- **Read the Docs**: [https://smrforge.readthedocs.io](https://smrforge.readthedocs.io) (alternative hosting)

[![Documentation Status](https://readthedocs.org/projects/smrforge/badge/?version=latest)](https://smrforge.readthedocs.io/en/latest/?badge=latest)

### Documentation Sections

- **Installation Guide** - Detailed installation instructions
- **Quick Start** - Get started in minutes
- **API Reference** - Complete API documentation
- **Examples** - Code examples and tutorials
- **Contributing** - Development guidelines

### Additional Resources

- **📚 Documentation Index**: See [`DOCUMENTATION_INDEX.md`](DOCUMENTATION_INDEX.md) for a complete index of all documentation
- **Tutorial**: See [`docs/guides/tutorial.md`](docs/guides/tutorial.md) for a beginner-friendly step-by-step guide
- **ENDF Setup**: See [`docs/technical/endf-documentation.md`](docs/technical/endf-documentation.md) for complete ENDF data setup guide (required before use)
- **Installation**: See [`docs/guides/installation.md`](docs/guides/installation.md) for detailed installation instructions
- **Usage Guide**: See [`docs/guides/usage.md`](docs/guides/usage.md) for usage examples and quick reference
- **Docker**: See [`docs/guides/docker.md`](docs/guides/docker.md) for Docker usage and troubleshooting
- **Feature Status**: See [`docs/status/feature-status.md`](docs/status/feature-status.md) for module status
- **Test Coverage**: See [`docs/status/test-coverage-summary.md`](docs/status/test-coverage-summary.md) for test coverage details
- **Production Readiness**: See [`docs/status/production-readiness-status.md`](docs/status/production-readiness-status.md) for production readiness assessment
- **Contributing**: See [`CONTRIBUTING.md`](CONTRIBUTING.md) for development guidelines
- **Changelog**: See [`CHANGELOG.md`](CHANGELOG.md) for version history

## Examples

See the [`examples/`](examples/) directory for complete working examples:

### Core Examples
- **`basic_neutronics.py`** - Basic neutronics calculations
- **`preset_designs.py`** - Using preset reactor designs
- **`custom_reactor.py`** - Creating custom reactor configurations
- **`thermal_analysis.py`** - Thermal-hydraulics analysis

### Advanced Examples
- **`comprehensive_examples.py`** - Complete workflow demonstrations
- **`advanced_features_examples.py`** - **NEW**: Advanced features including visualization, decay chains, LWR SMRs, self-shielding
- **`complete_integration_example.py`** - Full integration example
- **`integrated_safety_uq.py`** - Safety analysis with uncertainty quantification
- **`lwr_smr_example.py`** - **NEW**: LWR SMR geometry and analysis examples
- **`burnup_example.py`** - Burnup calculations with nuclide tracking
- **`decay_heat_example.py`** - Decay heat calculations
- **`thermal_scattering_example.py`** - Thermal scattering law usage

### Geometry Examples
- **`geometry_import_example.py`** - Importing geometries from external formats
- **`control_rods_example.py`** - Control rod positioning and reactivity
- **`assembly_refueling_example.py`** - Fuel assembly and refueling patterns
- **`visualization_examples.py`** - Geometry and result visualization
- **`visualization_3d_example.py`** - **NEW**: Advanced 3D visualization examples

All examples are runnable and include comments explaining each step.

## Testing

SMRForge has comprehensive test coverage with 70-73% overall coverage and 75-80%+ on priority modules. All critical modules are well-tested with extensive edge case coverage.

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=smrforge --cov-report=html tests/

# View coverage report
# Open htmlcov/index.html in your browser

# Run specific test
pytest tests/test_neutronics.py
```

**Test Coverage Status:**
- **Overall Coverage**: 70-73% (up from 35-40%)
- **Priority Modules**: 75-80%+ coverage achieved
- **14 Priority Modules**: Comprehensive test coverage completed
- **Critical Modules**: All critical modules at target coverage

See [`docs/status/test-coverage-summary.md`](docs/status/test-coverage-summary.md) for detailed coverage breakdown.

## Contributing

Contributions are welcome! Please see [`CONTRIBUTING.md`](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone repository
git clone https://github.com/cmwhalen/smrforge.git
cd smrforge

# Install with development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Format code
black smrforge/ tests/
isort smrforge/ tests/
```

## Citation

If you use SMRForge in your research, please cite:

```bibtex
@software{smrforge,
  author = {SMRForge Development Team},
  title = {SMRForge: Small Modular Reactor Design and Analysis Toolkit},
  year = {2025},
  url = {https://github.com/cmwhalen/smrforge},
  version = {0.1.0}
}
```

## License

MIT License - see [`LICENSE`](LICENSE) file for details.

## Contact

- **GitHub Issues**: https://github.com/cmwhalen/smrforge/issues
- **Documentation**: 
  - GitHub Pages: https://cmwhalen.github.io/smrforge/
  - Read the Docs: https://smrforge.readthedocs.io
- **Repository**: https://github.com/cmwhalen/smrforge
