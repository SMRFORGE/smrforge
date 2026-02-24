# Community vs Pro

SMRForge is available in two tiers: **Community** (open-source, MIT) and **Pro** (licensed). This page summarizes the differences and when to use each.

## Quick Comparison

| Capability | Community | Pro |
|------------|-----------|-----|
| Multi-group diffusion | ✅ | ✅ |
| Monte Carlo (built-in) | ✅ | ✅ |
| Serpent export | ❌ | ✅ Full |
| Serpent import | ❌ | ✅ Basic (materials, surfaces, cells) |
| Serpent run+parse (round-trip) | ✅ | ✅ |
| OpenMC export/import | ✅ Full | ✅ Full |
| OpenMC tally visualization | ❌ | ✅ |
| MCNP export | Placeholder | ✅ Full |
| Benchmark suite | ✅ 3 cases | ✅ Same + extended (planned) |
| Report generator | ✅ Basic (Markdown) | ✅ Full (PDF, traceability) |
| Regulatory traceability | Basic | Full (10 CFR, IAEA, ANS) |
| **AI / Surrogate** | ❌ None | ✅ Full (RBF/linear fit, BYOS ONNX/TorchScript, validation report, sweep --surrogate, ML export, audit trail) |
| API stability policy | — | ✅ Semver, deprecation |
| Licensing | MIT (free) | RSA license key |

## When to Use Community

- **Research and education:** Concept exploration, teaching, quick scoping
- **No external MC required:** Diffusion and built-in MC are sufficient
- **Basic reporting:** Markdown design summaries via `smrforge report design`
- **Open source workflow:** Contributions, transparency, no license cost

## When to Use Pro

- **Licensing preparation:** Need Serpent, OpenMC, or MCNP for regulatory submissions
- **Validation:** Full benchmark suite with automated comparison and reports
- **Regulatory traceability:** 10 CFR 50, IAEA SSR-2/1, ANS-5.1 presets
- **Professional reports:** PDF reports with traceability matrices
- **OpenMC integration:** Community has full export/import and statepoint parsing; Pro adds tally visualization
- **AI/surrogate workflows:** fit_surrogate, BYOS (ONNX/TorchScript/pickle), validation report, sweep with --surrogate, ML export, audit trail

## Pro Feature Callouts

Throughout the Community docs, you may see callouts like:

> **Pro:** For Serpent/MCNP export, tally visualization, and all AI/surrogate features (fit_surrogate, BYOS, validation report, ML export, audit trail, `--surrogate` sweep), use SMRForge Pro. OpenMC export/import is available in Community.

These indicate features available in the Pro tier. If you need them, consider upgrading.

## Learn More

- **Community docs:** This documentation (smrforge.readthedocs.io)
- **Pro docs:** Available with SMRForge Pro license
- **Install Community:** `pip install smrforge`
- **Install Pro:** `pip install smrforge-pro` (requires license)
- **Pro optional extras:** `pip install smrforge-pro[ai,reporting,ml]` for ONNX/Torch, PDF reports, Parquet/HDF5
