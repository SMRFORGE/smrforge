# Community vs Pro

SMRForge is available in two tiers: **Community** (open-source, MIT) and **Pro** (licensed). This page summarizes the differences and when to use each.

## Quick Comparison

| Capability | Community | Pro |
|------------|-----------|-----|
| Multi-group diffusion | ✅ | ✅ |
| Monte Carlo (built-in) | ✅ | ✅ |
| Serpent export/import | ❌ | ✅ Full |
| Serpent run+parse (round-trip with Pro export) | ✅ | ✅ |
| OpenMC export/import | ✅ Full | ✅ Full (Pro: tally viz) |
| MCNP export | ❌ | ✅ Full |
| Benchmark suite | ✅ 3 cases | ✅ 10+ cases |
| Report generator | ✅ Basic (Markdown) | ✅ Full (PDF, traceability) |
| Regulatory traceability | Basic | Full (10 CFR, IAEA, ANS) |
| OpenMC tally visualization | ❌ | ✅ |
| **AI / Surrogate (BYOS)** | ✅ RBF, linear, ONNX, TorchScript, pickle | ✅ + Surrogate Validation Report (PDF) |
| Audit trail for AI models | ✅ `record_ai_model`, `ai_models_used` | ✅ Full |
| Parameter sweep with surrogate | ✅ `--surrogate` for fast eval | ✅ |
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

## Pro Feature Callouts

Throughout the Community docs, you may see callouts like:

> **Pro:** For Serpent/MCNP export and tally visualization, use SMRForge Pro. OpenMC export/import is available in Community.

These indicate features available in the Pro tier. If you need them, consider upgrading.

## What Community Does NOT Include (Pro Exclusive)

To avoid confusion: Community does **not** implement:

- Full Serpent or MCNP export/import (placeholders only; Pro has full implementation)
- Surrogate Validation Report PDF export (Community has JSON only; Pro adds PDF)
- OpenMC tally visualization
- Pro license validation, activation, or entitlement checks

The only Pro reference in Community code is `smrforge/io/converters.py`, which optionally delegates to `smrforge_pro` when installed. When Pro is not installed, Community uses its own implementations or placeholders.

## AI and Surrogate Features (Community)

Community includes Bring Your Own Surrogate (BYOS) and audit integration:

- **RBF and linear surrogates** — Built-in
- **ONNX, TorchScript, pickle** — Load via `load_surrogate_from_path` (optional `smrforge[ai]` for ONNX)
- **Audit trail** — `fit_surrogate(audit_trail=...)` and `record_ai_model()`
- **Parameter sweep with surrogate** — `smrforge sweep --surrogate path.pkl --seed 42`
- **Validation report** — `generate_validation_report()` (Pro adds PDF export)

See **docs/AI_FEATURES.md** for details.

## Learn More

- **Community docs:** This documentation (smrforge.readthedocs.io)
- **AI features:** docs/AI_FEATURES.md
- **Pro docs:** Available with SMRForge Pro license
- **Install Community:** `pip install smrforge`
- **Install Pro:** `pip install smrforge-pro` (requires license)
