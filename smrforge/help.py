"""
Interactive help system for SMRForge.

Provides comprehensive help and documentation for functions, classes, and features.
"""

from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from rich.console import Console

try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.table import Table
    from rich import box

    _RICH_AVAILABLE = True
except ImportError:
    _RICH_AVAILABLE = False
    Console = Any  # type: ignore

# Import core modules for introspection (lazy import to avoid circular dependencies)
_CORE_AVAILABLE: Optional[bool] = None
_smr_module: Optional[Any] = None


def _get_smr_module() -> Optional[Any]:
    """
    Lazy import of smrforge module.
    
    Performs lazy import of the smrforge module to avoid circular dependencies.
    The import is cached after the first call.
    
    Returns:
        The smrforge module if available, None otherwise.
    """
    global _CORE_AVAILABLE, _smr_module
    if _CORE_AVAILABLE is None:
        try:
            import smrforge as smr
            _smr_module = smr
            _CORE_AVAILABLE = True
        except ImportError:
            _CORE_AVAILABLE = False
            _smr_module = None
    return _smr_module


def _is_core_available() -> bool:
    """
    Check if core modules are available.
    
    Returns:
        True if smrforge core modules can be imported, False otherwise.
    """
    _get_smr_module()
    return _CORE_AVAILABLE is True


def help(
    topic: Optional[Union[str, Any]] = None,
    category: Optional[str] = None,
    show_examples: bool = True,
) -> None:
    """
    Interactive help system for SMRForge.
    
    Provides comprehensive help for functions, classes, features, and workflows.
    
    Args:
        topic: Topic to get help on. Can be:
            - Function/class name (string)
            - Function/class object
            - Category name (e.g., "geometry", "neutronics", "burnup")
            - None (shows main help menu)
        category: Optional category filter
        show_examples: Whether to show usage examples
    
    Examples:
        >>> import smrforge as smr
        >>> smr.help()  # Show main help menu
        >>> smr.help("create_reactor")  # Help on specific function
        >>> smr.help("geometry")  # Help on geometry category
        >>> smr.help(create_reactor)  # Help on function object
    """
    if not _RICH_AVAILABLE:
        _print_help_plain(topic, category, show_examples)
        return
    
    console = Console()
    
    if topic is None:
        _show_main_menu(console)
    elif isinstance(topic, str):
        _show_topic_help(console, topic, show_examples)
    else:
        # Try to get help on the object
        _show_object_help(console, topic, show_examples)


