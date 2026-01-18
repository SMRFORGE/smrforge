# SMRForge CLI Guide

**Last Updated:** January 2026  
**Version:** SMRForge v1.0+

---

## Table of Contents

1. [Introduction](#introduction)
2. [Installation and Setup](#installation-and-setup)
3. [Getting Help](#getting-help)
4. [Command Overview](#command-overview)
5. [Reactor Operations](#reactor-operations)
6. [Data Management](#data-management)
7. [Burnup Calculations](#burnup-calculations)
8. [Transient Analysis](#transient-analysis)
9. [Thermal Hydraulics](#thermal-hydraulics)
10. [Validation and Testing](#validation-and-testing)
11. [Visualization](#visualization)
12. [Configuration Management](#configuration-management)
13. [Workflow Automation](#workflow-automation)
14. [Interactive Shell](#interactive-shell)
15. [Web Dashboard](#web-dashboard)
16. [Advanced Usage](#advanced-usage)
17. [Troubleshooting](#troubleshooting)

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
| `visualize` | Visualization | `geometry`, `flux`, `burnup` |
| `config` | Configuration | `show`, `set`, `init` |
| `workflow` | Workflow automation | `run` |
| `sweep` | Parameter sweeps | None |

---

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

```bash
smrforge reactor create \
    --power 10 \
    --enrichment 0.195 \
    --type htgr \
    --core-height 200 \
    --core-diameter 100 \
    --fuel-type UCO \
    --output reactor.json
```

#### Options

- `--preset NAME` - Use preset design (e.g., `valar-10`, `gt-mhr`, `htr-pm`)
- `--config FILE` - Load from configuration file (JSON or YAML)
- `--power FLOAT` - Thermal power [MW]
- `--enrichment FLOAT` - Fuel enrichment (0-1)
- `--type STR` - Reactor type (`htgr`, `pwr`, `bwr`, `fast`)
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

- `--reactor FILE` - Reactor specification file (JSON/YAML)
- `--keff` - Calculate k_eff only
- `--neutronics` - Full neutronics analysis
- `--burnup` - Burnup analysis
- `--safety` - Safety analysis
- `--complete` - Complete analysis (all above)
- `--output FILE` - Output file for results
- `--plot` - Generate plots
- `--plot-output DIR` - Plot output directory
- `--plot-backend STR` - Plot backend (`plotly`, `matplotlib`)

#### Advanced Options

```bash
# Custom solver options
smrforge reactor analyze \
    --reactor reactor.json \
    --neutronics \
    --max-iterations 200 \
    --tolerance 1e-7 \
    --parallel

# Parallel execution
smrforge reactor analyze \
    --reactor reactor.json \
    --neutronics \
    --parallel \
    --workers 8
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
    --output-dir ~/ENDF-Data

# Parallel downloads
smrforge data download \
    --library ENDF-B-VIII.1 \
    --nuclide-set common_smr \
    --parallel
```

**Options:**
- `--library STR` - ENDF library (`ENDF-B-VIII.0`, `ENDF-B-VIII.1`)
- `--nuclide-set STR` - Predefined nuclide set (`common_smr`, `all_actinides`, etc.)
- `--nuclides NUCLIDES...` - Specific nuclides (e.g., `U235 U238 Pu239`)
- `--output-dir DIR` - Download directory
- `--parallel` - Parallel downloads (faster)
- `--workers INT` - Number of parallel workers

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
smrforge data validate --endf-files file1.endf file2.endf

# Detailed validation report
smrforge data validate --endf-dir ~/ENDF-Data --output report.json
```

**Options:**
- `--endf-dir DIR` - ENDF directory to validate
- `--endf-files FILES...` - Specific ENDF files to validate
- `--output FILE` - Validation report output file

---

## Burnup Calculations

### Run Burnup Calculation

Calculate nuclide inventory over time (depletion).

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
    --checkpoint-dir checkpoints/

# Continuous output (save at each step)
smrforge burnup run \
    --reactor reactor.json \
    --time-steps 0 365 730 \
    --power-density 50 \
    --save-intermediate
```

**Options:**
- `--reactor FILE` - Reactor specification file
- `--time-steps FLOATS...` - Time steps [days] (e.g., `0 365 730`)
- `--power-density FLOAT` - Power density [W/cm³]
- `--output FILE` - Output file for results
- `--checkpoint-dir DIR` - Checkpoint directory (for long calculations)
- `--save-intermediate` - Save results at each time step
- `--plot` - Generate burnup plots
- `--plot-output DIR` - Plot output directory

### Visualize Burnup Results

Generate plots from burnup calculation results.

```bash
# Plot nuclide concentrations
smrforge burnup visualize \
    --input burnup_results.json \
    --plot-concentrations

# Plot k_eff evolution
smrforge burnup visualize \
    --input burnup_results.json \
    --plot-keff

# All plots
smrforge burnup visualize \
    --input burnup_results.json \
    --output plots/ \
    --backend plotly
```

**Options:**
- `--input FILE` - Burnup results file
- `--plot-concentrations` - Plot nuclide concentrations vs. time
- `--plot-keff` - Plot k_eff evolution
- `--plot-power` - Plot power distribution evolution
- `--output DIR` - Plot output directory
- `--backend STR` - Plot backend (`plotly`, `matplotlib`)

---

## Transient Analysis

### Run Transient Analysis

Analyze reactor behavior during transients (reactivity insertion, decay heat removal, etc.).

```bash
# Quick transient analysis
smrforge transient run \
    --type reactivity_insertion \
    --reactivity 0.01 \
    --duration 100

# With reactor specification
smrforge transient run \
    --reactor reactor.json \
    --type reactivity_insertion \
    --reactivity 0.01 \
    --duration 100 \
    --output transient_results.json

# Decay heat removal
smrforge transient run \
    --reactor reactor.json \
    --type decay_heat_removal \
    --duration 3600 \
    --output decay_heat.json

# With plots
smrforge transient run \
    --reactor reactor.json \
    --type reactivity_insertion \
    --reactivity 0.01 \
    --duration 100 \
    --plot \
    --plot-output plots/
```

**Transient Types:**
- `reactivity_insertion` - Reactivity insertion transient
- `decay_heat_removal` - Decay heat removal transient
- `power_transient` - Power transient
- `temperature_transient` - Temperature transient

**Options:**
- `--reactor FILE` - Reactor specification file (optional)
- `--type STR` - Transient type
- `--reactivity FLOAT` - Reactivity insertion [dk/k]
- `--duration FLOAT` - Transient duration [seconds]
- `--power FLOAT` - Initial power [W] (for power transient)
- `--temperature FLOAT` - Initial temperature [K] (for temperature transient)
- `--output FILE` - Output file for results
- `--plot` - Generate plots
- `--plot-output DIR` - Plot output directory
- `--plot-backend STR` - Plot backend (`plotly`, `matplotlib`)
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
    --plot-output plots/
```

**Options:**
- `--duration FLOAT` - Analysis duration [seconds]
- `--max-step FLOAT` - Maximum time step [seconds]
- `--adaptive` - Enable adaptive time stepping
- `--output FILE` - Output file for results
- `--plot` - Generate plots
- `--plot-output DIR` - Plot output directory

---

## Validation and Testing

### Run Validation Tests

Run validation test suite and compare with benchmarks.

```bash
# Run all validation tests
smrforge validate run

# Run specific test suite
smrforge validate run --suite benchmarks

# Generate validation report
smrforge validate run --output validation_report.json

# Compare with benchmark
smrforge validate run --benchmark oak-ridge-1
```

**Options:**
- `--suite STR` - Test suite (`all`, `benchmarks`, `unit`, `integration`)
- `--benchmark STR` - Specific benchmark to run
- `--output FILE` - Validation report output file
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

# Strict validation
smrforge validate design \
    --reactor reactor.json \
    --strict
```

**Options:**
- `--reactor FILE` - Reactor specification file
- `--output FILE` - Validation report output file
- `--strict` - Strict validation (fail on warnings)
- `--check-metallurgy` - Check metallurgical constraints
- `--check-thermal` - Check thermal constraints
- `--check-neutronics` - Check neutronics constraints

---

## Visualization

### Visualize Geometry

Generate 2D or 3D geometry visualizations.

```bash
# Basic geometry visualization
smrforge visualize geometry --reactor reactor.json

# 3D visualization
smrforge visualize geometry \
    --reactor reactor.json \
    --3d \
    --output geometry_3d.html

# Custom view
smrforge visualize geometry \
    --reactor reactor.json \
    --view xz \
    --output geometry_xz.png
```

**Options:**
- `--reactor FILE` - Reactor specification file
- `--3d` - Generate 3D visualization
- `--view STR` - 2D view (`xy`, `xz`, `yz`)
- `--output FILE` - Output file (HTML for 3D, PNG/SVG for 2D)
- `--backend STR` - Backend (`plotly`, `matplotlib`, `pyvista`)

### Visualize Flux Distribution

Plot neutron flux distribution.

```bash
# Flux distribution from neutronics results
smrforge visualize flux \
    --input neutronics_results.json \
    --output flux_plot.png

# Group-wise flux
smrforge visualize flux \
    --input neutronics_results.json \
    --groups 1 2 3 \
    --output flux_groups.png
```

**Options:**
- `--input FILE` - Neutronics results file
- `--groups INTS...` - Energy groups to plot
- `--output FILE` - Output file
- `--backend STR` - Backend (`plotly`, `matplotlib`)

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

# With output directory
smrforge workflow run workflow.yaml --output-dir results/

# Verbose output
smrforge workflow run workflow.yaml --verbose
```

**Workflow YAML Example:**

```yaml
name: Reactor Analysis Workflow
steps:
  - name: Create Reactor
    type: reactor_create
    preset: valar-10
    output: reactor.json
  
  - name: Neutronics Analysis
    type: reactor_analyze
    reactor: reactor.json
    analysis: neutronics
    output: neutronics_results.json
  
  - name: Burnup Calculation
    type: burnup_run
    reactor: reactor.json
    time_steps: [0, 365, 730]
    power_density: 50
    output: burnup_results.json
  
  - name: Generate Plots
    type: visualize
    inputs:
      - neutronics_results.json
      - burnup_results.json
    output_dir: plots/
```

**Options:**
- `workflow FILE` - Workflow YAML file
- `--output-dir DIR` - Output directory for workflow results
- `--verbose` - Verbose output

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
    --parallel \
    --workers 4
```

**Parallel Options:**
- `--parallel` - Enable parallel execution
- `--workers INT` - Number of parallel workers (default: auto)

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
smrforge reactor analyze --reactor reactor.json --neutronics --output results.yaml

# CSV export (for tabular data)
smrforge burnup visualize --input burnup_results.json --export-csv burnup.csv
```

### Combining Commands

Chain commands together using pipes or scripts.

```bash
# Create and analyze in one line
smrforge reactor create --preset valar-10 --output - | \
    smrforge reactor analyze --reactor - --neutronics

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
    --parallel

# 3. Create reactor
smrforge reactor create \
    --preset valar-10 \
    --output reactor.json

# 4. Neutronics analysis
smrforge reactor analyze \
    --reactor reactor.json \
    --neutronics \
    --output neutronics_results.json \
    --plot

# 5. Burnup calculation
smrforge burnup run \
    --reactor reactor.json \
    --time-steps 0 365 730 1095 \
    --power-density 50 \
    --output burnup_results.json \
    --checkpoint-dir checkpoints/

# 6. Visualize results
smrforge visualize flux \
    --input neutronics_results.json \
    --output flux_plot.png

smrforge burnup visualize \
    --input burnup_results.json \
    --output plots/

# 7. Validate design
smrforge validate design \
    --reactor reactor.json \
    --output validation_report.json
```

### Parameter Sweep Example

```bash
#!/bin/bash
# Parameter sweep: enrichment vs. k_eff

for enrichment in 0.15 0.17 0.19 0.21 0.23; do
    reactor_file="reactor_${enrichment}.json"
    results_file="results_${enrichment}.json"
    
    # Create reactor with specific enrichment
    smrforge reactor create \
        --preset valar-10 \
        --enrichment "$enrichment" \
        --output "$reactor_file"
    
    # Analyze
    smrforge reactor analyze \
        --reactor "$reactor_file" \
        --keff \
        --output "$results_file"
done

# Compare results
smrforge reactor compare \
    --reactors reactor_*.json \
    --metrics keff enrichment \
    --output sweep_comparison.json
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
smrforge burnup visualize --input <file>

# Transient
smrforge transient run --type <type> --duration <time>

# Thermal
smrforge thermal lumped --duration <time>

# Validation
smrforge validate run
smrforge validate design --reactor <file>

# Visualization
smrforge visualize geometry --reactor <file>
smrforge visualize flux --input <file>

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
