# Community vs Pro

SMRForge is available in two tiers: **Community** (open-source, MIT) and **Pro** (licensed). This page summarizes the differences and when to use each.

## Quick Comparison

| Capability | Community | Pro |
|------------|-----------|-----|
| Multi-group diffusion | ✅ | ✅ |
| Monte Carlo (built-in) | ✅ | ✅ |
| **Variance reduction** | Basic (ImportanceMap, WeightWindow) | ✅ Advanced (CADIS; Pro + air-gap) |
| **Geometry** | | |
| Parametric builders (fuel pins, moderators) | ✅ | ✅ |
| 2D Plotly flux maps, Matplotlib static plots | ✅ | ✅ |
| CAD import (STEP, IGES, STL) | ❌ | ✅ Direct (Pro + air-gap) |
| DAGMC h5m import | ❌ | ✅ Direct (Pro + air-gap) |
| Interactive 3D viz, geometry debugging | ❌ | ✅ |
| Serpent export | ❌ | ✅ Full (Pro + air-gap) |
| Serpent import | ❌ | ✅ Full (reactor, materials, surfaces, cells, lattices; Pro + air-gap) |
| Serpent run+parse (round-trip) | ✅ | ✅ |
| OpenMC export/import | ✅ Full | ✅ Full |
| OpenMC tally visualization | ❌ | ✅ |
| MCNP export | Placeholder | ✅ Full (Pro + air-gap) |
| Benchmark suite | ✅ 3 cases | ✅ Same + extended (planned) |
| Report generator | ✅ Basic (Markdown) | ✅ Full (PDF, traceability) |
| Regulatory traceability | Basic | Full (10 CFR, IAEA, ANS) |
| **AI / Surrogate** | ❌ None | ✅ Full (RBF/linear fit, BYOS ONNX/TorchScript, validation report, sweep --surrogate, ML export, audit trail) |
| **Natural-language design** | ❌ | ✅ Parse "10 MW HTGR, k-eff 1.0-1.05" → reactor spec |
| **Code-to-code verification** | ❌ | ✅ Diffusion, MC, OpenMC, Serpent, MCNP comparison |
| **Regulatory package** | Basic | ✅ Full (NRC/IAEA submission package, traceability matrix) |
| **Benchmark reproduction** | — | ✅ One-click reproduce, compare to reference |
| **Multi-objective optimization** | — | ✅ Optimize k_eff, safety, economics |
| **Physics-informed surrogates** | — | ✅ UQ + physics constraints (k_eff > 0) |
| API stability policy | — | ✅ Semver, deprecation |
| Licensing | MIT (free) | RSA license key |

## When to Use Community

- **Research and education:** Concept exploration, teaching, quick scoping
- **Parametric SMR design:** Use `create_fuel_pin`, `create_moderator_block`, `create_simple_prismatic_core` for geometry without CAD
- **Basic tally visualization:** 2D Plotly flux maps (`plot_flux_map_2d`), Matplotlib static plots
- **No external MC required:** Diffusion and built-in MC are sufficient
- **Basic reporting:** Markdown design summaries via `smrforge report design`
- **Open source workflow:** Contributions, transparency, no license cost
- **CAD workflows:** Document external CAD→DAGMC workflows; upgrade to Pro for direct STEP/STL import

## When to Use Pro

- **Advanced variance reduction:** CADIS-style weight windows from diffusion adjoint (single Python stack, no external codes); SMR presets; export to OpenMC/MCNP
- **CAD and DAGMC:** Direct STEP/STL/IGES import, DAGMC h5m, tessellation controls, hybrid CSG/mesh
- **Interactive 3D visualization:** Geometry debugging, ray-tracing previews, multiphysics overlays
- **Licensing preparation:** Need Serpent, OpenMC, or MCNP for regulatory submissions
- **Validation:** Full benchmark suite with automated comparison and reports
- **Regulatory traceability:** 10 CFR 50, IAEA SSR-2/1, ANS-5.1 presets
- **Professional reports:** PDF reports with traceability matrices
- **OpenMC integration:** Community has full export/import and statepoint parsing; Pro adds tally visualization
- **AI/surrogate workflows:** fit_surrogate, BYOS (ONNX/TorchScript/pickle), validation report, sweep with --surrogate, ML export, audit trail
- **Natural-language design:** Parse "10 MW HTGR with k-eff 1.0-1.05, enrichment <20%" → reactor spec
- **Code-to-code verification:** Run same reactor through diffusion, MC, OpenMC, Serpent, MCNP; unified comparison
- **Regulatory submission package:** NRC/IAEA-ready package (inputs, outputs, traceability matrix)
- **Benchmark reproduction:** One-click run and compare to reference
- **Multi-objective optimization:** Optimize neutronics, safety, economics in one framework
- **Physics-informed surrogates:** Surrogate with UQ and physics checks (e.g., k_eff > 0)

