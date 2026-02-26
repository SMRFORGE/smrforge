# SMRForge Pro Changelog

**Last Updated:** February 2026

All notable changes to SMRForge Pro (licensed tier) are documented here.
Pro follows the same [Semantic Versioning](https://semver.org/spec/v2.0.0.html) as Community.

**Compatibility:** Pro 0.1.x is tested with `smrforge` (Community) >= 0.6.0. Pin both versions for reproducible deployments.

---

## [Unreleased]

### Added
- **Natural-language design:** `workflow nl-design --text "10 MW HTGR with k-eff 1.0-1.05"` - parse intent and create reactor.
- **Code-to-code verification:** `workflow code-verify --reactor X` - run through diffusion, MC, OpenMC, Serpent, MCNP and compare.
- **Regulatory package:** `workflow regulatory-package --reactor X` - generate NRC/IAEA submission package with inputs, outputs, traceability.
- **Benchmark reproduction:** `workflow benchmark --id X` - one-click run and compare to reference.
- **Multi-objective optimization:** `workflow multi-optimize` - optimize across neutronics, safety, economics.
- **Physics-informed surrogates:** `physics_informed_surrogate_from_sweep()` with UQ and physics checks.
- **Serpent import:** Basic parsing of materials, surfaces, and cells for round-trip workflows.
- **MCNP converter:** Full MCNP export in Pro; Community delegates to Pro when installed.
- **Pro CLI commands:** `convert serpent/openmc/mcnp`, `workflow ml-export`, `report validation` (Pro features).
- **Pro CI job:** GitHub Actions job that installs Pro and runs `test_pro_integration.py`.
- **Workflow hooks:** `pre_export`, `post_sweep` hooks for Pro automation.
- **Pro Docker image:** `Dockerfile.pro` for licensed deployments.
- **API stability:** Pro section in `docs/API_STABILITY.md`; `CHANGELOG_PRO.md` for Pro releases.

### Changed
- **Docs:** `community_vs_pro.md` aligned with implementation (Serpent import, MCNP, tally viz status).

---

## [0.1.0] - 2026-02-XX

### Added
- **Converters:** OpenMCConverter (delegates to Community; Pro docs for tally viz), SerpentConverter (full export).
- **AI/surrogate:** `fit_surrogate`, `surrogate_from_sweep_results`, RBF/linear, BYOS (ONNX/TorchScript/pickle).
- **Validation report:** `SurrogateValidationReport`, `generate_validation_report`, PDF export with reportlab.
- **ML export:** `export_ml_dataset` for Parquet/HDF5.
- **Audit trail:** `record_ai_model` for AI model provenance.
- **Optional extras:** `[ai]`, `[reporting]`, `[ml]`, `[all]` in `smrforge-pro` package.
