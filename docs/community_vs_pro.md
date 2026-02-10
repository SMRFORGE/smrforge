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

## Learn More

- **Community docs:** This documentation (smrforge.readthedocs.io)
- **Pro docs:** Available with SMRForge Pro license
- **Install Community:** `pip install smrforge`
- **Install Pro:** `pip install smrforge-pro` (requires license)
