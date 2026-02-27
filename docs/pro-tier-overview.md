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

## Comparison

See [Community vs Pro](community_vs_pro.md) for a detailed tier comparison.
