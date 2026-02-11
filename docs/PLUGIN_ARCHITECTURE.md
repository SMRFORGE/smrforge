# SMRForge Plugin and Hook Architecture

**Purpose:** Enable AI/ML surrogates, external solvers, and post-processors to plug in without modifying core code.  
**Reference:** NUCLEAR_INDUSTRY_ANALYSIS_AND_AI_FUTURE_PROOFING.md (AI future-proofing recommendation #2)

---

## Overview

The plugin registry (`smrforge.workflows.plugin_registry`) provides:

1. **Surrogate Registry** — Register custom surrogate model factories (RBF, linear, GP, custom NN, external service).
2. **Hook Registry** — Register callbacks for key events (before/after solve, keff, burnup) for logging, audit, or integration.

## Surrogate Registry

### Registration

```python
from smrforge.workflows.plugin_registry import register_surrogate, get_surrogate

def my_ml_factory(X, y, param_names=None, output_name="output", **kwargs):
    """Factory returning object with .predict(X_new)."""
    import my_ml_lib
    model = my_ml_lib.fit(X, y, **kwargs)
    return type('Surrogate', (), {'predict': model.predict})()

register_surrogate("my_ml", my_ml_factory)
```

### Usage

```python
surrogate_factory = get_surrogate("my_ml")
if surrogate_factory:
    model = surrogate_factory(X_train, y_train, output_name="k_eff")
    y_pred = model.predict(X_new)
```

### Built-in Surrogates

`fit_surrogate()` in `smrforge.workflows.surrogate` uses methods `"rbf"` and `"linear"` directly. The registry allows third-party or Pro/Enterprise surrogates (e.g., custom NN, Gaussian process) to be added without forking.

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

### Standard Hook Names (proposed)

| Hook Name      | When Called           | Context Keys           |
|----------------|-----------------------|------------------------|
| `before_solve` | Before eigenvalue solve| reactor_spec, solver   |
| `after_keff`   | After k-eff converges | k_eff, flux_shape      |
| `after_burnup` | After burnup complete | inventory, burnup_mwd  |
| `after_transient` | After transient solve | time, temperature   |

## Integration with Surrogate Workflow

The parameter sweep / DoE workflow can use the surrogate registry:

```python
surrogate_method = "rbf"  # or "my_ml" if registered
factory = get_surrogate(surrogate_method)
if factory:
    surrogate = factory(X, y, param_names=param_names, output_name="k_eff")
else:
    surrogate = fit_surrogate(X, y, method=surrogate_method)
```

## AI Audit Trail Extension

For AI-assisted runs, hooks can append to `CalculationAuditTrail`:

```python
def audit_ai_models(context, **kwargs):
    trail = context.get("audit_trail")
    if trail and hasattr(trail, "metadata"):
        trail.metadata["ai_models_used"] = [
            {"name": "my_ml", "version": "1.0", "config_hash": "abc123"}
        ]

register_hook("after_keff", audit_ai_models)
```

## References

- NUCLEAR_INDUSTRY_ANALYSIS_AND_AI_FUTURE_PROOFING.md
- smrforge/workflows/surrogate.py
- smrforge/workflows/plugin_registry.py
