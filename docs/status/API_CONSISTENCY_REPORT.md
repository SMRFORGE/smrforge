# API Consistency Report

**Date:** January 2026  
**Status:** Comprehensive API consistency analysis across SMRForge codebase

---

## Executive Summary

This report analyzes API consistency across the SMRForge codebase, identifying patterns, inconsistencies, and recommendations for improvement.

### Key Findings

✅ **Consistent Patterns:**
- Reactor creation: `create_reactor()` is the primary entry point
- Solver initialization: All solvers take required parameters first, options last
- Visualization: Plot API provides consistent interface

⚠️ **Inconsistencies Found:**
- Parameter naming: `power_mw` vs `power_thermal` (inconsistent units)
- Time units: `time_steps` (days) vs `time_steps_days` (explicit)
- Function naming: Mix of `create_*`, `get_*`, `build_*`, `make_*`
- Return types: Some functions return objects, others return dictionaries

---

## 1. Reactor Creation API

### Current Implementation

**Primary Entry Point:**
```python
smr.create_reactor(
    name: Optional[str] = None,  # Preset name OR
    power_mw: Optional[float] = None,  # Custom parameters
    core_height: Optional[float] = None,
    core_diameter: Optional[float] = None,
    enrichment: Optional[float] = None,
    **kwargs
) -> SimpleReactor
```

**Preset Access:**
```python
smr.get_preset(name: str) -> ReactorSpecification
smr.list_presets() -> List[str]
```

**Convenience Functions:**
```python
smr.quick_keff(power_mw=10.0, enrichment=0.195, ...) -> float
smr.analyze_preset(design_name: str) -> Dict
smr.compare_designs(design_names: List[str]) -> Dict[str, Dict]
```

### Issues Identified

1. **Unit Inconsistency:**
   - `create_reactor()` uses `power_mw` (megawatts)
   - `ReactorSpecification` uses `power_thermal` (watts)
   - Conversion happens internally but is not explicit

2. **Parameter Naming:**
   - CLI uses `--power` (assumes MW)
   - GUI uses `power` input (assumes MW)
   - Internal model uses `power_thermal` (watts)

### Recommendations

✅ **Keep current API** - It's well-designed and consistent:
- Clear separation between preset and custom creation
- Sensible defaults for optional parameters
- Good use of `**kwargs` for extensibility

⚠️ **Document unit conversions** - Make it clear when conversions happen

---

## 2. Solver API

### Current Implementation

**Neutronics Solver:**
```python
MultiGroupDiffusion(
    geometry,  # Required: Core geometry object
    xs_data: CrossSectionData,  # Required: Cross-section data
    options: SolverOptions  # Required: Solver options
)
```

**Burnup Solver:**
```python
BurnupSolver(
    neutronics_solver: MultiGroupDiffusion,  # Required
    options: BurnupOptions,  # Required
    cache: Optional[NuclearDataCache] = None  # Optional
)
```

**Convenience Functions:**
```python
create_simple_solver(
    core: Optional[PrismaticCore] = None,
    xs_data: Optional[CrossSectionData] = None,
    n_groups: int = 2,
    max_iterations: int = 1000,
    tolerance: float = 1e-6,
    verbose: bool = False,
    skip_validation: bool = True
) -> MultiGroupDiffusion
```

### Consistency Analysis

✅ **Consistent Pattern:**
- All solvers follow: `Required parameters first, options/config last`
- Options are passed as dataclass objects (`SolverOptions`, `BurnupOptions`)
- Optional dependencies (cache, etc.) come after required parameters

✅ **Good Design:**
- Separation of concerns: geometry, data, options
- Validation via Pydantic models
- Convenience functions provide sensible defaults

---

## 3. Visualization API

### Current Implementation

**Unified Plot API (Recommended):**
```python
# Class-based approach
plot = Plot(
    plot_type='slice',
    origin=(0, 0, 200),
    width=(300, 300, 400),
    color_by='material',
    backend='plotly',
    output_file='plot.html'
)
fig = plot.plot(geometry, data=None, field_name=None)

# Convenience function
plot = create_plot(
    plot_type='slice',
    origin=(0, 0, 200),
    width=(300, 300, 400),
    color_by='material',
    backend='plotly'
)
fig = plot.plot(geometry)
```

**Standalone Functions (Legacy):**
```python
plot_voxel(
    geometry,
    origin=(0.0, 0.0, 0.0),
    width=(200.0, 200.0, 400.0),
    pixels=(800, 600),
    color_by='material',
    data: Optional[np.ndarray] = None,
    field_name: Optional[str] = None,
    colors: Optional[Dict] = None,
    background='white',
    backend='plotly',
    **kwargs
) -> Figure
```

