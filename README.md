<div align="center">
  <img src="docs/logo/nukepy-logo.png" alt="SMRForge Logo" width="400"/>
  
  # SMRForge
  
  **Small Modular Reactor Design and Analysis Toolkit**
</div>

SMRForge is a comprehensive Python toolkit for nuclear reactor design, analysis, and optimization with a focus on Small Modular Reactors (SMRs).

## Features

### ✅ Stable & Production Ready
- **Neutronics**: Multi-group diffusion solver (power iteration), validated and tested
- **Validation**: Pydantic-based input validation, physics checks
- **Presets**: Reference HTGR designs (Valar-10, GT-MHR, HTR-PM, etc.)
- **Geometry**: Prismatic and pebble bed core geometries
- **Convenience API**: One-liner functions for easy usage

### 🟡 Experimental (In Development)
- **Monte Carlo Transport**: Basic implementation, needs validation
- **Thermal-Hydraulics**: Channel models implemented, needs more testing
- **Safety Analysis**: Transient simulations (LOCA, LOFA, REA, ATWS) implemented
- **Uncertainty Quantification**: Basic framework exists

### ❌ Not Yet Implemented
- **Fuel Performance**: Stub module (use external tools)
- **Optimization**: Stub module (use scipy.optimize)
- **I/O Utilities**: Stub module (use Pydantic serialization)
- **Visualization**: Stub module (use matplotlib directly)
- **Control Systems**: Stub module
- **Economics**: Stub module

**See `FEATURE_STATUS.md` for detailed status of all features.**

See `CHANGELOG.md` for version history and recent changes.

## Installation

### Requirements
- **Python 3.8 or higher** (works with standard Python, no conda required!)
- Standard pip installation

### Quick Install

#### Using pip (Standard)

```bash
# Clone repository
git clone https://github.com/yourusername/smrforge.git
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
git clone https://github.com/yourusername/smrforge.git
cd smrforge

# Install with uv (much faster!)
uv pip install -e . --python 3.10
```

**Note**: This library works with standard Python installations using pip, uv, or conda. See `INSTALLATION_GUIDE.md` or `UV_INSTALLATION.md` for more details.

#### Using Docker

```bash
# Clone repository
git clone https://github.com/yourusername/smrforge.git
cd smrforge

# Build and run with Docker Compose
docker-compose up -d smrforge

# Run commands
docker-compose exec smrforge python -c "import smrforge as smr; print(smr.__version__)"
```

For detailed Docker usage, see `DOCKER_USAGE.md`.

## Quick Start

```python
import smrforge as smr

# Create a reactor
reactor = smr.Reactor(name="SMR-160")

# Run neutronics analysis
solver = smr.neutronics.NeutronicsSolver(reactor)
k_eff = solver.solve_eigenvalue()

# Run thermal-hydraulics
th = smr.thermal.ThermalHydraulics(reactor)
temperatures = th.solve_steady_state()

# Safety analysis
transient = smr.safety.LOCA(reactor)
results = transient.simulate(time=1000.0)
```

## Documentation

Full documentation available at: [https://smrforge.readthedocs.io](https://smrforge.readthedocs.io)

## Examples

See `examples/` directory for complete examples:
- Basic reactor setup
- Steady-state analysis
- Transient simulations
- Uncertainty quantification
- Design optimization

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

Contributions welcome! Please see `CONTRIBUTING.md` for guidelines.

## License

MIT License - see `LICENSE` file for details.

## Citation

If you use SMRForge in your research, please cite:

```bibtex
@software{smrforge,
  author = {Your Name},
  title = {SMRForge: Small Modular Reactor Design Toolkit},
  year = {2024},
  url = {https://github.com/yourusername/smrforge}
}
```

## Contact

- Email: your.email@example.com
- Issues: https://github.com/yourusername/smrforge/issues
