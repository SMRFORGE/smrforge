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
- **Geometry**: Prismatic and pebble bed core geometries with mesh generation
- **Geometry Tools**: Import/export (JSON, OpenMC XML, Serpent), control rod geometry, assembly management
- **Visualization**: 2D core layouts, flux/power distribution plots
- **Validation**: Pydantic-based input validation with physics checks
- **Presets**: Reference HTGR designs (Valar-10, GT-MHR, HTR-PM, Micro-HTGR)
- **Convenience API**: One-liner functions for quick analysis

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

**See `FEATURE_STATUS.md` for detailed status of all features.**

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

**Note**: This library works with standard Python installations using pip, uv, or conda. See [`INSTALLATION.md`](INSTALLATION.md) for more details.

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

For detailed Docker usage and troubleshooting, see [`DOCKER.md`](DOCKER.md).

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

**IMPORTANT**: ENDF files must be set up before use. Run the setup wizard:

```bash
python -m smrforge.core.endf_setup
```

Or use the command-line tool:
```bash
smrforge-setup-endf
```

The wizard will guide you through downloading and configuring ENDF files.

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

See [`USAGE.md`](USAGE.md) for more examples and the [`examples/`](examples/) directory for complete scripts.

**New to SMRForge?** Start with the **[Tutorial](TUTORIAL.md)** - a step-by-step guide for beginners!

## Documentation

[![Documentation Status](https://readthedocs.org/projects/smrforge/badge/?version=latest)](https://smrforge.readthedocs.io/en/latest/?badge=latest)

Full documentation available at: **[https://smrforge.readthedocs.io](https://smrforge.readthedocs.io)**

### Documentation Sections

- **Installation Guide** - Detailed installation instructions
- **Quick Start** - Get started in minutes
- **API Reference** - Complete API documentation
- **Examples** - Code examples and tutorials
- **Contributing** - Development guidelines

### Additional Resources

- **Tutorial**: See [`TUTORIAL.md`](TUTORIAL.md) for a beginner-friendly step-by-step guide
- **ENDF Setup**: See [`ENDF_SETUP_GUIDE.md`](ENDF_SETUP_GUIDE.md) for ENDF data setup instructions (required before use)
- **Installation**: See [`INSTALLATION.md`](INSTALLATION.md) for detailed installation instructions
- **Usage Guide**: See [`USAGE.md`](USAGE.md) for usage examples and quick reference
- **Docker**: See [`DOCKER.md`](DOCKER.md) for Docker usage and troubleshooting
- **Feature Status**: See [`FEATURE_STATUS.md`](FEATURE_STATUS.md) for module status
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
- **`complete_integration_example.py`** - Full integration example
- **`integrated_safety_uq.py`** - Safety analysis with uncertainty quantification

### Geometry Examples
- **`geometry_import_example.py`** - Importing geometries from external formats
- **`control_rods_example.py`** - Control rod positioning and reactivity
- **`assembly_refueling_example.py`** - Fuel assembly and refueling patterns
- **`visualization_examples.py`** - Geometry and result visualization

All examples are runnable and include comments explaining each step.

## Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=smrforge tests/

# Run specific test
pytest tests/test_neutronics.py
```

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
- **Documentation**: https://smrforge.readthedocs.io
- **Repository**: https://github.com/cmwhalen/smrforge
