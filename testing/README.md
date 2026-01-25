# SMRForge Manual Testing Guide

This directory contains comprehensive testing materials for manually testing all SMRForge features.

## Quick Start

1. **Review the Checklist**: Read `docs/testing/MANUAL_TESTING_CHECKLIST.md` for an overview
2. **Run Test Scripts**: Use the Python test scripts in this directory (`test_*.py`) - **Primary method**
3. **Use Jupyter Notebooks** (Optional): Use provided notebooks or create new ones from scripts for interactive testing
4. **Document Results**: Record your findings using the feedback template (`TEST_RESULTS_TEMPLATE.md`)

## Available Test Scripts

Each test script focuses on a specific feature category:

1. `test_01_cli_commands.py` - CLI command testing
2. `test_02_reactor_creation.py` - Reactor creation and analysis
3. `test_03_burnup.py` - Burnup calculations
4. `test_04_parameter_sweep.py` - Parameter sweep workflow
5. `test_05_templates.py` - Template library system
6. `test_06_constraints.py` - Design constraints validation
7. `test_07_io_converters.py` - I/O converters
8. `test_08_data_management.py` - Data management
9. `test_09_validation.py` - Validation framework
10. `test_10_visualization.py` - Visualization features
11. `test_11_workflows.py` - Workflow scripts
12. `test_12_config.py` - Configuration management
13. `test_13_advanced.py` - Advanced features

## Running Tests Locally

### Prerequisites

- SMRForge installed: `pip install -e .`
- ENDF data configured (optional, some tests require it)
- All dependencies installed
- Jupyter notebook (optional, for notebook format): `pip install jupyter`

### As Python Scripts

```bash
cd testing
python test_01_cli_commands.py
python test_02_reactor_creation.py
# ... etc
```

### As Jupyter Notebooks (Optional)

**Note:** Notebooks are **optional** for interactive testing. The Python scripts (`test_*.py`) are the primary testing mechanism and work independently.

If you prefer interactive testing with notebooks:

1. Start Jupyter: `jupyter notebook` or `jupyter lab`
2. Open the feature notebooks in `testing/notebooks/` (recommended)
3. **Or create notebooks from Python scripts:**
   - Copy code from `test_*.py` scripts into notebook cells
   - Add markdown cells for documentation
   - Run cells interactively
4. Document results inline using markdown cells

**Creating a notebook from a Python script:**
```python
# Example: Create notebook from test_02_reactor_creation.py
# 1. Open new Jupyter notebook
# 2. Copy functions from test_02_reactor_creation.py into code cells
# 3. Add markdown cells for documentation
# 4. Run cells interactively and document results
```

## Running Tests in Docker

### Prerequisites

- Docker Desktop installed and running
- Docker Compose v2 (or v1 with `docker-compose` command)

### Option 1: Production Container

**Start the container:**
```bash
docker compose up -d smrforge
```

**Run test scripts:**
```bash
# Run a single test script
docker compose exec smrforge python testing/test_01_cli_commands.py

# Run all test scripts (one at a time)
docker compose exec smrforge bash -c "cd testing && for f in test_*.py; do echo 'Running $f...'; python $f; done"
```

**Access interactive shell:**
```bash
docker compose exec smrforge bash
cd testing
python test_01_cli_commands.py
```

### Option 2: Development Container (Recommended for Testing)

**Start the development container:**
```bash
docker compose up -d smrforge-dev
```

**Run test scripts:**
```bash
# Run a single test
docker compose exec smrforge-dev python testing/test_01_cli_commands.py

# Run with output saved to host
docker compose exec smrforge-dev python testing/test_01_cli_commands.py > test_results.txt 2>&1
```

**Access interactive bash:**
```bash
docker compose exec smrforge-dev bash
cd testing
python test_01_cli_commands.py
```

### Running Jupyter Notebooks in Docker

**Method 1: Install Jupyter in existing container (Recommended)**

