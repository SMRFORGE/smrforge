# Example Input Files

Sample reactor specifications and configs for CLI workflows.

## reactor.json

Canonical example reactor spec (Valar-10 preset). Use with:

```bash
smrforge reactor analyze --reactor examples/inputs/reactor.json --neutronics --output results.json
smrforge visualize geometry --reactor examples/inputs/reactor.json --output geometry.png
smrforge validate design --reactor examples/inputs/reactor.json
```

When running from project root, you can also create a local `reactor.json`:

```bash
smrforge reactor create --preset valar-10 --output reactor.json
```

The root `reactor.json` is gitignored; use this file or `--output output/reactor.json` for versioned examples.
