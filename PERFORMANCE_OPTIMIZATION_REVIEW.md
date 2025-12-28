# Performance Optimization Review

**Date**: 2024-12-23  
**Focus**: Async/await and Polars optimizations for speed improvements

## Executive Summary

This review identifies key opportunities to speed up processing in SMRForge, with focus on:
1. **Async/await** for I/O-bound operations (network requests, file I/O)
2. **Polars optimizations** for DataFrame construction and operations
3. **Parallel processing** for batch operations

**Estimated Impact**: 2-10x speedup for typical workflows involving multiple nuclides/reactions and network fetches.

---

## 1. Async/Await Opportunities

### 1.1 Network I/O: ENDF File Downloads (HIGH PRIORITY)

**Location**: `smrforge/core/reactor_core.py:719-751` (`_ensure_endf_file`)

**Current Implementation**:
```python
def _ensure_endf_file(self, nuclide: Nuclide, library: Library) -> Path:
    # ...
    if not filepath.exists():
        url = self._get_endf_url(nuclide, library)
        response = requests.get(url)  # ❌ BLOCKING
        response.raise_for_status()
        filepath.write_bytes(response.content)
```

**Problem**: `requests.get()` is synchronous and blocks the event loop. When fetching multiple ENDF files (common in `generate_multigroup`), each download waits for the previous one to complete.

**Solution**: Use `httpx` (async-compatible) or `aiohttp`:
```python
import httpx

async def _ensure_endf_file_async(
    self, nuclide: Nuclide, library: Library, client: httpx.AsyncClient
) -> Path:
    # ...
    if not filepath.exists():
        url = self._get_endf_url(nuclide, library)
        response = await client.get(url)  # ✅ ASYNC
        response.raise_for_status()
        filepath.write_bytes(response.content)
```

**Impact**: 
- For N files: Sequential = N × latency, Async = latency (when N > 1)
- **Expected speedup**: 5-20x for batch downloads

---

### 1.2 Parallel Cross-Section Fetching in `generate_multigroup` (HIGH PRIORITY)

**Location**: `smrforge/core/reactor_core.py:867-892` (`generate_multigroup`)

**Current Implementation**:
```python
for nuclide in nuclides:
    for reaction in reactions:
        # ❌ Sequential fetching - blocks on each call
        energy, xs = self._cache.get_cross_section(
            nuclide, reaction, temperature
        )
        # Process...
```

**Problem**: Each `get_cross_section` call may trigger file I/O, parsing, or network requests. These are I/O-bound and can be parallelized.

**Solution**: Use `asyncio.gather()` for parallel fetching:
```python
async def generate_multigroup_async(
    self,
    nuclides: List[Nuclide],
    reactions: List[str],
    group_structure: np.ndarray,
    temperature: float = 900.0,
    weighting_flux: Optional[np.ndarray] = None,
) -> pl.DataFrame:
    # Create tasks for all nuclide/reaction combinations
    tasks = []
    for nuclide in nuclides:
        for reaction in reactions:
            tasks.append(
                self._cache.get_cross_section_async(
                    nuclide, reaction, temperature
                )
            )
    
    # Fetch all in parallel
    results = await asyncio.gather(*tasks)
    
    # Process results...
```

**Impact**:
- For M nuclides × N reactions: Sequential = M×N × avg_time, Parallel = max(avg_time) (when all cache misses)
- **Expected speedup**: 3-10x for typical scenarios (5 nuclides × 4 reactions = 20 operations)

---

### 1.3 File I/O in ENDF Parser (MEDIUM PRIORITY)

**Location**: `smrforge/core/endf_parser.py:143-152` (`_parse_file`)

**Current Implementation**:
```python
def _parse_file(self):
    with open(self.filename, "r") as f:  # ❌ BLOCKING
        lines = f.readlines()
```

**Problem**: Reading large ENDF files (10-100 MB) blocks. However, parsing is CPU-bound, so async I/O provides limited benefit unless combined with async parsing.

**Solution**: Use `aiofiles` for async file I/O (only if parsing is also made async):
```python
import aiofiles

async def _parse_file_async(self):
    async with aiofiles.open(self.filename, "r") as f:
        lines = await f.readlines()
    # Parse...
```

**Impact**: 
- **Expected speedup**: 1.1-1.5x (file I/O is usually fast compared to parsing)

**Recommendation**: **LOW PRIORITY** - Focus on network I/O first.

---

## 2. Polars Optimizations

### 2.1 DataFrame Construction from List of Dicts (HIGH PRIORITY)

**Location**: `smrforge/core/reactor_core.py:865-891` (`generate_multigroup`)

