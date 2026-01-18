# Release Checklist

**Last Updated:** January 18, 2026  
**Purpose:** Standard checklist for SMRForge releases

---

## Pre-Release Checklist

### Code Quality ✅
- [ ] All tests passing (`pytest`)
- [ ] Test coverage ≥ 80% (`pytest --cov=smrforge --cov-report=html`)
- [ ] No linting errors (`black`, `isort`, `flake8`, `mypy`)
- [ ] Code review completed (if applicable)
- [ ] Documentation updated

### Documentation ✅
- [ ] `CHANGELOG.md` updated with new version
- [ ] `README.md` updated (if needed)
- [ ] API documentation regenerated (`docs/`)
- [ ] All docstrings reviewed
- [ ] Examples updated (if API changed)

### Dependencies ✅
- [ ] Dependencies reviewed and updated (if needed)
- [ ] `requirements.txt` and `requirements-dev.txt` updated
- [ ] No security vulnerabilities (check `pip-audit` or `safety`)
- [ ] Version constraints appropriate (>= vs ==)

### Versioning ✅
- [ ] Version number updated in `smrforge/__version__.py`
- [ ] Version follows [Semantic Versioning](https://semver.org/)
  - **MAJOR** (x.0.0): Breaking changes
  - **MINOR** (0.x.0): New features, backward compatible
  - **PATCH** (0.0.x): Bug fixes, backward compatible

### Testing ✅
- [ ] All unit tests passing
- [ ] Integration tests passing
- [ ] Manual testing on target platforms (Linux, Windows, macOS)
- [ ] Performance regression tests passing (if applicable)

---

## Release Steps

### 1. Update Version

```bash
# Edit smrforge/__version__.py
__version__ = "0.1.1"  # Update version number
```

### 2. Update CHANGELOG.md

```bash
# Edit CHANGELOG.md
# Move items from [Unreleased] to [0.1.1] - YYYY-MM-DD
# Update [Unreleased] header
```

### 3. Commit Release

```bash
git add smrforge/__version__.py CHANGELOG.md
git commit -m "Bump version to 0.1.1"
```

### 4. Create Git Tag

```bash
# Annotated tag (recommended)
git tag -a v0.1.1 -m "Release version 0.1.1"

# Or lightweight tag
git tag v0.1.1
```

### 5. Push Changes and Tags

```bash
git push origin main
git push origin v0.1.1
```

### 6. Create GitHub Release (Optional)

1. Go to GitHub → Releases → Draft a new release
2. Tag: `v0.1.1`
3. Title: `SMRForge 0.1.1`
4. Description: Copy from CHANGELOG.md for this version
5. Attach release assets (if applicable)
6. Publish release

### 7. Publish to PyPI (When Ready)

```bash
# Build distribution
python -m build

# Test upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# If successful, upload to PyPI
python -m twine upload dist/*
```

---

## Post-Release Checklist

- [ ] Verify GitHub release created (if applicable)
- [ ] Verify PyPI package updated (if published)
- [ ] Update documentation URLs (if needed)
- [ ] Announce release (if applicable)
- [ ] Monitor for issues

---

## Version Tagging Conventions

**Format:** `vMAJOR.MINOR.PATCH`

**Examples:**
- `v0.1.0` - First release
- `v0.1.1` - Patch release (bug fixes)
- `v0.2.0` - Minor release (new features)
- `v1.0.0` - Major release (production ready)

**Tagging Best Practices:**
- Use annotated tags (`-a` flag) for important releases
- Tag message should describe release
- Push tags explicitly: `git push origin <tag-name>`

---

## Semantic Versioning Guidelines

### MAJOR Version (x.0.0)
- Breaking API changes
- Removing deprecated features
- Significant architecture changes

### MINOR Version (0.x.0)
- New features (backward compatible)
- New modules or capabilities
- Enhanced functionality

### PATCH Version (0.0.x)
- Bug fixes
- Documentation improvements
- Performance improvements (non-breaking)
- Security patches

---

## Release Frequency

**Current Stage:** Alpha (0.1.x)
- **Recommended:** Monthly or as-needed
- **Priority:** Stability and bug fixes

**Beta Stage (0.x.0):**
- **Recommended:** Bi-weekly or monthly
- **Priority:** Feature completion and stability

**Production (1.0.0+):**
- **Recommended:** Quarterly or as-needed
- **Priority:** Stability and security

---

## Emergency Release Process

For critical security or bug fixes:

1. Create hotfix branch: `git checkout -b hotfix/v0.1.1`
2. Fix issue
3. Update version (PATCH increment)
4. Update CHANGELOG.md
5. Tag and release (same process as above)
6. Merge hotfix to main

---

## Resources

- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [Git Tagging](https://git-scm.com/book/en/v2/Git-Basics-Tagging)
- [PyPI Publishing](https://packaging.python.org/tutorials/packaging-projects/)

---

**Status:** ✅ Release checklist documented  
**Last Updated:** January 18, 2026
