# SMRForge Plugin and Hook Architecture

**Purpose:** Enable external solvers and post-processors to plug in via hooks.  
**AI/surrogate features:** Pro tier only. See `docs/community_vs_pro.md`.

---

## Overview

The plugin registry (`smrforge.workflows.plugin_registry`) provides:

1. **Hook Registry** — Register callbacks for key events (before/after solve, keff, burnup) for logging, audit, or integration. Available in Community.
2. **Surrogate Registry** — Pro tier only. `register_surrogate`, `get_surrogate`, `list_surrogates`, `fit_surrogate` require SMRForge Pro.

## Hook Registry

### Registration

```python
from smrforge.workflows.plugin_registry import register_hook, run_hooks

def before_solve_callback(context, **kwargs):
    print("Starting solve", context)

register_hook("before_solve", before_solve_callback)
```

### Invocation (in core code)

```python
from smrforge.workflows.plugin_registry import run_hooks

run_hooks("before_solve", context={"reactor_spec": spec, "solver": "diffusion"})
# ... run solver ...
run_hooks("after_keff", context={"k_eff": k_eff, "flux_shape": flux.shape})
```

### Standard Hook Names

| Hook Name        | When Called              | Context Keys                    |
|------------------|--------------------------|---------------------------------|
| `before_solve`   | Before eigenvalue solve   | reactor_spec, solver            |
| `after_keff`    | After k-eff converges    | k_eff, flux_shape               |
| `after_burnup`  | After burnup complete     | inventory, burnup_mwd           |
| `after_transient` | After transient solve  | time, temperature               |
| `pre_export`    | Before Serpent/MCNP export | format, reactor, output_file  |
| `post_sweep`    | After parameter sweep    | result, config                  |

## Pro Tier: Surrogate Registry and AI Audit

Surrogate registry (`register_surrogate`, `get_surrogate`, `list_surrogates`), `fit_surrogate()`, `export_ml_dataset()`, and `record_ai_model()` are Pro tier only. Use SMRForge Pro for AI/ML workflows.

## References

- docs/community_vs_pro.md
- smrforge/workflows/plugin_registry.py (hooks)
