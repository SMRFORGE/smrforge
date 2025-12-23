# Logging in SMRForge

SMRForge includes a comprehensive logging framework for debugging, monitoring, and tracking solver operations.

## Quick Start

### Basic Usage

By default, SMRForge logs at WARNING level (to avoid noise). To enable more verbose logging:

```python
from smrforge.utils.logging import setup_logging

# Enable INFO level logging (recommended for normal use)
setup_logging(level="INFO")

# Enable DEBUG level logging (for detailed debugging)
setup_logging(level="DEBUG")

# Log to file
from pathlib import Path
setup_logging(level="INFO", log_file=Path("smrforge.log"))
```

### Using Loggers in Your Code

```python
from smrforge.utils.logging import get_logger

# Get logger for your module
logger = get_logger("smrforge.neutronics")

# Log messages
logger.info("Starting solver...")
logger.debug("Detailed information...")
logger.warning("Warning message...")
logger.error("Error occurred...")
```

## Automatic Logging

SMRForge automatically logs important events in core modules:

### Neutronics Solver

- Solver initialization (mesh size, method, tolerance)
- Iteration progress (every 10 iterations or on convergence)
- Convergence information (final k_eff, iterations, time)
- Errors and warnings

Example output:
```
2024-12-21 10:30:45 - smrforge.neutronics - INFO - Solving 2-group diffusion equation
2024-12-21 10:30:45 - smrforge.neutronics - DEBUG - Iteration   10: k_eff = 1.00123456, error = 1.23e-04
2024-12-21 10:30:45 - smrforge.neutronics - INFO - Converged in 25 iterations
2024-12-21 10:30:45 - smrforge.neutronics - INFO - Solver converged: k_eff = 1.00123456, time = 2.34 seconds
```

### Nuclear Data Cache

- Cache hits/misses
- Nuclear data fetching (which backend is used)
- Doppler broadening operations
- Backend fallbacks and errors

Example output:
```
2024-12-21 10:30:45 - smrforge.core - INFO - Fetching nuclear data: U235/fission at 1200.0K (backend: sandy)
2024-12-21 10:30:45 - smrforge.core - DEBUG - Cache write: endfb8.0/U235/fission/1200.0K
```

## Log Levels

- **DEBUG**: Detailed information for debugging (iterations, cache operations)
- **INFO**: General information (solver start/end, convergence, data fetching)
- **WARNING**: Warning messages (backend fallbacks, non-critical issues)
- **ERROR**: Error messages (convergence failures, parsing errors)
- **CRITICAL**: Critical errors (should rarely occur)

## Configuration Examples

### Development

```python
# Verbose logging for development
setup_logging(level="DEBUG", log_file=Path("dev.log"))
```

### Production

```python
# Minimal logging for production
setup_logging(level="WARNING")
```

### Debugging Specific Modules

```python
import logging

# Enable DEBUG only for neutronics
logging.getLogger("smrforge.neutronics").setLevel(logging.DEBUG)

# Keep other modules at INFO
logging.getLogger("smrforge").setLevel(logging.INFO)
```

## Custom Format

You can customize the log format:

```python
custom_format = "%(levelname)s [%(name)s] %(message)s"
setup_logging(level="INFO", format_string=custom_format)
```

## Integration with Solver Options

The solver's `verbose` option now uses logging instead of print statements. When `verbose=True`, logging is automatically set to INFO level for the neutronics logger.

```python
from smrforge.validation.models import SolverOptions
from smrforge.neutronics.solver import MultiGroupDiffusion

options = SolverOptions(verbose=True)  # Enables INFO-level logging
solver = MultiGroupDiffusion(geometry, xs_data, options)
k_eff, flux = solver.solve_steady_state()
```

## Best Practices

1. **Use appropriate log levels**: DEBUG for development, INFO for normal operation, WARNING+ for production
2. **Log to files for long runs**: Use `log_file` parameter for production simulations
3. **Module-specific loggers**: Use `get_logger("smrforge.module")` for module-specific logging
4. **Don't log sensitive data**: Avoid logging passwords, API keys, etc.

## Disabling Logging

To disable all SMRForge logging:

```python
import logging
logging.getLogger("smrforge").setLevel(logging.CRITICAL)
```

Or set the level to a high value to suppress most messages:

```python
setup_logging(level="ERROR")  # Only show errors
```

