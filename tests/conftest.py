"""
Pytest configuration and fixtures
"""

import pytest
import numpy as np
from pathlib import Path

@pytest.fixture
def test_data_dir():
    """Fixture providing path to test data directory"""
    return Path(__file__).parent / "data"

@pytest.fixture
def sample_reactor():
    """Fixture providing a sample reactor configuration"""
    from smrforge.core import reactor_core
    # Return sample reactor configuration
    return {}

@pytest.fixture
def rng():
    """Fixture providing random number generator with fixed seed"""
    return np.random.default_rng(42)
