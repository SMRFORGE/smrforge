# SMRForge Pro — Examples

Examples for **SMRForge Pro** (licensed edition). Requires Pro installation.

---

## Prerequisites

- SMRForge Pro: `pip install smrforge-pro`
- Valid Pro license

---

## Pro Examples

### Serpent I/O
| Example | Description | Required Data |
|---------|-------------|---------------|
| `serpent_export_example.py` | Export reactor to Serpent input | Reactor |
| `serpent_import_example.py` | Import from Serpent input | Serpent file |

### OpenMC I/O
| Example | Description | Required Data |
|---------|-------------|---------------|
| `openmc_export_example.py` | Export to OpenMC XML | Reactor |
| `openmc_visualization_pro.py` | OpenMC tally visualization | OpenMC results |

### Benchmarks & Reporting
| Example | Description | Required Data |
|---------|-------------|---------------|
| `benchmark_suite_example.py` | Run benchmark suite | Built-in |
| `benchmark_reproduction_example.py` | One-click benchmark reproduce and compare | Built-in |
| `report_generator_example.py` | Generate PDF/HTML report | Analysis results |

### AI & New Workflows
| Example | Description | Required Data |
|---------|-------------|---------------|
| `nl_design_example.py` | Natural-language reactor design | None |
| `code_verification_example.py` | Code-to-code verification | Reactor |
| `regulatory_package_example.py` | Regulatory submission package | Reactor |
| `multi_objective_optimization_example.py` | Multi-objective design optimization | Reactor |
| `physics_informed_surrogate_example.py` | Physics-informed surrogate with UQ | Sweep results |

---

## Workflow Summary

1. **Serpent export:** Create reactor → `SerpentConverter.export_reactor()` → run Serpent externally
2. **OpenMC export:** Create reactor → `OpenMCConverter.export_reactor()` → run OpenMC externally
3. **Benchmark:** `run_benchmark_suite()` or `reproduce_benchmark()` → compare to reference
4. **Report:** `ReportGenerator().generate(results, ...)` → PDF/HTML
5. **NL design:** `design_from_nl("10 MW HTGR")` → reactor spec + optional analysis
6. **Code verification:** `run_code_verification("valar-10")` → diffusion/MC/OpenMC/Serpent/MCNP comparison
7. **Regulatory package:** `generate_regulatory_package(reactor)` → NRC/IAEA submission
8. **Multi-objective:** `multi_objective_optimize(reactor_from_x, bounds, params)` → optimal design
9. **Physics-informed surrogate:** `physics_informed_surrogate_from_sweep(results, params)` → predictor with UQ

---

## Documentation

- [Pro Feature Matrix](../../docs/pro/pro-feature-matrix.md)
- [Serpent Export Guide](../../docs/pro/serpent-export-guide.md)
- [OpenMC Export Guide](../../docs/pro/openmc-export-guide.md)
- [Benchmark Suite Guide](../../docs/pro/benchmark-suite-guide.md)
- [Report Generator Guide](../../docs/pro/report-generator-guide.md)
