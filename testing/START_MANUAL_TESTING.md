# Starting Manual Testing - Quick Guide

**Date:** January 2026  
**Status:** Ready to Begin

---

## Prerequisites Checklist

Before starting manual testing, ensure:

- [ ] Docker container is running: `docker compose ps`
- [ ] CLI is working: `docker compose exec smrforge-dev smrforge --help`
- [ ] Jupyter is installed (optional): `docker compose exec smrforge-dev pip list | grep jupyter`
- [ ] ENDF data is available (optional, for validation tests): Check `/app/endf-data` in container

---

## Step 1: Verify Environment

### Check Container Status
```bash
docker compose ps smrforge-dev
```

### Verify CLI Works
```bash
# Test main help
docker compose exec smrforge-dev smrforge --help

# Test version check (if available)
docker compose exec smrforge-dev python -c "import smrforge; print(smrforge.__version__)"

# Test validate subcommands (should work now)
docker compose exec smrforge-dev smrforge validate --help
docker compose exec smrforge-dev smrforge validate run --help
docker compose exec smrforge-dev smrforge validate design --help
```

### Check Test Scripts
```bash
# List all test scripts
docker compose exec smrforge-dev ls -la /app/testing/test_*.py

# Verify test scripts are accessible
docker compose exec smrforge-dev python -c "import sys; sys.path.insert(0, '/app'); print('OK')"
```

---

## Step 2: Choose Your Testing Method

### Option A: Python Scripts (Recommended - Primary Method)

**Run individual tests:**
```bash
# Test 1: CLI Commands
docker compose exec smrforge-dev python testing/test_01_cli_commands.py

# Test 2: Reactor Creation
docker compose exec smrforge-dev python testing/test_02_reactor_creation.py

# Test 3: Burnup Calculations
docker compose exec smrforge-dev python testing/test_03_burnup.py

# ... continue with test_04 through test_13
```

**Run all tests sequentially:**
```bash
docker compose exec smrforge-dev bash -c "cd testing && for f in test_*.py; do echo '=== Running $f ==='; python \$f; echo ''; done"
```

### Option B: Jupyter Notebooks (Optional - Interactive)

**Start Jupyter:**
```bash
# Install Jupyter if not already installed
docker compose exec smrforge-dev pip install jupyter

# Start Jupyter in background
docker compose exec -d smrforge-dev jupyter notebook \
  --ip=0.0.0.0 --port=8888 --no-browser --allow-root \
  --notebook-dir=/app/testing

# Get access token
docker compose exec smrforge-dev jupyter notebook list
```

**Access Jupyter:**
- URL: `http://localhost:8888` (if port is mapped)
- Token: Use the token from `jupyter notebook list` command
- Example notebook: `01_CLI_Commands.ipynb` (optional template)

### Option C: Interactive Shell Testing

**Open interactive shell:**
```bash
docker compose exec smrforge-dev bash
cd testing
python test_01_cli_commands.py
# Or use Python interactively
python
>>> import smrforge as smr
>>> smr.create_reactor('valar-10')
```

---

## Step 3: Document Your Results

### Use the Test Results Template

```bash
# Create results directory
docker compose exec smrforge-dev mkdir -p /app/testing/results

# Copy template
docker compose exec smrforge-dev cp /app/testing/TEST_RESULTS_TEMPLATE.md /app/testing/results/test_01_results.md
```

### Record Findings

For each test, document:
- ✅ **Working features** - What works as expected
- ⚠️ **Minor issues** - Issues that don't prevent functionality
- ❌ **Major issues** - Critical problems or failures
- 💡 **Suggestions** - Ideas for improvements
- 📝 **Usability notes** - User experience observations

**Template Location:** `testing/TEST_RESULTS_TEMPLATE.md`

---

## Step 4: Test Categories Overview

### 1. CLI Commands (`test_01_cli_commands.py`)
- Basic help and version
- All command categories
- Error handling
- Output formatting

### 2. Reactor Creation (`test_02_reactor_creation.py`)
- Creating reactors from presets
- Custom reactor creation
- Reactor analysis
- Design comparison

### 3. Burnup Calculations (`test_03_burnup.py`)
- Basic burnup calculations
- Checkpointing and resume
- Visualization
- Results export

### 4. Parameter Sweep (`test_04_parameter_sweep.py`)
- Single parameter sweeps
- Multi-parameter sweeps
- Parallel execution
- Results analysis

### 5. Templates (`test_05_templates.py`)
- Template creation
- Template instantiation
- Template library management
- Template validation

### 6. Design Constraints (`test_06_constraints.py`)
- Constraint set creation
- Design validation
- Constraint checking
- Validation reports