### Issues Identified

1. **Dual API Pattern:**
   - Class-based `Plot` API (unified, recommended)
   - Standalone function API (legacy, still supported)
   - Both are valid but can be confusing

2. **Parameter Consistency:**
   - Both APIs use same parameter names ✅
   - Both support same backends ✅
   - Default values are consistent ✅

### Recommendations

✅ **Current design is good** - Dual API provides flexibility:
- `Plot` class for programmatic/reusable plots
- Standalone functions for quick/one-off plots

📝 **Document recommended pattern** - Clearly state when to use which API

---

## 4. Workflow/Template API

### Current Implementation

**Templates:**
```python
# Create from preset
template = ReactorTemplate.from_preset(preset_name='valar-10', name=None)

# Create manually
template = ReactorTemplate(
    name='my-template',
    description='Custom template',
    base_preset='valar-10',
    parameters={...},
    metadata={...}
)

# Save/Load
template.save(file_path: Path)
template = ReactorTemplate.load(file_path: Path)
```

**Parameter Sweep:**
```python
config = SweepConfig(
    parameters={
        'enrichment': [0.10, 0.15, 0.20, 0.25],  # List of values
        'power_mw': (0.10, 0.25, 0.05)  # OR tuple: (start, end, step)
    },
    analysis_types=['keff'],
    reactor_template={'name': 'valar-10'},
    output_dir=Path('sweep_results'),
    parallel=False
)

sweep = ParameterSweep(config)
results = sweep.run()
results.save('sweep_results.json')
```

**Design Validation:**
```python
constraints = ConstraintSet(name='basic_safety')
constraints.add_constraint('k_eff', '<=', 1.20, severity='error')
constraints.add_constraint('power_density', '<=', 100.0, severity='warning')

validator = DesignValidator(constraints)
result = validator.validate(reactor)
```

### Consistency Analysis

✅ **Consistent Patterns:**
- All use dataclasses for configuration
- `save()`/`load()` methods follow same pattern
- Validation uses consistent severity levels ('error', 'warning', 'info')

✅ **Good Design:**
- Template system follows factory pattern
- Parameter sweep uses configuration object
- Validation uses constraint sets

---

## 5. Data Access API

### Current Implementation

**Nuclear Data Cache:**
```python
cache = NuclearDataCache(local_endf_dir=Path('/path/to/ENDF'))
xs_table = cache.get_cross_section_table(nuclide, library='endfb8.1')
```

**Convenience Functions:**
```python
get_fission_yield_data(cache, nuclide, library='endfb8.1')
get_cross_section_with_self_shielding(cache, nuclide, reaction, temperature, sigma_0)
get_thermal_scattering_data(cache, material, temperature, library='endfb8.1')
get_delayed_neutron_data(cache, fissile_nuclide, library='endfb8.1')
```

### Issues Identified

1. **Mixed Patterns:**
   - Cache methods: `cache.get_*()` (object methods)
   - Standalone functions: `get_*()` (module-level functions)
   - Both patterns exist side-by-side

2. **Parameter Ordering:**
   - Some functions take `cache` first: `get_fission_yield_data(cache, nuclide, ...)`
   - Others take `cache` as optional parameter: `BurnupSolver(..., cache=None)`

### Recommendations

⚠️ **Standardize on one pattern:**
- Prefer cache methods: `cache.get_cross_section_table(...)` ✅
- Keep standalone functions for backward compatibility
- Document which is preferred

---

## 6. Error Handling Patterns

### Current Implementation

**Validation Errors:**
```python
# Pydantic validation
try:
    spec = ReactorSpecification(**data)
except ValidationError as e:
    # Handle validation error
```

**Value Errors:**
```python
# Custom validation
if name not in presets:
    raise ValueError(f"Unknown preset '{name}'. Available: {list_presets()}")
```

**Import Errors:**
```python
# Optional dependencies
try:
    import plotly
    _PLOTLY_AVAILABLE = True
except ImportError:
    _PLOTLY_AVAILABLE = False
    plotly = None
```

### Consistency Analysis

✅ **Consistent Error Types:**
- `ValueError` for invalid parameters
- `ImportError` for missing dependencies
- `ValidationError` (Pydantic) for data validation
- `RuntimeError` for solver failures

✅ **Good Practices:**
- Clear error messages with suggestions
- Graceful degradation for optional dependencies

---

## 7. Time Units Inconsistency

### Current Implementation

