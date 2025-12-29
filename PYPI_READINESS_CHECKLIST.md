# PyPI Release Readiness Checklist

This checklist ensures SMRForge is ready for publication on PyPI.

## ✅ Package Structure

- [x] **Version Number**: `0.1.0` in `smrforge/__version__.py` and `setup.py`
- [x] **Package Name**: `smrforge` (lowercase, no dashes, matches PyPI naming)
- [x] **Package Discovery**: `find_packages()` correctly configured
- [x] **MANIFEST.in**: Includes README.md, LICENSE, docs/logo images, pyproject.toml
- [x] **LICENSE**: MIT License file present
- [x] **README.md**: Comprehensive with installation, usage, examples

## ⚠️ Required Updates (Before Publishing)

### 1. Author Contact Information

- [ ] **ACTION REQUIRED**: Update `author_email` in `setup.py`
  - Current: `"your.email@example.com"`
  - Should be: Your actual email address
  - Location: `setup.py` line 16

- [ ] **ACTION REQUIRED**: Update contact info in `README.md`
  - Current: `your.email@example.com` and `Your Name`
  - Should be: Actual contact information
  - Locations: Lines 162 (citation) and 171 (contact section)

### 2. Optional Dependencies

- [x] **Fixed**: Added `SALib` and `seaborn` to `extras_require["uq"]`
- [x] **Fixed**: Included in `extras_require["all"]`

## ✅ Dependencies

- [x] **Core Dependencies**: All required packages listed with version constraints
- [x] **Optional Dependencies**: Organized in `extras_require`:
  - `dev`: Development tools (pytest, black, flake8, mypy)
  - `docs`: Documentation tools (sphinx, themes)
  - `viz`: Visualization (plotly, dash)
  - `nuclear-data`: Nuclear data backends (sandy)
  - `uq`: Uncertainty quantification (SALib, seaborn) - **NEWLY ADDED**
  - `all`: All optional dependencies
- [x] **Python Version**: `python_requires=">=3.8"` specified
- [x] **Version Constraints**: Reasonable minimum versions specified

## ✅ Metadata

- [x] **Description**: Clear and concise
- [x] **Long Description**: README.md included with proper content type
- [x] **URL**: GitHub repository URL correct
- [x] **Project URLs**: Bug reports, source, documentation links present
- [x] **Keywords**: Relevant keywords for discoverability
- [x] **Classifiers**: 
  - Development status (Alpha)
  - Intended audience (Science/Research)
  - Topic (Scientific/Engineering/Physics)
  - License (MIT)
  - Python versions (3.8-3.12)
  - OS Independent

## ✅ Documentation

- [x] **README.md**: 
  - Installation instructions
  - Quick start examples
  - Feature overview
  - Links to detailed docs
  - Examples directory mentioned
  - Testing instructions
  - Contributing guidelines
  - License information
  - Citation format (needs name update)

- [x] **CHANGELOG.md**: 
  - Well-structured with version history
  - Unreleased section documented
  - Version 0.1.0 entry present

- [x] **API Documentation**: 
  - Sphinx structure in place
  - API reference files generated
  - Examples documented

- [x] **Docstrings**: 
  - Comprehensive docstrings in code
  - Google/NumPy style docstrings
  - Examples in docstrings where appropriate

## ✅ Code Quality

- [x] **Tests**: Comprehensive test suite
- [x] **Test Coverage**: Good coverage across modules
- [x] **Code Formatting**: Black configuration in pyproject.toml
- [x] **Import Sorting**: isort configuration in pyproject.toml
- [x] **Type Hints**: Some type hints present (mypy configuration available)

## ✅ Build Configuration

- [x] **setup.py**: Properly configured
- [x] **pyproject.toml**: Build system configuration present
- [x] **Version Synchronization**: `__version__.py` and `setup.py` match

## 🔍 Pre-Publication Testing

Before publishing to PyPI, test the following:

### 1. Build the Package

```bash
# Install build tools
pip install build twine

# Build source and wheel distributions
python -m build

# Verify contents of distributions
tar -tzf dist/smrforge-0.1.0.tar.gz | head -20
unzip -l dist/smrforge-0.1.0-py3-none-any.whl | head -20
```

### 2. Check Package Metadata

```bash
# Check metadata
python -m twine check dist/*
```

### 3. Test Installation

```bash
# Test installation from local wheel
pip install dist/smrforge-0.1.0-py3-none-any.whl

# Test installation from source
pip install dist/smrforge-0.1.0.tar.gz

# Verify import
python -c "import smrforge; print(smrforge.__version__)"

# Test optional dependencies
pip install smrforge[uq]
python -c "from smrforge.uncertainty.uq import SensitivityAnalysis; print('UQ works!')"
```

### 4. Test in Clean Environment

```bash
# Create clean virtual environment
python -m venv test_env
source test_env/bin/activate  # Windows: test_env\Scripts\activate

# Install from PyPI (test upload)
pip install smrforge

# Or test with TestPyPI first
pip install -i https://test.pypi.org/simple/ smrforge
```

## 📦 PyPI Publishing Steps

1. **Update Contact Information** (REQUIRED)
   - Edit `setup.py`: Update `author_email`
   - Edit `README.md`: Update citation and contact sections

2. **Final Version Check**
   - Ensure version in `smrforge/__version__.py` matches `setup.py`
   - Update CHANGELOG.md with release date

3. **Build Distributions**
   ```bash
   python -m build
   ```

4. **Check Distributions**
   ```bash
   python -m twine check dist/*
   ```

5. **Test Upload to TestPyPI** (Recommended)
   ```bash
   python -m twine upload --repository testpypi dist/*
   # Test installation: pip install -i https://test.pypi.org/simple/ smrforge
   ```

6. **Upload to PyPI**
   ```bash
   python -m twine upload dist/*
   ```

7. **Verify Installation**
   ```bash
   pip install smrforge
   python -c "import smrforge; print(smrforge.__version__)"
   ```

## 🔗 Post-Publication

After successful publication:

- [ ] Create GitHub release tag matching version
- [ ] Update README.md installation instructions to show PyPI option
- [ ] Verify package appears on PyPI: https://pypi.org/project/smrforge/
- [ ] Test installation from PyPI in clean environment
- [ ] Update any documentation that references installation methods

## 📝 Notes

- **Development Status**: Currently "Alpha" - appropriate for 0.1.0 release
- **Optional Dependencies**: SALib and seaborn are optional (UQ features work without them but with reduced functionality)
- **License**: MIT License - confirmed
- **Python Support**: 3.8+ confirmed in setup.py

## ❌ Known Issues / Limitations

- Some modules are stubs (fuel, optimization, control, economics) - clearly documented
- Monte Carlo and transport solvers are experimental - clearly documented
- Visualization module exists but some features may be experimental - documented

These are acceptable for an alpha release (0.1.0) as long as they're clearly documented, which they are.

## ✅ Summary

**Status**: Ready for PyPI publication after updating contact information

**Required Actions**:
1. Update `author_email` in `setup.py`
2. Update contact info in `README.md` (citation and contact sections)

**Optional but Recommended**:
- Test build locally
- Upload to TestPyPI first for verification
- Create GitHub release tag after successful publication

