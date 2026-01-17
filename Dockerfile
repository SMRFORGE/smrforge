# SMRForge Dockerfile
# Supports both runtime and development use cases
#
# Build: docker build -t smrforge:latest .
# Run:   docker run -it smrforge:latest
#
# Last Updated: January 2026
# - Added comprehensive CLI with nested subcommands (reactor, data, burnup, validate, visualize, config, shell, workflow)
# - Added batch processing support for reactor analysis
# - Added interactive shell mode (IPython/REPL) via `smrforge shell`
# - Added workflow scripts support (YAML-based workflows) via `smrforge workflow run`
# - Added configuration management (`smrforge config show/set/init`)
# - Added validation testing framework with benchmark comparison
# - Added tab completion scripts (Bash/Zsh and PowerShell)
# - Enhanced CLI with Rich library (colored output, tables, progress bars)
# - Added Parameter Sweep Workflow (smrforge sweep) - automated parameter sweeps with parallel execution
# - Enhanced Design Comparison & Trade Studies (smrforge reactor compare) - multi-design comparison with metrics
# - Added Template Library System (smrforge reactor template) - parameterized reactor design templates
# - Added Simulation Checkpointing & Resume - automatic checkpointing for long burnup simulations
# - Added Design Constraints & Validation (smrforge validate design) - automated constraint checking
# - Added I/O Converters Framework - Serpent/OpenMC format support (framework ready)
# - Added Dash web dashboard with dark/gray mode support
# - Added CLI command (smrforge serve) for dashboard
# - Added LWR SMR transient analysis (PWR/BWR/Integral SMR transients)
# - Added LWR SMR burnup features (gadolinium depletion, assembly/rod-wise tracking)
# - Added automated data downloader with parallel downloads and progress indicators
# - Added Pint-based unit checking (pint>=0.20.0)
# - Added lumped-parameter thermal hydraulics (fast 0-D thermal circuits)
# - Added simplified point kinetics API (quick transient analysis)
# - Added transient and thermal visualization capabilities
# - Updated dashboard with quick transient and lumped thermal analysis interfaces
# - Optimized Monte Carlo solver (5-10x faster, 50-70% memory reduction)
#   * Vectorized particle tracking with NumPy arrays
#   * Memory pooling for reduced allocations
#   * Parallel processing with Numba (scales with CPU cores)
#   * Pre-computed cross-section lookup tables
#   * Batch tally processing
# - Structural mechanics module (fuel rod mechanics, stress/strain, PCI, fuel swelling)
# - Advanced control systems (PID controllers, load-following, reactor control)
# - Economics cost modeling (capital costs, operating costs, LCOE calculations)
# - Advanced two-phase flow models (drift-flux, two-fluid, enhanced boiling correlations, CHF)
# - Fuel cycle optimization and long-term simulation (optimization algorithms, material aging)
# - Visualization dependencies (plotly, pyvista, dash) are now required and included automatically
# - Fixed Debian Trixie compatibility (libgl1 instead of libgl1-mesa-glx)
# - Fixed Dash 3.x API compatibility (app.run() instead of app.run_server())
# - Fixed dashboard preset loading and validation issues
# - Fixed create_reactor and list_presets import resolution (convenience module conflict)
# - Fixed dashboard State component initialization (all analysis options always in layout)
# - Fixed LumpedThermalHydraulics parameter passing (adaptive/max_step moved to solve_transient)
# - Improved validation warning messages (show actual validation details)
# - Complete dashboard workflow: reactor creation → analysis → results → export
# - Real data capture: flux and power distributions from solver
# - Enhanced visualizations: plots use actual solver data, not sample data
# - Complete exports: JSON/CSV include reactor spec + analysis results
# - Project save/open: full workflow persistence
# - Enhanced error handling and user feedback throughout dashboard
# - Includes support for advanced features (mesh conversion, CAD import - optional)
# - Test coverage: 79.2% overall, 75-80%+ on priority modules
# - Comprehensive test suite: 133+ test files including Phase 1/2 module tests
# - Advanced error handling and async edge case coverage
# - Manual testing framework: 13 test scripts (test_*.py) for feature validation (testing/ directory)
#   Optional Jupyter notebooks available for interactive testing (01_CLI_Commands.ipynb)
# - Comprehensive test suite: 133+ test files including Phase 1/2 module tests
# - Advanced error handling and async edge case coverage
# - Quick start validation guide for running tests with real ENDF data (docs/validation/QUICK_START_VALIDATION.md)

