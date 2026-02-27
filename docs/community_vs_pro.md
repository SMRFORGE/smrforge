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
- **Natural-language design:** Parse "10 MW HTGR with k-eff 1.0-1.05, enrichment <20%" → reactor spec
- **Code-to-code verification:** Run same reactor through diffusion, MC, OpenMC, Serpent, MCNP; unified comparison
- **Regulatory submission package:** NRC/IAEA-ready package (inputs, outputs, traceability matrix)
- **Benchmark reproduction:** One-click run and compare to reference
- **Multi-objective optimization:** Optimize neutronics, safety, economics in one framework
- **Physics-informed surrogates:** Surrogate with UQ and physics checks (e.g., k_eff > 0)

## Pro Feature Callouts

Throughout the Community docs, you may see callouts like:

> **Pro:** For Serpent/MCNP export, tally visualization, AI/surrogate features, natural-language design, code-to-code verification, regulatory package, benchmark reproduction, multi-objective optimization, and physics-informed surrogates, use SMRForge Pro. OpenMC export/import is available in Community.

These indicate features available in the Pro tier. If you need them, consider upgrading.

## Repositories

| Tier | Repository | Visibility |
|------|------------|------------|
| **Community** | [github.com/SMRFORGE/smrforge](https://github.com/SMRFORGE/smrforge) | Public (MIT) |
| **Pro** | [github.com/SMRFORGE/smrforge-pro](https://github.com/SMRFORGE/smrforge-pro) | Private (licensed) |

Community is open-source; Pro is developed in a separate private repo and distributed under license.

**Pro distribution:** Pro and the air-gapped Pro version live in [smrforge-pro](https://github.com/SMRFORGE/smrforge-pro). Paid-tier bundles are delivered via **GitHub Packages**—wheel bundles on Releases, Docker images on `ghcr.io/smrforge/smrforge-pro`. Access requires Pro license and authenticated GitHub credentials.

## Learn More

- **Community docs:** [smrforge.readthedocs.io](https://smrforge.readthedocs.io)
- **Pro overview:** [docs/pro-tier-overview.md](pro-tier-overview.md) (in Community repo)
- **Install Community:** `pip install smrforge`
- **Install Pro:** Requires Pro license; install from private PyPI or `pip install smrforge-pro`
