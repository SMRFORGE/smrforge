# SMRForge Documentation Index

**Last Updated:** February 2026  
**Status:** Consolidated and reorganized — API reference and workflow docs updated

This document provides a comprehensive index of all SMRForge documentation files.

**Note:** Documentation has been consolidated and reorganized. Historical and session-specific documents are in [archive/](archive/README.md). See [Documentation Consolidation Plan](archive/DOCUMENTATION_CONSOLIDATION_PLAN_2026.md) for details.

---

## 📚 Core Documentation (Root)

### Essential Files
- **[README.md](../README.md)** - Main project overview and quick start
- **[CHANGELOG.md](../CHANGELOG.md)** - Version history and changes
- **[CONTRIBUTING.md](../CONTRIBUTING.md)** - Guidelines for contributing
- **[LICENSE](../LICENSE)** - License information

### Coverage & PyPI
- **[COVERAGE_TRACKING.md](../COVERAGE_TRACKING.md)** - **Source of truth** for test coverage tracking and path to 90%
- **[README_COVERAGE.md](../README_COVERAGE.md)** - Quick reference for coverage docs
- **[README_PYPI.md](../README_PYPI.md)** / **[PYPI_READINESS_CHECKLIST.md](../PYPI_READINESS_CHECKLIST.md)** - PyPI release notes and checklist

---

## 📖 User Guides (`guides/`)

### Getting Started
- **[Installation Guide](guides/installation.md)** - Installation instructions for all platforms
- **[Tutorial](guides/tutorial.md)** - Step-by-step tutorial for beginners
- **[Usage Guide](guides/usage.md)** - Usage guide with examples

### Additional Guides
- **[CLI Guide](guides/cli-guide.md)** - Command-line reference including workflow subcommands
- **[Complete Workflow Examples](guides/complete-workflow-examples.md)** - End-to-end Python and design-study examples
- **[Docker Guide](guides/docker.md)** - Docker usage and troubleshooting
- **[Help System](guides/help-system.md)** - Interactive help system documentation

---

## 🔧 Technical Documentation (`technical/`)

### Nuclear Data
- **[ENDF Documentation](technical/endf-documentation.md)** - Complete ENDF file usage guide
- **[Nuclear Data Backends](technical/nuclear-data-backends.md)** - Nuclear data backend alternatives
- **[ENDF Codebase Improvements](technical/endf-codebase-improvements.md)** - ENDF-related codebase improvements
- **[ENDF Improvements Implemented](technical/endf-improvements-implemented.md)** - Implemented ENDF improvements

### System Documentation
- **[Logging Usage](technical/logging-usage.md)** - Logging system usage
- **[Coupling Reduction](technical/coupling-reduction.md)** - Architecture and coupling reduction notes
- **[API Stability](API_STABILITY.md)** - Public API surface and deprecation policy (smrforge.api, workflows)
- **[Plugin Architecture](PLUGIN_ARCHITECTURE.md)** - Surrogate registry, hooks, AI integration
- **[Flux Weighting Limitation](FLUX_WEIGHTING_LIMITATION.md)** - Multi-group collapse assumptions

---

## 💻 Development Documentation (`development/`)

### Development Guidelines
- **[Code Style Guide](development/code-style.md)** - Code formatting, type hints, and style guide
- **[Type Hints Conventions](technical/type-hints-conventions.md)** - Type hint conventions and examples
- **[Release Process](development/release-process.md)** - Release procedures
- **[Testing and Coverage](development/testing-and-coverage.md)** - Testing documentation
- **[Coverage Exclusions](development/coverage-exclusions.md)** - Test coverage exclusions
- **[Memory and Performance Assessment](development/memory-and-performance-assessment.md)** - How to assess memory and CPU, where to optimize
- **[Performance and Benchmarking Assessment](development/performance-and-benchmarking-assessment.md)** - Plan vs. implementation status, profiling results, benchmark outcomes

---

## 🗺️ Roadmaps

