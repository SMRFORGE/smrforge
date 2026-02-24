# Pro Tier — Examples Index

All SMRForge Pro examples. **Requires Pro license.**

---

## Location

**Path:** `examples/pro/`

---

## Serpent & OpenMC

| Example | Description | Required Data |
|---------|-------------|---------------|
| `serpent_export_example.py` | Export reactor to Serpent | Reactor |
| `openmc_export_example.py` | Export reactor to OpenMC | Reactor |
| `openmc_visualization_pro.py` | OpenMC tally visualization | OpenMC results |

---

## Benchmarks & Reporting

| Example | Description | Required Data |
|---------|-------------|---------------|
| `benchmark_suite_example.py` | Run benchmark suite | None (built-in) |
| `benchmark_reproduction_example.py` | One-click benchmark reproduce and compare | None (built-in) |
| `report_generator_example.py` | Generate PDF report | Analysis results |

---

## AI & Workflows

| Example | Description | Required Data |
|---------|-------------|---------------|
| `nl_design_example.py` | Natural-language design ("10 MW HTGR, k-eff 1.0-1.05" → reactor) | None |
| `code_verification_example.py` | Code-to-code verification (diffusion, MC, OpenMC, Serpent, MCNP) | Reactor |
| `regulatory_package_example.py` | NRC/IAEA regulatory submission package | Reactor |
| `multi_objective_optimization_example.py` | Multi-objective design optimization | Reactor |
| `physics_informed_surrogate_example.py` | Physics-informed surrogate with UQ | Sweep results |

---

## Advanced Workflows

| Example | Description | Required Data |
|---------|-------------|---------------|
| `complete_pro_workflow.py` | Serpent export → run → compare | Reactor, Serpent |
| `regulatory_report_example.py` | Regulatory report with traceability | Results, constraints |
