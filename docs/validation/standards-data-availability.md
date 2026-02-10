# ENDF Standards Data Availability

**Last Updated:** January 25, 2026

## Overview

ENDF-B-VIII.1 includes a `standards-version.VIII.1` directory containing standard reference cross-section files (std-*.endf) for validation and benchmarking purposes.

## Standards Directory Structure

When using a complete ENDF-B-VIII.1 download, the standards directory is located at:

```
ENDF-B-VIII.1/
├── neutrons-version.VIII.1/
├── decay-version.VIII.1/
├── standards-version.VIII.1/    ← Standards reference data
│   ├── std-001_H_001.endf
│   ├── std-092_U_235.endf
│   ├── std-092_U_238.endf
│   └── ... (11 standard files)
└── ...
```

## Detection

The `scan_endf_directory()` function automatically detects the standards directory:

```python
from pathlib import Path
from smrforge.core.reactor_core import scan_endf_directory

results = scan_endf_directory(Path("C:/path/to/ENDF-B-VIII.1"))
print(f"Has standards: {results['has_standards']}")
print(f"Standards files: {results['standards_files']}")
```

## Available Standards Files

The `standards-version.VIII.1` directory typically contains reference files for:

- **H-1** (std-001_H_001.endf)
- **He-3** (std-002_He_003.endf)
- **Li-6** (std-003_Li_006.endf)
- **B-10** (std-005_B_010.endf)
- **C-0, C-12, C-13** (std-006_C_*.endf)
- **Au-197** (std-079_Au_197.endf)
- **U-235, U-238** (std-092_U_*.endf)
- **Cf-252** (std-098_Cf_252.endf)

## Usage in Validation

Standards files can be used for:

1. **Cross-section spot checks**: Compare calculated values against standard reference values at specific energies
2. **Validation benchmarks**: Use standard cross-sections as reference points for validation tests
3. **Quality assurance**: Verify that parsers correctly extract cross-section data

## Integration with Validation Framework

The validation framework (`scripts/run_validation.py`) automatically:

- Detects standards directory presence via `scan_endf_directory()`
- Reports standards availability in validation report metadata
- Can use standards files for cross-section spot checks (when benchmark database includes cross-section benchmarks)

## Example: Using Standards in Validation

```python
from pathlib import Path
from smrforge.core.reactor_core import NuclearDataCache, Nuclide
from tests.validation_benchmarks import ValidationBenchmarker

# Create cache with ENDF directory (includes standards)
cache = NuclearDataCache(
    local_endf_dir=Path("C:/path/to/ENDF-B-VIII.1")
)

# Create benchmarker
bench = ValidationBenchmarker(cache)

# Validate cross-section spot check (if benchmark DB has XS benchmarks)
# This compares calculated XS against expected reference values
result = bench.validate_cross_section_spot_check(
    nuclide=Nuclide(Z=92, A=235),
    reaction="fission",
    energy_ev=0.0253,  # Thermal energy
    expected_value=585.0,  # Reference value (barns)
    tolerance=0.05  # 5% tolerance
)
```

## Alternative Sources

If `standards-version.VIII.1` is not available in your ENDF download:

- **NNDC/IAEA**: Standards data may be available separately from NNDC or IAEA
- **Literature references**: Use published cross-section values from nuclear data handbooks
- **Other codes**: Compare against MCNP, Serpent, or other validated transport codes

## Notes

- Standards files use the same ENDF format as regular neutron files
- Standards are typically used for validation, not production calculations
- The validation framework reports standards availability but does not require them to run

---

**See also:**
- SMRForge-Private/roadmaps/CONSOLIDATED-ROADMAP.md (roadmap, local); `docs/archive/roadmaps-superseded/next-work-options.md` - historical validation status
- `benchmarks/validation_benchmarks.json` - Benchmark database format
- `scripts/run_validation.py` - Validation runner script
