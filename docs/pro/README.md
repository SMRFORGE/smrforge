# SMRForge Pro — Documentation

**Tier:** SMRForge Pro (licensed)  
**Scope:** Serpent/MCNP full I/O, benchmark suite (10+ cases), regulatory report generator, OpenMC tally visualization, AI/surrogate workflows.

---

## Pro Tier Feature Overview

SMRForge Pro extends the Community edition with production-grade interoperability, reporting, and AI/surrogate capabilities:

| Category | Features |
|----------|----------|
| **Serpent I/O** | Full export of reactor to Serpent input format; full import from Serpent |
| **OpenMC I/O** | Full export/import (Community has this); Pro adds OpenMC tally visualization |
| **MCNP Export** | Full export of reactor to MCNP input format |
| **Benchmark Suite** | 10+ IAEA/ANS benchmark cases (Community: 3); automated comparison and reports |
| **Report Generator** | PDF reports with margins and full regulatory traceability (Community: basic Markdown) |
| **Regulatory Traceability** | Full (10 CFR, IAEA SSR-2/1, ANS-5.1 presets) |
| **AI / Surrogate** | fit_surrogate, BYOS (ONNX/TorchScript/pickle); validation report; parameter sweep with --surrogate; ML export; audit trail |
| **Natural-language design** | Parse "10 MW HTGR, k-eff 1.0-1.05" → reactor spec |
| **Code-to-code verification** | Diffusion, MC, OpenMC, Serpent, MCNP unified comparison |
| **Regulatory package** | NRC/IAEA submission package with traceability matrix |
| **Benchmark reproduction** | One-click reproduce and compare to reference |
| **Multi-objective optimization** | Optimize k_eff, safety margins, economics |
| **Physics-informed surrogates** | UQ + physics constraints (e.g., k_eff > 0) |
| **API Stability** | Semver and deprecation policy |

---

## Quick Navigation

- [Pro Feature Matrix](pro-feature-matrix.md) — Feature-by-feature breakdown with workflows and required data
- [Pro Examples Index](../guides/pro/pro-examples-index.md) — Code examples for NL design, code verification, regulatory package, benchmark reproduction, multi-objective optimization, physics-informed surrogates
- [Serpent Export Guide](serpent-export-guide.md) — Serpent workflow and data requirements
- [OpenMC Export Guide](openmc-export-guide.md) — OpenMC workflow and data requirements
- [Benchmark Suite Guide](benchmark-suite-guide.md) — Verification workflows
- [Report Generator Guide](report-generator-guide.md) — Regulatory reporting

---

## Installation (Pro)

```bash
pip install smrforge-pro
```

Requires valid Pro license. See [Pro Licensing](pro-licensing.md) for activation.

---

## Pro vs Community

| Capability | Community | Pro |
|------------|-----------|-----|
| Multi-group diffusion | ✅ | ✅ |
| Monte Carlo (built-in) | ✅ | ✅ |
| Serpent export/import | ❌ | ✅ Full |
| Serpent run+parse | ✅ | ✅ |
| OpenMC export/import | ✅ Full | ✅ Full (Pro: tally viz) |
| MCNP export | ❌ | ✅ Full |
| Benchmark suite | ✅ 3 cases | ✅ 10+ cases |
| Report generator | ✅ Basic (Markdown) | ✅ Full (PDF, traceability) |
| Regulatory traceability | Basic | Full (10 CFR, IAEA, ANS) |
| OpenMC tally visualization | ❌ | ✅ |
| AI / Surrogate | ❌ | ✅ Full |
| Natural-language design | ❌ | ✅ |
| Code-to-code verification | ❌ | ✅ |
| Regulatory package | Basic | ✅ Full |
| Benchmark reproduction | — | ✅ |
| Multi-objective optimization | — | ✅ |
| Physics-informed surrogates | — | ✅ |
| API stability policy | — | ✅ Semver, deprecation |
| Licensing | MIT (free) | RSA license key |