FROM python:3.11-slim

# Metadata labels
LABEL maintainer="SMRForge Development Team" \
      description="Small Modular Reactor Design and Analysis Toolkit" \
      version="0.1.0"

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
# Scientific Python packages require various system libraries
# Added libgl1 and libglib2.0-0 for pyvista visualization support
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    pkg-config \
    libhdf5-dev \
    libblas-dev \
    liblapack-dev \
    libxml2-dev \
    libpng-dev \
    libgl1 \
    libglib2.0-0 \
    libxrender1 \
    libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

# Copy package metadata first (for better layer caching)
COPY setup.py pyproject.toml README.md MANIFEST.in /app/
COPY smrforge/ /app/smrforge/
# Copy CLI scripts and utilities (validation scripts, completion scripts, etc.)
COPY scripts/ /app/scripts/

# Install Python dependencies
# Upgrade pip and install wheel first (helps with some packages)
RUN pip install --upgrade pip wheel setuptools

# Install SMRForge with all dependencies from setup.py
# This includes visualization dependencies (plotly, pyvista, dash) which are now required
RUN pip install --no-cache-dir -e .

# Optional: Install additional mesh conversion and CAD import dependencies
# Uncomment the next lines to include mesh conversion and CAD import support:
# RUN pip install --no-cache-dir \
#     meshio>=5.0.0 \
#     trimesh>=3.0.0
# Note: joblib is already included as a dependency of scikit-learn

# Copy examples (optional - can be mounted as volume instead)
COPY examples/ /app/examples/

# Copy testing infrastructure (manual test scripts and documentation)
COPY testing/ /app/testing/
COPY docs/testing/ /app/docs/testing/

# Create directories for data/output and ENDF storage
# ENDF data can be mounted as volume or stored in container
RUN mkdir -p /app/data /app/output /app/endf-data

# Set environment variable for standard ENDF directory
# Users can override this or mount their own ENDF directory
# Also supports configuration file: ~/.smrforge/config.yaml
ENV SMRFORGE_ENDF_DIR=/app/endf-data

