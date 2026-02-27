"""
Tests for system code coupling (RELAP/TRACE).
"""

import pytest


class TestSystemCodeCoupling:
    """Tests for coupling.system_codes module."""

    def test_relap_coupler_import(self):
        """RELAPCoupler can be imported."""
        from smrforge.coupling import RELAPCoupler

        assert RELAPCoupler is not None

    def test_trace_coupler_import(self):
        """TRACECoupler can be imported."""
        from smrforge.coupling import TRACECoupler

        assert TRACECoupler is not None

    def test_system_code_available_returns_bool(self):
        """system_code_available returns boolean."""
        from smrforge.coupling.system_codes import system_code_available

        assert isinstance(system_code_available("relap"), bool)
        assert isinstance(system_code_available("trace"), bool)
