# SMRForge Tutorial: Getting Started

This tutorial will teach you how to use SMRForge step-by-step, even if you're completely new to Python or nuclear reactor analysis.

## Table of Contents

1. [Installation](#installation)
2. [Your First Calculation](#your-first-calculation)
3. [Working with Preset Designs](#working-with-preset-designs)
4. [Creating Custom Reactors](#creating-custom-reactors)
5. [Understanding the Results](#understanding-the-results)
6. [Visualizing Your Results](#visualizing-your-results)
7. [Next Steps](#next-steps)

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

SMRForge also has built-in visualization functions. Check out the `examples/visualization_examples.py` file for more advanced plotting options!

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

### Calculations Take Too Long

The neutronics solver can take a few seconds to minutes depending on the problem size. For faster results:
- Use simpler geometries (smaller core sizes)
- Use fewer mesh points
- Use the `quick_keff()` function for simple calculations

### k-eff is Very Far from 1.0

This could mean:
- The reactor design isn't physically realistic
- The parameters you chose don't make sense for the reactor type
- Try using preset designs first to see what reasonable values look like

---

## Next Steps

Congratulations! You've learned the basics of SMRForge. Here's what to explore next:

### 1. Explore Example Scripts

Check out the `examples/` directory for more detailed examples:
- `examples/basic_neutronics.py` - More detailed neutronics examples
- `examples/preset_designs.py` - Working with preset designs
- `examples/visualization_examples.py` - Advanced visualization
- `examples/thermal_analysis.py` - Thermal-hydraulics analysis

### 2. Read the Documentation

- **API Reference**: Full documentation of all functions at [smrforge.readthedocs.io](https://smrforge.readthedocs.io)
- **Usage Guide**: See `USAGE.md` for more usage examples
- **Feature Status**: See `FEATURE_STATUS.md` to see what features are available

### 3. Try Advanced Features

Once you're comfortable with the basics, try:
- **Geometry Creation**: Create custom reactor geometries
- **Thermal-Hydraulics**: Analyze coolant flow and heat transfer
- **Safety Analysis**: Run transient safety scenarios
- **Uncertainty Quantification**: Understand how uncertainty affects results

### 4. Join the Community

- **GitHub**: [github.com/cmwhalen/smrforge](https://github.com/cmwhalen/smrforge)
- **Issues**: Report bugs or request features on GitHub
- **Documentation**: Read the full docs online

---

## Quick Reference Card

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
```

---

## Summary

In this tutorial, you learned:

1. ✅ How to install SMRForge
2. ✅ How to calculate k-effective with one line of code
3. ✅ How to use preset reactor designs
4. ✅ How to create custom reactors
5. ✅ How to understand and visualize results
6. ✅ Common tasks and troubleshooting tips

You're now ready to start using SMRForge for your reactor analysis! Remember:
- Start simple with `quick_keff()` and presets
- Experiment with different parameters
- Check the examples directory for more ideas
- Read the documentation for advanced features

Happy analyzing! 🚀

