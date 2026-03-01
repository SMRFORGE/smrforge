# PINN Implementation Roadmap

**Purpose:** Guide the progression from Option 1 MVP to full PINN implementation in SMRForge Pro.

**Status:** MVP (Option 1) implemented. Full implementation planned for Phase 2a–2c.

**Last Updated:** February 2026

---

## Current State: Option 1 MVP (Completed)

### What Is Implemented

| Component | Location | Description |
|-----------|----------|-------------|
| **SimpleDiffusionPINN** | `smrforge_pro/ai/pinn/simple_diffusion_pinn.py` | Minimal PINN: k-eff, flux, temp from design params; physics + constraint loss |
| **train_simple_pinn()** | Same file | Training loop with early stopping, LR schedule |
| **CLI commands** | `smrforge_pro/cli/pinn_commands.py` | `pinn train`, `pinn predict` |
| **base.PhysicsInformedNN** | `smrforge_pro/ai/pinn/base.py` | Abstract base placeholder for Phase 2a refactor |
| **Package init** | `smrforge_pro/ai/pinn/__init__.py` | Exports SimpleDiffusionPINN, train_simple_pinn |

### Tests

| Test File | Purpose | Deps | Skip When |
|-----------|---------|------|-----------|
| `tests/test_pinn_synthetic_data.py` | Synthetic data generator | numpy | — (always runs) |
| `tests/test_pinn_mvp.py` | SimpleDiffusionPINN, train_simple_pinn, base.PhysicsInformedNN | torch, smrforge_pro | No torch or Pro |
| `tests/test_pinn_cli.py` | pinn train, pinn predict CLI | torch, smrforge_pro, click | No torch or Pro |

Run: `pytest tests/test_pinn_synthetic_data.py tests/test_pinn_mvp.py tests/test_pinn_cli.py -v`

### MVP Limitations

- Single 1D approximation; simplified physics residual
- No AutoDatasetGenerator (manual NPZ preparation)
- No SurrogateOptimizer (no surrogate-assisted design optimization)
- No integration with parameter sweep `--surrogate`
- No PINNEvaluator (MAE, RMSE, R²)
- No benchmark validation (Valar-10, etc.)

### MVP Usage

```bash
# 1. Generate training data (use SMRForge parameter sweep or custom script)
# Save as NPZ: np.savez("dataset.npz", x=<params>, y=<k_eff, flux, temp>)

# 2. Train
smrforge-pro pinn train --dataset dataset.npz --output model.pt

# 3. Predict
smrforge-pro pinn predict --model model.pt --params '{"enrichment":10,"mod_density":0.3,...}'
```

```python
from smrforge_pro.ai.pinn import SimpleDiffusionPINN, train_simple_pinn
import numpy as np

x = np.random.rand(150, 5) * np.array([15, 0.6, 1.0, 2.0, 0.5])
y = np.column_stack([...])  # k_eff, max_flux, avg_temp
model, history = train_simple_pinn(x[:120], y[:120], x[120:], y[120:])
```

---

## Phase 2a: PINN Foundations (M4–M6)

**Effort:** 2–3 engineer-months

### Tasks

| Task | Deliverable | Extends MVP |
|------|-------------|-------------|
| Refactor SimpleDiffusionPINN | Inherit from PhysicsInformedNN | base.py already exists |
| Add SimpleThermalPINN | `thermal_pinn.py` | New file |
| Implement PINNTrainer | `surrogate/pinn_trainer.py` | High-level train API |
| Implement AutoDatasetGenerator | `surrogate/auto_dataset.py` | LHS/random sampling + physics sims |
| Unit tests | `tests/test_pinn_*.py` | 80%+ coverage |
| Example notebook | `examples/pro/pinn_01_introduction.ipynb` | — |

### Migration: MVP → Phase 2a

1. Update `SimpleDiffusionPINN` to inherit `PhysicsInformedNN`:
   - Move `physics_loss` / `constraint_loss` to match base signature (`constraint_loss(outputs)`)
   - Delegate `compute_total_loss` to base or keep custom
2. Add `torch>=2.0` to Pro `extras_require` if not present
3. Replace inline `train_simple_pinn` usage with `PINNTrainer` (keep `train_simple_pinn` as thin wrapper for backward compat)