**Roadmaps moved to SMRForge-Private (local docs, not in repo).** If you have access, see `SMRForge-Private/roadmaps/` for:
- CONSOLIDATED-ROADMAP.md (primary)
- development-roadmap.md, implementation-priority-analysis.md
- optimization-suggestions.md, cli-enhancement-plan.md

**Archived (in repo):** [next-steps](archive/roadmaps-superseded/next-steps.md), [next-work-options](archive/roadmaps-superseded/next-work-options.md), [NEXT-FEATURES](archive/roadmaps-superseded/NEXT-FEATURES.md) → `archive/roadmaps-superseded/`

---

## 📊 Status Documents (`status/`)

### Consolidated Summaries (CURRENT)
- **[Data Import: Complete Summary](status/data-import-complete-summary.md)** - **CURRENT** - Complete data import implementation summary (consolidates improvement, implementation, and optimization summaries)
- **[SMR Implementation: Complete Summary](status/smr-implementation-complete-summary.md)** - **CURRENT** - Complete SMR implementation summary (consolidates all SMR summaries)
- **[Test Coverage: Complete Summary](status/test-coverage-complete-summary.md)** - **CURRENT** - Complete test coverage summary (consolidates coverage summary, inventory, and plan)
- **[Capability Gaps Analysis](status/capability-gaps-analysis.md)** - **CURRENT** - Comprehensive capability gaps analysis (consolidates all gap analyses)

### Status Reports
- **[Feature Status](status/feature-status.md)** - Implementation status of all features
- **[Deployment Readiness Analysis](status/DEPLOYMENT_READINESS_ANALYSIS.md)** - Community/Pro deployment blockers
- **[Production Readiness Status](status/production-readiness-status.md)** - Production readiness assessment
- **[SMRForge Fact Sheet](status/smrforge-fact-sheet.md)** - Comprehensive feature overview
- **[Codebase Consistency Report](status/codebase-consistency-report.md)** - Codebase consistency analysis
- **[Pain Points Assessment](status/pain-points-assessment.md)** - Gap analysis and pain points (moved from root)

### Detailed Analysis Documents
- **[Data Import Comparison and Plan](status/data-import-comparison-and-improvement-plan.md)** - Detailed OpenMC vs SMRForge comparison
- **[SMR-Focused Gaps Analysis](status/smr-focused-gaps-analysis.md)** - Detailed SMR capability analysis
- **[OpenMC Visualization Gaps Analysis](status/openmc-visualization-gaps-analysis.md)** - Detailed visualization comparison
- **[OpenMC Visualization Implementation Summary](status/openmc-visualization-implementation-summary.md)** - Visualization implementation details
- **[GUI/UX Strategy Analysis](status/gui-ux-strategy-analysis.md)** - GUI/UX strategy and recommendations

### Archived Summaries (Consolidated)
- ~~`data-import-improvement-summary.md`~~ → Consolidated into `data-import-complete-summary.md`
- ~~`data-import-implementation-summary.md`~~ → Consolidated into `data-import-complete-summary.md`
- ~~`data-downloader-optimization-summary.md`~~ → Consolidated into `data-import-complete-summary.md`
- ~~`smr-implementation-summary.md`~~ → Consolidated into `smr-implementation-complete-summary.md`
- ~~`smr-gaps-implementation-summary.md`~~ → Consolidated into `smr-implementation-complete-summary.md`
- ~~`smr-implementation-coverage-summary.md`~~ → Consolidated into `smr-implementation-complete-summary.md`
- ~~`test-coverage-summary.md`~~ → Consolidated into `test-coverage-complete-summary.md`
- ~~`comprehensive-coverage-inventory.md`~~ → Consolidated into `test-coverage-complete-summary.md`
- ~~`coverage-completion-plan.md`~~ → Consolidated into `test-coverage-complete-summary.md`
- ~~`advanced-capabilities-gaps-analysis.md`~~ → Consolidated into `capability-gaps-analysis.md`
- ~~`missing-features-analysis.md`~~ → Consolidated into `capability-gaps-analysis.md`
- ~~`missing-reactor-types-analysis.md`~~ → Consolidated into `capability-gaps-analysis.md`

