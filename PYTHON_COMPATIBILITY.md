# Python Compatibility - SMRForge

## Quick Answer

**Yes! This library works with standard Python installations. Conda is optional, not required.**

---

## Clarification

**Conda is NOT a Python version** - it's a package/environment manager (like pip, but more comprehensive).

- **Python versions**: 3.8, 3.9, 3.10, 3.11, 3.12 (actual versions of Python)
- **Conda**: A tool to manage Python environments and packages (alternative to pip)

---

## Compatibility Matrix

| Python Version | pip | uv | conda | venv | pipenv | poetry |
|----------------|-----|----|-------|------|--------|--------|
| 3.8            | ✅  | ✅ | ✅    | ✅   | ✅     | ✅     |
| 3.9            | ✅  | ✅ | ✅    | ✅   | ✅     | ✅     |
| 3.10           | ✅  | ✅ | ✅    | ✅   | ✅     | ✅     |
| 3.11           | ✅  | ✅ | ✅    | ✅   | ✅     | ✅     |
| 3.12           | ✅  | ✅ | ✅    | ✅   | ✅     | ✅     |

**All package managers work!** Use whatever you prefer. **uv is recommended for speed!**

---

## What We Checked

✅ **No conda-specific code** - The codebase uses standard Python  
✅ **All dependencies are on PyPI** - No conda-only packages  
✅ **Standard setuptools installation** - Works with pip  
✅ **No conda environment checks** - No conda-specific imports or assumptions  
✅ **Cross-platform compatible** - Works on Windows, Linux, macOS  

---

## Installation Examples

### Standard Python + pip (Most Common)

```bash
# Works with any Python 3.8+ installation
python -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate (Windows)
pip install -e .
```

### Using conda (If You Prefer It)

```bash
# Optional - conda is just another way to manage environments
conda create -n smrforge python=3.10
conda activate smrforge
pip install -e .  # Can still use pip with conda!
```

### Using uv (Fast Alternative - Recommended!)

```bash
# uv is a fast Rust-based package installer
# Install uv: https://github.com/astral-sh/uv

# Method 1: Let uv manage the environment
uv pip install -e . --python 3.10

# Method 2: Use existing virtual environment
uv venv venv
source venv/bin/activate
uv pip install -e .
```

**uv is 10-100x faster than pip!** It's a drop-in replacement - just use `uv pip` instead of `pip`.

### Using pipenv

```bash
pipenv install -e .
```

### Using poetry

```bash
poetry add -e .
```

---

## Why This Matters

Some scientific Python libraries have dependencies that are difficult to install with pip (like compiled libraries, BLAS/LAPACK, etc.), so they often recommend conda. However:

- ✅ **SMRForge uses standard PyPI packages** - All dependencies are easily installable with pip
- ✅ **No compiled dependencies issues** - Standard packages like numpy, scipy are well-supported
- ✅ **Cross-platform wheels** - Most dependencies have pre-built wheels for all platforms

---

## Recommendation

**Two great options:**

### Option 1: uv (Fastest - Recommended if available!)
1. Install uv: https://github.com/astral-sh/uv
2. Install SMRForge: `uv pip install -e . --python 3.10`
3. **That's it!** uv handles everything and is much faster than pip.

### Option 2: Standard pip (Most Common)
1. Install Python 3.8+ from python.org
2. Create virtual environment: `python -m venv venv`
3. Activate: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
4. Install: `pip install -e .`

**Both work perfectly!** uv is just faster. No conda needed.

---

## System Requirements

- **Python**: 3.8, 3.9, 3.10, 3.11, or 3.12
- **OS**: Windows, Linux, or macOS
- **Package Manager**: pip (standard), or conda/pipenv/poetry if you prefer

---

## Testing Compatibility

To verify your installation works:

```python
import smrforge as smr
print(f"SMRForge version: {smr.__version__}")
print(f"Python version: {smr.__version__}")  # Just checking imports work

# Test a one-liner
k = smr.quick_keff()
print(f"k-eff = {k:.6f}")
```

If this runs without errors, you're good to go!

---

*Last Updated: 2024-12-21*

