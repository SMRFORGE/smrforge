# SMRForge Easy Usage Summary

## Quick Reference Card

### One-Liners

```python
import smrforge as smr

# Get k-eff (simplest!)
k = smr.quick_keff()

# Analyze preset design
results = smr.analyze_preset("valar-10")

# Create and solve custom reactor
reactor = smr.create_reactor(power_mw=10, enrichment=0.195)
results = reactor.solve()
```

### Available Functions

| Function | Purpose | Returns |
|----------|---------|---------|
| `quick_keff(...)` | Quick k-eff calculation | `float` |
| `create_reactor(name)` | Create reactor from preset | `SimpleReactor` |
| `create_reactor(**kwargs)` | Create custom reactor | `SimpleReactor` |
| `analyze_preset(name)` | Full analysis of preset | `Dict` |
| `list_presets()` | List available presets | `List[str]` |
| `compare_designs(names)` | Compare multiple designs | `Dict[str, Dict]` |

### SimpleReactor Methods

| Method | Purpose | Returns |
|--------|---------|---------|
| `solve_keff()` | Get k-eff only | `float` |
| `solve()` | Full analysis | `Dict` |
| `save(filepath)` | Save to JSON | None |
| `load(filepath)` | Load from JSON | `SimpleReactor` |

### Preset Designs

- `"valar-10"` - Valar Atomics 10 MWth micro-reactor
- `"gt-mhr-350"` - GT-MHR 350 MWth
- `"htr-pm-200"` - HTR-PM 200 MWth
- `"micro-htgr-1"` - Micro HTGR 1 MWth

---

## Examples

See `EASY_USAGE_EXAMPLES.md` for complete examples.

