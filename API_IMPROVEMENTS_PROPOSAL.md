# API Improvements: Making SMRForge Easy to Use

## Overview

This document proposes high-level convenience functions, factory methods, and one-liner APIs to make SMRForge much easier to use for common tasks.

---

## Current Problems

### Current Usage (Too Many Steps)
```python
# Too many steps!
from smrforge.geometry.core_geometry import PrismaticCore
from smrforge.neutronics.solver import MultiGroupDiffusion
from smrforge.validation.models import CrossSectionData, SolverOptions

# Step 1: Create geometry
core = PrismaticCore(name="test")
core.build_hexagonal_lattice(n_rings=3, pitch=40.0, ...)

# Step 2: Create cross sections (lots of arrays!)
xs_data = CrossSectionData(
    n_groups=2, n_materials=2,
    sigma_t=np.array([[...]]),
    sigma_a=np.array([[...]]),
    # ... many more arrays
)

# Step 3: Create solver options
options = SolverOptions(max_iterations=1000, ...)

# Step 4: Create solver
solver = MultiGroupDiffusion(core, xs_data, options)

# Step 5: Solve
k_eff, flux = solver.solve_steady_state()
```

---

## Proposed Solutions

### 1. High-Level Factory Functions

#### A. Quick Reactor Creation
```python
import smrforge as smr

# One-liner: Create a reactor from preset
reactor = smr.create_reactor("valar-10")  # Uses preset design

# One-liner: Create custom reactor
reactor = smr.create_reactor(
    power_mw=10,
    core_height=200,
    core_diameter=100,
    enrichment=0.195
)

# One-liner: Load from file
reactor = smr.load_reactor("my_reactor.json")
```

#### B. Quick Analysis
```python
# One-liner: Get k-eff
k_eff = smr.solve_keff(reactor)

# One-liner: Full analysis
results = smr.analyze(reactor)  # Returns dict with k_eff, flux, power, etc.

# One-liner: Steady-state with thermal
results = smr.solve_steady_state(reactor)
```

#### C. Quick Cross-Section Generation
```python
# One-liner: Generate XS from materials
xs = smr.generate_xs(
    materials=["U235", "U238", "graphite"],
    temperature=900,
    groups=2
)

# One-liner: Use preset library XS
xs = smr.get_preset_xs("htgr-2group")
```

---

### 2. Simplified Reactor Class

Create a high-level `Reactor` class that wraps everything:

```python
class Reactor:
    """High-level reactor class - easy to use!"""
    
    def __init__(self, name: str, **kwargs):
        # Accept simple parameters, create everything internally
        self.name = name
        self.spec = self._create_spec(**kwargs)
        self.core = self._create_core()
        self.xs_data = self._generate_xs()
        
    def solve_keff(self) -> float:
        """One-liner to get k-eff"""
        solver = self._create_solver()
        k_eff, _ = solver.solve_steady_state()
        return k_eff
    
    def solve(self) -> Dict:
        """One-liner for full analysis"""
        # Returns dict with k_eff, flux, power, temperatures, etc.
        pass
```

---

### 3. Convenience Functions Module

Create `smrforge/convenience.py` with one-liners:

```python
# smrforge/convenience.py

def quick_keff(power_mw: float = 10, 
               enrichment: float = 0.195,
               **kwargs) -> float:
    """
    Quick one-liner to get k-eff for a simple reactor.
    
    Example:
        >>> k = smr.quick_keff(power_mw=10, enrichment=0.195)
        >>> print(f"k-eff = {k:.6f}")
    """
    reactor = create_simple_reactor(power_mw=power_mw, 
                                   enrichment=enrichment, 
                                   **kwargs)
    return reactor.solve_keff()

def analyze_preset(design_name: str) -> Dict:
    """
    Analyze a preset design with one line.
    
    Example:
        >>> results = smr.analyze_preset("valar-10")
        >>> print(f"k-eff: {results['k_eff']:.6f}")
    """
    pass

def compare_designs(designs: List[str]) -> pd.DataFrame:
    """
    Compare multiple designs side-by-side.
    
    Example:
        >>> df = smr.compare_designs(["valar-10", "htgr-50", "mhr-600"])
        >>> print(df)
    """
    pass
```

---

### 4. Context Managers for Workflows

```python
# Easy workflow management
with smr.ReactorAnalysis(reactor) as analysis:
    analysis.solve_neutronics()
    analysis.solve_thermal()
    results = analysis.get_results()
```

---

### 5. Simplified Preset Access

```python
# Easy preset access
from smrforge.presets import valar10, htgr50

reactor = valar10()  # One-liner to get preset
results = valar10().analyze()  # One-liner to analyze preset
```

---

## Proposed Implementation

Let me create the actual convenience module:

