# ENDF Parser Recommendations for SMRForge

## Current State

**Already in use:**
- ✅ **Polars** (`polars>=0.19.0`) - Fast DataFrame library, used throughout codebase
- ✅ **SANDY** (optional, installed but not in requirements.txt) - Pure Python ENDF parser
- ✅ **NumPy** - For array operations
- ✅ **Custom parser** (`smrforge.core.endf_parser`) - Built-in fallback

## Recommended Approach: **`endf-parserpy`** + Polars Integration

### Why `endf-parserpy`?

1. **Official IAEA library** - Maintained by IAEA Nuclear Data Section
2. **Comprehensive features** - Read, write, validate, convert ENDF-6 files
3. **Active development** - Regularly updated and well-maintained
4. **JSON conversion** - Easy integration with modern Python workflows
5. **Format validation** - Built-in validation ensures data quality
6. **No heavy dependencies** - Pure Python, similar to SANDY

### Architecture Recommendation

```
┌─────────────────────────────────────────────────┐
│         NuclearDataCache.get_cross_section()    │
└────────────────┬────────────────────────────────┘
                 │
                 ├─► Try 1: endf-parserpy (NEW - recommended)
                 │   ├─ Fast parsing
                 │   ├─ Full ENDF-6 support
                 │   └─ Convert to Polars DataFrame
                 │
                 ├─► Try 2: SANDY (existing)
                 │   └─ Good for uncertainty sampling
                 │
                 └─► Try 3: Custom parser (fallback)
                     └─ Minimal dependencies
```

### Implementation Strategy

#### Option A: Replace with `endf-parserpy` (Recommended)

**Pros:**
- Official IAEA library
- Full ENDF-6 format support
- Better error handling and validation
- JSON export for debugging
- Active maintenance

**Cons:**
- New dependency (but lightweight)
- Need to adapt existing code

**Code Example:**
```python
try:
    from endf_parserpy import read_endf
    import polars as pl
    
    # Read ENDF file
    endf_data = read_endf(str(endf_file))
    
    # Extract MF=3, MT=reaction_mt
    mf3 = endf_data.get_mf(3)
    if mf3 and reaction_mt in mf3:
        reaction_data = mf3[reaction_mt]
        
        # Convert to Polars DataFrame (fits existing codebase style)
        energy = reaction_data['energy'].values  # NumPy array
        xs = reaction_data['cross_section'].values
        
        # Use existing Polars workflow
        df = pl.DataFrame({
            'energy': energy,
            'xs': xs,
            'mt': reaction_mt
        })
        
        return energy, xs
except ImportError:
    # Fallback to existing backends
    pass
```

#### Option B: Enhance with Polars (Leverage Existing Library)

**Since Polars is already heavily used**, we can:

1. **Parse with any backend** (SANDY, endf-parserpy, or custom)
2. **Immediately convert to Polars DataFrame** for all operations
3. **Leverage Polars' speed** for filtering, grouping, pivoting

**Benefits:**
- Consistent with existing codebase (`CrossSectionTable`, `MaterialDatabase`)
- 10-100x faster than pandas for tabular ops
- Natural fit for multi-group cross-section processing

**Example Integration:**
```python
import polars as pl

def parse_endf_to_polars(endf_file: Path, reaction_mt: int) -> pl.DataFrame:
    """
    Parse ENDF file and return as Polars DataFrame.
    
    Uses best available parser, converts to Polars for consistency.
    """
    # Try multiple backends
    for parser in [_parse_with_endf_parserpy, _parse_with_sandy, _parse_custom]:
        try:
            energy, xs = parser(endf_file, reaction_mt)
            if energy is not None and xs is not None:
                return pl.DataFrame({
                    'energy': energy,
                    'cross_section': xs,
                    'reaction_mt': reaction_mt
                })
        except (ImportError, Exception):
            continue
    
    raise ValueError(f"Failed to parse {endf_file}")

# Now all ENDF data processing uses Polars
df = parse_endf_to_polars(file, mt=18)  # Fission
filtered = df.filter(pl.col('energy') > 1e6)  # Fast filtering
grouped = df.group_by('reaction_mt').agg([...])  # Fast aggregation
```

## Comparison Table

