# Nuclear Data Backend Alternatives

SMRForge supports multiple backends for parsing ENDF nuclear cross-section data. The system will try them in order until one succeeds.

## Supported Backends (in order of preference)

### 1. SANDY (Recommended)
- **Pros**: Pure Python, easy to install, no compilation needed, well-maintained
- **Cons**: Potentially slower than compiled alternatives for very large files
- **Installation**: `pip install sandy`
- **Status**: Recommended for most users

### 2. Simple ENDF Parser (Fallback)
- **Pros**: No external dependencies, built into SMRForge
- **Cons**: Limited to basic reactions (total, elastic, fission, capture), less robust
- **Installation**: None required (built-in)
- **Status**: Fallback for basic use cases

## How It Works

When cross-section data is needed:

1. **Check cache first**: Data is cached in Zarr format for fast access
2. **Try SANDY**: If data not cached and SANDY available, use it
3. **Try simple parser**: If SANDY not available, use built-in parser for common reactions
4. **Error if all fail**: Clear error message with installation instructions

## Installation Recommendations

### For Docker/Production
```bash
# Option 1: Install SANDY (recommended, no build tools)
pip install sandy

# Option 2: Pre-populate cache (no runtime dependencies)
# Pre-process cross-sections and place in cache directory
```

### For Development
```bash
# Install SANDY for best experience
pip install sandy

# Or use the built-in parser (limited features)
# No installation needed
```

## Pre-populating Cache (No Backend Needed)

You can pre-populate the cache directory with processed cross-section data:

```python
from pathlib import Path
from smrforge.core.reactor_core import NuclearDataCache, Nuclide, Library
import numpy as np
import zarr

# Cache location (default: ~/.smrforge/nucdata)
cache_dir = Path.home() / ".smrforge" / "nucdata"

# Pre-populate using any tool (SANDY, NJOY, etc.)
# Data should be stored as: {library}/{nuclide}/{reaction}/{temperature}K/energy and xs
```

## Docker Considerations

The Dockerfile does not require any nuclear data backends. At runtime:

1. **Option 1**: Install SANDY in the running container:
   ```bash
   docker compose exec smrforge pip install sandy
   ```

2. **Option 2**: Use pre-populated cache data mounted as a volume

## Error Messages

If no backend is available, you'll get a clear error message:
```
Failed to parse cross-section data for U235/total. No suitable backend available.

Installed backends: None

To enable cross-section fetching, install SANDY:
  - SANDY (recommended): pip install sandy
    Pure Python, easy to install

Note: SMRForge includes a built-in ENDF parser, but it failed to parse this file.
This may indicate an issue with the ENDF file format or unsupported reaction.
```

## Performance Notes

- **Cached data**: Fastest (no parsing needed)
- **SANDY**: Fast (pure Python, but efficient)
- **Simple parser**: Slowest (basic implementation)

Once data is cached, all backends perform the same (just reading from cache).