```bash
# 1. Install Jupyter in the container
docker compose exec smrforge-dev pip install jupyter

# 2. Start Jupyter server (interactive mode to see token)
docker compose exec smrforge-dev jupyter notebook \
  --ip=0.0.0.0 \
  --port=8888 \
  --no-browser \
  --allow-root \
  --notebook-dir=/app/testing

# 3. In another terminal, check logs to get access token:
docker compose logs smrforge-dev | grep token

# 4. Access Jupyter at http://localhost:8888 (if port 8888 is mapped in docker-compose.yml)
# If port is not mapped, add to docker-compose.yml:
#   ports:
#     - "8888:8888"
```

**To run Jupyter in background:**
```bash
# Start Jupyter in detached mode
docker compose exec -d smrforge-dev jupyter notebook \
  --ip=0.0.0.0 \
  --port=8888 \
  --no-browser \
  --allow-root \
  --notebook-dir=/app/testing

# Get the access URL and token
docker compose exec smrforge-dev jupyter notebook list
```

**Method 2: Map Jupyter port in docker-compose.yml**

Add to `smrforge-dev` service in `docker-compose.yml`:
```yaml
ports:
  - "8050:8050"  # Dashboard (existing)
  - "8888:8888"  # Jupyter (add this)
```

Then access at: `http://localhost:8888`

**Method 3: Use VS Code Remote Containers (Best for Development)**
- Install "Dev Containers" extension in VS Code
- Attach to running container: `smrforge-dev`
- Open notebooks in VS Code's integrated Jupyter interface
- No port mapping needed - VS Code handles it automatically