| Feature | `endf-parserpy` | SANDY | Custom Parser | Polars (Post-processing) |
|---------|----------------|-------|---------------|--------------------------|
| **Official Support** | ✅ IAEA | ❌ | ❌ | ❌ (but standard library) |
| **Ease of Use** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Performance** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Full ENDF-6 Support** | ✅ Yes | ✅ Yes | ❌ Limited | N/A |
| **Read/Write** | ✅ Both | ✅ Read | ❌ Read only | N/A |
| **Validation** | ✅ Built-in | ❌ | ❌ | N/A |
| **JSON Export** | ✅ Yes | ❌ | ❌ | ✅ Via Polars |
| **Already Installed** | ❌ | ✅ Yes | ✅ Built-in | ✅ Yes |
| **Uncertainty Quantification** | ❌ | ✅ Yes | ❌ | ❌ |
| **Polars Integration** | ✅ Easy | ✅ Easy | ✅ Easy | ✅ Native |

## Recommended Implementation Plan

### Phase 1: Add `endf-parserpy` Support (Priority: High)

1. **Add to requirements.txt** (optional dependency):
   ```txt
   # Nuclear data handling (optional)
   endf-parserpy>=1.0.0  # Official IAEA ENDF parser (recommended)
   sandy>=1.0.0  # Alternative: good for uncertainty sampling
   ```

2. **Update `_fetch_and_cache` method** in `reactor_core.py`:
   ```python
   def _fetch_and_cache(...):
       # Try 1: endf-parserpy (new, recommended)
       try:
           from endf_parserpy import read_endf
           # Parse and extract data
           ...
       except ImportError:
           pass
       
       # Try 2: SANDY (existing)
       try:
           import sandy
           ...
       except ImportError:
           pass
       
       # Try 3: Custom parser (fallback)
       ...
   ```

### Phase 2: Polars-First Architecture (Priority: Medium)

1. **Convert all ENDF parsing output to Polars DataFrames**
2. **Leverage Polars for all tabular operations** (already doing this in `CrossSectionTable`)
3. **Create unified ENDF-to-Polars pipeline**

### Phase 3: Enhanced Features (Priority: Low)

1. **Use `endf-parserpy` validation** to verify file integrity
2. **Export to JSON** for debugging and inspection
3. **Leverage format conversion** capabilities if needed

## Immediate Action Items

1. **Install and test `endf-parserpy`**:
   ```bash
   pip install endf-parserpy
   ```

2. **Evaluate performance** vs. current SANDY implementation

3. **Add `endf-parserpy` to requirements.txt** (as optional dependency)

4. **Update `NuclearDataCache._fetch_and_cache()`** to use `endf-parserpy` as first choice

5. **Keep Polars integration** - convert all parsed data to Polars DataFrames for consistency

## Code Example: Ideal Implementation

```python
import polars as pl
from pathlib import Path
from typing import Tuple, Optional
import numpy as np

def _parse_with_endf_parserpy(
    endf_file: Path, reaction_mt: int
) -> Optional[Tuple[np.ndarray, np.ndarray]]:
    """Parse ENDF file using endf-parserpy (official IAEA library)."""
    try:
        from endf_parserpy import read_endf
        
        # Read ENDF file (fast, validated)
        endf_data = read_endf(str(endf_file))
        
        # Extract MF=3 (cross sections)
        mf3 = endf_data.get_mf(3)
        if not mf3 or reaction_mt not in mf3:
            return None
        
        # Get reaction data
        reaction = mf3[reaction_mt]
        energy = reaction['energy'].values  # NumPy array
        xs = reaction['cross_section'].values
        
        # Convert to Polars for consistency (optional but recommended)
        # df = pl.DataFrame({'energy': energy, 'xs': xs})
        
        return energy, xs
    except ImportError:
        return None
    except Exception as e:
        logger.warning(f"endf-parserpy failed: {e}")
        return None

# In NuclearDataCache._fetch_and_cache():
# 1. Try endf-parserpy (new, recommended)
energy, xs = _parse_with_endf_parserpy(endf_file, reaction_mt)
if energy is not None:
    self._save_to_cache(key, energy, xs)
    return energy, xs

# 2. Try SANDY (existing)
# 3. Try custom parser (fallback)
```

## Conclusion

**Best approach:** Use `endf-parserpy` as the primary parser (official IAEA library) + leverage Polars for all post-processing (already in use). This gives you:
- ✅ Official, well-maintained library
- ✅ Full ENDF-6 support
- ✅ Fast Polars operations (already in codebase)
- ✅ Consistent architecture
- ✅ Better error handling and validation

**Keep SANDY** as secondary option (good for uncertainty quantification if needed).

**Keep custom parser** as final fallback (zero dependencies).

