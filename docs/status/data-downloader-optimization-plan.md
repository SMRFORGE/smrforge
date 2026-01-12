# Data Downloader Optimization Plan

**Date:** January 2026  
**Status:** Analysis and Implementation Plan

---

## Current Performance Analysis

### Current Implementation Issues

1. **Sequential Downloads** ❌
   - Downloads files one at a time
   - `max_workers` parameter exists but not implemented
   - For 20 files, if each takes 2 seconds = 40 seconds total
   - With 5 parallel workers = ~8 seconds (5x faster)

2. **New Session Per File** ❌
   - Creates new `requests.Session()` for each file
   - No connection pooling
   - Overhead of establishing connections repeatedly

3. **Individual Progress Bars** ⚠️
   - Shows progress bar for each file separately
   - No overall progress indicator
   - Clutters terminal output

4. **Sequential Validation** ⚠️
   - Validates files one at a time after download
   - Could validate in parallel

5. **No URL Caching** ⚠️
   - Tries IAEA, then NNDC for each file
   - No memory of which source works better
   - Wastes time trying failed URLs

6. **End-of-Batch Organization** ⚠️
   - Organizes all files at the end
   - Could organize incrementally as files download

---

## Optimization Opportunities

### 1. Parallel Downloads (High Impact) 🔴

**Current:** Sequential downloads  
**Optimized:** Parallel downloads with ThreadPoolExecutor or asyncio

**Expected Speedup:** 3-10x (depending on network and number of files)

**Implementation:**
- Use `concurrent.futures.ThreadPoolExecutor` for parallel downloads
- Or use `httpx` with `asyncio` for async downloads (already in requirements)
- Respect `max_workers` parameter
- Shared session for connection pooling

### 2. Connection Pooling (Medium Impact) 🟡

**Current:** New session per file  
**Optimized:** Shared session across all downloads

**Expected Speedup:** 10-20% (reduces connection overhead)

**Implementation:**
- Create one session at start
- Reuse across all downloads
- Configure connection pool size

### 3. Unified Progress Bar (Medium Impact) 🟡

**Current:** Individual progress bars  
**Optimized:** Single overall progress bar

**Expected Improvement:** Better UX, cleaner output

**Implementation:**
- Use `tqdm` with total file count
- Update as each file completes
- Show overall progress and current file

### 4. Parallel Validation (Low Impact) 🟢

**Current:** Sequential validation  
**Optimized:** Validate files in parallel after download

**Expected Speedup:** 2-3x for validation step

**Implementation:**
- Validate files in parallel using ThreadPoolExecutor
- Only validate after all downloads complete (or in background)

### 5. URL Source Caching (Low Impact) 🟢

**Current:** Tries both sources for each file  
**Optimized:** Remember which source works

**Expected Improvement:** 10-15% faster (fewer failed attempts)

**Implementation:**
- Cache successful URL patterns (e.g., "IAEA works for ENDF/B-VIII.1")
- Try cached source first
- Fall back to other sources if cached source fails

### 6. Incremental Organization (Low Impact) 🟢

**Current:** Organizes all files at end  
**Optimized:** Organize files as they download

**Expected Improvement:** Better memory usage, faster perceived completion

**Implementation:**
- Organize each file immediately after download
- Or organize in batches

---

## Recommended Optimizations

### Priority 1: Parallel Downloads + Connection Pooling 🔴

**Impact:** High (3-10x speedup)  
**Effort:** Medium (1-2 days)

**Implementation:**
- Use `ThreadPoolExecutor` for parallel downloads
- Shared `requests.Session` with connection pooling
- Implement `max_workers` parameter

### Priority 2: Unified Progress Bar 🟡

**Impact:** Medium (Better UX)  
**Effort:** Low (2-4 hours)

**Implementation:**
- Single `tqdm` progress bar
- Show overall progress and current file name

### Priority 3: URL Source Caching 🟢

**Impact:** Low (10-15% faster)  
**Effort:** Low (2-3 hours)

**Implementation:**
- Cache successful URL patterns
- Try cached source first

---

## Implementation Plan