**Current Implementation**:
```python
records = []
for nuclide in nuclides:
    for reaction in reactions:
        # ... process ...
        for g, xs_val in enumerate(mg_xs):
            records.append({  # ❌ Growing list of dicts
                "nuclide": nuclide.name,
                "reaction": reaction,
                "group": g,
                "xs": xs_val,
            })
# Create DataFrame
self.data = pl.DataFrame(records)  # ❌ Slow for large lists
```

**Problem**: 
1. Growing list of dicts has overhead (memory reallocation)
2. Polars DataFrame construction from list of dicts is slower than from structured data

**Solution**: Use NumPy arrays and create DataFrame more efficiently:
```python
n_total = len(nuclides) * len(reactions) * n_groups
nuclide_names = np.empty(n_total, dtype=object)
reaction_names = np.empty(n_total, dtype=object)
groups = np.empty(n_total, dtype=np.int32)
xs_values = np.empty(n_total, dtype=np.float64)

idx = 0
for nuclide in nuclides:
    for reaction in reactions:
        # ... process ...
        for g, xs_val in enumerate(mg_xs):
            nuclide_names[idx] = nuclide.name
            reaction_names[idx] = reaction
            groups[idx] = g
            xs_values[idx] = xs_val
            idx += 1

# Create DataFrame from arrays (much faster)
self.data = pl.DataFrame({
    "nuclide": nuclide_names,
    "reaction": reaction_names,
    "group": groups,
    "xs": xs_values,
})
```

**Alternative**: Use Polars `scan_ndjson` or build with `pl.concat`:
```python
# Build list of smaller DataFrames, then concat
dfs = []
for nuclide in nuclides:
    for reaction in reactions:
        # ... process ...
        df = pl.DataFrame({
            "nuclide": [nuclide.name] * n_groups,
            "reaction": [reaction] * n_groups,
            "group": np.arange(n_groups),
            "xs": mg_xs,
        })
        dfs.append(df)
self.data = pl.concat(dfs)  # ✅ Fast concatenation
```

**Impact**:
- For 1000+ rows: List of dicts = ~100ms, NumPy arrays = ~10ms
- **Expected speedup**: 5-10x for large tables

---

### 2.2 Lazy Evaluation in Polars Queries (MEDIUM PRIORITY)

**Location**: `smrforge/core/reactor_core.py:968-1008` (`pivot_for_solver`)

**Current Implementation**:
```python
filtered = self.data.filter(...)  # ✅ Eager
pivoted = filtered.pivot(...)     # ✅ Eager
return pivoted.select(reactions).to_numpy()
```

**Opportunity**: Use lazy evaluation to optimize query plan:
```python
result = (
    self.data
    .lazy()  # ✅ Enable lazy evaluation
    .filter((pl.col("nuclide").is_in(nuclides)) & 
            (pl.col("reaction").is_in(reactions)))
    .pivot(values="xs", index=["nuclide", "group"], columns="reaction")
    .select(reactions)
    .collect()  # Execute optimized plan
    .to_numpy()
)
```

**Impact**:
- For complex queries: Lazy evaluation can optimize the query plan
- **Expected speedup**: 1.2-2x for complex operations

---

### 2.3 Vectorized Operations (LOW PRIORITY)

**Current**: Most operations are already vectorized (NumPy, Numba). Polars operations are already optimized.

**Opportunity**: Review any remaining Python loops that could use Polars expressions:
- Already well-optimized with Numba for numerical operations
- Polars operations are already vectorized

---

## 3. Parallel Processing Opportunities

### 3.1 ThreadPoolExecutor for CPU-Bound Parsing (MEDIUM PRIORITY)

**Location**: `smrforge/core/reactor_core.py:216-411` (`_fetch_and_cache`)

**Problem**: ENDF parsing is CPU-bound. Multiple files could be parsed in parallel.

**Solution**: Use `concurrent.futures.ThreadPoolExecutor`:
```python
from concurrent.futures import ThreadPoolExecutor

def _fetch_and_cache_batch(
    self,
    requests: List[Tuple[Nuclide, str, float, Library]],
    max_workers: int = 4,
) -> List[Tuple[np.ndarray, np.ndarray]]:
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(
                self._fetch_and_cache, nuclide, reaction, temp, lib, key
            )
            for nuclide, reaction, temp, lib, key in requests
        ]
        return [f.result() for f in futures]
```

**Impact**:
- For CPU-bound parsing: Parallel = ~max_workers × speedup
- **Expected speedup**: 2-4x with 4 workers

---

## 4. Recommended Implementation Order

### Phase 1: High-Impact Async Network I/O (2-3 days)
1. ✅ Add `httpx` to requirements
2. ✅ Convert `_ensure_endf_file` to async
3. ✅ Add async methods to `NuclearDataCache`
4. ✅ Update `generate_multigroup` to use async batch fetching

