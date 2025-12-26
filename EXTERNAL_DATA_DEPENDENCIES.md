# External Data Dependencies for Testing

This document identifies modules that require external data, network access, or external dependencies for testing.

## Modules Requiring External Data

### 1. `smrforge/core/reactor_core.py` ⚠️ **HIGH DEPENDENCY**

**External Requirements:**
- **ENDF files**: Nuclear data files (Evaluated Nuclear Data File format)
- **Network access**: Downloads from IAEA Nuclear Data Services (`https://www-nds.iaea.org`)
- **Optional library**: SANDY (`pip install sandy`) - recommended for parsing ENDF files
- **Cache directory**: Uses `~/.smrforge/nucdata` for storing downloaded/processed data

**Key Classes/Methods:**
- `NuclearDataCache.get_cross_section()` - Downloads ENDF files if not cached
- `NuclearDataCache._ensure_endf_file()` - Downloads from IAEA if file missing
- `NuclearDataCache._fetch_and_cache()` - Requires SANDY or built-in parser
- `NuclearDataCache._get_endf_url()` - Constructs download URLs

**Current Test Strategy:**
- Tests use mocked/invalid nuclides to avoid actual downloads
- Tests verify error handling when files are missing
- Tests check URL construction without downloading
- Memory cache tests avoid external dependencies
- Some tests are skipped (`@pytest.mark.skip`) due to zarr API issues

**Coverage Impact:**
- **Current coverage: 38%** (172 lines uncovered)
- Many uncovered lines are in `_fetch_and_cache()`, `_ensure_endf_file()`, and parsing logic
- Would benefit from:
  - Mock ENDF files in `tests/data/` directory
  - `@pytest.fixture` providing sample ENDF data
  - Mocking `requests.get()` to avoid network calls
  - Pre-populated cache fixtures

---

### 2. `smrforge/core/endf_parser.py` ⚠️ **MEDIUM DEPENDENCY**

**External Requirements:**
- **ENDF files**: Requires actual ENDF file data to test parsing
- **File system**: Reads `.endf` files from disk

**Key Classes/Methods:**
- `ENDFEvaluation` - Parses ENDF files
- `ENDFCompatibility` - Compatibility layer for ENDF parsing
- `ReactionData` - Extracts reaction data from ENDF files

**Current Test Strategy:**
- Very limited testing (19% coverage, 142 lines uncovered)
- No test files found for this module specifically
- Would need sample ENDF files to test properly

**Coverage Impact:**
- **Current coverage: 19%** (142 lines uncovered)
- Would benefit from:
  - Sample ENDF files in `tests/data/` directory
  - Minimal valid ENDF files for testing
  - Mock ENDF file fixtures

---

### 3. `smrforge/utils/logo.py` ✅ **LOW DEPENDENCY**

**External Requirements:**
- **Logo file**: Package asset file (`smrforge/assets/logo.png` or similar)
- File must exist in package directory

**Key Functions:**
- `get_logo_path()` - Returns path to logo file
- `get_logo_data()` - Reads logo file as bytes

**Current Test Strategy:**
- Tests use `unittest.mock.patch` to mock file existence
- Tests skip if logo file doesn't exist (acceptable)
- **Coverage: 100%** - well tested

---

### 4. `smrforge/core/resonance_selfshield.py` ⚠️ **MEDIUM DEPENDENCY**

**External Requirements:**
- **Nuclear data**: References nuclear data for infinite dilution cross-sections
- Likely uses `NuclearDataCache` internally (which requires ENDF files)

**Coverage Impact:**
- **Current coverage: 27%** (137 lines uncovered)
- Low coverage likely due to nuclear data dependency

---

## Modules That Are Self-Contained (No External Data)

These modules generate their own test data or use fixtures:

- ✅ `smrforge/core/materials_database.py` - Uses built-in correlations (83% coverage)
- ✅ `smrforge/core/constants.py` - Hardcoded constants (86% coverage)
- ✅ `smrforge/validation/*` - Uses mock data fixtures (70-90% coverage)
- ✅ `smrforge/geometry/*` - Generates geometry programmatically (88% coverage)
- ✅ `smrforge/neutronics/solver.py` - Uses synthetic cross-section data (84% coverage)
- ✅ `smrforge/thermal/*` - Uses synthetic data (82% coverage)
- ✅ `smrforge/safety/*` - Uses synthetic parameters (91% coverage)

