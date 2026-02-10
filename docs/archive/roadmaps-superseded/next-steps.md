# SMRForge Next Steps (Consolidated)

**Last Updated:** January 25, 2026  
**Current Version:** 0.1.0 (Alpha)

This page is the **single source of truth for “what to do next”**.

## Quick links

- **Feature status**: `docs/status/feature-status.md`
- **Interactive “try every feature” notebooks**: `docs/guides/testing-notebooks.md` and `testing/notebooks/`
- **Testing + coverage**: `docs/development/testing-and-coverage.md`
- **Broader roadmap**: SMRForge-Private/roadmaps/development-roadmap.md (local)

## Current project health (last verified)

- **Automated tests**: \(4179 passed, 97 skipped\)
- **Coverage**: **76.7%**

## Next priorities (ordered)

1. **Docstrings + public API clarity**
   - Add/standardize examples on public entry points (CLI + convenience API).
2. **Documentation publishing**
   - Ensure Sphinx builds cleanly (Markdown enabled via MyST).
   - Keep the GitHub Pages workflow working and documented.
3. **Validation benchmark reference values**
   - The benchmarking framework exists; add real reference values and document provenance.
4. **User testing experience**
   - Keep `testing/test_*.py` as the source of truth.
   - Keep `testing/notebooks/*.ipynb` as thin wrappers that run scripts and show output inline.
5. **Optional dependencies / graceful degradation**
   - Tighten “optional dependency missing” behavior and docs (SALib, seaborn, pint, etc.).

## Historical documents

Older “next steps” and “next features” content was archived to reduce duplication:

- `docs/archive/next-steps-2026-01-25.md`
- `docs/archive/NEXT-FEATURES-2026-01-25.md`

