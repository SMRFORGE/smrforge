# SMRForge Pro Tier — Overview

**Pro tier code, documentation, and the air-gapped Pro version live in the Pro-tier repository:** [https://github.com/SMRFORGE/smrforge-pro](https://github.com/SMRFORGE/smrforge-pro). To bootstrap air-gap files into a new Pro repo, run `./scripts/setup_pro_airgap.sh /path/to/smrforge-pro` from the Community repo.

## What Pro Adds

SMRForge Pro extends the Community tier with:

- **Converters:** Full Serpent, OpenMC, and MCNP export/import (round-trip, validation)
- **Benchmarks:** BenchmarkRunner, validation_benchmarks.json, reproduce_benchmark
- **Reporting:** ReportGenerator (HTML/PDF), regulatory traceability matrix
- **Visualization:** OpenMC tally HDF5 parsing, 1D/2D Plotly plots
- **Licensing:** RSA-signed license keys, expiry, grace period
- **AI/Surrogate:** fit_surrogate, BYOS (ONNX/TorchScript/pickle), surrogate validation report, sweep --surrogate
- **Workflows:** Natural-language design, code verification, regulatory package, benchmark reproduction, multi-objective optimization, physics-informed surrogates

## Getting Pro

- **Repository:** [github.com/SMRFORGE/smrforge-pro](https://github.com/SMRFORGE/smrforge-pro) (private)
- **Distribution:** Pro and air-gapped bundles are delivered via **GitHub Packages** when you purchase a paid tier:
  - **Docker images:** `ghcr.io/smrforge/smrforge-pro` (GitHub Container Registry)
  - **Wheel bundles:** Attached to [Releases](https://github.com/SMRFORGE/smrforge-pro/releases) for offline install
- **Install:** Requires Pro license; `pip install smrforge-pro` or `docker pull ghcr.io/smrforge/smrforge-pro` with authenticated access
- **Contact:** Inquiries at [smrforge.io](https://smrforge.io) or your sales contact

## Pro Code Examples

Pro examples live in the [smrforge-pro](https://github.com/SMRFORGE/smrforge-pro) repository. Install Pro and run from `examples/pro/` there.

**Serpent full export (Pro):**
```python
from pathlib import Path
import smrforge as smr
from smrforge_pro.converters.serpent import SerpentConverter

reactor = smr.create_reactor("valar-10")
SerpentConverter.export_reactor(reactor, Path("serpent_output"))
```

**Natural-language design (Pro):**
```python
from smrforge_pro.ai.nl_design import design_from_nl, parse_nl_design

intent = parse_nl_design("10 MW HTGR with k-eff 1.0-1.05, enrichment <20%")
result = design_from_nl("10 MW HTGR", run_analysis=True)
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

**Surrogate fit and sweep (Pro):**
```python
from smrforge_pro.workflows.surrogate import fit_surrogate, run_sweep_with_surrogate

# Fit surrogate from parameter sweep results
surrogate = fit_surrogate(sweep_results, param_names=["enrichment"], metric="k_eff")

# Run sweep with surrogate for fast evaluation
results = run_sweep_with_surrogate(reactor_template, surrogate, n_points=100)
```

## Comparison

See [Community vs Pro](community_vs_pro.md) for a detailed tier comparison and more code examples.
