# Documentation Reorganization Plan

**Date:** January 1, 2026  
**Status:** Proposal

---

## Current Situation

- **50+ markdown files** in the root directory
- Mix of user guides, implementation summaries, status reports, and technical docs
- Difficult to navigate and find relevant documentation
- Root directory is cluttered

---

## Proposed Organization Structure

```
smrforge/
├── README.md                          # Main entry point (keep in root)
├── CHANGELOG.md                       # Version history (keep in root)
├── CONTRIBUTING.md                    # Contributor guide (keep in root)
├── LICENSE                            # Legal (keep in root)
│
├── docs/                              # Main documentation directory
│   ├── README.md                      # Documentation overview
│   │
│   ├── guides/                        # User guides
│   │   ├── installation.md
│   │   ├── tutorial.md
│   │   ├── usage.md
│   │   ├── docker.md
│   │   └── help-system.md
│   │
│   ├── technical/                    # Technical documentation
│   │   ├── endf-documentation.md
│   │   ├── nuclear-data-backends.md
│   │   ├── logging-usage.md
│   │   └── coupling-reduction.md
│   │
│   ├── development/                   # Development documentation
│   │   ├── code-style.md
│   │   ├── release-process.md
│   │   ├── testing-and-coverage.md
│   │   └── coverage-exclusions.md
│   │
│   ├── roadmaps/                      # Planning documents
│   │   ├── development-roadmap.md
│   │   ├── next-steps.md
│   │   ├── next-work-options.md
│   │   └── implementation-priority-analysis.md
│   │
│   ├── status/                        # Status and assessments
│   │   ├── feature-status.md
│   │   ├── production-readiness-status.md
│   │   ├── missing-features-analysis.md
│   │   └── test-coverage-summary.md
│   │
│   ├── implementation/                # Implementation summaries
│   │   ├── README.md                  # Index of implementations
│   │   ├── help-system.md
│   │   ├── optimization.md
│   │   ├── convenience-methods.md
│   │   ├── visualization.md
│   │   ├── mesh-3d.md
│   │   ├── photon-gamma-integration.md
│   │   ├── thermal-scattering.md
│   │   ├── burnup-solver.md
│   │   ├── fission-yields-decay.md
│   │   └── ...
│   │
│   ├── validation/                    # Validation documents
│   │   ├── validation-summary.md
│   │   ├── endf-workflow-validation.md
│   │   └── endf-file-types-analysis.md
│   │
│   ├── visualization/                 # Visualization docs
│   │   ├── visualization-readiness-assessment.md
│   │   ├── visualization-implementation-complete.md
│   │   └── advanced-visualization-requirements.md
│   │
│   ├── archive/                       # Historical/phase reports
│   │   ├── phase1-completion-report.md
│   │   ├── phase2-completion-report.md
│   │   ├── phase3-completion-report.md
│   │   ├── documentation-consolidation-summary.md
│   │   ├── documentation-update-2026-01-01.md
│   │   └── endf-improvements-implemented.md
│   │
│   └── sphinx/                        # Sphinx docs (existing)
│       └── (existing structure)
│
└── DOCUMENTATION_INDEX.md             # Master index (keep in root for visibility)
```

---

## File Mapping

### Keep in Root (Essential Files)
- `README.md` - Main entry point
- `CHANGELOG.md` - Version history
- `CONTRIBUTING.md` - Contributor guide
- `LICENSE` - Legal
- `DOCUMENTATION_INDEX.md` - Master index

### Move to `docs/guides/`
- `docs/guides/installation.md` → `docs/guides/installation.md`
- `docs/guides/tutorial.md` → `docs/guides/tutorial.md`
- `docs/guides/usage.md` → `docs/guides/usage.md`
- `docs/guides/docker.md` → `docs/guides/docker.md`
- `docs/guides/help-system.md` → `docs/guides/help-system.md`

### Move to `docs/technical/`
- `docs/technical/endf-documentation.md` → `docs/technical/endf-documentation.md`
- `docs/technical/nuclear-data-backends.md` → `docs/technical/nuclear-data-backends.md`
- `docs/technical/logging-usage.md` → `docs/technical/logging-usage.md`
- `docs/technical/coupling-reduction.md` → `docs/technical/coupling-reduction.md`
- `docs/technical/endf-codebase-improvements.md` → `docs/technical/endf-codebase-improvements.md`
- `docs/technical/endf-improvements-implemented.md` → `docs/technical/endf-improvements-implemented.md`

### Move to `docs/development/`
- `docs/development/code-style.md` → `docs/development/code-style.md`
- `docs/development/release-process.md` → `docs/development/release-process.md`
- `docs/development/testing-and-coverage.md` → `docs/development/testing-and-coverage.md`
- `docs/development/coverage-exclusions.md` → `docs/development/coverage-exclusions.md`
- `docs/development/coverage-inventory.md` → `docs/development/coverage-inventory.md`

### Move to `docs/roadmaps/`
- `docs/roadmaps/development-roadmap.md` → `docs/roadmaps/development-roadmap.md`
- `docs/roadmaps/next-steps.md` → `docs/roadmaps/next-steps.md`
- `docs/roadmaps/next-work-options.md` → `docs/roadmaps/next-work-options.md`
- `docs/roadmaps/implementation-priority-analysis.md` → `docs/roadmaps/implementation-priority-analysis.md`
- `docs/roadmaps/optimization-suggestions.md` → `docs/roadmaps/optimization-suggestions.md`

