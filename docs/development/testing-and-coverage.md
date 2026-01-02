# Testing and Coverage Guide

**Last Updated**: 2025  
**Current Overall Coverage**: 67%  
**Target Coverage**: 75-80% for all modules

This document consolidates information about test coverage, external data dependencies, and strategies for improving coverage.

---

## Table of Contents

1. [Current Coverage Status](#current-coverage-status)
2. [Modules Requiring External Data](#modules-requiring-external-data)
3. [Coverage Completion Roadmap](#coverage-completion-roadmap)
4. [Priority Tasks](#priority-tasks)
5. [Implementation Strategy](#implementation-strategy)

---

## Current Coverage Status

### Overall Coverage
- **Current**: 67% overall
- **Target**: 75-80% for all modules
- **Critical Modules Status**:
  - `reactor_core.py`: 49% (target: 75-80%)
  - `endf_parser.py`: 40% (target: 75-80%)

### Module Coverage Summary

| Module | Current | Target | Gap | Status |
|--------|---------|--------|-----|--------|
| `reactor_core.py` | 49% | 75-80% | +26-31% | 🔴 Needs Work |
| `endf_parser.py` | 40% | 75-80% | +35-40% | 🔴 Needs Work |
| `resonance_selfshield.py` | 27% | 75-80% | +48-53% | 🔴 Needs Work |
| `materials_database.py` | 79% | 80%+ | +1% | ✅ Near Target |
| `constants.py` | 86% | 80%+ | ✅ | ✅ Complete |
| `validation/*` | 70-90% | 80%+ | ✅ | ✅ Complete |
| `geometry/*` | 88% | 80%+ | ✅ | ✅ Complete |
| `neutronics/solver.py` | 84% | 80%+ | ✅ | ✅ Complete |
| `thermal/*` | 82% | 80%+ | ✅ | ✅ Complete |
| `safety/*` | 91% | 80%+ | ✅ | ✅ Complete |

---

## Modules Requiring External Data

### 1. `smrforge/core/reactor_core.py` ⚠️ **HIGH DEPENDENCY**

**Current Coverage**: 49% (142 lines uncovered)

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
- ✅ Mock network requests (`mock_requests_get` fixture)
- ✅ Mock ENDF file content (`mock_endf_file_content` fixture)
- ✅ Mock SANDY unavailability (`mock_sandy_unavailable` fixture)
- ✅ Pre-populated cache fixtures
- ⚠️ Some tests skipped due to zarr API issues

**Uncovered Line Ranges:**
- **106-116**: Zarr cache retrieval path
- **134-157**: SANDY backend parsing in `_fetch_and_cache`
- **178-198**: ENDF parser backend in `_fetch_and_cache`
- **208-221**: Simple parser backend in `_fetch_and_cache`
- **249-254**: Zarr cache storage (`_save_to_cache`)
- **285-341**: Full `_simple_endf_parse` implementation (57 lines)
- **436-466**: `CrossSectionTable.generate_multigroup` (31 lines)
- **480-504**: `CrossSectionTable._collapse_to_multigroup` (Numba, bug fix needed)

---

### 2. `smrforge/core/endf_parser.py` ⚠️ **MEDIUM DEPENDENCY**

**Current Coverage**: 40% (105 lines uncovered)

**External Requirements:**
- **ENDF files**: Requires actual ENDF file data to test parsing
- **File system**: Reads `.endf` files from disk

**Key Classes/Methods:**
- `ENDFEvaluation` - Parses ENDF files
- `ENDFCompatibility` - Compatibility layer for ENDF parsing
- `ReactionData` - Extracts reaction data from ENDF files

**Current Test Strategy:**
- ✅ Mock ENDF file fixtures
- ✅ Basic initialization tests
- ⚠️ Limited parsing tests (needs realistic mock files)

**Uncovered Line Ranges:**
- **38-49**: `ReactionData.interpolate` method (12 lines)
- **85-87**: `ENDFEvaluation.__getitem__` KeyError path
- **97-112**: `ENDFEvaluation.to_polars` method
- **225-321**: `_parse_mf3_section` full implementation (97 lines - **LARGEST GAP!**)
- **326-345**: `_mt_to_reaction_name` method (20 lines)
- **374-392**: `ENDFCompatibility.__getitem__` ReactionWrapper creation

---

### 3. `smrforge/core/resonance_selfshield.py` ⚠️ **MEDIUM DEPENDENCY**

**Current Coverage**: 27% (137 lines uncovered)

**External Requirements:**
- **Nuclear data**: References nuclear data for infinite dilution cross-sections
- Likely uses `NuclearDataCache` internally (which requires ENDF files)

**Status**: Low priority - depends on improvements to `reactor_core.py`

---

## Coverage Completion Roadmap

### Phase 1: Foundation (1-2 days) 🔴 CRITICAL

**Priority Tasks:**

1. **Create Realistic Mock ENDF Files** (HIGHEST PRIORITY)
   - **Location**: `tests/data/sample_U235.endf`, `sample_U238.endf`
   - **Requirements**:
     - Valid ENDF-6 format structure
     - Header section (MF=1, MT=451) with Z/A metadata
     - Cross-section sections (MF=3) with multiple MT numbers:
       - MT=1 (total)
       - MT=2 (elastic)
       - MT=18 (fission)
       - MT=102 (capture)
     - Proper ENDF format: 80-char lines, 6E11.0 data format
   - **Impact**: Unlocks 97+ lines in `_parse_mf3_section` (~55% of endf_parser gap)
   - **Estimated coverage gain**: +20-30% for endf_parser, +10-15% for reactor_core

2. **Fix Zarr API Usage in `_save_to_cache`** (BLOCKING)
   - **Location**: `smrforge/core/reactor_core.py:249-254`
   - **Issue**: Need to verify if zarr API requires explicit `shape` parameter
   - **Tests Blocked**: 
     - `test_get_cross_section_zarr_cache_hit` (line 466)
     - `test_save_to_cache` (line 506)
   - **Status**: Tests currently skipped with `@pytest.mark.skip`
   - **Estimated coverage gain**: +5-10%

### Phase 2: reactor_core.py Testing (3-4 days) 🟡 HIGH PRIORITY

3. **Test `_simple_endf_parse` Fully**
   - **Location**: `smrforge/core/reactor_core.py:285-341` (57 lines)
   - **Dependencies**: Mock ENDF files (task #1)
   - **Estimated coverage gain**: +21%

4. **Test `generate_multigroup`**
   - **Location**: `smrforge/core/reactor_core.py:436-466` (31 lines)
   - **Dependencies**: Pre-populated cache
   - **Estimated coverage gain**: +11%

5. **Test `_fetch_and_cache` Success Paths**
   - **Location**: `smrforge/core/reactor_core.py:134-221` (multiple sections)
   - **Dependencies**: Mock ENDF files, mocked SANDY
   - **Estimated coverage gain**: +10-15%

6. **Test Zarr Cache Retrieval**
   - **Location**: `smrforge/core/reactor_core.py:106-116`
   - **Dependencies**: Fix zarr API (task #2)
   - **Estimated coverage gain**: +4%

### Phase 3: endf_parser.py Testing (4-5 days) 🟡 HIGH PRIORITY

7. **Test `_parse_mf3_section` Fully** (LARGEST GAP)
   - **Location**: `smrforge/core/endf_parser.py:225-321` (97 lines)
   - **Dependencies**: Mock ENDF files (task #1)
   - **What to test**:
     - Data extraction from ENDF format
     - Energy/XS array construction
     - Sorting and deduplication
     - Multiple reaction types
   - **Estimated coverage gain**: +55% for endf_parser

8. **Test `ENDFEvaluation` Parsing Methods**
   - **Location**: `smrforge/core/endf_parser.py:154-321`
   - **Dependencies**: Mock ENDF files
   - **What to test**:
     - `_parse_header` (154-191): Metadata extraction
     - `_parse_file` (143-152): Full parsing workflow
     - `_parse_mf3` (176-214): Cross-section section parsing
   - **Estimated coverage gain**: +25-30%

9. **Test `ReactionData.interpolate`**
   - **Location**: `smrforge/core/endf_parser.py:38-49` (12 lines)
   - **Estimated coverage gain**: +7%

10. **Test `ENDFCompatibility` Wrapper Methods**
    - **Location**: `smrforge/core/endf_parser.py:167-172, 374-392`
    - **Estimated coverage gain**: +14%

### Phase 4: Integration & Polish (1-2 days) 🟢 MEDIUM PRIORITY

11. **Fix and Test `_collapse_to_multigroup`**
    - **Location**: `smrforge/core/reactor_core.py:480-504`
    - **Issue**: Known bug with `np.diff` in parallel context
    - **Status**: Tests currently skipped
    - **Estimated coverage gain**: +9%

12. **Test Integration Between Modules**
    - Test end-to-end workflows
    - Verify data flow between reactor_core and endf_parser

13. **Add Edge Case Tests**
    - Error handling
    - Boundary conditions
    - Invalid input handling

---

## Priority Tasks Summary

### 🔴 CRITICAL (Blocks significant coverage)

1. **Create Realistic Mock ENDF Files** 
   - Unlocks 97+ lines in `_parse_mf3_section`
   - Estimated: +20-30% for endf_parser, +10-15% for reactor_core

2. **Fix Zarr API Usage**
   - Unblocks zarr cache tests
   - Estimated: +5-10%

### 🟡 HIGH PRIORITY (Major coverage improvements)

3. **Test `_parse_mf3_section` Fully** (97 lines - largest gap!)
   - Estimated: +55% for endf_parser

4. **Test `_simple_endf_parse` Fully** (57 lines)
   - Estimated: +21% for reactor_core

5. **Test `generate_multigroup`** (31 lines)
   - Estimated: +11% for reactor_core

6. **Test `_fetch_and_cache` Success Paths**
   - Estimated: +10-15% for reactor_core

7. **Test `ENDFEvaluation` Parsing Methods**
   - Estimated: +25-30% for endf_parser

### 🟢 MEDIUM/LOW PRIORITY (Incremental improvements)

8. Test `ReactionData.interpolate` (+7%)
9. Test `ENDFCompatibility` wrapper methods (+14%)
10. Test zarr cache retrieval (+4%)
11. Fix `_collapse_to_multigroup` bug (+9%)
12. Test `_doppler_broaden` (+3%)
13. Test `_mt_to_reaction_name` (+11%)

---

## Implementation Strategy

### Test Fixtures Available

The test suite includes these fixtures in `tests/conftest.py`:

- ✅ `mock_endf_file_content` - Minimal valid ENDF file content
- ✅ `mock_endf_file` - Creates temporary ENDF files
- ✅ `mock_requests_get` - Mocks network requests
- ✅ `mock_sandy_unavailable` - Simulates SANDY not installed
- ✅ `pre_populated_cache` - Pre-loaded cache for testing
- ✅ `temp_dir` - Temporary directory for test outputs
- ✅ `simple_xs_data` - Synthetic 2-group cross-section data

### Mock ENDF File Requirements

To create realistic mock ENDF files, follow these guidelines:

1. **ENDF-6 Format Structure**:
   - 80-character lines
   - Control records: Columns 70-72 = MF, 72-75 = MT
   - Data records: 6E11.0 format (6 values per line, 11 chars each)

2. **Required Sections**:
   - **Header (MF=1, MT=451)**: Evaluation information with Z/A metadata
   - **Cross-sections (MF=3)**: 
     - MT=1 (total)
     - MT=2 (elastic)
     - MT=18 (fission)
     - MT=102 (capture)

3. **File Location**: `tests/data/sample_U235.endf`, `sample_U238.endf`

### Running Coverage Reports

```bash
# Generate coverage report
pytest --cov=smrforge --cov-report=html --cov-report=term-missing

# View HTML report
open htmlcov/index.html  # macOS/Linux
start htmlcov/index.html # Windows

# Check specific modules
pytest --cov=smrforge.core.reactor_core --cov-report=term-missing
pytest --cov=smrforge.core.endf_parser --cov-report=term-missing
```

### Expected Coverage After Completion

**reactor_core.py**:
- Current: 49%
- After Phase 1-2: ~70-75%
- Final Target: 75-80%

**endf_parser.py**:
- Current: 40%
- After Phase 1 + Phase 3: ~75-80%
- Final Target: 75-80%

**Overall**:
- Current: 67%
- Final Target: 75-80%

---

## Key Dependencies Graph

```
Task #1 (Mock ENDF Files) ← CRITICAL BLOCKER
  ├── Task #7 (Test _parse_mf3_section)
  ├── Task #3 (Test _simple_endf_parse)
  └── Task #5 (Test _fetch_and_cache)

Task #2 (Fix Zarr API)
  └── Task #6 (Test zarr cache retrieval)
```

---

## Notes

- **Largest Gap**: `_parse_mf3_section` (97 lines) represents ~55% of endf_parser coverage gap
- **Blocking Issue**: Mock ENDF files are needed before most parsing tests can be written
- **Known Bugs**: `_collapse_to_multigroup` has `np.diff` issue in parallel context (tests skipped)
- **Placeholder Code**: `DecayData._get_half_life` and `_get_daughters` are placeholders (low priority)
- **Implementation Status**: Mock fixtures are in place, ready for mock ENDF files

---

## References

- ENDF-6 Manual: Standard format for nuclear data files
- IAEA Nuclear Data Services: https://www-nds.iaea.org
- SANDY Library: Python library for ENDF file processing
- Zarr Documentation: https://zarr.readthedocs.io/