### Step 1: Parallel Downloads with ThreadPoolExecutor

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def download_endf_data_parallel(...):
    # Create shared session
    session = requests.Session()
    # Configure connection pooling
    adapter = HTTPAdapter(
        pool_connections=max_workers,
        pool_maxsize=max_workers * 2,
        max_retries=retry_strategy
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # Download in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(download_file_with_session, session, url, path, ...): nuclide
            for nuclide, url, path in download_tasks
        }
        
        # Process as they complete
        for future in as_completed(futures):
            nuclide = futures[future]
            try:
                success = future.result()
                # Update progress
            except Exception as e:
                # Handle error
```

### Step 2: Unified Progress Bar

```python
from tqdm import tqdm

# Create overall progress bar
with tqdm(total=len(nuclide_list), desc="Downloading ENDF files") as pbar:
    for future in as_completed(futures):
        nuclide = futures[future]
        success = future.result()
        pbar.set_description(f"Downloading {nuclide.name}")
        pbar.update(1)
        if success:
            pbar.set_postfix({"Downloaded": stats["downloaded"]})
```

### Step 3: URL Source Caching

```python
# Cache successful sources
_source_cache: Dict[str, str] = {}  # library -> preferred_source

def get_download_urls(nuclide, library):
    # Check cache first
    preferred_source = _source_cache.get(library.value)
    if preferred_source == "iaea":
        return [_get_endf_url(nuclide, library), _get_nndc_url(nuclide, library)]
    elif preferred_source == "nndc":
        return [_get_nndc_url(nuclide, library), _get_endf_url(nuclide, library)]
    else:
        # Try IAEA first (default)
        return [_get_endf_url(nuclide, library), _get_nndc_url(nuclide, library)]

# After successful download, cache the source
_source_cache[library.value] = "iaea"  # or "nndc"
```

---

## Expected Performance Improvements

### Before Optimization
- **20 files, 2s each (sequential):** 40 seconds
- **Connection overhead:** ~0.5s per file = 10s total
- **Total:** ~50 seconds

### After Optimization (5 workers)
- **20 files, 2s each (parallel, 5 workers):** ~8 seconds
- **Connection overhead (pooled):** ~1s total
- **Total:** ~9 seconds

**Speedup: 5.5x faster**

### With URL Caching
- **Fewer failed attempts:** Additional 10-15% improvement
- **Total:** ~8 seconds

**Overall Speedup: 6x faster**

---

## Code Changes Required

1. **Modify `download_file()` function:**
   - Accept session as parameter
   - Remove session creation

2. **Modify `download_endf_data()` function:**
   - Create shared session
   - Use ThreadPoolExecutor for parallel downloads
   - Implement unified progress bar
   - Add URL source caching

3. **Add helper functions:**
   - `download_file_with_session()` - Session-aware download
   - `get_download_urls()` - URL selection with caching
   - `validate_files_parallel()` - Parallel validation

---

## Testing Plan

1. **Unit Tests:**
   - Test parallel download functionality
   - Test connection pooling
   - Test URL caching
   - Test progress bar updates

2. **Integration Tests:**
   - Download small set of files (5-10)
   - Verify all files downloaded correctly
   - Verify organization works
   - Measure performance improvement

3. **Performance Tests:**
   - Compare sequential vs parallel
   - Measure speedup with different worker counts
   - Test with different network conditions

---

## Backward Compatibility

All optimizations maintain backward compatibility:
- Same API
- Same return values
- Same error handling
- Optional parameters (max_workers defaults to 5)

---

## Implementation Timeline

- **Day 1:** Implement parallel downloads + connection pooling
- **Day 2:** Add unified progress bar + URL caching
- **Day 3:** Testing and documentation

**Total:** 2-3 days

---

## Success Metrics

- **Speedup:** 5-6x faster for typical downloads
- **User Experience:** Cleaner progress output
- **Reliability:** Better error handling with parallel execution
- **Resource Usage:** Efficient connection pooling

---

## See Also

- [Data Downloader Guide](../guides/data-downloader-guide.md) - Current implementation
- [Data Import Comparison](data-import-comparison-and-improvement-plan.md) - Full analysis
