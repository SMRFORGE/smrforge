"""Comprehensive tests for _get_endf_url static method."""

import pytest

from smrforge.core.reactor_core import Library, NuclearDataCache, Nuclide


class TestGetEndfUrl:
    """Test _get_endf_url static method comprehensively."""

    def test_get_endf_url_endf_b_viii(self):
        """Test _get_endf_url with ENDF/B-VIII library."""
        nuc = Nuclide(Z=92, A=235, m=0)
        url = NuclearDataCache._get_endf_url(nuc, Library.ENDF_B_VIII)
        
        assert isinstance(url, str)
        assert "www-nds.iaea.org" in url
        assert "endfb8.0" in url
        assert "U_235" in url or "U235" in url  # URL uses U_235 format
        assert url.endswith(".endf")

    def test_get_endf_url_jeff_33(self):
        """Test _get_endf_url with JEFF-3.3 library."""
        nuc = Nuclide(Z=92, A=238, m=0)
        url = NuclearDataCache._get_endf_url(nuc, Library.JEFF_33)
        
        assert isinstance(url, str)
        assert "www-nds.iaea.org" in url
        assert "jeff3.3" in url
        assert "U_238" in url or "U238" in url  # URL uses U_238 format
        assert url.endswith(".endf")

    def test_get_endf_url_jendl_5(self):
        """Test _get_endf_url with JENDL-5.0 library."""
        nuc = Nuclide(Z=94, A=239, m=0)
        url = NuclearDataCache._get_endf_url(nuc, Library.JENDL_5)
        
        assert isinstance(url, str)
        assert "www-nds.iaea.org" in url
        assert "jendl5.0" in url
        assert "Pu_239" in url or "Pu239" in url  # URL uses Pu_239 format
        assert url.endswith(".endf")

    def test_get_endf_url_different_nuclides(self):
        """Test _get_endf_url with various nuclides."""
        test_cases = [
            (Nuclide(Z=1, A=1, m=0), ["H_001", "H1"]),
            (Nuclide(Z=2, A=4, m=0), ["He_004", "He4"]),
            (Nuclide(Z=6, A=12, m=0), ["C_012", "C12"]),
            (Nuclide(Z=92, A=235, m=0), ["U_235", "U235"]),
            (Nuclide(Z=92, A=238, m=0), ["U_238", "U238"]),
            (Nuclide(Z=94, A=239, m=0), ["Pu_239", "Pu239"]),
            (Nuclide(Z=94, A=240, m=0), ["Pu_240", "Pu240"]),
        ]
        
        for nuc, expected_names in test_cases:
            url = NuclearDataCache._get_endf_url(nuc, Library.ENDF_B_VIII)
            assert any(name in url for name in expected_names), f"None of {expected_names} found in {url}"
            assert url.endswith(".endf")

    def test_get_endf_url_metastable_nuclides(self):
        """Test _get_endf_url with metastable nuclides."""
        # Test metastable states (m > 0)
        nuc_meta = Nuclide(Z=92, A=239, m=1)
        url = NuclearDataCache._get_endf_url(nuc_meta, Library.ENDF_B_VIII)
        
        assert isinstance(url, str)
        assert "U_239m1" in url or "U239m1" in url or "U_239" in url or "U239" in url  # URL format uses underscores
        assert url.endswith(".endf")

    def test_get_endf_url_url_structure(self):
        """Test that _get_endf_url produces correct URL structure."""
        nuc = Nuclide(Z=92, A=235, m=0)
        url = NuclearDataCache._get_endf_url(nuc, Library.ENDF_B_VIII)
        
        # URL should follow pattern: base_url/library/nuclide.endf
        parts = url.split("/")
        assert len(parts) >= 3
        assert "https:" in parts[0]
        assert "www-nds.iaea.org" in url
        assert "endfb8.0" in parts
        assert "U_235.endf" in parts[-1] or "U235.endf" in parts[-1]  # URL format uses underscores

    def test_get_endf_url_all_libraries(self):
        """Test _get_endf_url with all supported libraries."""
        nuc = Nuclide(Z=92, A=235, m=0)
        
        libraries = [Library.ENDF_B_VIII, Library.JEFF_33, Library.JENDL_5]
        
        for library in libraries:
            url = NuclearDataCache._get_endf_url(nuc, library)
            assert isinstance(url, str)
            assert library.value in url
            assert "U_235" in url or "U235" in url  # URL format uses underscores
            assert url.endswith(".endf")

    def test_get_endf_url_large_atomic_number(self):
        """Test _get_endf_url with large atomic numbers."""
        # Test with heavy elements
        nuc = Nuclide(Z=98, A=252, m=0)  # Californium-252
        url = NuclearDataCache._get_endf_url(nuc, Library.ENDF_B_VIII)
        
        assert isinstance(url, str)
        assert "Cf_252" in url or "Cf252" in url  # URL format uses underscores
        assert url.endswith(".endf")

    def test_get_endf_url_large_mass_number(self):
        """Test _get_endf_url with large mass numbers."""
        nuc = Nuclide(Z=92, A=236, m=0)
        url = NuclearDataCache._get_endf_url(nuc, Library.ENDF_B_VIII)
        
        assert isinstance(url, str)
        assert "U_236" in url or "U236" in url  # URL format uses underscores
        assert url.endswith(".endf")

    def test_get_endf_url_multiple_metastable_states(self):
        """Test _get_endf_url with different metastable state indices."""
        nuc_m1 = Nuclide(Z=92, A=239, m=1)
        nuc_m2 = Nuclide(Z=92, A=239, m=2)
        
        url1 = NuclearDataCache._get_endf_url(nuc_m1, Library.ENDF_B_VIII)
        url2 = NuclearDataCache._get_endf_url(nuc_m2, Library.ENDF_B_VIII)
        
        assert isinstance(url1, str)
        assert isinstance(url2, str)
        # Both should contain the nuclide name (might differ in metastable notation)
        assert url1.endswith(".endf")
        assert url2.endswith(".endf")

    def test_get_endf_url_light_nuclei(self):
        """Test _get_endf_url with light nuclei."""
        light_nuclei = [
            Nuclide(Z=1, A=1, m=0),   # Hydrogen-1
            Nuclide(Z=1, A=2, m=0),   # Deuterium
            Nuclide(Z=2, A=3, m=0),   # Helium-3
            Nuclide(Z=2, A=4, m=0),   # Helium-4
        ]
        
        for nuc in light_nuclei:
            url = NuclearDataCache._get_endf_url(nuc, Library.ENDF_B_VIII)
            assert isinstance(url, str)
            assert url.endswith(".endf")
            # Verify nuclide name or URL format is in URL (URL uses underscores like H_001, He_003)
            from smrforge.core.constants import ELEMENT_SYMBOLS
            symbol = ELEMENT_SYMBOLS[nuc.Z]
            url_format = f"{symbol}_{nuc.A:03d}"
            assert nuc.name in url or url_format in url, f"Neither {nuc.name} nor {url_format} found in {url}"

    def test_get_endf_url_consistency(self):
        """Test that _get_endf_url produces consistent URLs for same inputs."""
        nuc = Nuclide(Z=92, A=235, m=0)
        library = Library.ENDF_B_VIII
        
        url1 = NuclearDataCache._get_endf_url(nuc, library)
        url2 = NuclearDataCache._get_endf_url(nuc, library)
        
        # Should produce identical URLs
        assert url1 == url2

    def test_get_endf_url_https_protocol(self):
        """Test that _get_endf_url uses HTTPS protocol."""
        nuc = Nuclide(Z=92, A=235, m=0)
        url = NuclearDataCache._get_endf_url(nuc, Library.ENDF_B_VIII)
        
        assert url.startswith("https://")

    def test_get_endf_url_iaea_domain(self):
        """Test that _get_endf_url uses IAEA domain."""
        nuc = Nuclide(Z=92, A=235, m=0)
        url = NuclearDataCache._get_endf_url(nuc, Library.ENDF_B_VIII)
        
        assert "iaea.org" in url

    def test_get_endf_url_file_extension(self):
        """Test that _get_endf_url includes .endf file extension."""
        nuc = Nuclide(Z=92, A=235, m=0)
        url = NuclearDataCache._get_endf_url(nuc, Library.ENDF_B_VIII)
        
        assert url.endswith(".endf")
        # Should not have double extension
        assert not url.endswith(".endf.endf")

    def test_get_endf_url_library_value_in_url(self):
        """Test that library enum value appears in URL."""
        nuc = Nuclide(Z=92, A=235, m=0)
        
        test_libraries = {
            Library.ENDF_B_VIII: "endfb8.0",
            Library.JEFF_33: "jeff3.3",
            Library.JENDL_5: "jendl5.0",
        }
        
        for library, expected_value in test_libraries.items():
            url = NuclearDataCache._get_endf_url(nuc, library)
            assert expected_value in url

