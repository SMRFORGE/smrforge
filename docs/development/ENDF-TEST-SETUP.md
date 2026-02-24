# ENDF Test Setup — Reducing Skipped Tests

**Last Updated:** February 2026

Many tests require real ENDF nuclear data. With ENDF-B-VIII.1 available, you can eliminate most ENDF-related skips.

## Quick Setup

Set the environment variable to your ENDF directory before running tests:

```bash
# Windows (PowerShell)
$env:SMRFORGE_ENDF_DIR="C:\Users\cmwha\Downloads\ENDF-B-VIII.1"

# Linux/macOS
export SMRFORGE_ENDF_DIR=/path/to/ENDF-B-VIII.1
```

Or rely on auto-detection: `conftest.py` sets `SMRFORGE_ENDF_DIR` at session start via an autouse fixture when it finds a directory at these paths (no manual env setup needed):
- `C:\Users\cmwha\Downloads\ENDF-B-VIII.1` (Windows)
- `~/Downloads/ENDF-B-VIII.1`
- `/data/ENDF-B-VIII.1`

## Required Directory Structure

ENDF-B-VIII.1 uses subdirectories:

- `neutrons-version.VIII.1/` — neutron cross-sections (e.g., `n-092_U_235.endf`)
- `thermal_scatt-version.VIII.1/` — thermal scattering (e.g., `tsl-HinH2O.endf`, `tsl-crystalline-graphite.endf`)
- `decay-version.VIII.1/` — decay data
- `nfy-version.VIII.1/` — fission yields
- `gammas-version.VIII.1/` — gamma production
- `photoat-version.VIII.1/` — photon cross-sections

## Tests Fixed by TSL Mapping (February 2026)

The thermal scattering parser now maps ENDF-B-VIII.1 filename variants to standard names:

| ENDF filename            | Standard name    |
|--------------------------|------------------|
| tsl-HinH2O.endf          | H_in_H2O         |
| tsl-crystalline-graphite.endf | C_in_graphite |
| tsl-graphiteSd.endf      | C_in_graphite    |
| tsl-reactor-graphite-10P.endf | C_in_graphite |

This fixes skips in:
- `test_endf_validation.py::test_parse_h2o_tsl`
- `test_endf_validation.py::test_parse_graphite_tsl`
- `test_validation_comprehensive.py::test_tsl_interpolation_accuracy`

## Remaining Skips (Not ENDF-Related)

Some tests skip for other reasons:
- **Presets not available** — Preset module import or config
- **examples/inputs/reactor.json not found** — Example input file
- **benchmarks/community_benchmarks.json not found** — Benchmark definition
- **plotly/matplotlib not installed** — Optional visualization deps
- **tqdm not available** — Progress bar dependency
- **Pro installed** — Community-path test skipped when Pro is present

## Verify Setup

```bash
python -c "
from pathlib import Path
from smrforge.core.reactor_core import NuclearDataCache
cache = NuclearDataCache(local_endf_dir=Path(r'C:\Users\cmwha\Downloads\ENDF-B-VIII.1'))
print('TSL H2O:', cache.get_tsl_file('H_in_H2O'))
print('TSL Graphite:', cache.get_tsl_file('C_in_graphite'))
print('Neutron U235:', 'n-092_U_235.endf' in str(cache._build_local_file_index().get('U235', '')))
"
```

All three should print non-None paths or True.
