# SMRForge Pro

**Small Modular Reactor Design and Analysis Toolkit — Pro Tier**

*Use this as `README.md` in the [smrforge-pro](https://github.com/SMRFORGE/smrforge-pro) repository.*

---

SMRForge Pro extends the Community edition with converters, benchmarks, reporting, AI/surrogate workflows, and regulatory traceability. Requires a Pro license.

## Repositories

| Repo | Contents |
|------|----------|
| [smrforge](https://github.com/SMRFORGE/smrforge) | Community (public, MIT) |
| [smrforge-pro](https://github.com/SMRFORGE/smrforge-pro) | Pro (private, licensed) — **this repo** |

smrforge-pro contains the full codebase: Community (`smrforge/`) + Pro (`smrforge_pro/`). Development happens here; Community-only changes sync to the public smrforge repo.

## Pro Features

- **Converters:** Serpent, OpenMC, MCNP (full export/import, round-trip)
- **Benchmarks:** BenchmarkRunner, validation_benchmarks.json, reproduce_benchmark
- **Reporting:** ReportGenerator (HTML/PDF), regulatory traceability matrix
- **Visualization:** OpenMC tally HDF5 parsing, 1D/2D Plotly
- **Licensing:** RSA-signed keys, expiry, grace period
- **AI/Surrogate:** fit_surrogate, BYOS, surrogate validation, sweep --surrogate
- **Workflows:** NL design, code verification, regulatory package, benchmark reproduction, multi-objective optimization

## Install (Pro)

```bash
# Requires Pro license; install from private PyPI or local
pip install smrforge-pro

# Optional extras
pip install smrforge-pro[licensing,ai]
```

## Quick Start

```python
import smrforge as smr
import smrforge_pro

# Serpent export
from smrforge_pro.converters.serpent import SerpentConverter
reactor = smr.create_reactor("valar-10")
SerpentConverter.export_reactor(reactor, Path("serpent_output"))

# Benchmark reproduction
from smrforge_pro.workflows.benchmark_reproduction import reproduce_benchmark
result = reproduce_benchmark("valar-10", output_dir=Path("benchmark_out"))
```

## Air-Gapped Deployment

For regulated environments without internet:

- **Bundle scripts:** `./scripts/airgap/bundle_wheels.sh`, `./scripts/airgap/bundle_docker.sh`
- **Releases:** Air-gap bundles attached to GitHub Releases (`airgap-bundle-*.zip`)
- **Docs:** [Air-Gapped Pro](docs/deployment/air-gapped-pro.md)

## Documentation

- **Pro guides:** See `docs/pro/` and `docs/guides/pro/` in this repo
- **Air-gapped Pro:** [docs/deployment/air-gapped-pro.md](docs/deployment/air-gapped-pro.md)
- **Community vs Pro:** [Community repo docs](https://github.com/SMRFORGE/smrforge/blob/main/docs/community_vs_pro.md)

## License

Pro — licensed. Contact for terms.