**Burnup Options:**
```python
BurnupOptions(
    time_steps=[0, 30, 60, 90, 365],  # Days (implicit)
    power_density=1e6,  # W/cm³
    initial_enrichment=0.195
)
```

**Convenience Functions:**
```python
create_simple_burnup_solver(
    time_steps_days=[0, 365, 730],  # Explicit "days" suffix
    ...
)
```

### Issue Identified

⚠️ **Inconsistent Naming:**
- `BurnupOptions.time_steps` (implicit days)
- `create_simple_burnup_solver(time_steps_days=...)` (explicit days)

### Recommendations

✅ **Document unit clearly** - `time_steps` should have clear documentation that it's in days

💡 **Consider consistency** - Could rename to `time_steps_days` for explicitness, but this would be a breaking change

---

## 8. Function Naming Patterns

### Current Patterns

**Creation Functions:**
- `create_reactor()` ✅
- `create_plot()` ✅
- `create_simple_solver()` ✅
- `create_simple_burnup_solver()` ✅

**Access Functions:**
- `get_preset()` ✅
- `get_design()` ✅
- `list_presets()` ✅

**Building Functions:**
- `build_mesh()` ✅
- `build_hexagonal_lattice()` ✅

**Making Functions:**
- `make_plot()` - NOT FOUND ✅

### Consistency Analysis

✅ **Consistent Patterns:**
- `create_*` for factory functions
- `get_*` for retrieval functions
- `list_*` for enumeration functions
- `build_*` for construction functions

✅ **Good Convention:**
- Clear distinction between create (new instance) and get (existing resource)

---

## 9. Return Type Consistency

### Current Patterns

**Object Returns:**
```python
create_reactor(...) -> SimpleReactor
create_plot(...) -> Plot
create_simple_solver(...) -> MultiGroupDiffusion
```

**Dictionary Returns:**
```python
analyze_preset(design_name) -> Dict
compare_designs(design_names) -> Dict[str, Dict]
sweep.run() -> SweepResult  # Dataclass, not dict
```

**Value Returns:**
```python
quick_keff(...) -> float
list_presets() -> List[str]
```

### Consistency Analysis

✅ **Consistent Patterns:**
- Factory functions return objects
- Analysis functions return dictionaries
- Enumeration functions return lists
- Computation functions return values

✅ **Good Design:**
- Clear return types for different operation categories

---

## 10. Summary & Recommendations

### ✅ Strengths

1. **Consistent Solver API** - All solvers follow same pattern
2. **Clear Factory Functions** - `create_*` pattern is well-established
3. **Good Error Handling** - Appropriate exception types with clear messages
4. **Flexible Visualization** - Dual API (class-based and functional) provides options
5. **Well-Structured Workflows** - Configuration objects for complex operations

### ⚠️ Areas for Improvement

1. **Power Units:**
   - **Current:** Mix of `power_mw` (MW) and `power_thermal` (W)
   - **Recommendation:** Document conversions clearly, consider explicit parameter names

2. **Time Units:**
   - **Current:** `time_steps` (implicit days) vs `time_steps_days` (explicit)
   - **Recommendation:** Document units clearly in docstrings

3. **Data Access:**
   - **Current:** Mix of cache methods and standalone functions
   - **Recommendation:** Prefer cache methods, keep standalone for backward compatibility

4. **Visualization API:**
   - **Current:** Dual API (class-based and functional)
   - **Recommendation:** Document when to use which, both are valid

### 📝 Documentation Recommendations

1. **Add unit documentation** to all parameter docstrings
2. **Create API style guide** for new code
3. **Document preferred patterns** in developer guide
4. **Add examples** showing both APIs where dual patterns exist

### 🎯 Priority Actions

**High Priority:**
- ✅ Document unit conversions in docstrings
- ✅ Add examples for dual API patterns
- ✅ Clarify when to use cache methods vs standalone functions

**Medium Priority:**
- 📝 Consider standardizing time parameter names (breaking change)
- 📝 Create API style guide document

**Low Priority:**
- 💡 Consider explicit unit suffixes for all parameters (major refactor)

---

## Conclusion

The SMRForge API is **generally consistent** with clear patterns established for:
- Reactor creation
- Solver initialization
- Workflow configuration
- Error handling

**Main areas of inconsistency:**
- Unit handling (power, time) - mostly documentation issue
- Dual visualization API - design choice, not a bug
- Mixed data access patterns - backward compatibility consideration

**Overall Assessment:** ✅ **Good API design** with minor documentation improvements needed.

---

**Report Generated:** January 2026  
**Next Review:** After major API changes
