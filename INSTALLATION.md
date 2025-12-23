# SMRForge Installation Guide

## Python Version Compatibility

**Yes, this library works with standard Python installations!** It does NOT require conda.

### Supported Python Versions

- **Python 3.8** or higher (as specified in `setup.py`)
- Tested with: Python 3.8, 3.9, 3.10, 3.11
- **All package managers work!** Use whatever you prefer.

### Package Manager Compatibility

SMRForge works with **any Python package manager**:

1. ✅ **pip** (standard Python package manager) - Recommended
2. ✅ **uv** (fast Rust-based installer) - Great choice! Very fast (10-100x faster)
3. ✅ **conda** (Anaconda/Miniconda) - Also works
4. ✅ **pipenv** - Works
5. ✅ **poetry** - Works
6. ✅ **venv/virtualenv** - Standard Python virtual environments

**Conda is NOT a Python version** - it's a package/environment manager. This library uses standard Python syntax (Python 3.8+) and standard PyPI packages.

---

## Installation Methods

### Method 1: Standard pip Installation (Recommended)

```bash
# Using pip with virtual environment (recommended)
python -m venv smrforge-env
source smrforge-env/bin/activate  # On Windows: smrforge-env\Scripts\activate
pip install -e .
```

### Method 2: Using uv (Fast Alternative - Recommended!)

[uv](https://github.com/astral-sh/uv) is a fast Python package installer written in Rust. It's **10-100x faster than pip**.

#### Install uv

```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip
pip install uv

# Or with Homebrew
brew install uv
```

#### Install SMRForge with uv

**Simplest method (uv manages everything):**
```bash
# Clone repository
git clone https://github.com/cmwhalen/smrforge.git
cd smrforge

# Install with uv (uv will create venv and install everything)
uv pip install -e . --python 3.10
```

**Manual virtual environment:**
```bash
# Create virtual environment
uv venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install SMRForge
uv pip install -e .
```

**With development dependencies:**
```bash
uv pip install -e ".[dev,docs,viz]" --python 3.10
```

### Method 3: Using conda (Optional)

If you prefer conda, you can use it:

```bash
# Create conda environment
conda create -n smrforge python=3.10
conda activate smrforge

# Install with pip (conda can use pip)
pip install -e .
```

**Note**: Using conda is optional. Standard pip installation works perfectly fine.

### Method 4: Development Installation

```bash
# Clone repository
git clone https://github.com/cmwhalen/smrforge.git
cd smrforge

# Install in development mode with all dependencies
pip install -e ".[dev,docs,viz]"
```

---

## Installation on Different Platforms

### Windows

```powershell
# Create virtual environment
python -m venv smrforge-env
smrforge-env\Scripts\activate

# Install
pip install -e .
```

### Linux/macOS

```bash
# Create virtual environment
python3 -m venv smrforge-env
source smrforge-env/bin/activate

# Install
pip install -e .
```

---

## Requirements

All dependencies are standard Python packages available on PyPI:

### Core Dependencies
- `numpy>=1.20.0`
- `scipy>=1.7.0`
- `matplotlib>=3.4.0`
- `pydantic>=2.0.0`
- `pandas>=1.3.0`
- `h5py>=3.0.0`
- `scikit-learn>=1.0.0`

### Additional Dependencies
- `numba>=0.56.0` - Performance optimization
- `zarr>=2.14.0` - Data storage
- `polars>=0.19.0` - Fast dataframes
- `openmc>=0.13.0` - Nuclear data handling (optional)
- `rich>=13.0.0` - Terminal formatting

All of these are **standard PyPI packages** - no conda-specific packages required.

---

## Verification

After installation, verify it works:

```python
import smrforge as smr
print(smr.__version__)

# Test one-liner
k = smr.quick_keff()
print(f"k-eff = {k:.6f}")
```

---

## Troubleshooting

### Issue: "openmc not found"

If `openmc` installation fails, it's an optional dependency for advanced nuclear data features. The core library works without it for basic calculations. SMRForge includes alternative backends (SANDY, custom parser) that work without OpenMC.

### Issue: "numba compilation errors"

Numba is used for performance optimization. If it fails to install, the library will still work but may be slower. You can install without numba optimizations if needed.

### Issue: "Package conflicts"

If you encounter dependency conflicts:

1. Use a fresh virtual environment
2. Upgrade pip: `pip install --upgrade pip`
3. Install dependencies one by one if needed
4. Try using `uv` - it has better dependency resolution

### Issue: "uv: command not found"

Make sure uv is installed and in your PATH. On Linux/macOS, you may need to restart your terminal or run:

```bash
source $HOME/.cargo/env  # If installed via cargo
```

---

## Performance Comparison

Typical installation times:

| Package Manager | Time (approx) |
|----------------|---------------|
| pip             | 30-60 seconds |
| uv              | 2-5 seconds   |

**uv is 10-20x faster!** Especially noticeable with packages like numpy, scipy, etc.

---

## Recommended Setup

### Option A: Standard Python + pip

```bash
# 1. Create virtual environment (Python 3.8+)
python -m venv venv

# 2. Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 3. Install SMRForge
pip install -e .

# 4. Verify installation
python -c "import smrforge; print(smrforge.__version__)"
```

### Option B: Using uv (Recommended for Speed!)

```bash
# 1. Install uv (if not already installed)
# See: https://github.com/astral-sh/uv

# 2. Install SMRForge (uv handles everything)
uv pip install -e . --python 3.10

# 3. Verify installation
python -c "import smrforge; print(smrforge.__version__)"
```

**Both work perfectly!** uv is just faster. No conda needed.

---

*Last Updated: 2024-12-21*