# Default command (can be overridden)
# Note: ENDF files can be downloaded automatically using the data downloader
# Run: smrforge data download --library ENDF-B-VIII.1 --output /app/endf-data
# Or: python -c "from smrforge.data_downloader import download_endf_data; download_endf_data(library='ENDF/B-VIII.1', output_dir='/app/endf-data')"
# Or set up manually: smrforge data setup
# 
# To run the web dashboard:
#   smrforge serve --host 0.0.0.0 --port 8050
#   Or: python -c "from smrforge.gui import run_server; run_server(host='0.0.0.0', port=8050)"
#   Then access at http://localhost:8050 (map port 8050 in docker run -p 8050:8050)
#
# CLI Commands available:
#   smrforge reactor create/list/analyze/compare
#   smrforge reactor template create/modify/validate (template library)
#   smrforge data setup/download/validate
#   smrforge burnup run/visualize (with checkpointing support)
#   smrforge transient run (quick transient analysis - reactivity insertion, decay heat, etc.)
#   smrforge thermal lumped (lumped-parameter thermal hydraulics)
#   smrforge validate run (validation framework - run validation tests)
#   Optimized Monte Carlo: Use OptimizedMonteCarloSolver for 5-10x faster calculations
#   Structural mechanics: Fuel rod analysis (thermal expansion, stress/strain, PCI, fuel swelling)
#   Control systems: PID controllers, load-following, reactor control (integrated with transients)
#   Economics: Capital cost estimation, operating costs, LCOE calculations
#   Advanced two-phase flow: Drift-flux models, two-fluid models, enhanced boiling correlations, CHF predictions
#   Fuel cycle optimization: Cycle length optimization, refueling strategy, material aging models
#   smrforge validate design (design constraints validation)
#   smrforge visualize geometry/flux
#   smrforge config show/set/init
#   smrforge shell (interactive IPython/REPL)
#   smrforge workflow run (YAML workflows)
#   smrforge sweep (parameter sweep and sensitivity analysis)
CMD ["python", "-c", "import smrforge as smr; print(f'SMRForge {smr.__version__} is ready!'); print(''); print('Features:'); print('  - Comprehensive CLI with nested subcommands'); print('  - Web Dashboard (smrforge serve) with dark/gray mode'); print('  - Interactive shell (smrforge shell)'); print('  - Workflow scripts (smrforge workflow run)'); print('  - Batch processing support'); print('  - Configuration management (smrforge config)'); print('  - Validation framework with benchmark comparison'); print('  - Parameter Sweep Workflow (smrforge sweep)'); print('  - Enhanced Design Comparison (smrforge reactor compare)'); print('  - Template Library System (smrforge reactor template)'); print('  - Simulation Checkpointing & Resume'); print('  - Design Constraints & Validation (smrforge validate design)'); print('  - I/O Converters Framework (Serpent/OpenMC)'); print('  - LWR SMR transient analysis (PWR/BWR/Integral SMR)'); print('  - LWR SMR burnup features (gadolinium depletion, assembly/rod tracking)'); print('  - Automated ENDF data downloader'); print('  - Advanced visualization, geometry import (OpenMC/Serpent/CAD/MCNP)'); print('  - Enhanced mesh generation'); print('  - Comprehensive test suite (133+ test files, 79.2% coverage)'); print('  - Manual testing scripts (testing/ directory) for feature validation'); print(''); print('ENDF Data Setup:'); print('  Option 1 (Recommended): Use CLI'); print('    smrforge data download --library ENDF-B-VIII.1 --output /app/endf-data'); print('  Option 2: Interactive setup'); print('    smrforge data setup'); print(''); print('Web Dashboard:'); print('  smrforge serve --host 0.0.0.0 --port 8050'); print('  Access at http://localhost:8050 (map port with -p 8050:8050)'); print(''); print('CLI Examples:'); print('  smrforge reactor list'); print('  smrforge reactor create --preset valar-10 --output reactor.json'); print('  smrforge reactor analyze --reactor reactor.json --keff'); print('  smrforge reactor compare --presets valar-10 htr-pm-200 --metrics k_eff'); print('  smrforge reactor template create --from-preset valar-10 --output template.json'); print('  smrforge sweep --reactor reactor.json --params enrichment:0.10:0.25:0.05 --analysis keff'); print('  smrforge burnup run --reactor reactor.json --checkpoint-interval 100 --checkpoint-dir checkpoints/'); print('  smrforge validate design --reactor reactor.json --output validation_report.json'); print('  smrforge validate run --endf-dir /app/endf-data'); print('  smrforge shell  # Interactive Python shell'); print(''); print('Testing:'); print('  pytest  # Run all automated tests'); print('  python testing/test_01_cli_commands.py  # Manual CLI testing'); print('  python testing/test_02_reactor_creation.py  # Manual reactor testing'); print('  python testing/test_03_burnup.py  # Manual burnup testing'); print('  # See testing/ directory for all 13 manual test scripts (test_*.py)
  # Optional: Jupyter notebooks available for interactive testing (01_CLI_Commands.ipynb)'); print('  # See docs/testing/MANUAL_TESTING_CHECKLIST.md for testing guide'); print('  # See docs/validation/QUICK_START_VALIDATION.md for ENDF validation testing'); print(''); print('Optional dependencies:'); print('  - Mesh conversion: pip install meshio'); print('  - CAD import: pip install trimesh'); print('Note: Visualization dependencies (plotly, pyvista, dash) are now required and included automatically')"]

