# SMRForge Master Examples Index

**Last Updated:** January 2026

Complete index of all example code and tutorials in SMRForge documentation.

---

## Quick Navigation

- [Complete Workflows](#complete-workflows)
- [Data Management](#data-management)
- [Geometry Creation](#geometry-creation)
- [Neutronics Analysis](#neutronics-analysis)
- [Burnup Analysis](#burnup-analysis)
- [Safety Analysis](#safety-analysis)
- [Visualization](#visualization)
- [Integration Examples](#integration-examples)

---

## Complete Workflows

### End-to-End SMR Analysis

**File:** `examples/complete_smr_workflow_example.py`  
**Guide:** `docs/guides/complete-workflow-examples.md`

Complete workflow from data setup to results export:
- Automated ENDF data download
- NuScale PWR SMR geometry creation
- Cross-section retrieval with self-shielding
- Advanced burnup analysis
- Safety transient analysis
- Comprehensive visualization

**Run:**
```bash
python examples/complete_smr_workflow_example.py
```

### Production-Ready Pipeline

**Guide:** `docs/guides/complete-workflow-examples.md` (Section: Production-Ready Analysis Pipeline)

Complete analysis pipeline with:
- Error handling and logging
- Result export (JSON, text summaries)
- Modular workflow design
- Production best practices

---

## Data Management

### Automated Data Download

**Guide:** `docs/guides/data-downloader-guide.md`

**Basic Download:**
```python
from smrforge.data_downloader import download_endf_data

stats = download_endf_data(
    library="ENDF/B-VIII.1",
    nuclide_set="common_smr",
    output_dir="~/ENDF-Data",
    show_progress=True,
)
```

**Parallel Downloads:**
```python
stats = download_endf_data(
    library="ENDF/B-VIII.1",
    isotopes=["U235", "U238", "Pu239"],
    max_workers=10,  # Maximum parallelization
    resume=True,
    validate=True,
)
```

**Multiple Libraries:**
```python
libraries = ["ENDF/B-VIII.1", "JEFF-3.3", "JENDL-5.0"]
for library in libraries:
    stats = download_endf_data(
        library=library,
        nuclide_set="common_smr",
        output_dir=f"~/ENDF-Data/{library}",
    )
```

### Configuration Setup

**Environment Variable:**
```bash
export SMRFORGE_ENDF_DIR=~/ENDF-Data
```

**Configuration File (`~/.smrforge/config.yaml`):**
```yaml
endf:
  default_directory: "~/ENDF-Data"
  default_library: "ENDF/B-VIII.1"
  auto_download: true
```

---

## Geometry Creation

### LWR SMR Geometry

**Guide:** `docs/guides/lwr-smr-transient-analysis.md`  
**File:** `examples/lwr_smr_example.py`

**NuScale PWR SMR:**
```python
from smrforge.geometry.lwr_smr import PWRSMRCore
from smrforge.geometry.smr_compact_core import CompactSMRCore

# Compact core (37 assemblies)
core = CompactSMRCore(
    name="NuScale-SMR",
    n_assemblies=37,
    assembly_pitch=21.5,  # cm
    active_height=200.0,  # cm
)

# Build square lattice (17x17)
core.build_square_lattice_core(
    n_assemblies_x=6,
    n_assemblies_y=6,
    lattice_size=17,
    rod_pitch=1.26,  # cm
)
```

**mPower PWR SMR:**
```python
core = CompactSMRCore(
    name="mPower-SMR",
    n_assemblies=69,
    assembly_pitch=21.5,
)
```

**BWR SMR:**
```python
from smrforge.geometry.lwr_smr import BWRSMRCore

core = BWRSMRCore(
    name="BWR-SMR",
    n_assemblies=37,
)
```

### Integral Reactor Designs

```python
from smrforge.geometry.lwr_smr import (
    InVesselSteamGenerator,
    IntegratedPrimarySystem,
)

# In-vessel steam generator
steam_generator = InVesselSteamGenerator(
    name="NuScale-SG",
    n_tubes=1000,
    tube_length=200.0,  # cm
    primary_pressure=15.5e6,  # Pa
    secondary_pressure=6.0e6,  # Pa
)

# Integrated primary system
integrated_system = IntegratedPrimarySystem(
    name="NuScale-Integrated",
    core=core,
    steam_generator=steam_generator,
)
```

### HTGR Geometry

```python
from smrforge.presets.htgr import ValarAtomicsReactor

reactor = ValarAtomicsReactor()
core = reactor.build_core()
```

---

## Neutronics Analysis

### Basic Neutronics

**File:** `examples/basic_neutronics.py`

```python
from smrforge.neutronics.solver import MultiGroupDiffusion
from smrforge.validation.models import CrossSectionData, SolverOptions

# Create solver
solver = MultiGroupDiffusion(geometry, xs_data, options)
k_eff, flux = solver.solve_steady_state()

# Compute power distribution
power_dist = solver.compute_power_distribution(total_power)
```

### Self-Shielding

**Guide:** `docs/quickstart.rst`

```python
from smrforge.core.self_shielding_integration import (
    get_cross_section_with_self_shielding,
)

# Bondarenko method
energy, xs = get_cross_section_with_self_shielding(
    cache,
    u238,
    "capture",
    temperature=600.0,
    sigma_0=1000.0,  # Background cross-section
    method="bondarenko",
)

# Subgroup method (higher accuracy)
energy, xs = get_cross_section_with_self_shielding(
    cache,
    u238,
    "capture",
    temperature=600.0,
    sigma_0=1000.0,
    method="subgroup",
)

# Equivalence theory (for fuel pin homogenization)
energy, xs = get_cross_section_with_equivalence_theory(
    cache,
    u238,
    "capture",
    temperature=600.0,
    fuel_radius=0.4,  # cm
    pitch=1.26,  # cm
    volume_fraction=0.4,
)
```

---

## Burnup Analysis

### Basic Burnup

**File:** `examples/burnup_example.py`

```python
from smrforge.burnup.solver import BurnupSolver, BurnupOptions

options = BurnupOptions(
    time_steps=[0, 365, 730, 1095],  # 0, 1, 2, 3 years
    power_density=1e6,  # W/cm³
    initial_enrichment=0.045,
)

solver = BurnupSolver(neutronics_solver, options)
inventory = solver.solve()
```

### Gadolinium Depletion

**Guide:** `docs/guides/lwr-smr-burnup-guide.md`

```python
from smrforge.burnup.lwr_burnup import GadoliniumDepletion, GadoliniumPoison

gd_depletion = GadoliniumDepletion(cache)
gd155 = Nuclide(Z=64, A=155)
gd157 = Nuclide(Z=64, A=157)

# Create poison configuration
gd_poison = GadoliniumPoison(
    nuclides=[gd155, gd157],
    initial_concentrations=[1e20, 1e20],  # atoms/cm³
)

# Calculate depletion over time
flux = 1e14  # n/cm²/s
time = 365 * 24 * 3600  # 1 year

final_gd155 = gd_depletion.deplete(gd155, 1e20, flux, time)
final_gd157 = gd_depletion.deplete(gd157, 1e20, flux, time)

# Calculate reactivity worth
worth = gd_depletion.calculate_reactivity_worth(gd_poison, flux, time)
print(f"Gd reactivity worth: {worth*1000:.1f} m$")
```

### Assembly-Wise Tracking

**Guide:** `docs/guides/lwr-smr-burnup-guide.md`

```python
from smrforge.burnup.lwr_burnup import AssemblyWiseBurnupTracker

tracker = AssemblyWiseBurnupTracker(n_assemblies=37)

for assembly_id in range(37):
    position = tracker.get_assembly_position(assembly_id)
    tracker.update_assembly(
        assembly_id=assembly_id,
        position=position,
        burnup=50.0,  # MWd/kgU
        enrichment=0.045,
    )

# Get distribution
distribution = tracker.get_burnup_distribution()
avg_burnup = tracker.get_average_burnup()
peak_burnup = tracker.get_peak_burnup()
```

### Rod-Wise Tracking

**Guide:** `docs/guides/lwr-smr-burnup-guide.md`

```python
from smrforge.burnup.lwr_burnup import RodWiseBurnupTracker

tracker = RodWiseBurnupTracker(assembly_size=(17, 17))

# Control rod positions
control_rods = [(8, 8), (2, 8), (14, 8), (8, 2), (8, 14)]

for rod_id in range(17 * 17):
    position = tracker.get_rod_position(rod_id)
    
    # Calculate shadowing
    shadowing = tracker.calculate_shadowing_factor(
        position, control_rods, pitch=1.26
    )
    
    tracker.update_rod(
        rod_id=rod_id,
        position=position,
        burnup=50.0 * shadowing,  # Reduced by shadowing
        enrichment=0.045,
        shadowing_factor=shadowing,
    )
```

---

## Safety Analysis

### PWR SMR Transients

**Guide:** `docs/guides/lwr-smr-transient-analysis.md`

**Steam Line Break:**
```python
from smrforge.safety.transients import (
    TransientType,
    TransientConditions,
    SteamLineBreakTransient,
)

slb = SteamLineBreakTransient(reactor_spec, core)
conditions = TransientConditions(
    initial_power=77e6,
    initial_temperature=600.0,
    initial_flow_rate=100.0,
    initial_pressure=15.5e6,
    transient_type=TransientType.STEAM_LINE_BREAK,
    trigger_time=0.0,
    t_end=3600.0,
    scram_available=True,
)

result = slb.simulate(conditions, break_area=0.01)
```

**Feedwater Line Break:**
```python
from smrforge.safety.transients import FeedwaterLineBreakTransient

fwlb = FeedwaterLineBreakTransient(reactor_spec, core)
result = fwlb.simulate(conditions, break_area=0.02)
```

**Pressurizer Transient:**
```python
from smrforge.safety.transients import PressurizerTransient

press = PressurizerTransient(reactor_spec, core)
result = press.simulate(
    conditions,
    pressure_setpoint=15.5e6,
    pressure_change_rate=1e5,
)
```

**LOCA (Small and Large Break):**
```python
from smrforge.safety.transients import LOCATransientLWR

loca = LOCATransientLWR(reactor_spec, core)

# Small break
result_sb = loca.simulate(conditions, break_area=0.05, break_type="small")

# Large break
result_lb = loca.simulate(conditions, break_area=0.5, break_type="large")
```

### BWR SMR Transients

**Guide:** `docs/guides/lwr-smr-transient-analysis.md`

**Recirculation Pump Trip:**
```python
from smrforge.safety.transients import RecirculationPumpTripTransient

rpt = RecirculationPumpTripTransient(reactor_spec, core)
result = rpt.simulate(conditions)
```

**Steam Separator Issue:**
```python
from smrforge.safety.transients import SteamSeparatorIssueTransient

ssi = SteamSeparatorIssueTransient(reactor_spec, core)
result = ssi.simulate(conditions, separator_efficiency=0.5)
```

### Integral SMR Transients

**Guide:** `docs/guides/lwr-smr-transient-analysis.md`

**Steam Generator Tube Rupture:**
```python
from smrforge.safety.transients import SteamGeneratorTubeRuptureTransient

sgt = SteamGeneratorTubeRuptureTransient(reactor_spec, core)
result = sgt.simulate(
    conditions,
    tube_rupture_count=1,
    rupture_area_per_tube=1e-4,
)
```

### Point Kinetics

**Guide:** `docs/guides/lwr-smr-transient-analysis.md`

```python
from smrforge.safety.transients import (
    PointKineticsSolver,
    PointKineticsParameters,
)

# Define parameters (6-group for LWR)
beta = np.array([0.00021, 0.00141, 0.00127, 0.00255, 0.00074, 0.00027])
lambda_d = np.array([0.0127, 0.0317, 0.115, 0.311, 1.40, 3.87])

params = PointKineticsParameters(
    beta=beta,
    lambda_d=lambda_d,
    alpha_fuel=-5e-5,  # dk/k/K
    alpha_moderator=-2e-5,
    Lambda=1e-4,  # s
    fuel_heat_capacity=1e6,  # J/K
    moderator_heat_capacity=5e5,  # J/K
)

solver = PointKineticsSolver(params)

# Define reactivity insertion
def reactivity(t):
    if t < 5.0:
        return 0.002 * (t / 5.0)  # Linear insertion
    else:
        return 0.002  # Constant

# Solve
result = solver.solve_transient(
    rho_external=reactivity,
    power_removal=lambda t, T_f, T_m: 0.9 * 77e6,
    initial_state={"power": 77e6, "T_fuel": 1200.0, "T_moderator": 900.0},
    t_span=(0.0, 100.0),
)
```

---

## Visualization

### 2D Core Layout

**File:** `examples/visualization_examples.py`

```python
from smrforge.visualization.geometry import plot_core_layout_2d

fig, ax = plt.subplots(figsize=(10, 10))
plot_core_layout_2d(core, ax=ax, show_legend=True)
plt.savefig("core_layout.png", dpi=300)
```

### 3D Ray-Traced Geometry

**File:** `examples/visualization_3d_example.py`  
**Guide:** `docs/status/openmc-visualization-gaps-analysis.md`

```python
from smrforge.visualization.advanced import plot_ray_traced_geometry

fig = plot_ray_traced_geometry(
    core,
    origin=(0, 0, 100),
    width=(300, 300, 200),
    pixels=(600, 600),
    backend='plotly',
)
fig.write_html("3d_geometry.html")
```

### Interactive Dashboard

**File:** `examples/openmc_visualization_examples.py`

```python
from smrforge.visualization.advanced import create_dashboard

dashboard = create_dashboard(
    core,
    flux=flux,
    power=power,
    views=['xy', 'xz', 'yz', '3d'],
    backend='plotly',
)
dashboard.write_html("dashboard.html")
```

### Slice Plots

```python
from smrforge.visualization.advanced import plot_slice

fig = plot_slice(
    core,
    flux=flux,
    axis='z',
    position=100.0,  # Mid-plane
    backend='matplotlib',
)
plt.savefig("flux_slice.png", dpi=300)
```

---

## Integration Examples

### Complete Safety Analysis

**Guide:** `docs/guides/lwr-smr-transient-analysis.md`

Analyze multiple design basis accidents:

```python
from smrforge.safety.transients import (
    SteamLineBreakTransient,
    FeedwaterLineBreakTransient,
    LOCATransientLWR,
)

# Run all transients
transients = {
    'SLB': SteamLineBreakTransient(reactor_spec, core),
    'FWLB': FeedwaterLineBreakTransient(reactor_spec, core),
    'SB-LOCA': LOCATransientLWR(reactor_spec, core),
}

results = {}
for name, analyzer in transients.items():
    conditions.transient_type = getattr(TransientType, name.replace('-', '_'))
    results[name] = analyzer.simulate(conditions)

# Compare results
# ... (visualization code)
```

### Integrated Burnup and Safety

**Guide:** `docs/guides/complete-workflow-examples.md`

Combine burnup analysis with safety margins:

```python
# Track safety margins over fuel cycle
for year in [0, 1, 2, 3]:
    # Update burnup
    # ... (burnup calculation)
    
    # Run safety transients
    # ... (transient analysis)
    
    # Store margins
    # ... (record results)
```

### Multi-Reactor Comparison

**Guide:** `docs/guides/complete-workflow-examples.md`

Compare different SMR designs:

```python
reactors = {
    'NuScale': {'type': 'PWR', 'power': 77e6, 'n_assemblies': 37},
    'mPower': {'type': 'PWR', 'power': 180e6, 'n_assemblies': 69},
    'Xe-100': {'type': 'HTGR', 'power': 80e6},
}

# Analyze each
for name, specs in reactors.items():
    # Create geometry
    # Run analysis
    # Store results
```

---

## Example Files Location

All example files are in the `examples/` directory:

- `complete_smr_workflow_example.py` - **NEW**: Complete end-to-end workflow
- `advanced_features_examples.py` - Advanced features showcase
- `lwr_smr_example.py` - LWR SMR specific examples
- `burnup_example.py` - Basic burnup analysis
- `visualization_examples.py` - 2D visualization
- `visualization_3d_example.py` - 3D visualization
- `openmc_visualization_examples.py` - OpenMC-inspired visualizations
- `data_downloader_example.py` - Data downloader usage

---

## Running Examples

### From Command Line

```bash
# Run specific example
python examples/complete_smr_workflow_example.py

# Run all examples
cd examples
python *.py
```

### From Python

```python
# Import and run
import sys
sys.path.insert(0, 'examples')
from complete_smr_workflow_example import *

# Or execute directly
exec(open('examples/complete_smr_workflow_example.py').read())
```

---

## Output

All examples generate output in the `output/` directory:

- PNG plots (high-resolution, 300 DPI)
- HTML files (interactive visualizations)
- JSON files (structured data)
- Text summaries (analysis reports)

---

## Best Practices

1. **Always check dependencies** - Some features require optional packages (plotly, pyvista)
2. **Use appropriate time steps** - Different analyses require different resolutions
3. **Validate inputs** - Check that parameters are physically reasonable
4. **Visualize results** - Always plot results to understand behavior
5. **Export data** - Save results for post-processing and comparison
6. **Use logging** - Enable logging for production workflows
7. **Handle errors gracefully** - Use try-except blocks for optional features

---

## Getting Help

- **Documentation:** See `docs/` directory
- **API Reference:** `docs/api_reference.rst`
- **Guides:** `docs/guides/` directory
- **Examples:** `examples/` directory
- **Issues:** GitHub Issues page

---

**See Also:**
- [Complete Workflow Examples](complete-workflow-examples.md) - Comprehensive end-to-end examples
- [LWR SMR Transient Analysis Guide](lwr-smr-transient-analysis.md) - Detailed transient examples
- [LWR SMR Burnup Guide](lwr-smr-burnup-guide.md) - Advanced burnup examples
- [Data Downloader Guide](data-downloader-guide.md) - Data management examples
