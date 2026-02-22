# SMRForge AI Features

**Purpose:** Document AI/ML surrogate capabilities, BYOS (Bring Your Own Surrogate), audit trail integration, and validation reporting.  
**Reference:** NUCLEAR_INDUSTRY_ANALYSIS_AND_AI_FUTURE_PROOFING.md § 3.5

---

## Overview

SMRForge supports AI-assisted reactor analysis with:

- **Offline-first, zero telemetry** — All AI features run locally; no cloud calls
- **Deterministic** — Use `--seed` for reproducible runs
- **Audit trail** — Every surrogate use recorded in `CalculationAuditTrail.ai_models_used`
- **Bring Your Own Surrogate (BYOS)** — Drop in ONNX, TorchScript, or pickle models

---

## Surrogate Models

### Built-in Methods

| Method   | Description           | Dependencies  |
|----------|-----------------------|---------------|
| `rbf`    | Radial basis function | scipy         |
| `linear` | Linear regression     | numpy         |

### BYOS: Load from File

```python
from smrforge.ai import load_surrogate_from_path

# Load ONNX, TorchScript (.pt/.pth), or pickle (.pkl)
sur = load_surrogate_from_path(
    "keff_predictor.onnx",
    param_names=["enrichment", "power"],
    output_name="k_eff"
)
pred = sur.predict([[0.20, 50.0]])
```

Supported formats:

| Format     | Extension  | Extra dependency      |
|------------|------------|------------------------|
| ONNX       | `.onnx`    | `pip install smrforge[ai]` |
| TorchScript| `.pt`, `.pth` | PyTorch            |
| Pickle     | `.pkl`     | None                   |

### Register Path for Use with fit_surrogate

```python
from smrforge.ai import register_surrogate_from_path

# Register ONNX model; then use method="my_model"
register_surrogate_from_path("my_model", Path("keff.onnx"))
sur = fit_surrogate(X, y, method="my_model")
```

---

## Audit Trail Integration

When using surrogates, pass `audit_trail` to record usage:

```python
from smrforge.validation.regulatory_traceability import create_audit_trail
from smrforge.workflows.surrogate import fit_surrogate

trail = create_audit_trail("keff", inputs={}, outputs={})
sur = fit_surrogate(X, y, method="rbf", audit_trail=trail)

# trail.ai_models_used now contains [{"name": "rbf", ...}]
trail.save("audit_trails/keff_001.json")
```

Or use the convenience function:

```python
from smrforge.api import fit_surrogate_with_audit

sur = fit_surrogate_with_audit(X, y, audit_trail=trail, method="rbf", seed=42)
```

---

## Parameter Sweep with Surrogate

Run fast sweeps using a pre-fitted surrogate instead of physics:

```bash
# Fit surrogate from prior sweep
smrforge workflow surrogate --sweep-results sweep_results.json \
    --params enrichment power --metric k_eff --method rbf \
    --output surrogate.pkl --seed 42

# Run sweep using surrogate (no physics)
smrforge sweep --params enrichment:0.10:0.25:0.05 power:50,75,100 \
    --surrogate surrogate.pkl --surrogate-metric k_eff \
    --seed 42 --output fast_sweep/
```

```python
from smrforge.workflows import ParameterSweep, SweepConfig

config = SweepConfig(
    parameters={"x": (0.0, 1.0, 0.1)},
    analysis_types=["keff"],
    surrogate_path=Path("surrogate.pkl"),
    surrogate_output_metric="k_eff",
    seed=42,
)
sweep = ParameterSweep(config)
results = sweep.run()
```

---

## Validation Report

Compare surrogate predictions against reference physics runs:

```python
from smrforge.ai import generate_validation_report

pred = [1.001, 0.999, 1.002]  # Surrogate predictions
ref = [1.0, 1.0, 1.0]         # Physics reference

report = generate_validation_report(
    pred, ref,
    surrogate_name="keff_rbf",
    surrogate_hash="abc123",
    param_names=["enrichment"],
    output_metric="k_eff",
    seed_used=42,
)

report.save_json("validation_report.json")
# Note: PDF export is Pro tier only; Community provides JSON.
```

---

## Optional Dependencies

```bash
# ONNX surrogate support
pip install smrforge[ai]

# All optional features
pip install smrforge[all]
```

---

## API Reference

| Symbol | Module | Purpose |
|--------|--------|---------|
| `load_surrogate_from_path` | `smrforge.ai` | Load .onnx, .pt, .pkl surrogate |
| `register_surrogate_from_path` | `smrforge.ai` | Register path for BYOS |
| `model_hash` | `smrforge.ai` | SHA-256 hash for audit |
| `record_ai_model` | `smrforge.ai` | Append to audit trail |
| `fit_surrogate_with_audit` | `smrforge.ai` | Fit + record to audit |
| `generate_validation_report` | `smrforge.ai` | Compare pred vs reference |
| `fit_surrogate` | `smrforge.workflows` | Fit surrogate (supports audit_trail) |
| `surrogate_from_sweep_results` | `smrforge.workflows` | Build surrogate from sweep |
| `register_surrogate` | `smrforge.workflows` | Register factory or path |

---

## References

- API_STABILITY.md
- PLUGIN_ARCHITECTURE.md
- NUCLEAR_INDUSTRY_ANALYSIS_AND_AI_FUTURE_PROOFING.md (SMRForge-Private)
