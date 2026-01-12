# SMRForge Web Dashboard Guide

**Last Updated:** January 2026

Complete guide for using the SMRForge web-based dashboard interface.

---

## Overview

SMRForge provides a web-based dashboard interface built with Dash, allowing you to interact with SMRForge through a modern browser interface. **All features remain fully available via CLI and Python API** - the dashboard is an optional, user-friendly interface.

### Key Features

- ✅ **Reactor Builder** - Form-based reactor creation with preset support
- ✅ **Analysis Panel** - Run neutronics, burnup, and safety analysis
- ✅ **Results Viewer** - Interactive visualization of analysis results
- ✅ **Data Manager** - Download and manage ENDF nuclear data
- ✅ **Project Management** - Save and load reactor projects
- ✅ **CLI Compatibility** - All features available via command line

---

## Installation

### Install Dashboard Dependencies

**IMPORTANT:** The dashboard requires Dash and related packages. These are **not installed by default**.

```bash
# Option 1: Install with visualization extras (includes Dash)
pip install smrforge[viz]

# Option 2: Install Dash separately
pip install dash dash-bootstrap-components

# Option 3: Install in development mode with extras
pip install -e ".[viz]"
```

### Verify Installation

```bash
# Check if Dash is installed
python -c "import dash; print('Dash version:', dash.__version__)"

# Check if dashboard module is available
python -c "from smrforge.gui import create_app; print('Dashboard available!')"

# Full dependency check
python -c "import dash; import dash_bootstrap_components; from smrforge.gui import create_app; print('All dependencies OK!')"
```

### Troubleshooting Installation

If you get `ModuleNotFoundError: No module named 'dash'`:

1. **Install dependencies:**
   ```bash
   pip install dash dash-bootstrap-components
   ```

2. **Verify installation:**
   ```bash
   pip list | grep dash
   ```

3. **Check Python environment:**
   - Ensure you're using the correct Python environment
   - If using virtual environment, activate it first
   - If using conda, ensure conda environment is activated

See [Dashboard Troubleshooting Guide](dashboard-troubleshooting.md) for more help.

---

## Quick Start

### Launch Dashboard

**Option 1: Using CLI Command**
```bash
smrforge serve
```

**Option 2: Using Python**
```python
from smrforge.gui import run_server
run_server()
```

**Option 3: Custom Port/Host**
```bash
smrforge serve --port 8080 --host 0.0.0.0
```

### Access Dashboard

Once started, open your browser to:
```
http://127.0.0.1:8050
```

---

## Dashboard Features

### 1. Reactor Builder

**Location:** Sidebar → "Reactor Builder"

**Features:**
- Select from preset designs (Valar-10, GT-MHR, HTR-PM, etc.)
- Create custom reactors with form inputs
- Real-time validation using Pydantic models
- View reactor specification summary

**Example Workflow:**
1. Select a preset or enter custom parameters
2. Click "Create Reactor"
3. Review the reactor specification
4. Proceed to Analysis panel

**CLI Equivalent:**
```python
import smrforge as smr
reactor = smr.create_reactor("valar-10")
# or
reactor = smr.create_reactor(power_mw=10, enrichment=0.195)
```

### 2. Analysis Panel

**Location:** Sidebar → "Analysis"

**Features:**
- **Neutronics Analysis** - k-eff calculation with configurable options
- **Burnup Analysis** - Fuel cycle analysis with time steps
- **Safety Transients** - Transient analysis (SLB, LOCA, etc.)
- **Complete Analysis** - Run all analyses together

**Example Workflow:**
1. Ensure a reactor is created (from Reactor Builder)
2. Select analysis type
3. Configure analysis options
4. Click "Run Analysis"
5. View results in Results panel

**CLI Equivalent:**
```python
import smrforge as smr
reactor = smr.create_reactor("valar-10")
k_eff = reactor.solve_keff()
results = reactor.solve()  # Complete analysis
```

### 3. Results Viewer

**Location:** Sidebar → "Results"

**Features:**
- **Results Summary** - Key metrics (k-eff, etc.)
- **Flux Distribution** - Interactive flux plots
- **Power Distribution** - Power density visualization
- **3D Geometry** - 3D reactor geometry viewer
- **Transient Results** - Time-dependent results
- **Export Options** - Export to JSON, CSV, or plots

**CLI Equivalent:**
```python
import smrforge as smr
from smrforge.visualization import plot_core_layout_2d

reactor = smr.create_reactor("valar-10")
results = reactor.solve()

# Visualize
plot_core_layout_2d(reactor.core)
```

### 4. Data Manager

**Location:** Sidebar → "Data Manager"

**Features:**
- **ENDF Data Download** - Download nuclear data libraries
- **Library Selection** - ENDF/B-VIII.1, JEFF-3.3, JENDL-5.0
- **Selective Download** - By nuclide set, isotopes, or elements
- **Parallel Downloads** - Configurable worker threads
- **Configuration** - Set ENDF and cache directories

**Example Workflow:**
1. Select library version
2. Choose download type (common SMR nuclides, specific isotopes, etc.)
3. Set output directory
4. Click "Download ENDF Data"
5. Monitor progress

**CLI Equivalent:**
```python
from smrforge.data_downloader import download_endf_data

stats = download_endf_data(
    library="ENDF/B-VIII.1",
    nuclide_set="common_smr",
    output_dir="~/ENDF-Data",
    max_workers=5,
)
```

