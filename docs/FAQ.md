# SMRForge Frequently Asked Questions

**Last Updated:** February 2026

---

## General

### What is SMRForge?

SMRForge is a Python toolkit for Small Modular Reactor (SMR) design, analysis, and optimization. It includes neutronics (diffusion, Monte Carlo), burnup, thermal-hydraulics, transients, and economics.

### Community vs Pro?

See [Community vs Pro](community_vs_pro.md). **Community** (free, MIT) has full OpenMC export, Serpent run+parse, built-in Monte Carlo, and most workflows. **Pro** ($5,000/year) adds full Serpent/MCNP export, PDF reports, AI/surrogate workflows, and 10+ benchmarks.

---

## Nuclear Data

### How do I get ENDF data?

```bash
smrforge data setup
# or
smrforge data download --library ENDF-B-VIII.1 --nuclide-set quickstart
```

Quick start downloads U235, U238, Pu239 (~3 files). Use `common_smr` for ~30 SMR nuclides.

### Can I use ENDF offline?

Yes. After downloading, set `SMRFORGE_ENDF_DIR` (or `local_endf_dir`) to your local directory. No network needed for runs.

### Which libraries are supported?

ENDF/B-VIII.0, ENDF/B-VIII.1, JEFF-3.3, JENDL-5.0. Download from IAEA or NNDC.

---

## Solver & Analysis

### Diffusion solver doesn't converge. What should I do?

Try `SolverOptions(tolerance=1e-4, max_iterations=200)`. Ensure you're using real ENDF data, not mocks.

### Can I use Serpent or MCNP with SMRForge?

**Community:** Serpent run + parse (execute Serpent, read output). No full Serpent/MCNP export.  
**Pro:** Full Serpent and MCNP round-trip export/import.

### How do I run a burnup calculation?

```python
from smrforge import create_reactor, quick_sweep
reactor = create_reactor("Valar-10")
results = quick_sweep(reactor, param="burnup", values=[0, 365, 730])
```

---

## Installation & Dependencies

### What Python version do I need?

Python 3.10+ recommended. 3.9 may work for core features.

### Are plotly, h5py, polars required?

They are optional. Core neutronics and burnup work without them. Install for:
- **plotly/matplotlib:** Visualization
- **h5py:** Burnup checkpointing
- **polars:** Some data operations

---

## Development & Contributing

### How do I run tests?

```bash
pytest tests/ -v
# Skip slow/isolated tests:
pytest tests/ -v -m "not isolated"
```

### Where is the API documentation?

[smrforge.readthedocs.io](https://smrforge.readthedocs.io) and the Sphinx build in `docs/`.
