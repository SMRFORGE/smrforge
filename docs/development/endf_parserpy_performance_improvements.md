# endf-parserpy Performance Improvement Recommendations

**Date:** January 1, 2026  
**Status:** Analysis and Recommendations

---

## Current Implementation Analysis

### Current Usage in SMRForge

SMRForge currently uses `endf-parserpy` as the primary backend for ENDF file parsing:

```python
from endf_parserpy import EndfParserFactory
parser = EndfParserFactory.create()
endf_dict = parser.parsefile(str(endf_file))
```

**Location:** `smrforge/core/reactor_core.py` in `_fetch_and_cache()` method

### Current Performance Characteristics

1. **Parser Creation:** New parser instance created for each file parse
2. **Caching:** Two-level caching (Zarr persistent + in-memory LRU)
3. **Backend Selection:** Uses `EndfParserFactory.create()` which should auto-select C++ parser if available
4. **File I/O:** Each parse reads entire ENDF file from disk

---

## Identified Performance Improvements

### 1. ⭐ **Parser Instance Reuse** (High Impact)

**Current Issue:**
- New parser instance created for every file parse
- Parser initialization overhead on each call

**Recommendation:**
Reuse a single parser instance (or small pool) across multiple file parses.

**Implementation:**
```python
class NuclearDataCache:
    def __init__(self, ...):
        # ... existing code ...
        self._parser = None  # Lazy initialization
    
    def _get_parser(self):
        """Get or create parser instance (reused across calls)."""
        if self._parser is None:
            from endf_parserpy import EndfParserFactory
            self._parser = EndfParserFactory.create()
        return self._parser
    
    def _fetch_and_cache(self, ...):
        # ... existing code ...
        parser = self._get_parser()  # Reuse parser instance
        endf_dict = parser.parsefile(str(endf_file))
```

**Expected Improvement:** 10-30% faster parsing (eliminates parser initialization overhead)

**Priority:** 🔴 **HIGH** - Easy to implement, significant impact

---

### 2. ⭐ **Ensure C++ Parser is Used** (High Impact)

**Current Status:**
- `EndfParserFactory.create()` should auto-select C++ parser if available
- Need to verify C++ parser is actually being used

**Recommendation:**
1. Verify C++ parser availability during initialization
2. Log which parser type is being used
3. Provide installation guidance for C++ parser

**Implementation:**
```python
def _get_parser(self):
    """Get or create parser instance, preferring C++ parser."""
    if self._parser is None:
        from endf_parserpy import EndfParserFactory
        try:
            # Try to get C++ parser explicitly
            from endf_parserpy import EndfParserCpp
            self._parser = EndfParserCpp()
            logger.info("Using endf-parserpy C++ parser (fast)")
        except (ImportError, AttributeError):
            # Fallback to factory (auto-selects best available)
            self._parser = EndfParserFactory.create()
            parser_type = type(self._parser).__name__
            logger.info(f"Using endf-parserpy parser: {parser_type}")
    return self._parser
```

**Expected Improvement:** 2-5x faster parsing (C++ parser is significantly faster than Python)

**Priority:** 🔴 **HIGH** - Critical for performance

**Installation Note:**
- C++ parser requires compilation or pre-built wheels
- May need to set `INSTALL_ENDF_PARSERPY_CPP_OPTIM` environment variable
- See: https://endf-parserpy.readthedocs.io/

---

### 3. **Lazy Section Parsing** (Medium Impact)

**Current Issue:**
- `parser.parsefile()` may parse entire file even if only one section (MF/MT) is needed
- ENDF files can be large (several MB)

**Recommendation:**
Use selective parsing if endf-parserpy supports it, or parse only needed sections.

**Implementation:**
```python
# If endf-parserpy supports selective parsing:
endf_dict = parser.parsefile(str(endf_file), mf_list=[3])  # Only parse MF=3

# Or parse file once and cache full structure:
if endf_file not in self._file_cache:
    self._file_cache[endf_file] = parser.parsefile(str(endf_file))
endf_dict = self._file_cache[endf_file]
```

**Expected Improvement:** 20-50% faster for large files when only one section needed

**Priority:** 🟡 **MEDIUM** - Depends on endf-parserpy API support

---

### 4. **Batch File Parsing** (Medium Impact)

**Current Issue:**
- Files parsed one at a time sequentially
- No parallelization for multiple file requests

**Recommendation:**
For bulk operations, parse multiple files in parallel using ThreadPoolExecutor or ProcessPoolExecutor.

**Implementation:**
```python
from concurrent.futures import ThreadPoolExecutor
import asyncio

def _parse_file_batch(self, file_requests: List[Tuple[Path, str, int]]):
    """Parse multiple ENDF files in parallel."""
    parser = self._get_parser()  # Reuse parser (thread-safe if C++ parser)
    
    def parse_one(file_path, reaction_mt):
        endf_dict = parser.parsefile(str(file_path))
        # Extract needed section
        return self._extract_mf3_data(endf_dict[3][reaction_mt])
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = executor.map(
            lambda args: parse_one(*args),
            file_requests
        )
    return list(results)
```

**Expected Improvement:** 2-4x faster for bulk operations (depending on CPU cores)

**Priority:** 🟡 **MEDIUM** - Useful for bulk operations, less impact for single requests

**Note:** Verify thread-safety of endf-parserpy parser instances

---

### 5. **File Metadata Caching** (Low-Medium Impact)

**Current Issue:**
- File existence and structure checked on each request
- No pre-indexing of available reactions in files

**Recommendation:**
Cache file metadata (available reactions, file size, modification time) to avoid redundant file I/O.

