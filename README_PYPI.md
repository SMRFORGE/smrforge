# SMRForge

![SMRForge Logo](https://raw.githubusercontent.com/SMRFORGE/smrforge/main/docs/logo/smrforge-logo.png)

**Small Modular Reactor Design and Analysis Toolkit**

SMRForge is a Python toolkit for nuclear reactor design, analysis, and optimization with a focus on **Small Modular Reactors (SMRs)**.

## Install

```bash
pip install smrforge
```

Optional extras:

```bash
pip install "smrforge[all]"      # all optional dependencies
pip install "smrforge[dev]"      # developer tooling (pytest, black, etc.)
pip install "smrforge[docs]"     # documentation build deps (Sphinx, MyST, etc.)
pip install "smrforge[uq]"       # uncertainty quantification helpers
```

## Quick start

```python
import smrforge as smr

# List built-in reactor presets
print(smr.list_presets())

# Create and analyze a preset reactor
reactor = smr.create_reactor("valar-10")
k_eff = reactor.solve_keff()
print(f"k-effective: {k_eff:.6f}")
```

## Stable API (integration & AI)

```python
from smrforge.api import fit_surrogate, export_ml_dataset, create_audit_trail

# Fit surrogate from sweep results (rbf, linear, or registered custom)
# Pro: full implementation; Community: delegates when smrforge-pro installed
surrogate = fit_surrogate(X, y, method="rbf")

# Export design points for ML training (Parquet or HDF5)
export_ml_dataset(results, "design_points.parquet")

# Audit trail with AI model tracking
trail = create_audit_trail("keff", inputs={}, outputs={"k_eff": 1.0})
from smrforge.ai import record_ai_model
record_ai_model(trail, "rbf", version="scipy-1.11")
```

**Tiers:** Community (this package) + Pro ([smrforge-pro](https://github.com/SMRFORGE/smrforge-pro)). See [Community vs Pro](https://github.com/SMRFORGE/smrforge/blob/main/docs/community_vs_pro.md).

## Nuclear data (ENDF) setup

Some features require ENDF data files.

```bash
python -m smrforge.core.endf_setup
```

## Documentation

- **Documentation (ReadTheDocs)**: `https://smrforge.readthedocs.io/`
- **API how-to (practical guide)**: `https://smrforge.readthedocs.io/en/latest/api/howto.html`
- **Full API reference**: `https://smrforge.readthedocs.io/en/latest/api_reference.html`
- **Interactive notebooks guide**: `https://smrforge.readthedocs.io/en/latest/guides/testing-notebooks.html`
- **Source / Issues**: `https://github.com/SMRFORGE/smrforge`

## License

MIT

