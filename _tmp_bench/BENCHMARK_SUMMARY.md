# Benchmark Validation Summary

**Executed:** 2026-02-26T17:53:33.294927
**Passed:** 0/4

**Accuracy target:** k-eff/flux within 1–2% of IAEA/NUREG reference benchmarks.

| Benchmark | Pass | k_eff (calc) | k_eff (ref) | Rel. Error | Message |
|-----------|------|--------------|-------------|------------|---------|
| godiva_bare_sphere | FAIL | 1.328184 | 1.000000 | 32.82% | Error 32.82% exceeds tolerance 0.50% |
| jezebel_pu239 | FAIL | 1.328184 | 1.000000 | 32.82% | Error 32.82% exceeds tolerance 0.50% |
| lra_benchmark | FAIL | 1.328184 | 1.000000 | 32.82% | Error 32.82% exceeds tolerance 1.00% |
| ans_5_1_decay_heat_u235 | FAIL | - | - | - | Benchmark not yet implemented |