**Implementation:**
```python
@dataclass
class EndfFileMetadata:
    """Cached metadata for an ENDF file."""
    path: Path
    available_mts: Set[int]  # Available MT numbers
    file_size: int
    mtime: float  # Modification time
    library_version: str

class NuclearDataCache:
    def __init__(self, ...):
        # ... existing code ...
        self._file_metadata_cache: Dict[Path, EndfFileMetadata] = {}
    
    def _get_file_metadata(self, endf_file: Path) -> EndfFileMetadata:
        """Get cached metadata or parse file header."""
        if endf_file in self._file_metadata_cache:
            metadata = self._file_metadata_cache[endf_file]
            # Check if file changed
            if metadata.mtime == endf_file.stat().st_mtime:
                return metadata
        
        # Parse file header to get available MTs
        parser = self._get_parser()
        endf_dict = parser.parsefile(str(endf_file))
        available_mts = set(endf_dict.get(3, {}).keys())
        
        metadata = EndfFileMetadata(
            path=endf_file,
            available_mts=available_mts,
            file_size=endf_file.stat().st_size,
            mtime=endf_file.stat().st_mtime,
            library_version="VIII.1"  # Extract from file
        )
        self._file_metadata_cache[endf_file] = metadata
        return metadata
```

**Expected Improvement:** 5-15% faster (avoids redundant file checks)

**Priority:** 🟡 **MEDIUM** - Useful for repeated queries

---

### 6. **Optimize Zarr Cache Operations** (Low Impact)

**Current Status:**
- Zarr caching already implemented
- Chunk size set to min(1024, array_length)

**Recommendation:**
- Consider larger chunk sizes for very large arrays
- Use compression level optimization
- Consider async Zarr writes for non-blocking cache updates

**Implementation:**
```python
# Optimize chunk size for large arrays
chunk_size = min(8192, len(energy))  # Larger chunks for big arrays

# Use better compression
import zarr
compressor = zarr.Blosc(cname='zstd', clevel=3, shuffle=2)
group.create_array("energy", data=energy, chunks=(chunk_size,), compressor=compressor)
```

**Expected Improvement:** 5-10% faster cache I/O for large datasets

**Priority:** 🟢 **LOW** - Current implementation is already good

---

### 7. **Memory-Mapped File Reading** (Low Impact)

**Current Issue:**
- Standard file I/O for ENDF files
- Files read entirely into memory

**Recommendation:**
Use memory-mapped files if endf-parserpy supports it, or implement custom memory-mapped reading for large files.

**Expected Improvement:** 10-20% faster for very large files (>10MB)

**Priority:** 🟢 **LOW** - Most ENDF files are <5MB, limited impact

---

## Implementation Priority

### Phase 1: Quick Wins (1-2 days)
1. ✅ **Parser Instance Reuse** - Easy, high impact
2. ✅ **Verify C++ Parser Usage** - Easy, high impact

### Phase 2: Medium Effort (3-5 days)
3. **Lazy Section Parsing** - Medium effort, good impact
4. **File Metadata Caching** - Medium effort, moderate impact

### Phase 3: Advanced (1-2 weeks)
5. **Batch File Parsing** - More complex, good for bulk operations
6. **Zarr Optimization** - Low priority, current implementation is good

---

## Performance Testing Recommendations

### Benchmark Script
```python
import time
from smrforge.core.reactor_core import NuclearDataCache, Nuclide, Library

cache = NuclearDataCache()
nuclides = [Nuclide(92, 235), Nuclide(92, 238), Nuclide(8, 16)]

# Benchmark single requests
start = time.time()
for nuc in nuclides:
    energy, xs = cache.get_cross_section(nuc, "total", 293.6)
single_time = time.time() - start

# Benchmark bulk requests
start = time.time()
results = [cache.get_cross_section(nuc, "total", 293.6) for nuc in nuclides * 10]
bulk_time = time.time() - start

print(f"Single requests: {single_time:.3f}s")
print(f"Bulk requests (30): {bulk_time:.3f}s")
```

### Metrics to Track
- Parser initialization time
- File parse time (first vs. cached)
- Cache hit/miss rates
- Memory usage
- Parser type (C++ vs. Python)

---

## Expected Overall Performance Improvement

### Conservative Estimate (Parser Reuse + C++ Parser)
- **Single file parse:** 2-3x faster
- **Bulk operations:** 2-4x faster
- **Cache hits:** Already fast (no change needed)

### Optimistic Estimate (All improvements)
- **Single file parse:** 3-5x faster
- **Bulk operations:** 4-8x faster
- **Memory usage:** 10-20% reduction

---

## Compatibility Notes

1. **Thread Safety:** Verify endf-parserpy parser instances are thread-safe before implementing batch parsing
2. **API Stability:** Check endf-parserpy version compatibility for selective parsing features
3. **C++ Parser Availability:** May require compilation on some platforms

---

## References

- **endf-parserpy Documentation:** https://endf-parserpy.readthedocs.io/
- **C++ Parser Guide:** https://endf-parserpy.readthedocs.io/en/latest/guide/python_and_cpp_parser.html
- **Installation Optimization:** https://endf-parserpy.readthedocs.io/

---

## Summary

**Immediate Actions (High Priority):**
1. ✅ Implement parser instance reuse
2. ✅ Verify and ensure C++ parser usage
3. ✅ Add logging to track parser type

**Medium-Term Actions:**
4. Implement lazy section parsing (if supported)
5. Add file metadata caching

**Long-Term Actions:**
6. Implement batch parsing for bulk operations
7. Optimize Zarr cache settings

**Expected Result:** 2-5x overall performance improvement with minimal code changes.