---

## 🔀 Workflows and Design Study

Design-of-experiments, parameter sweeps, sensitivity (OAT and Sobol), safety margins, scenario-based design, and design-space atlas. See the **API Reference** (Sphinx) for `smrforge.workflows`, `smrforge.validation.safety_report`, and `smrforge.visualization.design_study_plots`.

- **[CLI Guide → Workflow subcommands](guides/cli-guide.md#workflow-subcommands)** - `workflow design-point`, `safety-report`, `doe`, `pareto`, `sensitivity`, `sobol`, `design-study`, `scenario`, `atlas`, `surrogate`, `requirements-to-constraints`
- **[Complete Workflow Examples → Design study and workflow API](guides/complete-workflow-examples.md#design-study-and-workflow-api)** - Python examples: `get_design_point`, `safety_margin_report`, `run_scenario_design`, `build_atlas`

---

## 🚀 Implementation Summaries (`implementation/`)

### Recent Implementations
- **[Help System](implementation/help-system.md)** - Help system implementation
- **[Optimization](implementation/optimization.md)** - Performance optimizations
- **[Convenience Methods](implementation/convenience-methods.md)** - Convenience functions
- **[Visualization](implementation/visualization.md)** - 3D visualization implementation
- **[Mesh 3D](implementation/mesh-3d.md)** - 3D mesh support
- **[Photon Gamma Integration](implementation/photon-gamma-integration.md)** - Photon and gamma transport
- **[Thermal Scattering](implementation/thermal-scattering.md)** - Thermal scattering laws
- **[Burnup Solver](implementation/burnup-solver.md)** - Burnup solver implementation
- **[Fission Yields Decay](implementation/fission-yields-decay.md)** - Fission yields and decay data

### Complete Summaries
- **[Next Steps Complete](implementation/next-steps-complete.md)** - **CURRENT** - Comprehensive summary of all recent implementations (January 2026)
- **[Complete Summary](implementation/complete-summary.md)** - Photon/gamma integration summary (historical)
- **[Options 1 2 4 6](implementation/options-1-2-4-6.md)** - Options 1, 2, 4, 6 summary

See [Implementation Summaries Index](implementation/README.md) for a complete list.

---

## ✅ Validation Documents (`validation/`)

- **[Validation Summary](validation/validation-summary.md)** - Validation framework summary
- **[ENDF Workflow Validation](validation/endf-workflow-validation.md)** - ENDF workflow validation
- **[ENDF File Types Analysis](validation/endf-file-types-analysis.md)** - Analysis of ENDF-B-VIII.1 file types

---

## 📐 Visualization Documents

- **[Visualization Implementation](implementation/visualization.md)** - **CURRENT** - Visualization implementation summary
  - Historical assessments archived in `archive/`

---

## 📦 Archive (`docs/archive/`)

See **[archive/README.md](archive/README.md)** for the archive layout and subdirectories.

### Subdirectories (Jan 2026)
| Directory | Contents |
|-----------|----------|
| **[root-session/](archive/root-session/)** | One-off root docs (COVERAGE_RUN_*, TEST_*, EXCLUDED_FILES_*, etc.) |
| **[testing-session/](archive/testing-session/)** | Manual testing session notes, result templates (from `testing/`) |
| **[roadmaps-superseded/](archive/roadmaps-superseded/)** | next-steps, next-work-options, NEXT-FEATURES (→ CONSOLIDATED-ROADMAP) |
| **[technical-superseded/](archive/technical-superseded/)** | Redundant technical/coverage docs (→ OPTIMIZATION-STATUS-REPORT, etc.) |

### Historical Documents (flat archive)
- **[Phase 1–3 Completion Reports](archive/phase1-completion-report.md)** - Phase completion
- **[Documentation Consolidation Summary](archive/documentation-consolidation-summary.md)** - Consolidation history
- **[Coverage Improvements 2026-01](archive/coverage-improvements-2026-01.md)** - Coverage improvements (historical)
- **[Coverage Inventory (archived Jan 2026)](archive/coverage-inventory-archived-2026-01-29.md)** - Superseded by COVERAGE_TRACKING.md
- **[Feature Implementation Summary](archive/feature-implementation-summary.md)** - Historical implementation summary
- **[Visualization Readiness / Advanced Requirements](archive/visualization-readiness-assessment.md)** - Historical assessments

---

## 📝 Documentation Management

- **[Documentation Consolidation Plan](archive/DOCUMENTATION_CONSOLIDATION_PLAN_2026.md)** - Consolidation plan (January 2026)
- **[Documentation README](README.md)** - Documentation directory overview (in `docs/`)

---

## 📅 Document Update Policy

**All documentation files should include:**
- **Date:** Original creation date
- **Last Updated:** Most recent update date (format: Month Day, Year)

**When updating documents:**
1. Update the "Last Updated" field to the current date
2. Keep the original "Date" field unchanged
3. Document significant changes in the document or CHANGELOG.md

---

## 🔗 API Reference and Sphinx

### API Reference (Sphinx)
- **Single entry point:** Build Sphinx from `docs/`; the **API Reference** page lists all modules.
- **Core:** `smrforge.core`, `smrforge.neutronics`, `smrforge.thermal`, `smrforge.geometry`, `smrforge.visualization`, `smrforge.validation`, `smrforge.presets`, `smrforge.convenience`, `smrforge.api`, `smrforge.ai`
- **Workflows and design study:** `smrforge.workflows`, `smrforge.validation.constraints`, `smrforge.validation.safety_report`, `smrforge.validation.constraint_builder`, `smrforge.validation.requirements_parser`, `smrforge.visualization.design_study_plots`
- See `README.md` in `docs/` for build instructions (`sphinx-build -b html . _build/html`).

### Online Resources
- ReadTheDocs: [smrforge.readthedocs.io](https://smrforge.readthedocs.io)
- GitHub Pages: (if configured)

---

## 📊 Documentation Statistics

- **Total Documentation Files:** ~50+ markdown files
- **Core Documentation:** 4 files (root)
- **User Guides:** 5 files
- **Technical Documentation:** 6 files
- **Development Documentation:** 5 files
- **Roadmaps:** 5 files
- **Status Documents:** 6 files
- **Implementation Summaries:** 12+ active files
- **Validation Documents:** 3 files
- **Archive:** 10+ historical files

**Note:** Redundant and outdated documents have been archived. Current documents are clearly marked with **CURRENT** tags where applicable.

---

## 🎯 Quick Reference

### For New Users
1. Start with [README](../README.md)
2. Follow [Installation Guide](guides/installation.md)
3. Read [Tutorial](guides/tutorial.md)
4. Explore [Usage Guide](guides/usage.md) and [CLI Guide](guides/cli-guide.md)

### For Developers
1. Read [CONTRIBUTING](../CONTRIBUTING.md)
2. Follow [Code Style Guide](development/code-style.md)
3. Check SMRForge-Private/roadmaps/CONSOLIDATED-ROADMAP.md or development-roadmap.md (local)
4. Review [Feature Status](status/feature-status.md)
5. Use Sphinx **API Reference** (see above) for module-level docs

### For Contributors
1. Review [CONTRIBUTING](../CONTRIBUTING.md)
2. Check [Release Process](development/release-process.md)
3. See [CHANGELOG](../CHANGELOG.md) for recent changes

---

## 📝 Notes

- All dates in documentation use format: **Month Day, Year** (e.g., January 18, 2026)
- Documents are updated when features are implemented or information changes
- Historical implementation summaries are kept in `docs/archive/` for reference
- For the most current status, see [Feature Status](status/feature-status.md) and SMRForge-Private/roadmaps/CONSOLIDATED-ROADMAP.md (local)
- Documentation structure follows the consolidation plan in [Documentation Consolidation Plan](archive/DOCUMENTATION_CONSOLIDATION_PLAN_2026.md)