### 7. I/O Converters (`test_07_io_converters.py`)
- Serpent export (placeholder)
- OpenMC export (placeholder)
- Format conversion testing

### 8. Data Management (`test_08_data_management.py`)
- ENDF file discovery
- Data organization
- Data validation
- Download functionality

### 9. Validation Framework (`test_09_validation.py`)
- Validation test execution
- Benchmark comparison
- Test reporting

### 10. Visualization (`test_10_visualization.py`)
- Geometry visualization
- Flux plots
- 3D visualization
- Interactive plots

### 11. Workflows (`test_11_workflows.py`)
- YAML workflow execution
- Multi-step workflows
- Workflow error handling

### 12. Configuration (`test_12_config.py`)
- Configuration management
- Config file handling
- Environment variables

### 13. Advanced Features (`test_13_advanced.py`)
- Advanced workflows
- Edge cases
- Performance testing
- Integration testing

---

## Step 5: Common Testing Workflow

### Daily Testing Session

1. **Start fresh:**
   ```bash
   docker compose restart smrforge-dev
   ```

2. **Run one test category:**
   ```bash
   docker compose exec smrforge-dev python testing/test_01_cli_commands.py > testing/results/test_01_output.txt 2>&1
   ```

3. **Review output:**
   ```bash
   cat testing/results/test_01_output.txt
   ```

4. **Document findings:**
   - Open `testing/results/test_01_results.md`
   - Fill in the template with your findings
   - Note any bugs or issues

5. **Move to next test:**
   - Repeat for `test_02`, `test_03`, etc.

---

## Step 6: Reporting Issues

### After Testing Session

1. **Consolidate findings** from all test results
2. **Create GitHub issues** for bugs and major issues
3. **Document suggestions** for enhancements
4. **Update test scripts** if you find test issues

### Issue Creation

See `testing/README.md` section "Incorporating Feedback and Issues" for detailed workflow.

**Quick reference:**
- Bug: Create GitHub issue with `bug` label
- Enhancement: Create issue with `enhancement` label
- Test fix: Update test script and create PR

---

## Quick Start Commands

### Minimal Testing (5 minutes)
```bash
# Test CLI only
docker compose exec smrforge-dev python testing/test_01_cli_commands.py
```

### Standard Testing (30-60 minutes)
```bash
# Test core features
docker compose exec smrforge-dev python testing/test_01_cli_commands.py
docker compose exec smrforge-dev python testing/test_02_reactor_creation.py
docker compose exec smrforge-dev python testing/test_03_burnup.py
docker compose exec smrforge-dev python testing/test_04_parameter_sweep.py
```

### Comprehensive Testing (2-4 hours)
```bash
# Run all 13 test scripts
docker compose exec smrforge-dev bash -c "cd testing && for f in test_*.py; do echo '=== Running $f ==='; python \$f 2>&1 | tee results/\${f%.py}_output.txt; echo ''; done"
```

---

## Troubleshooting

### CLI Command Fails
```bash
# Reinstall SMRForge in container
docker compose exec smrforge-dev pip install -e . --no-deps

# Test again
docker compose exec smrforge-dev smrforge --help
```

### Test Script Import Errors
```bash
# Check Python path
docker compose exec smrforge-dev python -c "import sys; print(sys.path)"

# Verify SMRForge is importable
docker compose exec smrforge-dev python -c "import smrforge; print(smrforge.__version__)"
```

### Container Not Running
```bash
# Start container
docker compose up -d smrforge-dev

# Check status
docker compose ps smrforge-dev

# View logs
docker compose logs smrforge-dev --tail 50
```

### ENDF Data Not Found
```bash
# Check if mounted
docker compose exec smrforge-dev ls -la /app/endf-data

# Set up ENDF data
docker compose exec smrforge-dev smrforge data setup
```

---

## Next Steps

After completing manual testing:

1. ✅ Review all test results in `testing/results/`
2. ✅ Create issues for bugs and enhancements
3. ✅ Update test scripts with fixes
4. ✅ Share feedback with development team
5. ✅ Test fixes in follow-up sessions

---

## Related Documentation

- **Full Testing Guide:** `testing/README.md`
- **Testing Checklist:** `docs/testing/MANUAL_TESTING_CHECKLIST.md`
- **Test Results Template:** `testing/TEST_RESULTS_TEMPLATE.md`
- **Validation Guide:** `docs/validation/QUICK_START_VALIDATION.md`

---

*Ready to start? Run your first test:*
```bash
docker compose exec smrforge-dev python testing/test_01_cli_commands.py
```