**Method 4: Manual port forwarding (if ports aren't mapped)**
```bash
# Forward port from container to host
docker port smrforge-dev 8888
# Or start container with explicit port mapping
docker run -p 8888:8888 ... smrforge-dev
```

### Running Validation Tests in Docker

For validation tests that require ENDF data:

```bash
# Set ENDF directory in container (already mounted from docker-compose.yml)
docker compose exec smrforge-dev bash -c "LOCAL_ENDF_DIR=/app/endf-data pytest tests/test_validation_comprehensive.py -v"

# Or use the validation script
docker compose exec smrforge-dev python scripts/run_validation.py --endf-dir /app/endf-data --verbose
```

### Saving Test Results from Docker

**Method 1: Use existing testing directory (Recommended)**

The `testing/` directory is already mounted, so results save directly to your host:

```bash
# Results saved to ./testing/ on your host machine
docker compose exec smrforge-dev python testing/test_01_cli_commands.py > testing/results/test_01_results.txt 2>&1

# Create results directory first if needed
mkdir -p testing/results
```

**Method 2: Add dedicated test results volume**

Add to `smrforge-dev` service in `docker-compose.yml`:

```yaml
volumes:
  - ./:/app:rw  # Already included
  - ./test_results:/app/test_results:rw  # Add this for results
```

Then run tests:
```bash
docker compose exec smrforge-dev python testing/test_01_cli_commands.py > test_results/test_01_results.txt 2>&1
```

**Method 3: Copy files from container**

```bash
# Run test in container
docker compose exec smrforge-dev python testing/test_01_cli_commands.py > container_output.txt

# Copy result file from container
docker compose cp smrforge-dev:/app/testing/result.json ./test_results/
```

**Organizing Results:**
```bash
# Create organized directory structure
mkdir -p testing/results/{2026-01-XX,logs,screenshots}
```

## Documenting Test Results

### Using the Feedback Template

After running each test, document your findings using `TEST_RESULTS_TEMPLATE.md`:

```bash
# Create results directory
mkdir -p testing/results

# Copy template for each test
cp testing/TEST_RESULTS_TEMPLATE.md testing/results/test_01_cli_commands_results.md

# Edit with your findings
# Use your preferred editor, VS Code, or Jupyter notebook
```

**In Docker:**
```bash
# Create results directory in container (maps to host)
docker compose exec smrforge-dev mkdir -p /app/testing/results

# Copy template
docker compose exec smrforge-dev cp /app/testing/TEST_RESULTS_TEMPLATE.md /app/testing/results/test_01_results.md

# Edit using VS Code Remote Containers or copy out and edit locally
```

### Test Results Structure

For each test, document:

- ✅ **Working features** - What works as expected
- ⚠️ **Features with minor issues** - Issues that don't prevent functionality
- ❌ **Features with major issues** - Critical problems or failures
- 💡 **Suggestions for improvements** - Ideas for enhancements
- 📝 **Notes on usability and clarity** - User experience observations
- ⏱️ **Performance notes** - Execution times, memory usage
- 🐛 **Bug reports** - Detailed error messages, stack traces

### Example Test Result Entry

```markdown
## Test: test_01_cli_commands.py

**Date:** 2026-01-XX
**Tester:** [Your Name]
**Environment:** Docker (smrforge-dev)

### Results Summary
- Passed: 12/15 tests
- Failed: 3 tests
- Warnings: 2

### Working Features ✅
- `smrforge --help` works correctly
- `smrforge reactor list` shows all presets
- Version command displays correctly

### Minor Issues ⚠️
- `smrforge reactor create` error message could be clearer
- Progress bar doesn't update smoothly

### Major Issues ❌
- `smrforge burnup run` fails with ENDF data not found error
- Command timeout after 60 seconds on large reactors

### Suggestions 💡
- Add --verbose flag to show more detailed output
- Improve error messages to include troubleshooting tips

### Bug Reports 🐛
1. **Issue:** `smrforge reactor analyze` crashes with specific preset
   **Error:** `AttributeError: 'NoneType' has no attribute 'to_dict'`
   **Steps to reproduce:** `smrforge reactor analyze --preset invalid-preset`
   **Expected:** Clear error message about invalid preset
   **Actual:** AttributeError crash
```

## Incorporating Feedback and Issues

This section describes the workflow for incorporating feedback, errors, and issues from manual testing into the SMRForge development process.

### Workflow Overview

```
Manual Testing → Document Results → Create Issues/PRs → Track Progress → Verify Fixes
```

### Step 1: Document Test Results

**Using the Template:**
1. Copy `TEST_RESULTS_TEMPLATE.md` for each test:
   ```bash
   cp testing/TEST_RESULTS_TEMPLATE.md testing/results/test_01_cli_commands_results.md
   ```
2. Fill in the template with your findings
3. Save results in `testing/results/` directory (create if it doesn't exist)

**Structure Your Results:**
- Use emojis consistently (✅ ⚠️ ❌ 💡 📝 ⏱️ 🐛)
- Include screenshots/logs for errors
- Note environment details (OS, Python version, Docker image)
- Categorize by severity (Critical/Major/Minor)

### Step 2: Create Issue Reports

**For GitHub Issues:**
1. Go to the repository Issues page
2. Create a new issue with appropriate labels:
   - `bug` - For bugs and errors
   - `enhancement` - For suggestions and improvements
   - `documentation` - For documentation gaps
   - `testing` - For test-related feedback
   - `priority: high/medium/low` - Set priority level
3. Use the test result template structure in your issue

**Issue Template:**
```markdown
**Test Script:** test_XX_feature.py
**Feature:** [Feature name]
**Severity:** [Critical / Major / Minor]
**Environment:** [Local / Docker]

**Description:**
[Clear description of the issue]

**Steps to Reproduce:**
1. Run: `python testing/test_XX_feature.py`
2. [Additional steps]

**Expected Behavior:**
[What should happen]

**Actual Behavior:**
[What actually happens]

**Error Messages:**
```
[Full error message]
```

**Test Results File:**
[Link to test_XX_results.md if available]
```

### Step 3: Prioritize Issues

**Categorize by Impact:**
- **Critical (P0):** Blocks core functionality, security issues
- **Major (P1):** Significant feature broken, major usability issues
- **Minor (P2):** Small bugs, minor improvements, documentation gaps

**Categorize by Type:**
- **Bug Fixes:** Things that are broken
- **Enhancements:** New features or improvements
- **Documentation:** Missing or incorrect docs
- **Testing:** Test framework improvements

### Step 4: Update Test Scripts

If you find issues that can be fixed in the test scripts themselves:

1. **Fix the test** - Update the test to handle edge cases
2. **Add better error handling** - Improve test robustness
3. **Document assumptions** - Add comments about expected behavior
4. **Add test cases** - Cover newly discovered edge cases

**Example:**
```python
# Before
reactor = smr.create_reactor(preset='valar-10')

# After (with better error handling)
try:
    reactor = smr.create_reactor(preset='valar-10')
    assert reactor is not None, "Reactor creation returned None"
    print("✅ Reactor created successfully")
except FileNotFoundError as e:
    print(f"⚠️  Reactor creation failed: ENDF data not found")
    print(f"   Expected ENDF directory: {smr.get_endf_dir()}")
    print("   Run: smrforge data setup")
    return None  # Skip dependent tests
except Exception as e:
    print(f"❌ Reactor creation failed: {e}")
    import traceback
    traceback.print_exc()
    return None
```

### Step 5: Create Pull Requests

For improvements to the testing framework or bug fixes:

**Branching Strategy:**
```bash
# Create feature branch
git checkout -b testing/fix-cli-error-handling
# or
git checkout -b bugfix/reactor-creation-timeout
```

**Commit Messages:**
Follow conventional commits format:
- `test: improve error handling in test_01_cli_commands.py`
- `fix: handle missing ENDF data gracefully in reactor creation`
- `docs: add Docker Jupyter instructions to testing README`
- `feat: add timeout handling to burnup tests`

**Pull Request Template:**
```markdown
## Description
[Clear description of changes]

## Related Issues
Fixes #123
Closes #456

## Changes Made
- [ ] Fixed test script error handling
- [ ] Added new test cases
- [ ] Updated documentation

## Test Results
- Test script: test_XX_feature.py
- Before: X/Y tests passed
- After: X/Y tests passed
- [Attach test results]

## Checklist
- [ ] Tests pass locally
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

**PR Best Practices:**
- Reference related issues (#123)
- Include before/after test results
- Add screenshots for UI changes
- Request review from maintainers
- Link to test results file if available

### Step 6: Update Documentation

Based on test feedback, update documentation:

**Types of Documentation Updates:**
- **Fix documentation errors** - Correct incorrect examples, typos
- **Add missing information** - Document discovered features or edge cases
- **Improve clarity** - Rewrite confusing sections with better examples
- **Add troubleshooting** - Document common issues and solutions
- **Add examples** - Include working code examples from test scripts

**Documentation Files to Update:**
- `README.md` - Main project documentation
- `docs/testing/` - Testing guides and checklists
- `docs/guides/` - Feature-specific guides
- `docs/api/` - API reference documentation
- Inline code comments - Improve code documentation

**Example Update:**
```markdown
# Before
smrforge reactor create --preset valar-10

# After (with error handling example)
smrforge reactor create --preset valar-10
# Note: Requires ENDF data. If error occurs, run: smrforge data setup
```

### Step 7: Fix Code Issues (For Developers)

If you have access to fix code issues:

**Development Workflow:**
1. **Create branch** for the fix:
   ```bash
   git checkout -b bugfix/fix-reactor-creation-error
   ```

2. **Write/fix tests** - Ensure test coverage for the fix:
   ```bash
   # Add test case that reproduces the bug
   pytest tests/test_reactor_creation.py::test_fix_for_issue_123
   ```

3. **Implement fix** - Address the issue in code

4. **Run full test suite** - Verify fix doesn't break existing functionality:
   ```bash
   pytest  # All tests
   pytest tests/test_reactor_creation.py -v  # Specific module
   pytest --cov=smrforge --cov-report=html  # With coverage
   ```

5. **Update documentation** - Document the fix and new behavior

6. **Create PR** - Follow PR template from Step 5

**Testing Fixes:**
- Run the original test script that found the issue
- Verify it now passes
- Run related automated tests
- Test edge cases

### Step 8: Track Progress

**Issue Tracking:**
- Use GitHub Projects or Issues for tracking
- Update issue status: `open` → `in progress` → `closed`
- Link PRs to issues: `Fixes #123`
- Add labels for categorization

**Feedback Loop:**
1. Tester creates issue → Developer picks it up
2. Developer fixes → Creates PR → Tester reviews
3. Tester verifies fix → Closes issue
4. Update test scripts with new test cases

**Regular Review:**
- Weekly review of open testing issues
- Monthly review of test result trends
- Update test scripts based on common issues found

## Test Results Template

See `TEST_RESULTS_TEMPLATE.md` for a structured template to document test results.

## Troubleshooting

### Issue: Test scripts fail with import errors

**Solution:**
```bash
# Local: Ensure SMRForge is installed
pip install -e .

# Docker: Ensure container is running and dependencies are installed
docker compose exec smrforge-dev pip install -e .
```

### Issue: ENDF data not found

**Solution:**
```bash
# Check ENDF directory is mounted (Docker)
docker compose exec smrforge-dev ls -la /app/endf-data

# Set ENDF directory (Local)
export SMRFORGE_ENDF_DIR=/path/to/endf-data

# Or configure via CLI
smrforge data setup
```

### Issue: Jupyter notebooks are empty or missing

**Solution:**
- **Notebooks are optional** - The Python scripts (`test_*.py`) are complete and sufficient
- If you want notebooks, you can:
  - Copy content from corresponding Python scripts (`test_XX_feature.py`) into notebook cells
  - Create notebooks manually with the test code
  - Use the Python scripts directly (recommended)

### Issue: Docker container won't start

**Solution:**
```bash
# Check Docker is running
docker ps

# Rebuild containers
docker compose down
docker compose build
docker compose up -d smrforge-dev

# Check logs
docker compose logs smrforge-dev
```

### Issue: Tests timeout or hang

**Solution:**
- Check if ENDF data is properly configured
- Some tests may take a long time (burnup calculations)
- Use `--timeout` flag or run interactively to see progress

## Next Steps

After completing manual testing:

1. **Review all test results** - Consolidate findings
2. **Create issues** - Document bugs and improvements
3. **Update tests** - Fix any test script issues
4. **Share feedback** - Discuss findings with development team
5. **Follow up** - Test fixes and improvements

## Docker Quick Reference

### Starting Containers
```bash
# Development container (recommended for testing)
docker compose up -d smrforge-dev

# Production container
docker compose up -d smrforge
```

### Running Tests in Docker
```bash
# Single test script
docker compose exec smrforge-dev python testing/test_01_cli_commands.py

# All test scripts sequentially
docker compose exec smrforge-dev bash -c "cd testing && for f in test_*.py; do echo 'Running $f...'; python \$f; done"

# Interactive shell
docker compose exec smrforge-dev bash
cd testing
python test_01_cli_commands.py
```

### Jupyter Notebooks in Docker
```bash
# Install Jupyter
docker compose exec smrforge-dev pip install jupyter

# Start Jupyter (add -d for detached mode)
docker compose exec smrforge-dev jupyter notebook \
  --ip=0.0.0.0 --port=8888 --no-browser --allow-root \
  --notebook-dir=/app/testing

# Access: http://localhost:8888 (if port is mapped)
# Get token: docker compose exec smrforge-dev jupyter notebook list
```

### Saving Results
```bash
# Save to testing/results/ (already mounted)
mkdir -p testing/results
docker compose exec smrforge-dev python testing/test_01_cli_commands.py > testing/results/test_01_output.txt 2>&1
```

### Useful Docker Commands
```bash
# View logs
docker compose logs smrforge-dev

# Restart container
docker compose restart smrforge-dev

# Rebuild and restart
docker compose down
docker compose build smrforge-dev
docker compose up -d smrforge-dev

# Check container status
docker compose ps

# Execute Python in container
docker compose exec smrforge-dev python -c "import smrforge; print(smrforge.__version__)"
```

## Related Documentation

- **Testing Checklist:** `docs/testing/MANUAL_TESTING_CHECKLIST.md`
- **Docker Guide:** `docs/guides/docker.md`
- **Validation Guide:** `docs/validation/QUICK_START_VALIDATION.md`
- **Contributing Guide:** `CONTRIBUTING.md`
