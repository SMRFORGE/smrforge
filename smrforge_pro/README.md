# SMRForge Pro

SMRForge Pro extends the Community edition with AI/surrogate, full Serpent/OpenMC converters, validation reports, and ML export.

## Features

- **AI / Surrogate**: `fit_surrogate`, `surrogate_from_sweep_results`, BYOS (ONNX, TorchScript, sklearn), `register_surrogate`, `fit_surrogate` with RBF/linear
- **Converters**: Full Serpent export/import, OpenMC export/import, MCNP export
- **OpenMC tally viz**: `visualize_openmc_tallies(statepoint_path)` — plot mesh tallies (requires `smrforge-pro[openmc]`)
- **Validation reports**: `SurrogateValidationReport`, `generate_validation_report`, PDF export
- **ML export**: `export_ml_dataset` for Parquet/HDF5
- **Audit trail**: `record_ai_model` for regulatory traceability

## Installation

```bash
# Base Pro (extends smrforge)
pip install smrforge-pro

# With AI extras (ONNX, TorchScript)
pip install smrforge-pro[ai]

# With PDF reporting
pip install smrforge-pro[reporting]

# With Parquet/HDF5 export
pip install smrforge-pro[ml]

# All extras
pip install smrforge-pro[all]
```

## Optional Extras

| Extra | Packages | Purpose |
|-------|----------|---------|
| `ai` | onnxruntime, torch | ONNX/TorchScript surrogate loading |
| `reporting` | reportlab | PDF validation reports |
| `ml` | pyarrow, tables | Parquet and HDF5 export |
| `openmc` | openmc | OpenMC tally visualization from statepoint |
| `all` | All of the above | Full Pro feature set |

## Usage

Pro modules are used automatically when installed. Community delegates to Pro for:

- `smrforge.io.converters.SerpentConverter` / `OpenMCConverter`
- `smrforge.workflows.surrogate.fit_surrogate`, `surrogate_from_sweep_results`
- `smrforge.workflows.ml_export.export_ml_dataset`
- `smrforge.ai.audit.record_ai_model`

See [community_vs_pro.md](../docs/community_vs_pro.md) for a full comparison.

## Licensing

SMRForge Pro requires a license key for production use. Licensing is validated via environment variable or config:

- **Environment:** `SMRFORGE_PRO_LICENSE` (JSON or key string)
- **Config:** Optional license file path in `~/.smrforge/pro_license.json`

For evaluation or development, some features may run without a key; see https://smrforge.io for terms.

## Workflow Hooks

Pro workflows integrate with Community hooks. Register handlers for automation:

```python
from smrforge.workflows import register_hook, run_hooks

# Called before Serpent/MCNP export
register_hook("pre_export", lambda ctx: print(f"Exporting to {ctx['format']}"))

# Called after parameter sweep completes
register_hook("post_sweep", lambda ctx: print(f"Sweep finished: {len(ctx['result'].results)} points"))
```

## License

SMRForge Pro requires a license. See https://smrforge.io for pricing and terms.
