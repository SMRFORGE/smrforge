# Documentation Consolidation Plan - January 2026

**Date:** January 2026  
**Purpose:** Organize and consolidate documentation for better maintainability

---

## Current Issues

1. **Root directory cluttered** - Many markdown files in root that should be in `docs/`
2. **Redundant documentation** - Multiple files covering similar topics
3. **Outdated status docs** - Some documents need updating to reflect Phase 3 completion
4. **Scattered optimization docs** - Multiple optimization-related files that could be consolidated

---

## Consolidation Strategy

### 1. Archive Root-Level Implementation Summaries

**Move to `docs/archive/`:**
- `CLI_AND_TESTING_SUMMARY.md` → `docs/archive/cli-and-testing-summary.md`
- `ECONOMICS_MODULE_IMPLEMENTATION.md` → `docs/archive/economics-module-implementation.md`
- `IMPLEMENTATION_SUMMARY.md` → `docs/archive/implementation-summary.md`
- `MONTE_CARLO_OPTIMIZATION_SUMMARY.md` → `docs/archive/monte-carlo-optimization-summary.md`
- `STRUCTURAL_MECHANICS_AND_CONTROL_IMPLEMENTATION.md` → `docs/archive/structural-mechanics-control-implementation.md`
- `VERIFICATION_REPORT.md` → `docs/archive/verification-report.md`
- `PYRK_SMRFORGE_COMPARISON.md` → `docs/archive/pyrk-smrforge-comparison.md`

**Reason:** Historical implementation summaries, should be in archive

---

### 2. Consolidate Optimization Documentation

**Keep as primary:**
- `docs/technical/OPTIMIZATION-STATUS-REPORT.md` - Main status report
- `docs/technical/OPTIMIZATION-ROADMAP.md` - Roadmap
- `docs/technical/PHASE2-IMPLEMENTATION-SUMMARY.md` - Phase 2 summary
- `docs/technical/overcoming-openmc-performance.md` - Strategy document

**Archive duplicates:**
- `docs/technical/IMPLEMENTATION-SUMMARY.md` → `docs/archive/openmc-implementation-summary.md` (duplicate of OPTIMIZATION-STATUS-REPORT)
- `docs/technical/openmc-improvements-summary.md` → Merge into `OPTIMIZATION-STATUS-REPORT.md`
- `docs/technical/performance-optimization-summary.md` → Merge into `OPTIMIZATION-STATUS-REPORT.md`

**Keep as detailed reference:**
- `docs/technical/adaptive-sampling-implementation.md` - Detailed Phase 2 doc
- `docs/technical/hybrid-solver-implementation.md` - Detailed Phase 2 doc
- `docs/technical/jit-optimization-implemented.md` - Detailed Phase 1 doc
- `docs/technical/ALL-OPTIMIZATIONS-SUMMARY.md` - Comprehensive reference

---

### 3. Keep Root-Level Status Documents (Current)

**Keep in root:**
- `README.md` - Main readme (update with Phase 3)
- `CHANGELOG.md` - Version history
- `CONTRIBUTING.md` - Contribution guidelines
- `LICENSE` - License file

**Move to docs:**
- `SMR_PAIN_POINTS_ASSESSMENT.md` → `docs/status/pain-points-assessment.md`
- `DOCUMENTATION_INDEX.md` → `docs/README.md` (update existing docs/README.md)
- `DOCUMENTATION_REORGANIZATION_PLAN.md` → `docs/archive/reorganization-plan.md`

---

### 4. Archive Setup/Configuration Docs

**Move to `docs/archive/`:**
- `GITHUB_PAGES_SETUP.md` → `docs/archive/github-pages-setup.md`
- `README_READTHEDOCS.md` → `docs/archive/readthedocs-setup.md`
- `READTHEDOCS_SETUP_SUMMARY.md` → `docs/archive/readthedocs-setup-summary.md`

**Reason:** Historical setup documents, should be in archive

---

## New README Structure

Update `README.md` to:
1. Highlight Phase 3 completion (Implicit MC, Memory pooling, Memory-mapped files)
2. Simplify documentation links (point to consolidated docs)
3. Remove outdated status references
4. Add quick links to key docs

---

## Implementation Steps

1. ✅ Create consolidation plan
2. ⏳ Move files to archive
3. ⏳ Update README.md
4. ⏳ Update Docker files
5. ⏳ Create updated DOCUMENTATION_INDEX.md in docs/

---

**Status:** Plan created, ready for implementation
