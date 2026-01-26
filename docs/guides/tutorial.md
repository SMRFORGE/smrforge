# SMRForge Tutorial: Getting Started

**Last Updated:** January 2026

This tutorial will teach you how to use SMRForge step-by-step, even if you're completely new to Python or nuclear reactor analysis.

## Table of Contents

1. [Installation](#installation)
2. [Your First Calculation](#your-first-calculation)
3. [Using the Command-Line Interface (CLI)](#using-the-command-line-interface-cli)
4. [Working with Preset Designs](#working-with-preset-designs)
5. [Creating Custom Reactors](#creating-custom-reactors)
6. [Understanding the Results](#understanding-the-results)
7. [Visualizing Your Results](#visualizing-your-results)
8. [Advanced Features Overview](#advanced-features-overview)
9. [Next Steps](#next-steps)

---

## Installation

### Step 1: Make Sure You Have Python

SMRForge requires Python 3.8 or higher. To check if you have Python installed, open a terminal (Command Prompt on Windows, Terminal on Mac/Linux) and type:

```bash
python --version
```

If you see something like `Python 3.8.0` or higher, you're good! If not, download Python from [python.org](https://www.python.org/downloads/).

### Step 2: Install SMRForge

The easiest way to install SMRForge is using `pip`:

```bash
pip install smrforge
```

This will download and install SMRForge and all its dependencies. Wait for the installation to complete - it may take a minute or two.

**Alternative Installation Options:**

- **From source (development):**
  ```bash
  git clone https://github.com/cmwhalen/smrforge.git
  cd smrforge
  pip install -e .
  ```

- **Using Docker:**
  ```bash
  docker-compose up -d
  # Or build and run manually
  docker build -t smrforge:latest .
  docker run -it smrforge:latest
  ```

### Step 3: Verify Installation

Let's make sure everything installed correctly. Create a new file called `test_install.py` with this content:

```python
import smrforge as smr
print("SMRForge version:", smr.__version__)
print("Installation successful!")
```

Run it:

```bash
python test_install.py
```

If you see the version number and "Installation successful!", you're ready to go!

**Alternative verification using CLI:**
```bash
smrforge --version
```

---

## Your First Calculation

Let's start with the simplest possible calculation: finding the k-effective (k-eff) of a reactor.

### What is k-eff?

k-eff (or k-effective) tells us if a reactor is:
- **Critical** (k-eff = 1.0): The reactor can sustain a chain reaction
- **Subcritical** (k-eff < 1.0): The chain reaction will die out
- **Supercritical** (k-eff > 1.0): The chain reaction is growing

### Simple Example

Create a new file called `first_calculation.py`:

```python
# Import SMRForge (we'll use 'smr' as a short name)
import smrforge as smr

# Calculate k-eff for a simple reactor
# We'll use: 10 MW power, 19.5% enrichment (typical for HTGRs)
k_eff = smr.quick_keff(power_mw=10, enrichment=0.195)

# Print the result
print(f"k-effective = {k_eff:.6f}")
```

Run it:

```bash
python first_calculation.py
```

You should see output like:

```
k-effective = 1.001234
```

That's it! You just calculated the k-effective of a reactor in just 3 lines of code!

### Understanding the Parameters

In the example above, we used two parameters:

- **`power_mw=10`**: The thermal power of the reactor in megawatts (MW). This is how much heat the reactor produces.
- **`enrichment=0.195`**: The fuel enrichment, meaning 19.5% of the fuel is fissile material (U-235). This is written as a decimal (0.195 = 19.5%).

You can change these values:

```python
import smrforge as smr

# Try a different power level
k_eff = smr.quick_keff(power_mw=50, enrichment=0.195)
print(f"k-effective = {k_eff:.6f}")

# Try a different enrichment
k_eff = smr.quick_keff(power_mw=10, enrichment=0.15)
print(f"k-effective = {k_eff:.6f}")
```

---

## Using the Command-Line Interface (CLI)

SMRForge includes a comprehensive command-line interface that lets you perform calculations without writing Python code!

### Basic CLI Commands

**Check version:**
```bash
smrforge --version
```

**Get help:**
```bash
smrforge --help
smrforge reactor --help
```

### Quick Examples

**Create a reactor from preset:**
```bash
smrforge reactor create --preset valar-10 --output reactor.json
```

**List available presets:**
```bash
smrforge reactor list
```

**Calculate k-eff from CLI:**
```bash
smrforge reactor analyze --reactor reactor.json --keff
```

### Windows note (PowerShell vs Bash)

Many multi-line examples on the internet use Bash line continuations (`\`). **PowerShell does not use `\`**.

- **PowerShell**: use the backtick (`` ` ``) at the end of each continued line.
- **Git Bash / WSL**: use `\` at the end of each continued line.

### Beginner workflow (CLI): preset → input file → results file → plots

This is the safest “start-to-finish” workflow using a preset design.

1) **Create the input file** (`reactor.json`) from a preset:

```bash
smrforge reactor create --preset valar-10 --output reactor.json
```

2) **Run neutronics** and save the results to `results.json`:

```bash
smrforge reactor analyze --reactor reactor.json --neutronics --output results.json
```

3) **Make a geometry image** from `reactor.json`:

```bash
smrforge visualize geometry --reactor reactor.json --output geometry.png --format png
```

4) **Validate the reactor input** (sanity checks) from `reactor.json`:

```bash
smrforge validate design --reactor reactor.json --output validation_report.json
```

Notes:
- `reactor.json` is your **input data** you can edit and reuse.
- `results.json` is your **output data** from analysis.

**Launch the web dashboard:**
```bash
smrforge serve
# Then open http://localhost:8050 in your browser
```

**Start an interactive Python shell with SMRForge pre-loaded:**
```bash
smrforge shell
# Then use: reactor = smr.create_reactor("valar-10")
```

### CLI vs Python API

- **CLI**: Great for quick calculations, automation, batch processing, and workflow scripts
- **Python API**: Better for complex analysis, custom workflows, and programmatic control

See the [CLI Guide](cli-guide.md) for comprehensive documentation of all CLI commands.

---

## Working with Preset Designs

Instead of creating a reactor from scratch every time, SMRForge comes with several **preset designs** - real reactor designs that are already configured. This makes it much easier to get started!

### Available Presets

SMRForge includes these preset reactor designs:

- **`"valar-10"`**: Valar Atomics 10 MWth micro-reactor
- **`"gt-mhr-350"`**: GT-MHR 350 MWth reactor
- **`"htr-pm-200"`**: HTR-PM 200 MWth reactor
- **`"micro-htgr-1"`**: Micro HTGR 1 MWth reactor

### Listing Available Presets

To see all available presets, create a file called `list_presets.py`:

```python
import smrforge as smr

# Get list of available presets
presets = smr.list_presets()
print("Available reactor designs:")
for preset in presets:
    print(f"  - {preset}")
```

### Analyzing a Preset Design

To analyze a preset design, we use the `analyze_preset()` function. Create a file called `analyze_preset.py`:

```python
import smrforge as smr

# Analyze the Valar-10 design
results = smr.analyze_preset("valar-10")

# Print the results
print("Valar-10 Reactor Analysis:")
print(f"  k-effective: {results['k_eff']:.6f}")
print(f"  Thermal Power: {results['power_thermal_mw']:.1f} MW")
print(f"  Flux shape: {results['flux'].shape}")
```

The `results` dictionary contains:
- **`k_eff`**: The k-effective value
- **`power_thermal_mw`**: The thermal power in MW
- **`flux`**: The neutron flux distribution (a numpy array)
- And more!

### Comparing Multiple Designs

You can compare multiple preset designs at once:

```python
import smrforge as smr

# Compare two designs
designs = ["valar-10", "gt-mhr-350"]
comparison = smr.compare_designs(designs)

# Print comparison
for name, results in comparison.items():
    print(f"\n{name}:")
    print(f"  k-effective: {results['k_eff']:.6f}")
    print(f"  Power: {results['power_thermal_mw']:.1f} MW")
```

---

## Creating Custom Reactors

Sometimes you want to create your own reactor design instead of using a preset. SMRForge makes this easy!

### Basic Custom Reactor

Create a file called `custom_reactor.py`:

```python
import smrforge as smr

# Create a custom reactor
reactor = smr.create_reactor(
    power_mw=20,           # 20 MW thermal power
    enrichment=0.18,       # 18% enrichment
    core_height=250.0,     # 250 cm core height
    core_diameter=150.0    # 150 cm core diameter
)

# Solve for k-effective
k_eff = reactor.solve_keff()
print(f"Custom reactor k-effective: {k_eff:.6f}")
```

### Getting Full Analysis Results

Instead of just k-effective, you can get a full analysis:

```python
import smrforge as smr

# Create reactor
reactor = smr.create_reactor(
    power_mw=15,
    enrichment=0.195,
    core_height=200.0,
    core_diameter=120.0
)

# Get full analysis
results = reactor.solve()

# Print all results
print("Full Analysis Results:")
for key, value in results.items():
    if isinstance(value, (int, float)):
        print(f"  {key}: {value}")
    else:
        print(f"  {key}: {type(value).__name__} (shape: {getattr(value, 'shape', 'N/A')})")
```

---

## Understanding the Results

When you run an analysis, you get a dictionary with various results. Here's what each key means:

### Basic Results

- **`k_eff`** (float): The k-effective value. Should be close to 1.0 for a critical reactor.
- **`power_thermal_mw`** (float): The thermal power in megawatts.
- **`flux`** (numpy array): The neutron flux distribution throughout the reactor core.
- **`power_distribution`** (numpy array): The power density distribution (where power is produced).

### Working with Arrays

The `flux` and `power_distribution` are numpy arrays (think of them as tables of numbers). You can do calculations with them:

```python
import smrforge as smr
import numpy as np

# Get analysis results
results = smr.analyze_preset("valar-10")

# Get the flux array
flux = results['flux']

# Basic statistics
print(f"Flux shape: {flux.shape}")
print(f"Maximum flux: {np.max(flux):.2e}")
print(f"Average flux: {np.mean(flux):.2e}")
print(f"Minimum flux: {np.min(flux):.2e}")
```

---

## Visualizing Your Results

Visualizing results helps you understand what's happening in your reactor!

### Plotting Flux Distribution

Create a file called `visualize_flux.py`:

```python
import smrforge as smr
import matplotlib.pyplot as plt
import numpy as np

# Get analysis results
results = smr.analyze_preset("valar-10")

# Get the flux (we'll use the first energy group)
flux = results['flux']
if flux.ndim > 2:
    flux_2d = flux[:, :, 0]  # Take first energy group
else:
    flux_2d = flux

# Create a simple plot
plt.figure(figsize=(8, 6))
plt.imshow(flux_2d, cmap='hot', aspect='auto')
plt.colorbar(label='Neutron Flux')
plt.title('Neutron Flux Distribution')
plt.xlabel('Radial Position')
plt.ylabel('Axial Position')
plt.tight_layout()
plt.savefig('flux_distribution.png')
print("Saved plot to flux_distribution.png")
```

### Plotting Power Distribution

Similarly, you can plot the power distribution:

```python
import smrforge as smr
import matplotlib.pyplot as plt

# Get results
results = smr.analyze_preset("valar-10")

# Get power distribution
power_dist = results.get('power_distribution')
if power_dist is not None:
    plt.figure(figsize=(8, 6))
    plt.imshow(power_dist, cmap='hot', aspect='auto')
    plt.colorbar(label='Power Density (W/cm³)')
    plt.title('Power Distribution')
    plt.xlabel('Radial Position')
    plt.ylabel('Axial Position')
    plt.tight_layout()
    plt.savefig('power_distribution.png')
    print("Saved plot to power_distribution.png")
```

### Using SMRForge's Visualization Tools

SMRForge also has built-in visualization functions:

```python
import smrforge as smr

# Get results
results = smr.analyze_preset("valar-10")

# Use built-in visualization (if available)
# smr.visualization.plot_flux(results['flux'])  # Check examples for exact API
```

Check out the `examples/visualization_examples.py` file for more advanced plotting options!

### CLI Visualization

You can also visualize from the command line:

```bash
# Visualize geometry
smrforge visualize geometry --reactor reactor.json --output geometry.png --format png

# Visualize flux distribution (requires a results file)
#
# NOTE: As of this version, `smrforge visualize flux` prints the Python API snippet
# for plotting. It does not generate a plot by itself yet.
smrforge visualize flux --results results.json
```

---

## Advanced Features Overview

SMRForge includes many advanced features beyond basic neutronics. Here's a brief overview:

### Transient Analysis

Quick transient analysis for reactivity insertions and decay heat:

```python
import smrforge as smr

# Quick reactivity insertion transient
result = smr.quick_transient(
    power=1e6,  # W
    temperature=600.0,  # K
    transient_type="reactivity_insertion",
    reactivity=0.005,  # 5 mk
    duration=100.0  # seconds
)
```

Or from CLI:
```bash
smrforge transient run --power 1000000 --temperature 600 --type reactivity_insertion --reactivity 0.005 --duration 100
```

### Thermal Hydraulics

Lumped-parameter thermal hydraulics for fast 0-D thermal circuit analysis:

```python
from smrforge.thermal.lumped import LumpedThermalHydraulics, ThermalLump, ThermalResistance

# Create thermal lumps (e.g., fuel and moderator)
fuel = ThermalLump(name="fuel", capacitance=1e8, temperature=1200.0)
moderator = ThermalLump(name="moderator", capacitance=5e7, temperature=800.0)
resistance = ThermalResistance(name="fuel_to_moderator", resistance=1e-3, 
                               lump1_name="fuel", lump2_name="moderator")

# Solve transient
solver = LumpedThermalHydraulics(
    lumps={"fuel": fuel, "moderator": moderator},
    resistances=[resistance]
)
result = solver.solve_transient(t_span=(0.0, 3600.0))
```

Or from CLI:
```bash
smrforge thermal lumped --duration 3600 --plot
```

### Other Advanced Features

SMRForge includes many other capabilities:

- **Structural Mechanics**: Fuel rod mechanics, thermal expansion, stress/strain analysis
- **Control Systems**: PID controllers, load-following algorithms
- **Economics**: Cost modeling, LCOE calculations
- **Fuel Cycle Optimization**: Refueling strategies, material aging
- **Advanced Two-Phase Flow**: Drift-flux models, CHF predictions
- **Parallelization**: Multi-core and MPI support for faster calculations

See the [SMR Pain Points Assessment](../../SMR_PAIN_POINTS_ASSESSMENT.md) and [API documentation](https://smrforge.readthedocs.io) for details.

---

## Common Tasks

### Task 1: Find k-eff for Multiple Designs

```python
import smrforge as smr

designs = smr.list_presets()
print("k-effective values:")
print("-" * 40)

for design in designs:
    results = smr.analyze_preset(design)
    k_eff = results['k_eff']
    power = results['power_thermal_mw']
    print(f"{design:15s}: k-eff = {k_eff:.6f}, Power = {power:.1f} MW")
```

### Task 2: Parameter Study

Let's see how k-eff changes with enrichment:

```python
import smrforge as smr

enrichments = [0.15, 0.17, 0.19, 0.21, 0.23]
print("Enrichment Study:")
print("-" * 40)
print("Enrichment (%)    k-effective")
print("-" * 40)

for enrich in enrichments:
    k_eff = smr.quick_keff(power_mw=10, enrichment=enrich)
    print(f"{enrich*100:8.1f}%          {k_eff:.6f}")
```

### Task 3: Save Results to a File

```python
import smrforge as smr
import json

# Get results
results = smr.analyze_preset("valar-10")

# Convert numpy arrays to lists for JSON
json_results = {
    'k_eff': float(results['k_eff']),
    'power_thermal_mw': float(results['power_thermal_mw']),
    # Add other scalar values you want
}

# Save to file
with open('results.json', 'w') as f:
    json.dump(json_results, f, indent=2)

print("Results saved to results.json")
```

### Task 4: Using CLI for Batch Operations

The CLI makes it easy to run multiple analyses:

```bash
# Compare multiple designs
smrforge reactor compare --presets valar-10 gt-mhr-350 htr-pm-200 --metrics k_eff

# Run parameter sweep
smrforge sweep --reactor reactor.json --params enrichment:0.15:0.25:0.02 --analysis keff

# Batch process multiple reactor files
smrforge reactor analyze --batch reactor1.json reactor2.json reactor3.json --keff
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'smrforge'"

This means SMRForge isn't installed. Run:
```bash
pip install smrforge
```

### "ImportError" or Other Import Errors

Try reinstalling:
```bash
pip install --upgrade smrforge
```

Or if installed from source:
```bash
pip install -e . --upgrade
```

### "Command not found: smrforge" (CLI not available)

If the `smrforge` command isn't found:
- Make sure SMRForge is installed: `pip show smrforge`
- Check that the installation script path is in your PATH
- Try using Python module syntax: `python -m smrforge.cli --help`
- On Windows, make sure Python Scripts directory is in PATH

### Calculations Take Too Long

The neutronics solver can take a few seconds to minutes depending on the problem size. For faster results:
- Use simpler geometries (smaller core sizes)
- Use fewer mesh points
- Use the `quick_keff()` function for simple calculations
- Enable parallelization (automatic on multi-core systems)
- Use the optimized Monte Carlo solver for Monte Carlo calculations

### k-eff is Very Far from 1.0

This could mean:
- The reactor design isn't physically realistic
- The parameters you chose don't make sense for the reactor type
- Try using preset designs first to see what reasonable values look like
- Check that enrichment and geometry parameters are reasonable

### Dashboard Not Opening

If `smrforge serve` doesn't open in browser:
- Check that port 8050 is available
- Try `smrforge serve --host 0.0.0.0 --port 8050`
- Manually open `http://localhost:8050` in your browser
- Check firewall settings

---

## Next Steps

Congratulations! You've learned the basics of SMRForge. Here's what to explore next:

### 1. Explore Example Scripts

Check out the `examples/` directory for more detailed examples:
- `examples/basic_neutronics.py` - More detailed neutronics examples
- `examples/preset_designs.py` - Working with preset designs
- `examples/visualization_examples.py` - Advanced visualization
- `examples/thermal_analysis.py` - Thermal-hydraulics analysis
- `examples/convenience_methods_example.py` - Using convenience functions
- `examples/complete_smr_workflow_example.py` - Complete workflow example

### 2. Read the Documentation

- **CLI Guide**: Comprehensive guide to all CLI commands - see [CLI Guide](cli-guide.md)
- **API Reference**: Full documentation of all functions at [smrforge.readthedocs.io](https://smrforge.readthedocs.io)
- **Usage Guide**: See `docs/guides/usage.md` for more usage examples
- **Docker Guide**: See `docs/guides/docker.md` for Docker usage
- **Feature Status**: See `docs/status/feature-status.md` to see what features are available

### 3. Try Advanced Features

Once you're comfortable with the basics, try:
- **CLI Workflows**: Use `smrforge workflow run` for YAML-based automation
- **Web Dashboard**: Launch `smrforge serve` for interactive analysis
- **Transient Analysis**: Run safety transients and decay heat calculations
- **Thermal Hydraulics**: Analyze coolant flow and heat transfer
- **Geometry Creation**: Create custom reactor geometries
- **Uncertainty Quantification**: Understand how uncertainty affects results

### 4. Join the Community

- **GitHub**: [github.com/cmwhalen/smrforge](https://github.com/cmwhalen/smrforge)
- **Issues**: Report bugs or request features on GitHub
- **Documentation**: Read the full docs online

---

## Quick Reference Card

### Python API

```python
# Import
import smrforge as smr

# Quick k-eff
k = smr.quick_keff(power_mw=10, enrichment=0.195)

# List presets
presets = smr.list_presets()

# Analyze preset
results = smr.analyze_preset("valar-10")

# Create custom reactor
reactor = smr.create_reactor(power_mw=20, enrichment=0.18)

# Get k-eff only
k = reactor.solve_keff()

# Get full analysis
results = reactor.solve()

# Compare designs
comparison = smr.compare_designs(["valar-10", "gt-mhr-350"])

# Quick transient
transient_result = smr.quick_transient(
    power=1e6, temperature=600.0,
    transient_type="reactivity_insertion",
    reactivity=0.005, duration=100.0
)
```

### CLI Commands

```bash
# Basic commands
smrforge --version
smrforge --help
smrforge reactor list

# Create and analyze
smrforge reactor create --preset valar-10 --output reactor.json
smrforge reactor analyze --reactor reactor.json --keff

# Dashboard and shell
smrforge serve
smrforge shell

# Advanced
smrforge transient run --type reactivity_insertion --duration 100
smrforge thermal lumped --duration 3600
smrforge workflow run workflow.yaml
```

---

## Summary

In this tutorial, you learned:

1. ✅ How to install SMRForge (pip, source, or Docker)
2. ✅ How to calculate k-effective with one line of code
3. ✅ How to use the command-line interface (CLI)
4. ✅ How to use preset reactor designs
5. ✅ How to create custom reactors
6. ✅ How to understand and visualize results
7. ✅ Overview of advanced features (transients, thermal hydraulics, etc.)
8. ✅ Common tasks and troubleshooting tips

You're now ready to start using SMRForge for your reactor analysis! Remember:
- Start simple with `quick_keff()` and presets
- Use the CLI for quick calculations: `smrforge reactor create --preset valar-10`
- Use the web dashboard: `smrforge serve`
- Experiment with different parameters
- Check the examples directory for more ideas
- Read the [CLI Guide](cli-guide.md) for comprehensive CLI documentation
- Read the API documentation for advanced features

Happy analyzing! 🚀

