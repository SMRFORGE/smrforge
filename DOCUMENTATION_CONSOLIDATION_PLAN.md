# Documentation Consolidation Plan

## Analysis Summary

**Total .md files found:** 41
**Recommended for consolidation/removal:** ~15-20 files

## Consolidation Strategy

### 1. Keep These Core Documentation Files ✅
- `README.md` - Main entry point (KEEP)
- `CHANGELOG.md` - Version history (KEEP)
- `CONTRIBUTING.md` - Contributor guide (KEEP, EXPAND)
- `LICENSE` - Legal (KEEP)
- `FEATURE_STATUS.md` - Feature status (KEEP)
- `RELEASE_PROCESS.md` - Release procedures (KEEP)

### 2. Consolidate Installation Guides → Single `INSTALLATION.md`
**Merge:**
- `INSTALLATION_GUIDE.md` (comprehensive)
- `UV_INSTALLATION.md` (uv-specific section)
- `PYTHON_COMPATIBILITY.md` (compatibility section)

**Action:** Create `INSTALLATION.md` merging all three, then delete originals.

### 3. Consolidate Git/GitHub Guides → Merge into CONTRIBUTING.md
**Merge into CONTRIBUTING.md:**
- `GITHUB_SETUP.md` (comprehensive)
- `QUICK_START_GITHUB.md` (quick reference section)

**Action:** Add GitHub setup section to CONTRIBUTING.md, delete both files.

### 4. Consolidate Docker Documentation → Single `DOCKER.md`
**Merge:**
- `DOCKER_USAGE.md` (main content)
- `DOCKER_TROUBLESHOOTING.md` (troubleshooting section)

**Action:** Merge troubleshooting into DOCKER_USAGE.md, rename to `DOCKER.md`, delete DOCKER_TROUBLESHOOTING.md.

### 5. Consolidate Code Style/Formatting → Keep `CODE_STYLE.md`
**Merge into CODE_STYLE.md:**
- `FORMATTING_INSTRUCTIONS.md` (redundant with CODE_STYLE.md)

**Action:** Delete FORMATTING_INSTRUCTIONS.md (CODE_STYLE.md is more comprehensive).

### 6. Consolidate Testing Documentation → Merge into CONTRIBUTING.md
**Merge into CONTRIBUTING.md:**
- `TEST_COVERAGE_INSTRUCTIONS.md` (testing section)
- `TESTING_IMPROVEMENTS.md` (historical, archive or remove)

**Action:** Add testing/coverage section to CONTRIBUTING.md, delete both files.

### 7. Archive/Remove Historical Status Documents
**These are historical status reports - can be archived or removed:**
- `CODE_QUALITY_COMPLETE.md` (status report - completed)
- `CODE_QUALITY_IMPROVEMENTS.md` (status report - completed)
- `CODE_REVIEW_REPORT.md` (historical review)
- `CODEBASE_CONSISTENCY_REVIEW.md` (recent status report)
- `FIXES_APPLIED.md` (historical fixes log)
- `OPTIMIZATIONS_APPLIED.md` (historical optimizations log)
- `PRODUCTION_READINESS_ASSESSMENT.md` (old assessment)
- `PRODUCTION_READINESS_STATUS.md` (newer assessment - KEEP THIS ONE)
- `CORE_NEUTRONICS_ADDED.md` (historical feature addition log)
- `MODULE_CLEANUP_SUMMARY.md` (historical cleanup log)
- `DUPLICATE_FILES.md` (historical cleanup - marked completed)
- `GITIGNORE_REVIEW.md` (recent status report)

**Action:** Move to `docs/archive/` or delete. Keep only `PRODUCTION_READINESS_STATUS.md` as the current assessment.

### 8. Consolidate API Documentation
**Keep/Consolidate:**
- `API_IMPROVEMENTS_PROPOSAL.md` (keep if active proposal)
- `API_IMPROVEMENTS_SUMMARY.md` (merge into proposal or remove if completed)

**Action:** Review and consolidate or remove if outdated.

### 9. Consolidate Usage/Examples Documentation
**Review and potentially merge:**
- `USAGE_SUMMARY.md` (check if redundant with README/examples)
- `EASY_USAGE_EXAMPLES.md` (merge into examples or README)

**Action:** Review content and consolidate into README or examples documentation.

### 10. Keep Specialized Documentation ✅
- `CUSTOM_ENDF_PARSER.md` - Technical documentation (KEEP)
- `NUCLEAR_DATA_BACKENDS.md` - Technical documentation (KEEP)
- `LOGGING_USAGE.md` - User guide (KEEP)
- `COUPLING_REDUCTION.md` - Architecture notes (KEEP or archive)
- `OPTIMIZATION_SUGGESTIONS.md` - Future work (KEEP or archive)
- `NEXT_STEPS.md` - Roadmap (KEEP)
- `RECOMMENDED_ADDITIONS.md` - Future work (KEEP or consolidate with NEXT_STEPS.md)

### 11. Documentation in docs/ Directory
- `docs/README.md` - Keep (Sphinx docs guide)
- `docs/GENERATE_API_DOCS.md` - Keep (Sphinx generation guide)

## Execution Order

1. Create consolidated files (INSTALLATION.md, DOCKER.md)
2. Merge content into CONTRIBUTING.md (GitHub setup, testing)
3. Delete redundant files
4. Archive historical documents (optional)
5. Update README.md with links to new consolidated docs

## Expected Reduction

**Before:** 41 .md files
**After:** ~25-30 .md files
**Reduction:** ~25-35% reduction in documentation files