---

## CLI vs Dashboard

### When to Use Dashboard

- ✅ **Interactive Exploration** - Explore parameters visually
- ✅ **Quick Prototyping** - Fast iteration on designs
- ✅ **Visualization** - See results immediately
- ✅ **Non-Programmers** - User-friendly interface
- ✅ **Learning** - Understand SMRForge workflows

### When to Use CLI

- ✅ **Automation** - Scripts and batch processing
- ✅ **Reproducibility** - Version-controlled workflows
- ✅ **Performance** - No web server overhead
- ✅ **Integration** - Embed in larger workflows
- ✅ **Advanced Features** - Full API access

### Both Work Together

The dashboard and CLI use the **same underlying SMRForge functions**, so:
- Projects created in dashboard can be used in CLI
- CLI scripts can be run while dashboard is open
- Results are compatible between interfaces

---

## Advanced Usage

### Custom Port and Host

```bash
# Make dashboard accessible on network
smrforge serve --host 0.0.0.0 --port 8080

# Debug mode (auto-reload on code changes)
smrforge serve --debug
```

### Programmatic Access

```python
from smrforge.gui import create_app, run_server

# Create app instance
app = create_app()

# Run with custom settings
run_server(host='0.0.0.0', port=8080, debug=False)
```

### Integration with Existing Code

```python
import smrforge as smr
from smrforge.gui import run_server
import threading

# Start dashboard in background
dashboard_thread = threading.Thread(
    target=run_server,
    kwargs={'port': 8050, 'debug': False}
)
dashboard_thread.daemon = True
dashboard_thread.start()

# Continue with CLI/Python workflow
reactor = smr.create_reactor("valar-10")
k_eff = reactor.solve_keff()
print(f"k-eff: {k_eff:.6f}")

# Dashboard is available at http://127.0.0.1:8050
```

---

## Project Management

### Save Project

1. Create reactor and run analysis
2. Click "Save Project" in sidebar
3. Choose save location
4. Project saved as JSON

### Load Project

1. Click "Open Project" in sidebar
2. Select project file
3. Reactor and results loaded

### CLI Project Management

```python
import smrforge as smr

# Save
reactor = smr.create_reactor("valar-10")
reactor.save("my_reactor.json")

# Load
reactor = smr.SimpleReactor.load("my_reactor.json")
```

---

## Troubleshooting

### Dashboard Won't Start

**Error:** `Dash is not installed`

**Solution:**
```bash
pip install dash dash-bootstrap-components
# or
pip install smrforge[viz]
```

### Port Already in Use

**Error:** `Address already in use`

**Solution:**
```bash
# Use different port
smrforge serve --port 8051
```

### Import Errors

**Error:** `ModuleNotFoundError: dash`

**Solution:**
- Ensure dashboard dependencies are installed
- Check Python environment
- Try: `pip install --upgrade dash dash-bootstrap-components`

### Results Not Showing

**Solution:**
- Ensure analysis completed successfully
- Check browser console for errors
- Verify reactor was created before running analysis

---

## Keyboard Shortcuts

- **Ctrl+C** - Stop dashboard server (in terminal)
- **F5** - Refresh browser (reload dashboard)
- **Ctrl+Shift+R** - Hard refresh (clear cache)

---

## Best Practices

1. **Start Simple** - Use presets first, then customize
2. **Validate Inputs** - Check reactor specification before analysis
3. **Save Projects** - Save frequently to avoid losing work
4. **Use CLI for Automation** - Dashboard for exploration, CLI for production
5. **Monitor Resources** - Large analyses may take time

---

## Examples

### Complete Workflow in Dashboard

1. **Launch Dashboard:**
   ```bash
   smrforge serve
   ```

2. **Create Reactor:**
   - Go to Reactor Builder
   - Select "valar-10" preset
   - Click "Load Preset"
   - Click "Create Reactor"

3. **Run Analysis:**
   - Go to Analysis panel
   - Select "Neutronics"
   - Click "Run Analysis"

4. **View Results:**
   - Go to Results panel
   - View k-eff value
   - Explore flux and power plots

5. **Export:**
   - Click "Export to JSON"
   - Save results for later use

### Equivalent CLI Workflow

```python
import smrforge as smr

# Create reactor
reactor = smr.create_reactor("valar-10")

# Run analysis
k_eff = reactor.solve_keff()
results = reactor.solve()

# Visualize
from smrforge.visualization import plot_core_layout_2d
plot_core_layout_2d(reactor.core)

# Export
reactor.save("valar10_results.json")
```

---

## API Reference

### `run_server()`

Launch the dashboard server.

```python
from smrforge.gui import run_server

run_server(
    host="127.0.0.1",  # Host address
    port=8050,         # Port number
    debug=False,       # Debug mode
)
```

### `create_app()`

Create Dash application instance (for advanced usage).

```python
from smrforge.gui import create_app

app = create_app()
app.run_server(debug=True)
```

---

## See Also

- [Complete Workflow Examples](complete-workflow-examples.md) - Comprehensive examples
- [Data Downloader Guide](data-downloader-guide.md) - ENDF data management
- [Usage Guide](usage.md) - General SMRForge usage
- [CLI Documentation](../status/gui-ux-strategy-analysis.md) - GUI strategy details

---

**Remember:** All dashboard features are available via CLI and Python API. Choose the interface that works best for your workflow!
