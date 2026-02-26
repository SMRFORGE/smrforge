# Converters Tutorial

SMRForge exports reactor designs to Serpent, OpenMC, and MCNP formats for use in external Monte Carlo codes.

## Quick Start

```python
from smrforge.convenience import create_reactor
from smrforge.io.converters import SerpentConverter, OpenMCConverter, MCNPConverter

reactor = create_reactor("valar-10")

# Serpent
SerpentConverter.export_reactor(reactor, "reactor.serp")

# OpenMC (creates directory with geometry.xml, materials.xml, settings.xml)
OpenMCConverter.export_reactor(reactor, "openmc_output", particles=1000, batches=20)

# MCNP
MCNPConverter.export_reactor(reactor, "reactor.mcnp")
```

## CLI

```bash
smrforge convert --reactor valar-10 --output reactor.serp --format serpent
smrforge convert --reactor valar-10 --output openmc_dir --format openmc
smrforge convert --reactor valar-10 --output reactor.mcnp --format mcnp
```

## Pre-export Hooks

Register a `pre_export` hook to run custom logic before any Serpent or MCNP export:

```python
from smrforge.workflows.plugin_registry import register_hook

def my_pre_export(ctx):
    print(f"Exporting to {ctx['format']} -> {ctx['output_file']}")

register_hook("pre_export", my_pre_export)
```

See `examples/converters_workflow_example.py` for a full example.

## Community vs Pro

| Feature        | Community | Pro   |
|----------------|-----------|-------|
| Serpent export | Placeholder | Full |
| Serpent import | Not available | Full |
| MCNP export    | Full (delegates to Pro if installed) | Full |
| OpenMC export | Full      | Enhanced |
