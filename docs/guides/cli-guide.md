# SMRForge CLI Guide

**Last Updated:** January 2026  
**Version:** SMRForge v1.0+

---

## Table of Contents

1. [Introduction](#introduction)
2. [Installation and Setup](#installation-and-setup)
3. [Beginner Quickstart (Start Here)](#beginner-quickstart-start-here)
4. [Getting Help](#getting-help)
5. [Command Overview](#command-overview)
6. [Reactor Operations](#reactor-operations)
7. [Data Management](#data-management)
8. [Burnup Calculations](#burnup-calculations)
9. [Transient Analysis](#transient-analysis)
10. [Thermal Hydraulics](#thermal-hydraulics)
11. [Validation and Testing](#validation-and-testing)
12. [Visualization](#visualization)
13. [Configuration Management](#configuration-management)
14. [Workflow Automation](#workflow-automation)
15. [Interactive Shell](#interactive-shell)
16. [Web Dashboard](#web-dashboard)
17. [Advanced Usage](#advanced-usage)
18. [Troubleshooting](#troubleshooting)

---

## Introduction

SMRForge provides a comprehensive command-line interface (CLI) for Small Modular Reactor (SMR) design, analysis, and simulation. The CLI enables automation, batch processing, and integration with other tools while maintaining all capabilities of the Python API.

### Key Features

- **Comprehensive Command Set:** Reactor creation, analysis, burnup, validation, visualization
- **Rich Output:** Colored output, progress bars, tables (via Rich library)
- **Multiple Formats:** JSON, YAML, CSV export/import
- **Batch Processing:** Parallel execution support
- **Workflow Automation:** YAML-based workflow scripts
- **Interactive Shell:** IPython/REPL with SMRForge pre-loaded

### Command Structure

SMRForge uses a hierarchical command structure:

```
smrforge <command> <subcommand> [options]
```

Example:
```bash
smrforge reactor create --preset valar-10 --output reactor.json
```

---

## Installation and Setup

### Prerequisites

```bash
pip install smrforge
```

### Optional Dependencies

For full functionality:

```bash
# Visualization and dashboard
pip install smrforge[viz]

# All optional features
pip install smrforge[all]
```

### Verify Installation

```bash
smrforge --version
```

### Shell Completion (Optional)

**Bash/Zsh:**
```bash
source scripts/smrforge-completion.bash
# Or add to ~/.bashrc or ~/.zshrc
```

**PowerShell:**
```powershell
. scripts/smrforge-completion.ps1
```

---

## Beginner Quickstart (Start Here)

This section assumes you have **never** used SMRForge before. Follow these steps **in order**.

### Step 0 — Pick a terminal (Windows users)

Many examples online use Bash line continuations (`\`). **PowerShell does not use `\`**.

- **PowerShell**: multi-line commands use the **backtick** (`` ` ``) at end-of-line.
- **Git Bash**: Bash-compatible (supports `\`). Install “Git for Windows”, then select **Git Bash** as your Cursor terminal profile.
- **WSL (Ubuntu)**: Bash-compatible, but requires WSL to be installed first.

### Step 1 — Confirm SMRForge runs

Run:

```bash
smrforge --version
smrforge --help
```

If `smrforge` is not found, try:

```bash
python -m smrforge.cli --help
```

### Step 2 — List presets (built-in reactor designs)

Run:

```bash
smrforge reactor list
```

Pick one preset name (e.g. `valar-10`) and keep using that name below.

### Step 3 — Create a reactor input file from a preset

This creates `reactor.json`, which you will reuse as input for multiple features.

```bash
smrforge reactor create --preset valar-10 --output reactor.json
```

### Step 4 — Analyze the reactor (generate a results file)

Run:

```bash
smrforge reactor analyze --reactor reactor.json --neutronics --output results.json
```

### Step 5 — Visualize geometry (works from `reactor.json`)

2D PNG:

```bash
smrforge visualize geometry --reactor reactor.json --output geometry.png --format png
```

3D HTML (requires Plotly; safe to try):

```bash
smrforge visualize geometry --reactor reactor.json --3d --backend plotly --output geometry.html --format html
```

### Step 6 — Burnup and flux visualization (important note)

As of this version:

- `smrforge burnup run` **does not** generate a full burnup results file yet; it prints the Python API snippet and can save your chosen burnup options.
- `smrforge burnup visualize` can plot `k_eff` / `burnup` **only if** your results file already contains those arrays.
- `smrforge visualize flux` currently prints Python API guidance; it does not generate a plot by itself yet.

If your goal is “use every feature end-to-end from a preset”, expect a mixed workflow:

- **CLI**: presets → reactor create/analyze → geometry visualization → validation
- **Python API**: burnup inventory workflows and flux plotting

## Getting Help

### General Help

```bash
smrforge --help
```

### Command-Specific Help

```bash
# Reactor commands
smrforge reactor --help

# Specific subcommand
smrforge reactor create --help

# Data commands
smrforge data --help
```

### Verbose Output

Add `--verbose` or `-v` to any command for detailed output:

```bash
smrforge reactor create --preset valar-10 --verbose
```

---

## Command Overview

### Main Commands

| Command | Description | Subcommands |
|---------|-------------|-------------|
| `serve` | Launch web dashboard | None |
| `shell` | Interactive Python shell | None |
| `reactor` | Reactor operations | `create`, `analyze`, `list`, `compare` |
| `data` | Data management | `setup`, `download`, `validate` |
| `burnup` | Burnup calculations | `run`, `visualize` |
| `transient` | Transient analysis | `run` |
| `thermal` | Thermal hydraulics | `lumped` |
| `validate` | Validation/testing | `run`, `design` |
| `visualize` | Visualization | `geometry`, `flux` |
| `config` | Configuration | `show`, `set`, `init` |
| `workflow` | Workflow automation | `run` |
| `sweep` | Parameter sweeps | None |

---

## What each feature needs (inputs → outputs)

If you’re new, this is the “map” so you know what to run first.

- **`smrforge reactor list`**
  - **Input**: none
  - **Output**: prints available preset names

- **`smrforge reactor create`**
  - **Input**: preset name (`--preset ...`) or a config file (`--config ...`)
  - **Output**: a reactor input file (usually `reactor.json`)

- **`smrforge reactor analyze`**
  - **Input**: a reactor input file (`--reactor reactor.json`)
  - **Output**: a results file (e.g. `results.json`)

- **`smrforge visualize geometry`**
  - **Input**: a reactor input file (`--reactor reactor.json`)
  - **Output**: an image/HTML file (e.g. `geometry.png` / `geometry.html`)

- **`smrforge validate design`**
  - **Input**: a reactor input file (`--reactor reactor.json`) or a preset (`--preset valar-10`)
  - **Output**: a validation report JSON (optional via `--output ...`)

- **`smrforge data setup / download / validate`**
  - **Input**: (optional) directories / nuclide set choices
  - **Output**: an ENDF data directory on disk
  - **Used by**: advanced workflows/tests that need real nuclear data files

- **`smrforge transient run`**
  - **Input**: `--power` and `--temperature` (and transient parameters like `--reactivity`)
  - **Output**: a transient results JSON (optional via `--output ...`) and optional plots

- **`smrforge thermal lumped`**
  - **Input**: optional thermal config file (`--config ...`) and simulation options
  - **Output**: a results JSON (optional via `--output ...`) and optional plots

- **Burnup + flux plotting**
  - In this version, these are primarily **Python API workflows**; the CLI subcommands provide guidance but don’t fully generate plots/results end-to-end yet.

## Reactor Operations

### Create Reactor

Create a reactor from preset, configuration file, or custom parameters.

#### From Preset

```bash
smrforge reactor create --preset valar-10 --output reactor.json
```

#### From Configuration File

**JSON:**
```bash
smrforge reactor create --config reactor_config.json --output reactor.json
```

**YAML:**
```bash
smrforge reactor create --config reactor_config.yaml --output reactor.json
```

#### Custom Parameters

**Bash (Linux/macOS/Git Bash):**

```bash
smrforge reactor create \
    --power 10 \
    --enrichment 0.195 \
    --type prismatic \
    --core-height 200 \
    --core-diameter 100 \
    --fuel-type UCO \
    --output reactor.json
```

**PowerShell (Windows):**

```powershell
smrforge reactor create `
    --power 10 `
    --enrichment 0.195 `
    --type prismatic `
    --core-height 200 `
    --core-diameter 100 `
    --fuel-type UCO `
    --output reactor.json
```

#### Options

- `--preset NAME` - Use preset design (e.g., `valar-10`, `gt-mhr`, `htr-pm`)
- `--config FILE` - Load from configuration file (JSON or YAML)
- `--power FLOAT` - Thermal power [MW]
- `--enrichment FLOAT` - Fuel enrichment (0-1)
- `--type STR` - Reactor type (`prismatic`, `pebble_bed`, `annular`, `hybrid`)
- `--core-height FLOAT` - Core height [cm]
- `--core-diameter FLOAT` - Core diameter [cm]
- `--fuel-type STR` - Fuel type (`UCO`, `UO2`, `UC`, `UN`)
- `--output FILE` - Output file path (JSON or YAML)

### List Available Presets

```bash
smrforge reactor list
```

**Output:**
```
Available reactor presets:
  - valar-10 (10 MW HTGR)
  - gt-mhr (300 MW HTGR)
  - htr-pm (210 MW HTGR)
  - ...
```

### Analyze Reactor

Run neutronics, burnup, or safety analysis on a reactor.

#### Neutronics Analysis

```bash
# Calculate k_eff
smrforge reactor analyze --reactor reactor.json --keff

# Full neutronics analysis
smrforge reactor analyze --reactor reactor.json --neutronics

# With output file
smrforge reactor analyze --reactor reactor.json --neutronics --output results.json
```

#### Options

- `--reactor FILE` - Reactor specification file (JSON)
- `--keff` - Calculate k_eff only
- `--neutronics` - Full neutronics analysis
- `--burnup` - Burnup analysis
- `--safety` - Safety analysis
- `--full` - Complete analysis (all above)
- `--max-iterations INT` - Solver max iterations
- `--tolerance FLOAT` - Solver tolerance
- `--output FILE` - Output file for results

#### Advanced Options

```bash
# Custom solver options
smrforge reactor analyze \
    --reactor reactor.json \
    --neutronics \
    --max-iterations 200 \
    --tolerance 1e-7

# Batch processing (glob patterns) + parallel workers
smrforge reactor analyze \
    --batch "reactors/*.json" \
    --keff \
    --parallel \
    --workers 8 \
    --output batch_keff.json
```

### Compare Reactors

Compare multiple reactor designs.

```bash
smrforge reactor compare \
    --reactors reactor1.json reactor2.json reactor3.json \
    --output comparison.json

# With metrics
smrforge reactor compare \
    --reactors reactor1.json reactor2.json \
    --metrics keff burnup cycle_length \
    --output comparison.json
```

**Options:**
- `--reactors FILES...` - Multiple reactor specification files
- `--metrics METRICS...` - Metrics to compare (`keff`, `burnup`, `cycle_length`, `power`, etc.)
- `--output FILE` - Comparison output file

---

## Data Management

### Setup ENDF Data Directory

Interactive setup wizard for ENDF nuclear data directory.

```bash
smrforge data setup
```

**Interactive prompts:**
- ENDF data directory path
- Library selection (ENDF-B-VIII.0, ENDF-B-VIII.1, etc.)
- Nuclide set selection

### Download ENDF Data

Download nuclear data from online repositories.

```bash
# Download common SMR nuclides
smrforge data download \
    --library ENDF-B-VIII.1 \
    --nuclide-set common_smr

# Download specific nuclides
smrforge data download \
    --library ENDF-B-VIII.1 \
    --nuclides U235 U238 Pu239

# Download to custom directory
smrforge data download \
    --library ENDF-B-VIII.1 \
    --nuclide-set common_smr \
    --output ~/ENDF-Data \
    --max-workers 8 \
    --validate
```

**Options:**
- `--library STR` - ENDF library (`ENDF-B-VIII.0`, `ENDF-B-VIII.1`)
- `--nuclide-set STR` - Predefined nuclide set (`common_smr`, `all_actinides`, etc.)
- `--nuclides NUCLIDES...` - Specific nuclides (e.g., `U235 U238 Pu239`)
- `--output DIR` - Download directory
- `--max-workers INT` - Parallel downloads
- `--validate` - Validate downloaded files
- `--resume` - Resume interrupted download

**Available Nuclide Sets:**
- `common_smr` - Common SMR isotopes (U235, U238, Pu239, etc.)
- `all_actinides` - All actinides
- `all_fission_products` - Fission products
- `full_library` - Entire library (very large)

### Validate ENDF Data

Validate ENDF files for correctness and completeness.

```bash
# Validate entire directory
smrforge data validate --endf-dir ~/ENDF-Data

# Validate specific files
smrforge data validate --files file1.endf file2.endf

# Detailed validation report
smrforge data validate --endf-dir ~/ENDF-Data --output report.json
```

**Options:**
- `--endf-dir DIR` - ENDF directory to validate
- `--files FILES...` - Specific ENDF files to validate
- `--output FILE` - Validation report output file

---

## Burnup Calculations

### Run Burnup Calculation

Burnup/depletion tracks nuclide inventory over time.

**Important:** In this version, `smrforge burnup run` prints guidance for running burnup via the Python API and can save your chosen burnup options. It does **not** generate a full burnup inventory/results file by itself yet.

```bash
# Basic burnup calculation
smrforge burnup run \
    --reactor reactor.json \
    --time-steps 0 365 730 1095 \
    --power-density 50

# With output file
smrforge burnup run \
    --reactor reactor.json \
    --time-steps 0 365 730 \
    --power-density 50 \
    --output burnup_results.json

# With checkpointing
smrforge burnup run \
    --reactor reactor.json \
    --time-steps 0 365 730 1095 \
    --power-density 50 \
    --checkpoint-interval 30 \
    --checkpoint-dir checkpoints/
```

**Options:**
- `--reactor FILE` - Reactor specification file
- `--time-steps FLOATS...` - Time steps [days] (e.g., `0 365 730`)
- `--power-density FLOAT` - Power density [W/cm³]
- `--output FILE` - Output file for results
- `--checkpoint-interval FLOAT` - Checkpoint every N days
- `--checkpoint-dir DIR` - Directory for checkpoint files
- `--resume-from FILE` - Resume from a checkpoint file
- `--adaptive-tracking` - Enable adaptive nuclide tracking
- `--nuclide-threshold FLOAT` - Threshold for tracking nuclides

### Visualize Burnup Results

Generate plots from burnup calculation results.

```bash
# Plot k_eff evolution
smrforge burnup visualize \
    --results burnup_results.json \
    --keff \
    --output burnup_keff.png \
    --format png

# Plot burnup evolution
smrforge burnup visualize \
    --results burnup_results.json \
    --burnup \
    --output burnup_burnup.png \
    --format png
```

**Options:**
- `--results FILE` - Burnup results file (JSON or HDF5)
- `--keff` - Plot k-eff evolution (if present in file)
- `--burnup` - Plot burnup evolution (if present in file)
- `--composition` - Prints guidance for composition plotting via Python API
- `--nuclides U235 U238 ...` - Nuclides to plot (Python API workflow)
- `--output FILE` - Output plot file path (not a directory)
- `--format png|pdf|svg|html` - Output format

---

## Transient Analysis

### Run Transient Analysis

Analyze reactor behavior during transients (reactivity insertion, decay heat removal, etc.).

```bash
# Reactivity insertion transient (requires power + temperature)
smrforge transient run \
    --power 1000000 \
    --temperature 600 \
    --type reactivity_insertion \
    --reactivity 0.01 \
    --duration 100 \
    --output transient_results.json

# Decay heat transient
smrforge transient run \
    --power 1000000 \
    --temperature 600 \
    --type decay_heat \
    --duration 3600 \
    --output decay_heat.json

# With plots (plot-output is a file path)
smrforge transient run \
    --power 1000000 \
    --temperature 600 \
    --type reactivity_insertion \
    --reactivity 0.01 \
    --duration 100 \
    --plot \
    --plot-output transient_plot.png \
    --plot-backend matplotlib
```

**Transient Types:**
- `reactivity_insertion` - Reactivity insertion transient
- `reactivity_step` - Step reactivity insertion transient
- `power_change` - Power change transient
- `decay_heat` - Decay heat transient

**Options:**
- `--power FLOAT` - Initial reactor power [W] (required)
- `--temperature FLOAT` - Initial temperature [K] (required)
- `--type STR` - Transient type
- `--reactivity FLOAT` - Reactivity inserted [dk/k] (reactivity transient types)
- `--duration FLOAT` - Transient duration [seconds]
- `--output FILE` - Output file for results
- `--plot` - Generate plots
- `--plot-output FILE` - Save plot to file
- `--plot-backend STR` - Plot backend (`plotly`, `matplotlib`)
- `--scram-available` - Scram available (default: True)
- `--scram-delay FLOAT` - Scram delay [s]
- `--long-term` - Enable long-term optimization (for durations > 1 day)

---

## Thermal Hydraulics

### Lumped Thermal Hydraulics

Run lumped-parameter (0-D) thermal hydraulics analysis.

```bash
# Basic lumped thermal analysis
smrforge thermal lumped \
    --duration 3600 \
    --output thermal_results.json

# With custom parameters
smrforge thermal lumped \
    --duration 7200 \
    --max-step 3600 \
    --adaptive \
    --output thermal_results.json

# With plots
smrforge thermal lumped \
    --duration 3600 \
    --plot \
    --plot-output thermal_plot.png \
    --plot-backend matplotlib
```

**Options:**
- `--duration FLOAT` - Analysis duration [seconds]
- `--config FILE` - Configuration file (JSON/YAML) with lump definitions
- `--max-step FLOAT` - Maximum time step [seconds]
- `--adaptive` - Enable adaptive time stepping
- `--output FILE` - Output file for results
- `--plot` - Generate plots
- `--plot-output FILE` - Save plot to file
- `--plot-backend plotly|matplotlib` - Plotting backend

---

## Validation and Testing

### Run Validation Tests

Run SMRForge’s validation test suite (pytest-based). This is primarily for developers / verifying an installation.

```bash
# Run all validation tests
smrforge validate run

# Use a specific ENDF directory
smrforge validate run --endf-dir ~/ENDF-Data --verbose

# Run specific tests
smrforge validate run --tests tests/test_validation_comprehensive.py tests/test_endf_workflows_e2e.py --verbose
```

**Options:**
- `--endf-dir DIR` - ENDF directory
- `--tests FILES...` - Specific pytest files to run
- `--benchmarks FILE` - Benchmark database file (optional)
- `--output FILE` - Output file for results
- `--verbose` - Verbose output

### Validate Reactor Design

Validate reactor design against constraints.

```bash
# Validate reactor design
smrforge validate design --reactor reactor.json

# With output report
smrforge validate design \
    --reactor reactor.json \
    --output validation_report.json

# Validate a preset directly (no reactor file needed)
smrforge validate design --preset valar-10 --output preset_validation.json
```

**Options:**
- `--reactor FILE` - Reactor file
- `--preset NAME` - Preset name
- `--constraints FILE` - Constraint set file (JSON)
- `--output FILE` - Validation report output file

---

## Visualization

### Visualize Geometry

Generate 2D or 3D geometry visualizations.

```bash
# Basic geometry visualization
smrforge visualize geometry --reactor reactor.json --output geometry.png --format png

# 3D visualization
smrforge visualize geometry \
    --reactor reactor.json \
    --3d \
    --output geometry_3d.html
```

**Options:**
- `--reactor FILE` - Reactor specification file
- `--3d` - Generate 3D visualization
- `--output FILE` - Output file (HTML for 3D, PNG/SVG for 2D)
- `--format png|pdf|svg|html` - Output format
- `--backend plotly|pyvista` - Visualization backend
- `--interactive` - Display interactive window (if supported)

### Visualize Flux Distribution

Plot neutron flux distribution.

```bash
# Flux plotting (currently prints Python API guidance)
smrforge visualize flux --results results.json
```

**Options:**
- `--results FILE` - Neutronics results file (JSON)
- `--group INT` - Energy group index
- `--output FILE` - Output file
  (Note: as of this version, the CLI prints guidance; plotting is done via Python API.)

### Visualize Burnup Results

See [Burnup Calculations - Visualize Burnup Results](#visualize-burnup-results)

---

## Configuration Management

### Show Configuration

Display current configuration.

```bash
# Show all configuration
smrforge config show

# Show specific setting
smrforge config show --key endf_data_dir
```

**Options:**
- `--key STR` - Specific configuration key to show

### Set Configuration

Set configuration value.

```bash
# Set ENDF data directory
smrforge config set --key endf_data_dir --value ~/ENDF-Data

# Set default solver options
smrforge config set --key solver.max_iterations --value 500
```

**Options:**
- `--key STR` - Configuration key
- `--value STR` - Configuration value

### Initialize Configuration

Create default configuration file.

```bash
smrforge config init

# With custom path
smrforge config init --output ~/.smrforge/config.yaml
```

**Options:**
- `--output FILE` - Configuration file path

---

## Workflow Automation

### Run Workflow

Execute workflow from YAML file.

```bash
# Run workflow
smrforge workflow run workflow.yaml
```

**Workflow YAML Example:**

```yaml
name: Reactor Analysis Workflow
steps:
  - name: Create Reactor
    type: create_reactor
    preset: valar-10
    output: reactor.json
  
  - name: Neutronics Analysis
    type: analyze
    neutronics: true
    output: results.json
```

**Options:**
- `workflow FILE` - Workflow YAML file

---

## Interactive Shell

### Launch Interactive Shell

Start IPython/REPL with SMRForge pre-loaded.

```bash
smrforge shell
```

**Features:**
- SMRForge pre-imported as `smr` alias
- Convenience functions available (`create_reactor`, `list_presets`, etc.)
- Rich formatting support
- Tab completion

**Example session:**

```python
>>> import smrforge as smr
>>> reactor = smr.create_reactor("valar-10")
>>> k_eff = reactor.solve_keff()
>>> print(f"k_eff: {k_eff:.6f}")
```

---

## Web Dashboard

### Launch Dashboard

Start the SMRForge web dashboard.

```bash
# Default (localhost:8050)
smrforge serve

# Custom host and port
smrforge serve --host 0.0.0.0 --port 8080

# Debug mode
smrforge serve --debug
```

**Options:**
- `--host STR` - Host address (default: `127.0.0.1`)
- `--port INT` - Port number (default: `8050`)
- `--debug` - Enable debug mode

**Access dashboard:**
- Open browser to: `http://localhost:8050` (or specified host:port)
- Press `Ctrl+C` to stop server

---

## Advanced Usage

### Parallel Execution

Many commands support parallel execution for faster processing.

```bash
# Parallel reactor analysis
smrforge reactor analyze \
    --reactor reactor.json \
    --neutronics \
    --parallel \
    --workers 8

# Parallel data downloads
smrforge data download \
    --library ENDF-B-VIII.1 \
    --nuclide-set common_smr \
    --output ~/ENDF-Data \
    --max-workers 8 \
    --validate
```

**Parallel Options:**
- `smrforge reactor analyze --batch ...`:
  - `--parallel` - Enable parallel batch execution
  - `--workers INT` - Number of worker processes (default: 4)
- `smrforge data download ...`:
  - `--max-workers INT` - Parallel downloads

### Batch Processing

Process multiple reactors or configurations.

```bash
# Process multiple reactors
for reactor in reactor*.json; do
    smrforge reactor analyze --reactor "$reactor" --neutronics
done

# Using xargs for parallel batch processing
ls reactor*.json | xargs -n 1 -P 4 -I {} smrforge reactor analyze --reactor {} --neutronics
```

### Output Formats

Export results in various formats.

```bash
# JSON output (default)
smrforge reactor analyze --reactor reactor.json --neutronics --output results.json

# YAML output
# (Reactor creation supports YAML. Many analysis outputs are JSON in this version.)
```

### Combining Commands

Chain commands together using pipes or scripts.

```bash
# Shell script example
#!/bin/bash
REACTOR="reactor.json"
smrforge reactor create --preset valar-10 --output "$REACTOR"
smrforge reactor analyze --reactor "$REACTOR" --neutronics
smrforge burnup run --reactor "$REACTOR" --time-steps 0 365 730
```

---

## Troubleshooting

### Common Issues

#### Command Not Found

**Issue:** `smrforge: command not found`

**Solution:**
```bash
# Verify installation
pip show smrforge

# Reinstall if needed
pip install --upgrade smrforge

# Check PATH
which python
python -m smrforge.cli --help  # Alternative invocation
```

#### Import Errors

**Issue:** `ModuleNotFoundError` or import errors

**Solution:**
```bash
# Install missing dependencies
pip install -r requirements.txt

# Install with all optional features
pip install smrforge[all]
```

#### ENDF Data Not Found

**Issue:** ENDF data directory not configured

**Solution:**
```bash
# Run setup wizard
smrforge data setup

# Or manually set directory
smrforge config set --key endf_data_dir --value ~/ENDF-Data
```

#### Port Already in Use

**Issue:** Dashboard port already in use

**Solution:**
```bash
# Use different port
smrforge serve --port 8051

# Find process using port (Linux/Mac)
lsof -i :8050

# Kill process if needed
kill <PID>
```

#### Permission Errors

**Issue:** Permission denied when writing files

**Solution:**
```bash
# Check file/directory permissions
ls -l output_directory

# Create directory if needed
mkdir -p output_directory

# Use absolute paths
smrforge reactor create --preset valar-10 --output /absolute/path/reactor.json
```

### Getting More Help

```bash
# Command help
smrforge <command> --help

# Verbose output
smrforge <command> --verbose

# Version information
smrforge --version

# Python API documentation
python -c "import smrforge; help(smrforge)"
```

---

## Examples

### Complete Workflow Example

```bash
#!/bin/bash
# Complete SMR analysis workflow

# 1. Setup ENDF data
smrforge data setup

# 2. Download nuclear data
smrforge data download \
    --library ENDF-B-VIII.1 \
    --nuclide-set common_smr \
    --output ~/ENDF-Data \
    --max-workers 8 \
    --validate

# 3. Create reactor
smrforge reactor create \
    --preset valar-10 \
    --output reactor.json

# 4. Neutronics analysis
smrforge reactor analyze \
    --reactor reactor.json \
    --neutronics \
    --output results.json

# 5. Visualize geometry (2D)
smrforge visualize geometry \
    --reactor reactor.json \
    --output geometry.png \
    --format png

# 6. Burnup + flux plots
# NOTE: In this version, burnup + flux plotting are primarily done via the Python API.
# - `smrforge burnup run` saves options + prints the Python API snippet.
# - `smrforge visualize flux` prints the Python API snippet.

# 7. Validate design (constraints/sanity checks)
smrforge validate design \
    --reactor reactor.json \
    --output validation_report.json
```

### Parameter Sweep Example

```bash
#!/bin/bash
# Parameter sweep: enrichment vs. k_eff (advanced)
#
# The sweep command accepts either:
# - name:start:end:step   (range sweep)
# - name:val1,val2,val3   (explicit values)
#
# You can pass a preset name directly via --reactor.
smrforge sweep \
    --reactor valar-10 \
    --params enrichment:0.15:0.25:0.02 \
    --analysis keff \
    --output sweep_results/
```

### Transient Analysis Example

```bash
#!/bin/bash
# Transient analysis for reactivity insertion

# Create reactor
smrforge reactor create --preset valar-10 --output reactor.json

# Run different reactivity insertion transients
for reactivity in 0.005 0.01 0.02 0.05; do
    smrforge transient run \
        --reactor reactor.json \
        --type reactivity_insertion \
        --reactivity "$reactivity" \
        --duration 100 \
        --output "transient_${reactivity}.json" \
        --plot
done
```

---

## Additional Resources

- **API Documentation:** `python -c "import smrforge; help(smrforge)"`
- **Examples:** `examples/` directory
- **Workflow Examples:** `docs/guides/complete-workflow-examples.md`
- **Dashboard Guide:** `docs/guides/dashboard-guide.md`
- **Installation Guide:** `docs/guides/installation.md`

---

## Command Quick Reference

```bash
# Reactor
smrforge reactor create --preset <name> --output <file>
smrforge reactor list
smrforge reactor analyze --reactor <file> --neutronics
smrforge reactor compare --reactors <files...> --output <file>

# Data
smrforge data setup
smrforge data download --library <lib> --nuclide-set <set>
smrforge data validate --endf-dir <dir>

# Burnup
smrforge burnup run --reactor <file> --time-steps <times...>
smrforge burnup visualize --results <file> --keff --output keff.png --format png

# Transient
smrforge transient run --type <type> --duration <time>

# Thermal
smrforge thermal lumped --duration <time>

# Validation
smrforge validate run
smrforge validate design --reactor <file>

# Visualization
smrforge visualize geometry --reactor <file>
smrforge visualize flux --results <file>

# Configuration
smrforge config show
smrforge config set --key <key> --value <value>

# Workflow
smrforge workflow run <workflow.yaml>

# Dashboard
smrforge serve --host <host> --port <port>

# Shell
smrforge shell
```

---

**End of CLI Guide**

For additional help, run `smrforge --help` or visit the SMRForge documentation.
