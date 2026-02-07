# Contributing to SMRForge

**Last Updated:** January 29, 2026

Thank you for your interest in contributing to SMRForge! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful, inclusive, and collaborative. This is a technical project focused on nuclear reactor design and analysis.

## How to Contribute

### Reporting Bugs

1. Check existing issues to see if the bug has already been reported
2. Create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, SMRForge version)
   - Minimal code example if applicable

### Suggesting Features

1. Check existing issues for similar suggestions
2. Create a new issue with:
   - Clear description of the feature
   - Use case and motivation
   - Proposed implementation approach (if you have ideas)

### Pull Requests

1. **Fork the repository** and create a feature branch
2. **Make your changes** following our code style
3. **Add tests** for new functionality
4. **Update documentation** if needed
5. **Run tests** locally before submitting
6. **Submit PR** with clear description

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Git
- (Optional) Docker for containerized development

### Installation

1. **Clone your fork:**
   ```bash
   git clone https://github.com/cmwhalen/smrforge.git
   cd smrforge
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install in development mode:**
   ```bash
   pip install -e ".[dev]"
   ```

   This installs SMRForge in editable mode with development dependencies (pytest, black, mypy, etc.)

4. **Verify installation:**
   ```bash
   python -c "import smrforge; print(smrforge.__version__)"
   pytest tests/  # Run tests to verify
   ```

5. **Git on OneDrive (Windows):** If the repo is in a OneDrive-synced folder and you see `Permission denied` when creating `.git/index.lock`, run `.\scripts\setup_git_onedrive.ps1` once, then use `.\scripts\git_safe.ps1` for `add` / `commit` / `push`. See [Git and OneDrive](docs/development/git-onedrive.md) for details.

## Code Style

### Formatting

We use **Black** for code formatting:

```bash
# Format all Python files
black smrforge/ tests/

# Check formatting without making changes
black --check smrforge/ tests/
```

Configuration is in `pyproject.toml`. Line length is 88 characters.

### Import Sorting

We use **isort** for import organization:

```bash
isort smrforge/ tests/

# Check import order
isort --check-only smrforge/ tests/
```

### Type Hints

We encourage type hints for better code clarity:

```python
def my_function(x: float, y: float) -> float:
    """Add two numbers."""
    return x + y
```

Run **mypy** for type checking:

```bash
mypy smrforge/
```

(Note: Some modules may have `# type: ignore` comments for third-party libraries)

### Documentation Strings

Use Google-style docstrings:

```python
def solve_keff(reactor: ReactorSpecification) -> float:
    """
    Solve for k-effective of a reactor.
    
    Args:
        reactor: Reactor specification
        
    Returns:
        k-effective value
        
    Raises:
        ValueError: If reactor configuration is invalid
    """
    pass
```

## Testing

### Running Tests

Run all tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=smrforge --cov-report=html
```

Run specific test file:
```bash
pytest tests/test_neutronics.py
```

Run with markers:
```bash
pytest -m "not slow"  # Skip slow tests
pytest -m integration  # Run only integration tests
```

### Writing Tests

- Follow pytest conventions
- Use descriptive test names
- One assertion per test (when possible)
- Use fixtures for common setup
- Mark slow tests with `@pytest.mark.slow`

Example:
```python
def test_solver_converges(solver):
    """Test that solver converges to reasonable k-eff."""
    k_eff, flux = solver.solve_steady_state()
    assert 0.5 < k_eff < 2.0
    assert np.all(flux >= 0)
```

### Test Coverage

We aim for 80%+ test coverage on critical modules. New code should include tests.

#### Check Coverage

Run tests with coverage:
```bash
pytest --cov=smrforge --cov-report=html
```

This generates an HTML report in `htmlcov/index.html` showing:
- Overall coverage percentage
- Coverage by module
- Line-by-line coverage details

For a quick terminal report:
```bash
pytest --cov=smrforge --cov-report=term-missing
```

For CI/CD integration:
```bash
pytest --cov=smrforge --cov-report=xml
```

#### Coverage Targets

Critical modules should have 80%+ coverage:
- `smrforge.neutronics.solver` - Core solver
- `smrforge.validation.models` - Validation framework
- `smrforge.core.reactor_core` - Nuclear data handling

See `.github/workflows/ci.yml` for automated coverage in CI/CD.

## Commit Messages

Use clear, descriptive commit messages:

```
Short summary (50 chars or less)