def _show_main_menu(console: "Console") -> None:
    """Show main help menu."""
    console.print("\n[bold cyan]SMRForge Help System[/bold cyan]\n")
    
    # Categories table
    table = Table(title="Available Help Categories", box=box.ROUNDED)
    table.add_column("Category", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")
    table.add_column("Example", style="dim")
    
    categories = [
        ("geometry", "Geometry creation and manipulation", "smr.help('geometry')"),
        ("neutronics", "Neutronics solvers and calculations", "smr.help('neutronics')"),
        ("burnup", "Burnup and depletion calculations", "smr.help('burnup')"),
        ("thermal", "Thermal-hydraulics analysis", "smr.help('thermal')"),
        ("decay", "Decay heat calculations", "smr.help('decay')"),
        ("gamma", "Gamma transport and shielding", "smr.help('gamma')"),
        ("visualization", "3D visualization and plotting", "smr.help('visualization')"),
        ("materials", "Material database and properties", "smr.help('materials')"),
        ("nuclides", "Nuclide operations", "smr.help('nuclides')"),
        ("convenience", "Convenience functions and shortcuts", "smr.help('convenience')"),
        ("presets", "Preset reactor designs", "smr.help('presets')"),
    ]
    
    for cat, desc, example in categories:
        table.add_row(cat, desc, example)
    
    console.print(table)
    
    # Quick start
    console.print("\n[bold]Quick Start:[/bold]")
    console.print("  [cyan]smr.help('create_reactor')[/cyan] - Get help on creating reactors")
    console.print("  [cyan]smr.help('quick_keff')[/cyan] - Get help on quick k-eff calculation")
    console.print("  [cyan]smr.help('geometry')[/cyan] - Get help on geometry features")
    
    # Common functions
    console.print("\n[bold]Common Functions:[/bold]")
    common_funcs = [
        "create_reactor",
        "create_simple_core",
        "create_simple_solver",
        "quick_keff",
        "quick_keff_calculation",
        "get_nuclide",
        "get_material",
        "list_presets",
        "list_materials",
    ]
    
    for func in common_funcs:
        console.print(f"  [cyan]smr.help('{func}')[/cyan]")


def _show_topic_help(console: "Console", topic: str, show_examples: bool) -> None:
    """Show help for a specific topic."""
    topic_lower = topic.lower()
    
    # Category help
    if topic_lower in ["geometry", "neutronics", "burnup", "thermal", "decay", "gamma", 
                       "visualization", "materials", "nuclides", "convenience", "presets"]:
        _show_category_help(console, topic_lower, show_examples)
        return
    
    # Function/class help
    smr = _get_smr_module()
    if smr is not None:
        # Try to find the function/class
        if hasattr(smr, topic):
            obj = getattr(smr, topic)
            _show_object_help(console, obj, show_examples)
            return
    
    # Built-in help topics
    help_topics = {
        "getting_started": _help_getting_started,
        "examples": _help_examples,
        "workflows": _help_workflows,
        "troubleshooting": _help_troubleshooting,
    }
    
    if topic_lower in help_topics:
        help_topics[topic_lower](console, show_examples)
    else:
        console.print(f"[yellow]No help found for '{topic}'[/yellow]")
        console.print("\nTry:")
        console.print("  [cyan]smr.help()[/cyan] - Show main menu")
        console.print("  [cyan]smr.help('geometry')[/cyan] - Show geometry help")


def _show_category_help(console: "Console", category: str, show_examples: bool) -> None:
    """Show help for a category."""
    category_help = {
        "geometry": _help_geometry,
        "neutronics": _help_neutronics,
        "burnup": _help_burnup,
        "thermal": _help_thermal,
        "decay": _help_decay,
        "gamma": _help_gamma,
        "visualization": _help_visualization,
        "materials": _help_materials,
        "nuclides": _help_nuclides,
        "convenience": _help_convenience,
        "presets": _help_presets,
    }
    
    if category in category_help:
        category_help[category](console, show_examples)
    else:
        console.print(f"[yellow]No help available for category '{category}'[/yellow]")


def _show_object_help(console: Any, obj: Any, show_examples: bool) -> None:
    """Show help for a function or class object."""
    import inspect
    
    obj_name = obj.__name__ if hasattr(obj, "__name__") else str(obj)
    
    # Get docstring
    doc = inspect.getdoc(obj)
    if doc:
        # Format docstring nicely
        console.print(Panel(Markdown(doc), title=obj_name, border_style="cyan"))
    else:
        console.print(f"[yellow]No documentation available for {obj_name}[/yellow]")
    
    # Get signature
    try:
        sig = inspect.signature(obj)
        console.print(f"\n[bold]Signature:[/bold]")
        console.print(f"  [cyan]{obj_name}{sig}[/cyan]")
        
        # Show parameter details
        params = sig.parameters
        if params:
            console.print(f"\n[bold]Parameters:[/bold]")
            for param_name, param in params.items():
                param_info = f"  [cyan]{param_name}[/cyan]"
                if param.annotation != inspect.Parameter.empty:
                    # Handle built-in types directly
                    if param.annotation in (str, int, float, bool, list, dict, tuple, set):
                        ann = param.annotation.__name__
                    else:
                        ann = str(param.annotation)
                        # Simplify type hints - only for complex types
                        if "." in ann or "<" in ann:
                            import re
                            # Replace typing. and smrforge. module prefixes
                            ann = re.sub(r"typing\.", "", ann)
                            # Only replace smrforge. if it's a full module path
                            ann = re.sub(r"smrforge\.core\.reactor_core\.", "core.", ann)
                            ann = re.sub(r"smrforge\.geometry\.", "geometry.", ann)
                            ann = re.sub(r"smrforge\.", "", ann)
                            # Remove <class '...'> wrapper
                            if ann.startswith("<class '") and ann.endswith("'>"):
                                ann = ann[9:-2]
                    param_info += f" [dim]: {ann}[/dim]"
                if param.default != inspect.Parameter.empty:
                    default_val = repr(param.default)
                    if len(default_val) > 30:
                        default_val = default_val[:27] + "..."
                    param_info += f" [dim]= {default_val}[/dim]"
                console.print(param_info)
    except (ValueError, TypeError):
        pass
    
    # Show return type if available
    try:
        sig = inspect.signature(obj)
        if sig.return_annotation != inspect.Signature.empty:
            ret_ann = str(sig.return_annotation)
            # Simplify type hints - only for complex types
            # Simple types (str, int, float, etc.) are left as-is
            if "." in ret_ann or "<" in ret_ann:
                import re
                # Remove <class '...'> wrapper first
                if ret_ann.startswith("<class '") and ret_ann.endswith("'>"):
                    ret_ann = ret_ann[9:-2]
                # Replace typing. and smrforge. module prefixes
                ret_ann = re.sub(r"typing\.", "", ret_ann)
                # Replace specific smrforge module paths
                ret_ann = re.sub(r"smrforge\.core\.reactor_core\.", "core.", ret_ann)
                ret_ann = re.sub(r"smrforge\.geometry\.core_geometry\.", "geometry.", ret_ann)
                ret_ann = re.sub(r"smrforge\.geometry\.", "geometry.", ret_ann)
                # Replace smrforge.module.Class with module.Class
                ret_ann = re.sub(r"smrforge\.([a-z_]+)\.([A-Z][a-zA-Z0-9_]*)", r"\1.\2", ret_ann)
                # Remove remaining smrforge. prefix
                ret_ann = re.sub(r"^smrforge\.", "", ret_ann)
            console.print(f"\n[bold]Returns:[/bold] [cyan]{ret_ann}[/cyan]")
    except (ValueError, TypeError):
        pass
    
    # Show examples if available
    if show_examples:
        _show_examples_for_object(console, obj)


def _show_examples_for_object(console: Any, obj: Any) -> None:
    """Show examples for an object."""
    examples = _get_examples()
    obj_name = obj.__name__ if hasattr(obj, "__name__") else str(obj)
    
    if obj_name in examples:
        console.print("\n[bold]Examples:[/bold]")
        for example in examples[obj_name]:
            console.print(f"  [dim]# {example['description']}[/dim]")
            console.print(f"  [green]{example['code']}[/green]\n")


def _help_getting_started(console: "Console", show_examples: bool) -> None:
    """Help for getting started."""
    console.print(Panel(
        Markdown("""
# Getting Started with SMRForge

## Quick Start

1. **Install SMRForge:**
   ```bash
   pip install smrforge
   ```

2. **Create your first reactor:**
   ```python
   import smrforge as smr
   reactor = smr.create_reactor("valar-10")
   k_eff = reactor.solve_keff()
   print(f"k-eff = {k_eff:.6f}")
   ```

3. **Quick k-eff calculation:**
   ```python
   k_eff = smr.quick_keff(power_mw=10, enrichment=0.195)
   ```

## Next Steps

- Run `smr.help('examples')` to see more examples
- Run `smr.help('workflows')` to see common workflows
- Check out the examples/ directory for complete examples
        """),
        title="Getting Started",
        border_style="green"
    ))


def _help_examples(console: "Console", show_examples: bool) -> None:
    """Help for examples."""
    console.print(Panel(
        Markdown("""
# SMRForge Examples

## Basic Examples

### 1. Quick k-eff Calculation
```python
import smrforge as smr
k_eff = smr.quick_keff(power_mw=10, enrichment=0.195)
```

### 2. Create and Solve Reactor
```python
reactor = smr.create_reactor("valar-10")
results = reactor.solve()
print(f"k-eff: {results['k_eff']:.6f}")
```

### 3. Custom Reactor
```python
reactor = smr.create_reactor(
    power_mw=10,
    core_height=200,
    core_diameter=100,
    enrichment=0.195
)
k_eff = reactor.solve_keff()
```

## Complete Examples

See the `examples/` directory for:
- `basic_neutronics.py` - Basic neutronics calculation
- `burnup_example.py` - Burnup calculation
- `decay_heat_example.py` - Decay heat analysis
- `gamma_transport_example.py` - Gamma transport
- `mesh_3d_example.py` - 3D mesh extraction
- `visualization_3d_example.py` - 3D visualization
        """),
        title="Examples",
        border_style="blue"
    ))


def _help_workflows(console: "Console", show_examples: bool) -> None:
    """Help for common workflows."""
    console.print(Panel(
        Markdown("""
# Common Workflows

## 1. Reactor Analysis Workflow

```python
import smrforge as smr

# Create reactor
reactor = smr.create_reactor("valar-10")

# Solve for k-eff
k_eff = reactor.solve_keff()

# Full analysis
results = reactor.solve()
print(f"k-eff: {results['k_eff']:.6f}")
print(f"Peak flux: {results['peak_flux']:.2e}")
```

## 2. Burnup Calculation Workflow

```python
from smrforge.burnup import BurnupSolver, BurnupOptions
from smrforge.core.reactor_core import Nuclide

# Create solver
burnup = smr.create_simple_burnup_solver(
    time_steps_days=[0, 365, 730],
    power_density=1e6
)

# Solve
inventory = burnup.solve()
```

## 3. Visualization Workflow

```python
from smrforge import create_simple_core, quick_mesh_extraction, quick_plot_mesh

# Create core and extract mesh
core = create_simple_core()
mesh = quick_mesh_extraction(core, mesh_type="volume")

# Visualize
quick_plot_mesh(mesh, color_by="material")
```
        """),
        title="Common Workflows",
        border_style="magenta"
    ))


def _help_geometry(console: "Console", show_examples: bool) -> None:
    """Help for geometry features."""
    console.print(Panel(
        Markdown("""
# Geometry Features

## Core Classes

- **PrismaticCore**: Prismatic block HTGR core
- **PebbleBedCore**: Pebble bed HTGR core
- **Mesh3D**: 3D mesh representation

## Key Functions

- `create_simple_core()` - Quick core creation
- `extract_core_volume_mesh()` - Extract 3D volume mesh
- `extract_core_surface_mesh()` - Extract surface mesh
- `extract_material_boundaries()` - Extract material boundaries

## Examples

```python
from smrforge import create_simple_core, quick_mesh_extraction

# Create core
core = create_simple_core(n_rings=3, pitch=40.0)

# Extract mesh
mesh = quick_mesh_extraction(core, mesh_type="volume")
```
        """),
        title="Geometry",
        border_style="cyan"
    ))


def _help_neutronics(console: "Console", show_examples: bool) -> None:
    """Help for neutronics features."""
    console.print(Panel(
        Markdown("""
# Neutronics Features

## Core Classes

- **MultiGroupDiffusion**: Multi-group diffusion solver
- **CrossSectionData**: Cross-section data container

## Key Functions

- `create_simple_solver()` - Quick solver creation
- `create_simple_xs_data()` - Quick cross-section creation
- `quick_keff_calculation()` - Quick k-eff calculation

## Examples

```python
from smrforge import create_simple_solver, quick_keff_calculation

# Quick k-eff
k_eff, flux = quick_keff_calculation()

# Create solver
solver = create_simple_solver()
k_eff, flux = solver.solve_steady_state()
```
        """),
        title="Neutronics",
        border_style="blue"
    ))


def _help_burnup(console: "Console", show_examples: bool) -> None:
    """Help for burnup features."""
    console.print(Panel(
        Markdown("""
# Burnup Features

## Core Classes

- **BurnupSolver**: Burnup/depletion solver
- **BurnupOptions**: Burnup configuration
- **NuclideInventory**: Nuclide concentration tracking

## Key Functions

- `create_simple_burnup_solver()` - Quick burnup solver creation
- `quick_burnup_calculation()` - Quick burnup calculation

## Examples

```python
from smrforge import create_simple_burnup_solver

# Create solver
burnup = create_simple_burnup_solver(
    time_steps_days=[0, 365, 730],
    power_density=1e6
)

# Solve
inventory = burnup.solve()
```
        """),
        title="Burnup",
        border_style="yellow"
    ))


def _help_thermal(console: "Console", show_examples: bool) -> None:
    """Help for thermal features."""
    console.print(Panel(
        Markdown("""
# Thermal-Hydraulics Features

## Core Classes

- **ChannelThermalHydraulics**: Channel thermal-hydraulics solver
- **ChannelGeometry**: Channel geometry definition
- **FluidProperties**: Fluid property calculations

## Examples

```python
from smrforge.thermal import ChannelThermalHydraulics, ChannelGeometry

# Create geometry
geometry = ChannelGeometry(radius=0.5, length=200)

# Create solver
thermal = ChannelThermalHydraulics(geometry)
```
        """),
        title="Thermal-Hydraulics",
        border_style="red"
    ))


def _help_decay(console: "Console", show_examples: bool) -> None:
    """Help for decay heat features."""
    console.print(Panel(
        Markdown("""
# Decay Heat Features

## Core Classes

- **DecayHeatCalculator**: Decay heat calculator
- **DecayHeatResult**: Decay heat results

## Key Functions

- `quick_decay_heat()` - Quick decay heat calculation

## Examples

```python
from smrforge import quick_decay_heat

# Calculate decay heat
heat = quick_decay_heat(
    {"U235": 1e20, "Cs137": 1e19},
    time_seconds=86400.0
)
```
        """),
        title="Decay Heat",
        border_style="green"
    ))


def _help_gamma(console: "Console", show_examples: bool) -> None:
    """Help for gamma transport features."""
    console.print(Panel(
        Markdown("""
# Gamma Transport Features

## Core Classes

- **GammaTransportSolver**: Gamma transport solver
- **GammaTransportOptions**: Solver options

## Examples

```python
from smrforge.gamma_transport import GammaTransportSolver, GammaTransportOptions

# Create solver
options = GammaTransportOptions(n_groups=20)
solver = GammaTransportSolver(geometry, options)

# Solve
flux = solver.solve(source)
```
        """),
        title="Gamma Transport",
        border_style="magenta"
    ))


def _help_visualization(console: "Console", show_examples: bool) -> None:
    """Help for visualization features."""
    console.print(Panel(
        Markdown("""
# Visualization Features

## Key Functions

- `quick_plot_core()` - Quick core layout plot
- `quick_plot_mesh()` - Quick 3D mesh plot
- `plot_mesh3d_plotly()` - Plotly 3D visualization
- `plot_mesh3d_pyvista()` - PyVista 3D visualization
- `export_mesh_to_vtk()` - Export to VTK format

## Examples

```python
from smrforge import quick_plot_core, quick_plot_mesh

# Plot core layout
quick_plot_core(core, view="xy")

# Plot 3D mesh
mesh = quick_mesh_extraction(core)
quick_plot_mesh(mesh, color_by="material")
```

## Installation

For 3D visualization, install:
```bash
pip install smrforge[viz]
```
        """),
        title="Visualization",
        border_style="cyan"
    ))


def _help_materials(console: "Console", show_examples: bool) -> None:
    """Help for material features."""
    console.print(Panel(
        Markdown("""
# Material Features

## Key Functions

- `get_material(name)` - Get material from database
- `list_materials(category)` - List available materials

## Available Materials

- Graphite: `graphite_IG-110`, `graphite_H-451`, `graphite_NBG-18`
- Coolant: `helium`
- Fuel: `triso_uco`, `triso_uo2`
- Structural: `b4c`, `alloy_800h`

## Examples

```python
from smrforge import get_material, list_materials

# Get material
graphite = get_material("graphite_IG-110")
k = graphite.thermal_conductivity(1200.0)

# List materials
materials = list_materials()
moderators = list_materials(category="moderator")
```
        """),
        title="Materials",
        border_style="yellow"
    ))


def _help_nuclides(console: "Console", show_examples: bool) -> None:
    """Help for nuclide features."""
    console.print(Panel(
        Markdown("""
# Nuclide Features

## Key Functions

- `get_nuclide(name)` - Get Nuclide from name string
- `create_nuclide_list(names)` - Create list of Nuclides

## Examples

```python
from smrforge import get_nuclide, create_nuclide_list

# Single nuclide
u235 = get_nuclide("U235")
print(u235.zam)  # 922350

# Multiple nuclides
nuclides = create_nuclide_list(["U235", "U238", "Pu239"])
```
        """),
        title="Nuclides",
        border_style="blue"
    ))


def _help_convenience(console: "Console", show_examples: bool) -> None:
    """Help for convenience functions."""
    console.print(Panel(
        Markdown("""
# Convenience Functions

## Quick Creation Functions

- `create_simple_core()` - Quick core creation with defaults
- `create_simple_solver()` - Quick neutronics solver setup
- `create_simple_xs_data()` - Quick cross-section data creation
- `create_simple_burnup_solver()` - Quick burnup solver setup
- `create_nuclide_list()` - Create list of Nuclide objects

## Quick Calculation Functions

- `quick_keff()` - Quick k-eff calculation (from convenience module)
- `quick_keff_calculation()` - Quick k-eff with flux return
- `quick_burnup_calculation()` - Quick burnup calculation
- `quick_decay_heat()` - Quick decay heat calculation

## Material and Nuclide Functions

- `get_nuclide(name)` - Get Nuclide from name string
- `get_material(name)` - Get material from database
- `list_materials(category)` - List available materials

## Visualization Functions

- `quick_mesh_extraction()` - Extract 3D mesh from core
- `quick_plot_core()` - Quick 2D core layout plot
- `quick_plot_mesh()` - Quick 3D mesh visualization

## Complete Workflow

- `run_complete_analysis()` - Complete reactor analysis workflow

## Examples

```python
from smrforge import (
    create_simple_core,
    create_simple_solver,
    quick_keff_calculation,
    get_nuclide,
    get_material,
    quick_mesh_extraction,
    run_complete_analysis
)

# Create core
core = create_simple_core(n_rings=3, pitch=40.0)

# Quick k-eff
k_eff, flux = quick_keff_calculation()

# Get nuclide and material
u235 = get_nuclide("U235")
graphite = get_material("graphite_IG-110")

# Extract mesh
mesh = quick_mesh_extraction(core, mesh_type="volume")

# Complete analysis
results = run_complete_analysis(power_mw=10.0)
```
        """),
        title="Convenience Functions",
        border_style="green"
    ))


def _help_presets(console: "Console", show_examples: bool) -> None:
    """Help for preset designs."""
    console.print(Panel(
        Markdown("""
# Preset Reactor Designs

## Available Presets

- `valar-10` - Valar Atomics 10 MWth micro-reactor
- `gt-mhr-350` - GT-MHR 350 MWth
- `htr-pm-200` - HTR-PM 200 MWth
- `micro-htgr-1` - Micro HTGR 1 MWth

## Functions

- `list_presets()` - List all available presets
- `get_preset(name)` - Get preset specification
- `create_reactor(name)` - Create reactor from preset
- `analyze_preset(name)` - Analyze a preset design
- `compare_designs(names)` - Compare multiple preset designs

## Examples

```python
from smrforge import list_presets, create_reactor, get_preset

# List presets
presets = list_presets()
print(presets)  # ['valar-10', 'gt-mhr-350', ...]

# Get preset details
spec = get_preset("valar-10")
print(f"Power: {spec.power_thermal/1e6:.1f} MWth")

# Create from preset
reactor = create_reactor("valar-10")
results = reactor.solve()
print(f"k-eff: {results['k_eff']:.6f}")
```
        """),
        title="Preset Designs",
        border_style="cyan"
    ))


def _help_troubleshooting(console: "Console", show_examples: bool) -> None:
    """Help for troubleshooting."""
    console.print(Panel(
        Markdown("""
# Troubleshooting

## Common Issues

### Import Errors
- Ensure all dependencies are installed: `pip install smrforge`
- For visualization: `pip install smrforge[viz]`

### ENDF File Errors
- ENDF files must be set up manually
- Run: `python -m smrforge.core.endf_setup`

### Validation Errors
- Some solvers may produce warnings for approximate cross-sections
- Use `skip_validation=True` in solver options if needed

### Performance Issues
- Use convenience functions for faster setup
- Consider using preset designs for quick testing

## Getting More Help

- Check examples in `examples/` directory
- Review documentation files
- Run `smr.help('topic')` for specific help
        """),
        title="Troubleshooting",
        border_style="red"
    ))


def _print_help_plain(
    topic: Optional[Union[str, Any]], 
    category: Optional[str], 
    show_examples: bool
) -> None:
    """Print help without rich formatting."""
    print("\nSMRForge Help System\n")
    print("Usage: smr.help('topic')")
    print("\nAvailable topics:")
    print("  - geometry, neutronics, burnup, thermal, decay, gamma")
    print("  - visualization, materials, nuclides, convenience, presets")
    print("  - getting_started, examples, workflows, troubleshooting")
    print("\nOr get help on specific functions:")
    print("  - smr.help('create_reactor')")
    print("  - smr.help('quick_keff')")
    print("  - smr.help('get_nuclide')")


def _format_docstring(doc: str) -> str:
    """
    Format docstring for better markdown display.
    
    Processes a docstring to ensure proper markdown formatting, particularly
    for Python code examples that should be in code blocks.
    
    Args:
        doc: Raw docstring text.
    
    Returns:
        Formatted docstring with proper markdown code block formatting.
    """
    # Split into sections if needed
    lines = doc.split("\n")
    formatted = []
    in_code_block = False
    
    for line in lines:
        # Detect code blocks
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            formatted.append(line)
        elif in_code_block:
            formatted.append(line)
        elif line.strip().startswith(">>>"):
            # Python examples - ensure they're in code blocks
            if not in_code_block:
                formatted.append("```python")
                in_code_block = True
            formatted.append(line)
        elif in_code_block and not line.strip():
            # End code block on empty line after code
            formatted.append("```")
            formatted.append(line)
            in_code_block = False
        else:
            formatted.append(line)
    
    if in_code_block:
        formatted.append("```")
    
    return "\n".join(formatted)


def _get_examples() -> Dict[str, List[Dict[str, str]]]:
    """
    Get examples for various objects.
    
    Returns a dictionary mapping object names to lists of example dictionaries.
    Each example dictionary contains 'description' and 'code' keys.
    
    Returns:
        Dictionary mapping object names to their example code snippets.
    """
    return {
        "create_reactor": [
            {
                "description": "Create reactor from preset",
                "code": "reactor = smr.create_reactor('valar-10')",
            },
            {
                "description": "Create custom reactor",
                "code": "reactor = smr.create_reactor(power_mw=10, enrichment=0.195)",
            },
        ],
        "quick_keff": [
            {
                "description": "Quick k-eff calculation",
                "code": "k_eff = smr.quick_keff(power_mw=10, enrichment=0.195)",
            },
        ],
        "quick_keff_calculation": [
            {
                "description": "Quick k-eff with flux",
                "code": "k_eff, flux = smr.quick_keff_calculation()",
            },
        ],
        "get_nuclide": [
            {
                "description": "Get nuclide from name",
                "code": "u235 = smr.get_nuclide('U235')",
            },
        ],
        "get_material": [
            {
                "description": "Get material from database",
                "code": "graphite = smr.get_material('graphite_IG-110')",
            },
        ],
        "create_simple_core": [
            {
                "description": "Create simple core",
                "code": "core = smr.create_simple_core(n_rings=3, pitch=40.0)",
            },
        ],
        "create_simple_solver": [
            {
                "description": "Create simple solver",
                "code": "solver = smr.create_simple_solver(core=core)",
            },
        ],
    }


# Make help available as a module-level function
__all__ = ["help"]