---

## Phase 2b: Integration & Workflows (M6–M8)

**Effort:** 2–3 engineer-months

### Tasks

| Task | Deliverable | Notes |
|------|-------------|-------|
| SurrogateOptimizer | `workflows/surrogate_optimization.py` | Differential evolution + PINN |
| CLI: pinn optimize | Extend pinn_commands.py | Full optimization workflow |
| Integrate with parameter_sweep | `--surrogate` accepts PINN .pt | Extend `load_surrogate_from_path` |
| load_surrogate_from_path | Add PINN loader in `smrforge_pro/ai/surrogates` | Detect .pt, load SimpleDiffusionPINN |
| 5+ examples | `examples/pro/pinn_02_*.py` | generate_dataset, train, optimize |

### Integration Points

- `smrforge.workflows.parameter_sweep`: Already has `_get_surrogate()` calling `load_surrogate_from_path`. Add PINN support there (Pro-side).
- `smrforge.convenience.quick_surrogate_fit`: Optionally support `method="pinn"` when Pro is installed.

---

## Phase 2c: Validation & Launch (M8–M10)

**Effort:** 1–2 engineer-months

### Tasks

| Task | Deliverable | Notes |
|------|-------------|-------|
| PINNEvaluator | `surrogate/pinn_evaluator.py` | MAE, RMSE, R², validation report |
| Benchmark validation | Valar-10, GT-MHR | R² > 0.95 target |
| Export ONNX/TorchScript | `export/onnx_export.py` | Interoperability |
| Uncertainty quantification | Confidence bands on predictions | Optional |
| White paper | "Physics-Informed Surrogate Models for SMR Design" | Marketing |
| Documentation | `docs/pro/pinn-cli-guide.md`, `pinn-api.md` | — |

---

## Phase 3+: Advanced Features (M10+)

| Feature | Description | Effort |
|---------|-------------|--------|
| Burnup PINN | Time-dependent burnup surrogate | 2–3 months |
| Multi-physics PINN | Coupled neutronics + thermal | 3–4 months |
| RL-assisted optimization | RL on top of PINN | 2–3 months |
| Inverse problems | Infer material properties from measurements | 2+ months |

---

## Dependencies

| Phase | Additional Deps |
|-------|-----------------|
| MVP | `torch>=2.0` (Pro extras) |
| Phase 2a | `scipy` (LHS in AutoDatasetGenerator) |
| Phase 2c | `onnx`, `onnxruntime` (optional) |

---

## GitHub / Repo Notes

- **PINN code lives in:** `smrforge-pro` (private repo)
- **Note:** In the Community repo, `smrforge_pro/` is gitignored. If you developed the MVP in the Community workspace, copy `smrforge_pro/ai/pinn/` and `smrforge_pro/cli/pinn_commands.py` into your smrforge-pro private repo to commit and distribute.
- **Sync exclusion:** `sync_to_public.py` must exclude `smrforge_pro/ai/pinn/*` (and related Pro PINN paths)
- **Pre-sync check:** `pre_sync_check.py` should fail if PINN code appears in Community sync
- **Distribution:** Pro wheel includes `smrforge_pro.ai.pinn`; PyTorch as `extras_require` or optional
- **CI:** PINN model/CLI tests skip when torch or smrforge_pro unavailable (Community CI). Pro repo should run them with `torch` in test deps.

---

## Success Criteria (from Strategic Documents)

| Metric | Target |
|--------|--------|
| R² on benchmark cases | > 0.95 |
| Inference latency | < 5 ms per prediction |
| Physics constraints satisfied | 90%+ of random samples |
| Training time (200 samples, GPU) | < 1 hour |
| Speedup vs pure physics | 50–100x |

---

## References

- `SMRForge_PINNS_Strategic_Opportunity.md` — Market, pricing, go-to-market
- `PINNS_Integration_SMRForge_Pro.md` — Full architecture, code sketches
- `PINNS_Code_and_Checklist.py` — Original copy-paste MVP, checklist
- `PINNS_Executive_Summary_and_Next_Steps.md` — Timeline, decisions