More detailed explanation if needed. Wrap at 72 characters.
Explain what and why, not how.

- Bullet points for multiple changes
- Reference issues: Fixes #123
```

Examples:
- `Add logging framework for neutronics solver`
- `Fix zarr compatibility issue (DirectoryStore → LocalStore)`
- `Add integration tests for complete workflow`

## GitHub Setup (For New Contributors)

If you're setting up the repository on GitHub for the first time:

1. **Create a GitHub repository:**
   - Go to https://github.com/new
   - Name it `smrforge` (or your preferred name)
   - Choose public or private
   - **Don't initialize with README** (we already have one)

2. **Connect your local repository:**
   ```bash
   # Add GitHub remote (replace cmwhalen with your GitHub username)
   git remote add origin https://github.com/cmwhalen/smrforge.git
   
   # Or use SSH (recommended for long-term):
   git remote add origin git@github.com:cmwhalen/smrforge.git
   ```

3. **Push to GitHub:**
   ```bash
   # Set default branch to main
   git branch -M main
   
   # Push to GitHub
   git push -u origin main
   ```

**Authentication:** GitHub no longer accepts passwords. Use:
- **Personal Access Token** (for HTTPS) - Generate at GitHub → Settings → Developer settings
- **SSH Keys** (recommended) - Generate with `ssh-keygen` and add to GitHub
- **GitHub CLI** - Use `gh auth login`

## Git Workflow

1. **Create a branch:**
   ```bash
   git checkout -b feature/my-new-feature
   # or
   git checkout -b fix/bug-description
   ```

2. **Make changes and commit:**
   ```bash
   git add .
   git commit -m "Add feature description"
   ```

3. **Keep branch updated:**
   ```bash
   git fetch origin
   git rebase origin/main
   ```

4. **Push and create PR:**
   ```bash
   git push origin feature/my-new-feature
   ```

## Pull Request Process

1. **Ensure tests pass** - CI will run automatically
2. **Update documentation** - If adding features, update relevant docs
3. **Add changelog entry** - Add entry to CHANGELOG.md in [Unreleased]
4. **Request review** - Assign reviewers if possible
5. **Address feedback** - Respond to review comments

### PR Checklist

- [ ] Tests pass locally
- [ ] Code follows style guidelines (Black, isort)
- [ ] Type hints added (where appropriate)
- [ ] Documentation updated
- [ ] Changelog updated
- [ ] No merge conflicts

## Project Structure

```
smrforge/
├── smrforge/          # Main package
│   ├── core/          # Core functionality
│   ├── neutronics/    # Neutronics solvers
│   ├── geometry/      # Geometry handling
│   ├── thermal/       # Thermal-hydraulics
│   ├── validation/    # Validation framework
│   └── ...
├── tests/             # Test suite
├── examples/          # Example scripts
├── docs/              # Documentation
└── ...
```

## Areas for Contribution

We welcome contributions in many areas:

### High Priority
- Additional test cases
- Documentation improvements
- Bug fixes
- Performance optimizations

### Medium Priority
- New features (discuss in issues first)
- Visualization module implementation
- I/O utilities
- Additional examples

### Low Priority
- Optimization module
- Fuel performance module
- Control systems module
- Economics module

## Getting Help

- **Documentation:** See `docs/` directory
- **Issues:** Open an issue on GitHub
- **Examples:** Check `examples/` directory
- **Code Review:** Ask in PR comments

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (see LICENSE file).

## Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md (if we create one)
- Release notes
- Documentation (where appropriate)

Thank you for contributing to SMRForge! 🚀

