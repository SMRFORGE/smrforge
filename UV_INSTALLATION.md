# Installing SMRForge with uv

[uv](https://github.com/astral-sh/uv) is a fast Python package installer and resolver written in Rust. It's **10-100x faster than pip** and is a great choice for SMRForge!

## Why Use uv?

- ⚡ **Much faster** - 10-100x faster than pip
- 🔒 **Better dependency resolution** - More reliable conflict resolution
- 🎯 **Drop-in replacement** - Same commands, just use `uv pip` instead of `pip`
- 🌍 **Cross-platform** - Works on Windows, Linux, macOS

## Installation

### Step 1: Install uv

```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip
pip install uv

# Or with Homebrew
brew install uv

# Or with cargo
cargo install uv
```

See [uv installation guide](https://github.com/astral-sh/uv#installation) for more options.

### Step 2: Install SMRForge

#### Method A: Let uv manage everything (Simplest!)

```bash
# Clone repository
git clone https://github.com/yourusername/smrforge.git
cd smrforge

# Install with uv (uv will create venv and install everything)
uv pip install -e . --python 3.10
```

This command:
- Creates a virtual environment automatically
- Installs Python 3.10 (if not present)
- Installs SMRForge and all dependencies
- All in one command!

#### Method B: Manual virtual environment

```bash
# Create virtual environment
uv venv venv

# Activate it
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Install SMRForge
uv pip install -e .
```

#### Method C: With dev dependencies

```bash
# Install with development dependencies
uv pip install -e ".[dev,docs,viz]" --python 3.10
```

## Usage

Once installed, use SMRForge normally:

```python
import smrforge as smr

# One-liner to get k-eff
k = smr.quick_keff()
print(f"k-eff = {k:.6f}")
```

## Virtual Environment Management

### Create new environment

```bash
uv venv my-env
source my-env/bin/activate  # or: my-env\Scripts\activate (Windows)
```

### Install packages

```bash
# Same as pip, just use 'uv pip'
uv pip install numpy
uv pip install -e .
```

### List packages

```bash
uv pip list
```

### Sync requirements

```bash
uv pip sync requirements.txt
```

## Performance Comparison

Typical installation times:

| Package Manager | Time (approx) |
|----------------|---------------|
| pip             | 30-60 seconds |
| uv              | 2-5 seconds   |

**uv is 10-20x faster!** Especially noticeable with packages like numpy, scipy, etc.

## Compatibility

✅ **Fully compatible** with SMRForge!  
✅ **Same commands** - just replace `pip` with `uv pip`  
✅ **Same PyPI packages** - uses standard package repository  
✅ **Same virtual environments** - creates standard Python venvs  

## Troubleshooting

### Issue: "uv: command not found"

Make sure uv is installed and in your PATH. On Linux/macOS, you may need to restart your terminal or run:

```bash
source $HOME/.cargo/env  # If installed via cargo
```

### Issue: Python version not found

uv can automatically install Python versions:

```bash
# Install specific Python version
uv python install 3.10

# Then use it
uv pip install -e . --python 3.10
```

### Issue: Dependency conflicts

uv has better conflict resolution than pip. If you still encounter issues:

```bash
# Update uv
uv self update

# Try with explicit resolver
uv pip install -e . --resolution highest
```

## More Information

- [uv GitHub](https://github.com/astral-sh/uv)
- [uv Documentation](https://github.com/astral-sh/uv#readme)
- [uv Installation Guide](https://github.com/astral-sh/uv#installation)

---

**Summary**: uv works perfectly with SMRForge and is much faster than pip. Just use `uv pip` instead of `pip` - that's it!

