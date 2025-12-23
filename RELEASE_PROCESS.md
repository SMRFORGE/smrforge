# Release Process

This document outlines the release process for SMRForge.

## Version Numbering

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR.MINOR.PATCH** (e.g., 1.2.3)
- **MAJOR**: Breaking changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

## Pre-Release Checklist

Before creating a release:

### 1. Code Quality
- [ ] All tests pass: `pytest`
- [ ] Test coverage ≥ 80% on critical modules: `pytest --cov=smrforge`
- [ ] Code formatted: `black smrforge/ tests/`
- [ ] Imports sorted: `isort smrforge/ tests/`
- [ ] Type checking: `mypy smrforge/` (may have some ignores)
- [ ] Linting passes: `flake8 smrforge/`

### 2. Documentation
- [ ] CHANGELOG.md updated with release notes
- [ ] README.md up to date
- [ ] API documentation generated (if applicable)
- [ ] Examples work correctly

### 3. Version Updates
- [ ] Update version in `smrforge/__version__.py`
- [ ] Update version in `setup.py` (if different from __version__.py)
- [ ] Update any version references in documentation

### 4. Testing
- [ ] Run full test suite
- [ ] Test installation: `pip install -e .`
- [ ] Test in clean environment (or Docker)
- [ ] Verify examples run correctly

### 5. Git
- [ ] All changes committed
- [ ] Branch is up to date with main
- [ ] No merge conflicts

## Release Steps

### For Patch/Mino Releases

1. **Update version:**
   ```bash
   # Edit smrforge/__version__.py
   __version__ = "0.1.1"  # Increment appropriately
   ```

2. **Update CHANGELOG.md:**
   ```markdown
   ## [0.1.1] - 2024-12-22
   
   ### Fixed
   - Fix bug description
   ```

3. **Commit version change:**
   ```bash
   git add smrforge/__version__.py CHANGELOG.md
   git commit -m "Bump version to 0.1.1"
   ```

4. **Create git tag:**
   ```bash
   git tag -a v0.1.1 -m "Release version 0.1.1"
   git push origin main --tags
   ```

5. **Create GitHub Release:**
   - Go to GitHub Releases
   - Click "Draft a new release"
   - Select tag: `v0.1.1`
   - Title: `Version 0.1.1`
   - Copy relevant section from CHANGELOG.md
   - Publish release

### For Major Releases

Major releases should follow the same steps but with additional considerations:

1. **Breaking changes documentation:**
   - Document all breaking changes in CHANGELOG.md
   - Provide migration guide if significant

2. **Deprecation warnings:**
   - Deprecated features should have been warned in previous releases
   - Remove deprecated code in major releases

3. **Announcement:**
   - Consider blog post or announcement
   - Notify users of breaking changes

## Post-Release

After creating a release:

1. **Verify installation:**
   ```bash
   pip install smrforge==0.1.1
   python -c "import smrforge; print(smrforge.__version__)"
   ```

2. **Update development version:**
   - In `smrforge/__version__.py`, update to next dev version:
     ```python
     __version__ = "0.1.2.dev0"  # Next version + .dev0
     ```

3. **Update CHANGELOG.md:**
   - Add new [Unreleased] section at top
   - Move completed items to release section

4. **Communication:**
   - Update any relevant documentation
   - Notify users if significant changes

## Release Types

### Alpha Release (0.1.0a1)
- Early development versions
- May have incomplete features
- Not recommended for production

### Beta Release (0.2.0b1)
- Feature complete
- Testing phase
- API may still change

### Release Candidate (1.0.0rc1)
- Final testing before production
- No new features
- Only bug fixes

### Production Release (1.0.0)
- Stable release
- Production ready
- API stable

## Automation

### GitHub Actions

The CI/CD pipeline automatically:
- Runs tests on push/PR
- Checks code formatting
- Validates package build

Future enhancements:
- Auto-generate release notes from PRs
- Auto-version based on commits
- Automated PyPI publishing (if desired)

### Manual Steps

Currently, releases require manual steps:
1. Version bump
2. CHANGELOG update
3. Tag creation
4. GitHub release creation

These could be automated with release scripts in the future.

## Version History

See CHANGELOG.md for detailed version history.

## Release Schedule

We do not have a fixed release schedule. Releases are made when:
- Significant features are added
- Critical bugs are fixed
- Enough changes accumulate for a minor release

For production releases (1.0.0+), we will be more deliberate about:
- Extended testing period
- User feedback incorporation
- Documentation completeness

## Questions?

If you have questions about the release process:
- Open an issue
- Check existing issues
- Review CHANGELOG.md for examples