## Pro Feature Callouts

Throughout the Community docs, you may see callouts like:

> **Pro:** For Serpent/MCNP export and import, tally visualization, AI/surrogate features, natural-language design, code-to-code verification, regulatory package, benchmark reproduction, multi-objective optimization, and physics-informed surrogates, use SMRForge Pro. All Pro features are available in air-gapped deployments. OpenMC export/import is available in Community.

These indicate features available in the Pro tier. If you need them, consider upgrading.

## Repositories

| Tier | Repository | Visibility |
|------|------------|------------|
| **Community** | [github.com/SMRFORGE/smrforge](https://github.com/SMRFORGE/smrforge) | Public (MIT) |
| **Pro** | [github.com/SMRFORGE/smrforge-pro](https://github.com/SMRFORGE/smrforge-pro) | Private (licensed) |

Community is open-source; Pro is developed in a separate private repo and distributed under license.

**Pro distribution:** Pro and the air-gapped Pro version live in [smrforge-pro](https://github.com/SMRFORGE/smrforge-pro). Paid-tier bundles are delivered via **GitHub Packages**—wheel bundles on Releases, Docker images on `ghcr.io/smrforge/smrforge-pro`. Access requires Pro license and authenticated GitHub credentials.

**Air-gapped Pro = Pro (full feature parity):** Air-gapped Pro has the same features as Pro-tier when running offline. No capabilities are disabled. Use `scripts/airgap/bundle_wheels.sh` or `airgap-bundle-*.zip` from Pro Releases. Pre-stage ENDF data per the [Air-Gapped Deployment Guide](guides/air-gapped-deployment.md).

## Convenience & Help Functions by Tier

### Community (All Available)

**Workflows:** `quick_validation_run`, `quick_openmc_run`, `quick_preprocessed_data`, `quick_design_study`, `quick_atlas`, `quick_doe`, `quick_pareto`, `quick_sensitivity`

**Discovery:** `list_validation_benchmarks`, `list_preset_types`, `list_pro_features`, `list_tier_capabilities`, `get_tier_info`, `list_workflows`, `list_convenience_functions`, `list_cli_commands`, `get_quick_start_commands`, `list_functions_by_category`

**Data & Paths:** `find_endf_directory`, `get_data_paths`, `list_available_benchmarks`

**Help:** `check_setup`, `get_environment_summary`, `validate_installation`, `get_support_info`, `get_function_signature`, `suggest_next_steps`, `what_can_i_do_with`, `get_workflow_help`, `help_search`, `list_help_topics`, `get_cheat_sheet`

**Pro messaging:** `get_upgrade_benefits`, `check_pro_feature`, `list_pro_vs_community`

### Pro (Additional)

`quick_code_verify`, `quick_regulatory_package`, `quick_benchmark_reproduce`, `quick_surrogate_fit`, `quick_nl_design`, `quick_multi_optimize`, `quick_tally_visualization` — these raise a clear upgrade message when Pro is not installed.

---

## Code Examples by Tier

### Community Examples

**Quick k-eff (no data required):**
```python
import smrforge as smr

# Create preset reactor and solve
reactor = smr.create_reactor("valar-10")
k_eff, flux = smr.quick_keff_calculation(core=reactor.build_core())
print(f"k-eff: {k_eff:.6f}")
```

**OpenMC export and run (Community):**
```python
from pathlib import Path
import smrforge as smr
from smrforge.io import OpenMCConverter
from smrforge.io.openmc_run import run_and_parse

reactor = smr.create_reactor("valar-10")
reactor.build_core()
out = Path("output/openmc")
OpenMCConverter.export_reactor(reactor, out, particles=1000, batches=20)
results = run_and_parse(out, timeout=60)  # Requires OpenMC installed
print(f"k_eff: {results['k_eff']:.6f} ± {results['k_eff_std']:.6f}")
```

**Serpent run+parse (Community — works with Pro-exported input):**
```python
from pathlib import Path
from smrforge.io import run_serpent, parse_serpent_res

work_dir = Path("serpent_work")
proc = run_serpent(work_dir, "model.sss", timeout=300)  # Requires Serpent 2
if proc.returncode == 0:
    parsed = parse_serpent_res(work_dir / "model_res.m")
    print(f"k_eff: {parsed['k_eff']:.6f}")
```

**Design point and safety report (Community):**
```python
import smrforge as smr
from smrforge.validation.safety_report import safety_margin_report
from smrforge.validation.constraint_builder import constraint_set_from_design_and_report

reactor = smr.create_reactor("valar-10")
point = smr.get_design_point(reactor)
cs = constraint_set_from_design_and_report(reactor, margin_report=None)
report = safety_margin_report(reactor, constraint_set=cs)
print(report.to_text())
```

**Community benchmark suite:**
```python
from smrforge.benchmarks import CommunityBenchmarkRunner

runner = CommunityBenchmarkRunner()
results = runner.run_all()
runner.generate_report(results, output_path=Path("output/community_benchmark_report.md"))
```

**CLI equivalents:**
```bash
smrforge workflow design-point --reactor valar-10 --output design_point.json
smrforge workflow safety-report --reactor valar-10 --output safety_report.json
smrforge report design --preset valar-10 -o design_summary.md
smrforge decay calculate --inventory inventory.json --cooling-time 3600
```

### Pro Examples

Pro examples live in [smrforge-pro](https://github.com/SMRFORGE/smrforge-pro). Install Pro and run from `examples/pro/` there.

**Natural-language design (Pro):**
```python
from smrforge_pro.ai.nl_design import design_from_nl, parse_nl_design

intent = parse_nl_design("10 MW HTGR with k-eff 1.0-1.05, enrichment <20%")
result = design_from_nl("10 MW HTGR", run_analysis=True)
```

**Serpent full export (Pro):**
```python
from pathlib import Path
import smrforge as smr
from smrforge_pro.converters.serpent import SerpentConverter

reactor = smr.create_reactor("valar-10")
SerpentConverter.export_reactor(reactor, Path("serpent_output"))
```

**Code-to-code verification (Pro):**
```python
from pathlib import Path
from smrforge_pro.workflows.code_verification import run_code_verification

report = run_code_verification("valar-10", output_dir=Path("verification_output"))
```

**Regulatory package (Pro):**
```python
from pathlib import Path
from smrforge_pro.workflows.regulatory_package import generate_regulatory_package

path = generate_regulatory_package(reactor, output_dir=Path("regulatory_package"))
```

**Benchmark reproduction (Pro):**
```python
from pathlib import Path
from smrforge_pro.workflows.benchmark_reproduction import list_benchmarks, reproduce_benchmark

for bid in list_benchmarks():
    result = reproduce_benchmark(bid, output_dir=Path("benchmark_output"))
```

**Multi-objective optimization (Pro):**
```python
from smrforge_pro.workflows.multi_objective_optimization import multi_objective_optimize

result = multi_objective_optimize(reactor_from_x, bounds, param_names, max_evaluations=50)
```

**Physics-informed surrogate (Pro):**
```python
from smrforge_pro.ai.physics_informed import physics_informed_surrogate_from_sweep

predictor = physics_informed_surrogate_from_sweep(
    results, ["enrichment"], output_metric="k_eff"
)
pred = predictor(np.array([0.19]))
```

---

## Learn More

- **Community docs:** [smrforge.readthedocs.io](https://smrforge.readthedocs.io)
- **Pro overview:** [docs/pro-tier-overview.md](pro-tier-overview.md) (in Community repo)
- **Install Community:** `pip install smrforge`
- **Install Pro:** Requires Pro license; install from private PyPI or `pip install smrforge-pro`