---

## Recommendations for Improving Test Coverage

### For `reactor_core.py` (38% → 80%+):

1. **Create sample ENDF files**:
   ```python
   # tests/data/sample_U235.endf
   # Minimal valid ENDF file for testing
   ```

2. **Mock network requests**:
   ```python
   @pytest.fixture
   def mock_endf_download(monkeypatch):
       def mock_get(url):
           # Return sample ENDF file content
           return MockResponse(sample_endf_content)
       monkeypatch.setattr("requests.get", mock_get)
   ```

3. **Pre-populated cache fixtures**:
   ```python
   @pytest.fixture
   def pre_populated_cache(temp_dir):
       cache = NuclearDataCache(cache_dir=temp_dir)
       # Pre-populate with test data
       return cache
   ```

4. **Mock SANDY library**:
   ```python
   @pytest.fixture
   def mock_sandy(monkeypatch):
       # Mock sandy.Endf6.from_file()
   ```

### For `endf_parser.py` (19% → 80%+):

1. **Sample ENDF files in `tests/data/`**:
   - `sample_U235.endf` - U-235 total cross-section
   - `sample_U238.endf` - U-238 capture cross-section
   - Minimal but valid ENDF files

2. **ENDF file fixtures**:
   ```python
   @pytest.fixture
   def sample_endf_file(test_data_dir):
       return test_data_dir / "sample_U235.endf"
   ```

---

## Test Fixtures Available

The test suite includes these fixtures in `tests/conftest.py`:

- `test_data_dir` - Directory for test data files (`tests/data/`)
- `temp_dir` - Temporary directory for test outputs
- `simple_xs_data` - Synthetic 2-group cross-section data
- `multi_group_xs_data` - Synthetic 4-group cross-section data
- `simple_geometry` - Synthetic geometry for testing

**Note**: `tests/data/` directory exists but is currently empty. This would be the ideal place for sample ENDF files.

---

## Summary

**Critical External Dependencies:**
1. `reactor_core.py` - Requires ENDF files + network access (38% coverage)
2. `endf_parser.py` - Requires ENDF files (19% coverage)
3. `resonance_selfshield.py` - Requires nuclear data (27% coverage)

**Action Items:**
1. Add sample ENDF files to `tests/data/` directory
2. Mock network requests in tests
3. Create fixtures for pre-populated caches
4. Add ENDF file fixtures for parser testing

**Estimated Coverage Gains:**
- `reactor_core.py`: 38% → 60-70% (with mocks/fixtures)
- `endf_parser.py`: 19% → 70-80% (with sample files)
- Overall: 66% → 70-72% (with these improvements)

---

## Implementation Status ✅

**Completed Improvements:**

1. ✅ **Mock Network Requests**: Added `mock_requests_get` fixture in `tests/conftest.py`
   - Mocks `requests.get()` to return mock ENDF file content
   - Avoids actual network calls during testing

2. ✅ **Mock ENDF Files**: Added `mock_endf_file` and `mock_endf_file_content` fixtures
   - Provides minimal valid ENDF file content for testing
   - Creates temporary ENDF files in test directories

3. ✅ **Mock SANDY Unavailability**: Added `mock_sandy_unavailable` fixture
   - Simulates SANDY library not being installed
   - Tests fallback to built-in parser

4. ✅ **New Tests Added**:
   - `test_ensure_endf_file_downloads_when_missing()` - Tests download path
   - `test_ensure_endf_file_uses_existing_file()` - Tests file reuse
   - `test_ensure_endf_file_invalid_nuclide()` - Tests error handling
   - `test_fetch_and_cache_with_builtin_parser()` - Tests parser fallback
   - `test_simple_endf_parse_basic()` - Tests simple parser
   - `test_endf_evaluation_initialization_*()` - Tests ENDF parser initialization
   - `test_endf_compatibility_*()` - Tests compatibility layer

**Current Coverage:**
- `reactor_core.py`: **49%** (improved from 38%, +11 percentage points)
- `endf_parser.py`: **40%** (improved from 19%, +21 percentage points!)
- **Overall coverage**: **67%** (improved from 66%, +1 percentage point)

**All new tests passing**: ✅ 35 passed, 5 skipped (pre-existing skips)