**Expected Impact**: **5-20x speedup** for workflows with network requests

### Phase 2: Polars DataFrame Optimization (1-2 days)
1. ✅ Optimize `generate_multigroup` DataFrame construction (NumPy arrays or `pl.concat`)
2. ✅ Use lazy evaluation in `pivot_for_solver`

**Expected Impact**: **5-10x speedup** for DataFrame construction

### Phase 3: Parallel CPU Processing (1 day)
1. ✅ Add ThreadPoolExecutor for batch parsing
2. ✅ Integrate with async methods

**Expected Impact**: **2-4x speedup** for CPU-bound parsing

### Phase 4: Fine-Tuning (Optional)
1. Async file I/O (limited benefit)
2. Additional lazy evaluation opportunities

---

## 5. Dependencies to Add

```txt
# For async HTTP requests (recommended over aiohttp - easier API)
httpx>=0.24.0

# Optional: For async file I/O (only if needed)
aiofiles>=23.0.0
```

---

## 6. Backward Compatibility

**Strategy**: Add async methods alongside existing sync methods:

```python
# Keep existing sync method
def _ensure_endf_file(self, nuclide: Nuclide, library: Library) -> Path:
    # ... existing code ...

# Add async version
async def _ensure_endf_file_async(
    self, nuclide: Nuclide, library: Library, client: httpx.AsyncClient
) -> Path:
    # ... async implementation ...

# Optional: Sync wrapper using asyncio.run (for convenience)
def _ensure_endf_file_sync_wrapper(self, nuclide, library):
    return asyncio.run(self._ensure_endf_file_async(nuclide, library))
```

This ensures existing code continues to work while new code can use async methods.

---

## 7. Testing Considerations

1. **Mock async HTTP clients** in tests (use `httpx.AsyncClient` with mock transport)
2. **Test both sync and async paths** to ensure compatibility
3. **Performance benchmarks** to measure actual speedup

---

## 8. Example: Optimized `generate_multigroup_async`

```python
async def generate_multigroup_async(
    self,
    nuclides: List[Nuclide],
    reactions: List[str],
    group_structure: np.ndarray,
    temperature: float = 900.0,
    weighting_flux: Optional[np.ndarray] = None,
) -> pl.DataFrame:
    """Async version with parallel fetching and optimized DataFrame construction."""
    n_groups = len(group_structure) - 1
    
    # Pre-allocate NumPy arrays (faster than list of dicts)
    n_total = len(nuclides) * len(reactions) * n_groups
    nuclide_names = np.empty(n_total, dtype=object)
    reaction_names = np.empty(n_total, dtype=object)
    groups = np.empty(n_total, dtype=np.int32)
    xs_values = np.empty(n_total, dtype=np.float64)
    
    # Create async HTTP client for downloads
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Fetch all cross sections in parallel
        tasks = []
        task_indices = []
        
        idx = 0
        for nuclide in nuclides:
            for reaction in reactions:
                tasks.append(
                    self._cache.get_cross_section_async(
                        nuclide, reaction, temperature, client
                    )
                )
                task_indices.append((nuclide, reaction, idx, n_groups))
                idx += n_groups
        
        # Wait for all fetches to complete
        results = await asyncio.gather(*tasks)
        
        # Process results and populate arrays
        for (nuclide, reaction, start_idx, n_g), (energy, xs) in zip(
            task_indices, results
        ):
            mg_xs = self._collapse_to_multigroup(
                energy, xs, group_structure, weighting_flux
            )
            
            for g, xs_val in enumerate(mg_xs):
                i = start_idx + g
                nuclide_names[i] = nuclide.name
                reaction_names[i] = reaction
                groups[i] = g
                xs_values[i] = xs_val
    
    # Create DataFrame from arrays (much faster)
    self.data = pl.DataFrame({
        "nuclide": nuclide_names,
        "reaction": reaction_names,
        "group": groups,
        "xs": xs_values,
    })
    return self.data
```

**Expected Performance**: 
- **20 nuclides × 4 reactions = 80 operations**
- Sequential: ~80 × 0.5s = 40s
- Async: ~0.5s (parallel network I/O)
- **Speedup: ~80x** (for network-bound operations)

---

## Summary

**Top 3 Optimizations** (by impact):

1. **Async network I/O** for ENDF file downloads → **5-20x speedup**
2. **Optimized Polars DataFrame construction** → **5-10x speedup**
3. **Parallel cross-section fetching** in `generate_multigroup` → **3-10x speedup**

**Combined Expected Impact**: **10-100x speedup** for typical workflows involving multiple nuclides/reactions and network fetches.

**Implementation Effort**: ~5-7 days for high-priority items.