### Move to `docs/status/`
- `docs/status/feature-status.md` → `docs/status/feature-status.md`
- `docs/status/production-readiness-status.md` → `docs/status/production-readiness-status.md`
- `docs/status/missing-features-analysis.md` → `docs/status/missing-features-analysis.md`
- `docs/status/test-coverage-summary.md` → `docs/status/test-coverage-summary.md`
- `docs/status/smrforge-fact-sheet.md` → `docs/status/smrforge-fact-sheet.md`

### Move to `docs/implementation/`
- `docs/guides/help-system.md` → `docs/implementation/help-system.md`
- `docs/implementation/optimization.md` → `docs/implementation/optimization.md`
- `docs/implementation/convenience-methods.md` → `docs/implementation/convenience-methods.md`
- `docs/implementation/visualization.md` → `docs/implementation/visualization.md`
- `docs/implementation/mesh-3d.md` → `docs/implementation/mesh-3d.md`
- `docs/implementation/photon-gamma-integration.md` → `docs/implementation/photon-gamma-integration.md`
- `docs/implementation/thermal-scattering.md` → `docs/implementation/thermal-scattering.md`
- `docs/implementation/burnup-solver.md` → `docs/implementation/burnup-solver.md`
- `docs/implementation/fission-yields-decay.md` → `docs/implementation/fission-yields-decay.md`
- `docs/implementation/complete-summary.md` → `docs/implementation/complete-summary.md`
- `docs/implementation/status-high-medium.md` → `docs/implementation/status-high-medium.md`
- `docs/implementation/options-1-2-4-6.md` → `docs/implementation/options-1-2-4-6.md`
- `docs/implementation/feature-implementation-summary.md` → `docs/implementation/feature-implementation-summary.md`
- `docs/implementation/next-steps-complete.md` → `docs/implementation/next-steps-complete.md`

### Move to `docs/validation/`
- `docs/validation/validation-summary.md` → `docs/validation/validation-summary.md`
- `docs/validation/endf-workflow-validation.md` → `docs/validation/endf-workflow-validation.md`
- `docs/validation/endf-file-types-analysis.md` → `docs/validation/endf-file-types-analysis.md`

### Move to `docs/visualization/`
- `docs/visualization/readiness-assessment.md` → `docs/visualization/readiness-assessment.md`
- `docs/implementation/visualization.md` → `docs/visualization/implementation-complete.md`
- `docs/visualization/advanced-requirements.md` → `docs/visualization/advanced-requirements.md`

### Move to `docs/archive/`
- `docs/archive/phase1-completion-report.md` → `docs/archive/phase1-completion-report.md`
- `docs/archive/phase2-completion-report.md` → `docs/archive/phase2-completion-report.md`
- `docs/archive/phase3-completion-report.md` → `docs/archive/phase3-completion-report.md`
- `docs/archive/documentation-consolidation-summary.md` → `docs/archive/documentation-consolidation-summary.md`
- `docs/archive/documentation-update-2026-01-01.md` → `docs/archive/documentation-update-2026-01-01.md`

### Keep Sphinx Docs
- `docs/sphinx/` or keep existing `docs/` structure for Sphinx

---

## Benefits

1. **Clear Organization** - Related documents grouped together
2. **Easy Navigation** - Logical folder structure
3. **Reduced Clutter** - Root directory only has essential files
4. **Better Discoverability** - Users can find docs by category
5. **Maintainability** - Easier to update and maintain
6. **Scalability** - Easy to add new docs in appropriate folders

---

## Implementation Steps

### Option 1: Manual Reorganization (Recommended)
1. Create new directory structure
2. Move files to new locations
3. Update all internal links
4. Update `DOCUMENTATION_INDEX.md`
5. Update `README.md` links
6. Test all links
7. Commit changes

### Option 2: Scripted Reorganization
1. Create Python script to:
   - Create directory structure
   - Move files
   - Update links automatically
   - Generate new index

---

## Link Updates Required

After moving files, update links in:
- `README.md`
- `DOCUMENTATION_INDEX.md`
- All cross-referencing documents
- `CONTRIBUTING.md`
- Any other files with links

---

## Alternative: GitHub Wiki

Consider using GitHub Wiki for:
- User guides
- Tutorials
- How-to articles

Keep in repository:
- Technical documentation
- Implementation summaries
- Status reports
- Roadmaps

---

## Alternative: GitHub Pages

Use GitHub Pages to host:
- Sphinx documentation (already set up)
- User guides
- Tutorials

Keep in repository:
- Development docs
- Implementation summaries
- Status reports

---

## Recommendation

**Use the proposed directory structure** because:
1. ✅ Keeps all docs in repository (version controlled)
2. ✅ Works with GitHub's file viewer
3. ✅ Easy to navigate
4. ✅ Can still use GitHub Pages for Sphinx docs
5. ✅ Maintains git history

**Implementation Priority:**
1. High: Move guides, technical, and development docs
2. Medium: Move implementation summaries
3. Low: Move archive documents

---

## Next Steps

1. Review and approve this plan
2. Create directory structure
3. Move files (can be done incrementally)
4. Update links
5. Test all links
6. Update documentation index
7. Commit changes

