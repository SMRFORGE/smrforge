# SMRForge Custom ENDF Parser

SMRForge includes its own lightweight, pure-Python ENDF-6 file parser that provides OpenMC-compatible functionality without requiring OpenMC installation.

## Overview

The `smrforge.core.endf_parser` module implements a custom ENDF parser that:
- ✅ **Pure Python** - No compilation needed, no external dependencies (beyond NumPy)
- ✅ **OpenMC-compatible API** - Drop-in replacement for `openmc.data.endf.Evaluation`
- ✅ **Focused functionality** - Only implements what SMRForge needs
- ✅ **Robust parsing** - Handles standard ENDF-6 format files
- ✅ **Lightweight** - Much smaller and faster to install than OpenMC

## Features

### Supported Reactions
- Total (MT=1)
- Elastic scattering (MT=2)
- Non-elastic (MT=3)
- Inelastic (MT=4)
- Fission (MT=18, 19, 20, 21)
- Capture (MT=102)
- And other common reactions

### Capabilities
- Parse MF=3 (cross-section) sections
- Extract energy-dependent cross sections
- Handle ENDF-6 format variations
- Provide OpenMC-like interface

## Usage

### Basic Usage (OpenMC-compatible)

```python
from smrforge.core.endf_parser import ENDFCompatibility
from pathlib import Path

# Parse an ENDF file
evaluation = ENDFCompatibility(Path("U235.endf"))

# Check if a reaction exists
if 1 in evaluation:  # MT=1 is total cross section
    rxn_data = evaluation[1]
    
    # Access energy and cross section (OpenMC-compatible)
    energy = rxn_data.xs['0K'].x  # Energy in eV
    xs = rxn_data.xs['0K'].y      # Cross section in barns
    
    print(f"Energy range: {energy.min():.2e} - {energy.max():.2e} eV")
    print(f"Cross section range: {xs.min():.3f} - {xs.max():.3f} barns")
```

### Direct Usage (SMRForge API)

```python
from smrforge.core.endf_parser import ENDFEvaluation, ReactionData

# Parse an ENDF file
evaluation = ENDFEvaluation("U235.endf")

# Access reactions
if 18 in evaluation:  # MT=18 is fission
    fission = evaluation[18]
    print(f"Reaction: {fission.reaction_name}")
    print(f"Energy points: {len(fission.energy)}")
    
    # Interpolate at specific energy
    xs_at_1MeV = fission.interpolate(1e6)  # 1 MeV in eV
```

### Integration with NuclearDataCache

The ENDF parser is automatically used as a fallback in `NuclearDataCache`:

```python
from smrforge.core.reactor_core import NuclearDataCache, Nuclide, Library

cache = NuclearDataCache()

# This will try:
# 1. OpenMC (if installed)
# 2. SANDY (if installed)
# 3. SMRForge ENDF parser (built-in)
# 4. Simple parser (fallback)
energy, xs = cache.get_cross_section(
    nuclide=Nuclide(92, 235),
    reaction='total',
    temperature=1200.0,
    library=Library.ENDF_B_VIII
)
```

## Comparison with OpenMC

| Feature | OpenMC | SMRForge Parser |
|---------|--------|-----------------|
| Installation | Requires build tools (CMake, gfortran) | Pure Python, no compilation |
| Dependencies | C++ libraries, HDF5 | NumPy only |
| Build time | Several minutes | Instant |
| API compatibility | N/A | OpenMC-compatible |
| Feature set | Full ENDF support | Cross-sections (MF=3) |
| Performance | Very fast (C++) | Fast (Python, optimized) |

## Advantages

1. **No Build Dependencies**: Works immediately, no CMake or compilers needed
2. **Docker-Friendly**: Easy to use in containers without complex build steps
3. **Maintainable**: Pure Python makes it easy to debug and extend
4. **Focused**: Only implements what SMRForge actually uses
5. **Fallback**: Automatically used if OpenMC/SANDY unavailable

## Limitations

The custom parser is designed for SMRForge's needs:
- ✅ Parses MF=3 (cross sections) sections
- ✅ Handles common reactions (total, elastic, fission, capture, etc.)
- ✅ Supports standard ENDF-6 format
- ❌ Does NOT parse other MF sections (e.g., MF=4 for angular distributions)
- ❌ Does NOT handle advanced ENDF features (complex interpolation, etc.)
- ❌ Temperature-dependent data handled via Doppler broadening (not from file)

For full ENDF support, use OpenMC or SANDY.

## File Format Support

The parser supports:
- ENDF-6 format (standard)
- 6E11.0 data format (6 values per line, 11 characters each)
- Standard control record format
- Multiple reaction sections per file

## Error Handling

The parser includes robust error handling:
- Graceful degradation if file format issues
- Clear error messages for unsupported features
- Fallback to simpler parser if needed

## Contributing

To extend the parser:
1. Add support for additional MF sections in `endf_parser.py`
2. Extend reaction support in `_mt_to_reaction_name()`
3. Improve scientific notation parsing if needed

## Example: Complete Workflow

```python
from smrforge.core.endf_parser import ENDFCompatibility
from smrforge.core.reactor_core import Nuclide
from pathlib import Path

# Download ENDF file (example)
# endf_file = download_endf_file(Nuclide(92, 235))

# Parse it
evaluation = ENDFCompatibility(Path("U235.endf"))

# Extract fission cross section
if 18 in evaluation:
    fission = evaluation[18]
    energy = fission.xs['0K'].x
    xs = fission.xs['0K'].y
    
    # Use in your code
    for e, xs_val in zip(energy[:10], xs[:10]):
        print(f"{e:.2e} eV: {xs_val:.3f} barns")
```

## Testing

To test the parser:

```python
# Test with a known ENDF file
from smrforge.core.endf_parser import ENDFCompatibility

try:
    eval = ENDFCompatibility("test.endf")
    if 1 in eval:
        print("✓ Total cross section found")
    if 18 in eval:
        print("✓ Fission cross section found")
except Exception as e:
    print(f"Error: {e}")
```

The parser is automatically tested as part of SMRForge's nuclear data cache system.

