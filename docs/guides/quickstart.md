# SMRForge Quickstart — First 5 Minutes

**Last Updated:** February 2026  
**Audience:** New users who want to run SMRForge in under 5 minutes

---

## 1. Install

```bash
pip install smrforge
```

## 2. Download Nuclear Data (Quick Start)

To run neutronics or burnup, you need ENDF nuclear data. For a minimal setup (U‑235, U‑238, Pu‑239):

```bash
smrforge data setup
# Or download directly (3 files, ~few MB):
smrforge data download --library ENDF-B-VIII.1 --nuclide-set quickstart
```

For full SMR modeling, use the `common_smr` set (~30 nuclides):

```bash
smrforge data download --library ENDF-B-VIII.1 --nuclide-set common_smr
```

## 3. Run a Quick Analysis

```python
from smrforge import create_reactor, quick_keff

# Create a preset reactor (HTGR)
reactor = create_reactor("Valar-10")

# Get k-eff (requires ENDF data)
keff, _ = quick_keff(reactor)
print(f"k-eff: {keff:.5f}")
```

## 4. Verify Installation

```bash
smrforge --version
smrforge reactor list
smrforge data validate --endf-dir <path-to-your-endf>
```

## 5. Next Steps

- **[Tutorial](tutorial.md)** — Step-by-step walkthrough
- **[CLI Guide](cli-guide.md)** — All commands
- **[Community vs Pro](../community_vs_pro.md)** — Tier comparison
- **[Troubleshooting](troubleshooting.md)** — Common issues

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `FileNotFoundError: ENDF file not found` | Run `smrforge data download --library ENDF-B-VIII.1 --nuclide-set quickstart` |
| `SMRFORGE_ENDF_DIR` not set | Run `smrforge data setup` or set env var to your ENDF directory |
| Solver doesn't converge | Try `tolerance=1e-4` or `max_iterations=200` in solver options |
| Serpent/MCNP export fails | Full export is Pro-tier; Community has Serpent run+parse only |

See [Troubleshooting](troubleshooting.md) for details.
