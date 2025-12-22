# Nuclear Data Backend Alternatives

SMRForge now supports multiple backends for parsing ENDF nuclear cross-section data. The system will try them in order until one succeeds.

## Supported Backends (in order of preference)

### 1. OpenMC (Preferred)
- **Pros**: Fast C++ backend, well-maintained, comprehensive
- **Cons**: Requires build tools (CMake, gfortran), takes several minutes to build
- **Installation**: `pip install openmc>=0.13.0`
- **Status**: Preferred method if installation succeeds

### 2. SANDY (Alternative)
- **Pros**: Pure Python, easier to install, no compilation needed
- **Cons**: Potentially slower than OpenMC for large files
- **Installation**: `pip install sandy`
- **Status**: Good alternative if OpenMC fails to build

### 3. Simple ENDF Parser (Fallback)
- **Pros**: No external dependencies, built into SMRForge
- **Cons**: Limited to basic reactions (total, elastic, fission, capture), less robust
- **Installation**: None required (built-in)
- **Status**: Fallback for basic use cases

## How It Works

When cross-section data is needed:

1. **Check cache first**: Data is cached in Zarr format for fast access
2. **Try OpenMC**: If data not cached and OpenMC available, use it
3. **Try SANDY**: If OpenMC not available, try SANDY
4. **Try simple parser**: If both fail, use built-in parser for common reactions
5. **Error if all fail**: Clear error message with installation instructions

## Installation Recommendations

### For Docker/Production
```bash
# Option 1: Install OpenMC (if build tools available)
pip install openmc>=0.13.0

# Option 2: Install SANDY (easier, no build tools)
pip install sandy

# Option 3: Pre-populate cache (no runtime dependencies)
# Pre-process cross-sections and place in cache directory
```

### For Development
```bash
# Install at least one backend
pip install sandy  # Easiest option

# Or if you have build tools
pip install openmc>=0.13.0
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

# Pre-populate using any tool (OpenMC, SANDY, NJOY, etc.)
# Data should be stored as: {library}/{nuclide}/{reaction}/{temperature}K/energy and xs
```

## Docker Considerations

The Dockerfile tries to install OpenMC, but if it fails (common in slim images), the container will still build. At runtime:

1. **Option 1**: Install SANDY in the running container:
   ```bash
   docker-compose exec smrforge pip install sandy
   ```

2. **Option 2**: Use pre-populated cache data mounted as a volume

3. **Option 3**: Use a base image that has OpenMC pre-installed

## Error Messages

If no backend is available, you'll get a clear error message:
```
Failed to parse cross-section data for U235/total. No suitable backend available.

Installed backends: None

To enable cross-section fetching, install one of:
  - OpenMC (preferred): pip install openmc>=0.13.0
  - SANDY (lighter alternative): pip install sandy
```

## Performance Notes

- **Cached data**: Fastest (no parsing needed)
- **OpenMC**: Fast (C++ backend)
- **SANDY**: Moderate (pure Python, but efficient)
- **Simple parser**: Slowest (basic implementation)

Once data is cached, all backends perform the same (just reading from cache).

