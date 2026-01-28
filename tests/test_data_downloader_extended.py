"""
Extended tests for data_downloader.py to improve coverage.

This test file focuses on additional edge cases and uncovered paths:
- download_endf_data edge cases (different library formats, nuclide sets, validation scenarios)
- download_file edge cases (resume, progress bar, error handling)
- _download_parallel edge cases (progress bar, validation, errors)
- download_preprocessed_library edge cases
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
import tempfile

try:
    from smrforge.data_downloader import (
        download_endf_data,
        download_file,
        _download_parallel,
        download_preprocessed_library,
        _get_download_urls,
        _cache_successful_source,
    )
    from smrforge.core.reactor_core import Nuclide, Library
    import smrforge.data_downloader as downloader_module
    DATA_DOWNLOADER_AVAILABLE = True
except ImportError:
    DATA_DOWNLOADER_AVAILABLE = False


class TestDownloadEndfDataExtended:
    """Extended tests for download_endf_data function."""
    
    @patch('smrforge.data_downloader.REQUESTS_AVAILABLE', True)
    @patch('smrforge.data_downloader.download_file')
    @patch('smrforge.data_downloader.NuclearDataCache._validate_endf_file')
    def test_download_endf_data_string_library(self, mock_validate, mock_download):
        """Test download_endf_data with string library format."""
        if not DATA_DOWNLOADER_AVAILABLE:
            pytest.skip("Data downloader module not available")
        
        mock_download.return_value = True
        mock_validate.return_value = True
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            nuclides = [Nuclide(Z=92, A=235)]
            
            # Test with string library format
            result = downloader_module.download_endf_data(
                library="ENDF/B-VIII.1",
                nuclides=nuclides,
                output_dir=output_dir,
                show_progress=False,
                validate=False
            )
            
            assert isinstance(result, dict)
            assert "downloaded" in result
            assert "skipped" in result
            assert "failed" in result
            assert "total" in result
    
    @patch('smrforge.data_downloader.REQUESTS_AVAILABLE', True)
    @patch('smrforge.data_downloader.download_file')
    @patch('smrforge.data_downloader.NuclearDataCache._validate_endf_file')
    def test_download_endf_data_unknown_library_string(self, mock_validate, mock_download):
        """Test download_endf_data with unknown library string (should default)."""
        if not DATA_DOWNLOADER_AVAILABLE:
            pytest.skip("Data downloader module not available")
        
        mock_download.return_value = True
        mock_validate.return_value = True
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            nuclides = [Nuclide(Z=92, A=235)]
            
            # Test with unknown library string (should default to ENDF_B_VIII_1)
            result = downloader_module.download_endf_data(
                library="UNKNOWN-LIBRARY",
                nuclides=nuclides,
                output_dir=output_dir,
                show_progress=False,
                validate=False
            )
            
            assert isinstance(result, dict)
    
    @patch('smrforge.data_downloader.REQUESTS_AVAILABLE', True)
    @patch('smrforge.data_downloader.download_file')
    def test_download_endf_data_nuclide_set_common_smr(self, mock_download):
        """Test download_endf_data with nuclide_set='common_smr'."""
        if not DATA_DOWNLOADER_AVAILABLE:
            pytest.skip("Data downloader module not available")
        
        mock_download.return_value = True
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            result = downloader_module.download_endf_data(
                library=Library.ENDF_B_VIII_1,
                nuclide_set="common_smr",
                output_dir=output_dir,
                show_progress=False,
                validate=False
            )
            
            assert isinstance(result, dict)
            assert result["total"] > 0  # Should have nuclides from COMMON_SMR_NUCLIDES
    
    @patch('smrforge.data_downloader.REQUESTS_AVAILABLE', True)
    @patch('smrforge.data_downloader.download_file')
    def test_download_endf_data_with_isotopes(self, mock_download):
        """Test download_endf_data with isotopes parameter."""
        if not DATA_DOWNLOADER_AVAILABLE:
            pytest.skip("Data downloader module not available")
        
        mock_download.return_value = True
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            result = downloader_module.download_endf_data(
                library=Library.ENDF_B_VIII_1,
                isotopes=["U235", "Pu239"],
                output_dir=output_dir,
                show_progress=False,
                validate=False
            )
            
            assert isinstance(result, dict)
            assert result["total"] > 0
    
    @patch('smrforge.data_downloader.REQUESTS_AVAILABLE', True)
    @patch('smrforge.data_downloader._parse_isotope_string')
    def test_download_endf_data_no_nuclides(self, mock_parse):
        """Test download_endf_data with no nuclides specified (should raise ValueError)."""
        if not DATA_DOWNLOADER_AVAILABLE:
            pytest.skip("Data downloader module not available")
        
        # Mock _parse_isotope_string to return None for all nuclides
        # This makes COMMON_SMR_NUCLIDES parse to empty list
        mock_parse.return_value = None
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            # Test with all None - will try COMMON_SMR_NUCLIDES but all parse to None
            # Resulting in empty nuclide_list, which raises ValueError
            with pytest.raises(ValueError, match="No nuclides specified"):
                downloader_module.download_endf_data(
                    library=Library.ENDF_B_VIII_1,
                    output_dir=output_dir,
                    nuclides=None,
                    isotopes=None,
                    elements=None,
                    nuclide_set=None,
                    show_progress=False
                )
    
    @patch('smrforge.data_downloader.REQUESTS_AVAILABLE', True)
    @patch('smrforge.data_downloader.NuclearDataCache._validate_endf_file')
    @patch('smrforge.data_downloader.download_file')
    @patch('pathlib.Path.exists')
    def test_download_endf_data_resume_with_validation(self, mock_exists, mock_download, mock_validate):
        """Test download_endf_data with resume=True and validate=True."""
        if not DATA_DOWNLOADER_AVAILABLE:
            pytest.skip("Data downloader module not available")
        
        mock_exists.return_value = True  # File exists
        mock_validate.return_value = True  # Valid file
        mock_download.return_value = True
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            nuclides = [Nuclide(Z=92, A=235)]
            
            result = downloader_module.download_endf_data(
                library=Library.ENDF_B_VIII_1,
                nuclides=nuclides,
                output_dir=output_dir,
                resume=True,
                validate=True,
                show_progress=False
            )
            
            assert isinstance(result, dict)
            # File exists and is valid, should be skipped
            assert result["skipped"] > 0
    
    @patch('smrforge.data_downloader.REQUESTS_AVAILABLE', True)
    @patch('smrforge.data_downloader.NuclearDataCache._validate_endf_file')
    @patch('smrforge.data_downloader.download_file')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.unlink')
    def test_download_endf_data_resume_invalid_file(self, mock_unlink, mock_exists, mock_download, mock_validate):
        """Test download_endf_data with resume=True and invalid existing file."""
        if not DATA_DOWNLOADER_AVAILABLE:
            pytest.skip("Data downloader module not available")
        
        mock_exists.return_value = True  # File exists
        mock_validate.return_value = False  # Invalid file
        mock_download.return_value = True
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            nuclides = [Nuclide(Z=92, A=235)]
            
            result = downloader_module.download_endf_data(
                library=Library.ENDF_B_VIII_1,
                nuclides=nuclides,
                output_dir=output_dir,
                resume=True,
                validate=True,
                show_progress=False
            )
            
            assert isinstance(result, dict)
            # Invalid file should be deleted and re-downloaded
            mock_unlink.assert_called()
    
    @patch('smrforge.data_downloader.REQUESTS_AVAILABLE', True)
    @patch('smrforge.data_downloader.download_file')
    def test_download_endf_data_sequential_download(self, mock_download):
        """Test download_endf_data with sequential download (max_workers=1)."""
        if not DATA_DOWNLOADER_AVAILABLE:
            pytest.skip("Data downloader module not available")
        
        mock_download.return_value = True
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            nuclides = [Nuclide(Z=92, A=235), Nuclide(Z=92, A=238)]
            
            result = downloader_module.download_endf_data(
                library=Library.ENDF_B_VIII_1,
                nuclides=nuclides,
                output_dir=output_dir,
                max_workers=1,  # Sequential
                show_progress=False,
                validate=False
            )
            
            assert isinstance(result, dict)
            assert mock_download.called
    
    @patch('smrforge.data_downloader.REQUESTS_AVAILABLE', True)
    @patch('smrforge.data_downloader.download_file')
    @patch('smrforge.data_downloader.organize_bulk_endf_downloads')
    def test_download_endf_data_with_organize(self, mock_organize, mock_download):
        """Test download_endf_data with organize=True."""
        if not DATA_DOWNLOADER_AVAILABLE:
            pytest.skip("Data downloader module not available")
        
        mock_download.return_value = True
        mock_organize.return_value = {"files_organized": 2}
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            nuclides = [Nuclide(Z=92, A=235)]
            
            result = downloader_module.download_endf_data(
                library=Library.ENDF_B_VIII_1,
                nuclides=nuclides,
                output_dir=output_dir,
                organize=True,
                show_progress=False,
                validate=False
            )
            
            assert isinstance(result, dict)
            assert "organized" in result
            if result["downloaded"] > 0:
                mock_organize.assert_called_once()
    
    @patch('smrforge.data_downloader.REQUESTS_AVAILABLE', True)
    @patch('smrforge.data_downloader.download_file')
    @patch('smrforge.data_downloader.organize_bulk_endf_downloads')
    def test_download_endf_data_organize_no_downloads(self, mock_organize, mock_download):
        """Test download_endf_data with organize=True but no downloads."""
        if not DATA_DOWNLOADER_AVAILABLE:
            pytest.skip("Data downloader module not available")
        
        mock_download.return_value = False  # All downloads fail
        mock_organize.return_value = {"files_organized": 0}
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            nuclides = [Nuclide(Z=92, A=235)]
            
            result = downloader_module.download_endf_data(
                library=Library.ENDF_B_VIII_1,
                nuclides=nuclides,
                output_dir=output_dir,
                organize=True,
                show_progress=False,
                validate=False
            )
            
            assert isinstance(result, dict)
            # Should not organize if no files downloaded
            mock_organize.assert_not_called()
    
    @patch('smrforge.data_downloader.REQUESTS_AVAILABLE', True)
    @patch('smrforge.data_downloader.download_file')
    @patch('smrforge.data_downloader.NuclearDataCache._validate_endf_file')
    def test_download_endf_data_sequential_with_validation(self, mock_validate, mock_download):
        """Test sequential download with validation."""
        if not DATA_DOWNLOADER_AVAILABLE:
            pytest.skip("Data downloader module not available")
        
        mock_download.return_value = True
        mock_validate.return_value = True
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            nuclides = [Nuclide(Z=92, A=235)]
            
            result = downloader_module.download_endf_data(
                library=Library.ENDF_B_VIII_1,
                nuclides=nuclides,
                output_dir=output_dir,
                max_workers=1,
                validate=True,
                show_progress=False
            )
            
            assert isinstance(result, dict)
            mock_validate.assert_called()
    
    @patch('smrforge.data_downloader.REQUESTS_AVAILABLE', True)
    @patch('smrforge.data_downloader.download_file')
    @patch('smrforge.data_downloader.NuclearDataCache._validate_endf_file')
    @patch('pathlib.Path.unlink')
    def test_download_endf_data_sequential_invalid_then_valid(self, mock_unlink, mock_validate, mock_download):
        """Test sequential download where first URL fails validation, second succeeds."""
        if not DATA_DOWNLOADER_AVAILABLE:
            pytest.skip("Data downloader module not available")
        
        # First download succeeds but validation fails, second succeeds
        call_count = 0
        def mock_download_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return True
        
        def mock_validate_side_effect(filepath):
            nonlocal call_count
            # First call fails, subsequent succeed
            if call_count == 1:
                return False
            return True
        
        mock_download.side_effect = mock_download_side_effect
        mock_validate.side_effect = mock_validate_side_effect
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            nuclides = [Nuclide(Z=92, A=235)]
            
            result = downloader_module.download_endf_data(
                library=Library.ENDF_B_VIII_1,
                nuclides=nuclides,
                output_dir=output_dir,
                max_workers=1,
                validate=True,
                show_progress=False
            )
            
            assert isinstance(result, dict)
            # Should try multiple URLs if first fails validation
            assert mock_download.call_count >= 1


class TestDownloadFileExtended:
    """Extended tests for download_file function."""
    
    @patch('smrforge.data_downloader.REQUESTS_AVAILABLE', True)
    @patch('smrforge.data_downloader.requests')
    @patch('builtins.open', create=True)
    def test_download_file_with_progress_bar(self, mock_open, mock_requests):
        """Test download_file with progress bar (tqdm available or not)."""
        if not DATA_DOWNLOADER_AVAILABLE:
            pytest.skip("Data downloader module not available")
        
        from pathlib import Path
        from unittest.mock import MagicMock
        
        # Mock response
        mock_response = MagicMock()
        mock_response.headers = {'content-length': '1000'}
        mock_response.iter_content.return_value = [b'chunk1', b'chunk2']
        mock_response.raise_for_status = MagicMock()
        
        # Mock session
        mock_session = MagicMock()
        mock_session.get.return_value = mock_response
        mock_requests.Session.return_value = mock_session
        
        # Mock file
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        mock_open.return_value.__exit__ = MagicMock(return_value=False)
        
        # Mock path stat for initial position
        with patch('pathlib.Path.exists', return_value=False):
            # Test download with progress bar (will use tqdm if available, otherwise skip)
            success = downloader_module.download_file(
                "https://example.com/file.endf",
                Path("file.endf"),
                show_progress=True
            )
        
        assert success is True
        # Download should succeed regardless of tqdm availability
    
    @patch('smrforge.data_downloader.REQUESTS_AVAILABLE', True)
    @patch('smrforge.data_downloader.requests')
    @patch('builtins.open', create=True)
    def test_download_file_with_provided_session(self, mock_open, mock_requests):
        """Test download_file with provided session."""
        if not DATA_DOWNLOADER_AVAILABLE:
            pytest.skip("Data downloader module not available")
        
        from pathlib import Path
        from unittest.mock import MagicMock
        
        # Mock response
        mock_response = MagicMock()
        mock_response.headers = {'content-length': '1000'}
        mock_response.iter_content.return_value = [b'chunk1']
        mock_response.raise_for_status = MagicMock()
        
        # Mock provided session
        mock_session = MagicMock()
        mock_session.get.return_value = mock_response
        
        # Mock file
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Test download with provided session
        success = downloader_module.download_file(
            "https://example.com/file.endf",
            Path("file.endf"),
            session=mock_session,
            show_progress=False
        )
        
        assert success is True
        # Should not create new session
        mock_requests.Session.assert_not_called()
        mock_session.get.assert_called_once()
    
    @patch('smrforge.data_downloader.REQUESTS_AVAILABLE', True)
    @patch('smrforge.data_downloader.requests')
    @patch('builtins.open', create=True)
    def test_download_file_no_content_length(self, mock_open, mock_requests):
        """Test download_file with response having no content-length header."""
        if not DATA_DOWNLOADER_AVAILABLE:
            pytest.skip("Data downloader module not available")
        
        from pathlib import Path
        from unittest.mock import MagicMock
        
        # Mock response without content-length
        mock_response = MagicMock()
        mock_response.headers = {}  # No content-length
        mock_response.iter_content.return_value = [b'chunk1']
        mock_response.raise_for_status = MagicMock()
        
        # Mock session
        mock_session = MagicMock()
        mock_session.get.return_value = mock_response
        mock_requests.Session.return_value = mock_session
        
        # Mock file
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Test download
        success = downloader_module.download_file(
            "https://example.com/file.endf",
            Path("file.endf"),
            show_progress=False
        )
        
        assert success is True
    
    @patch('smrforge.data_downloader.REQUESTS_AVAILABLE', True)
    @patch('smrforge.data_downloader.requests')
    @patch('builtins.open', create=True)
    def test_download_file_empty_chunks(self, mock_open, mock_requests):
        """Test download_file with empty chunks in response."""
        if not DATA_DOWNLOADER_AVAILABLE:
            pytest.skip("Data downloader module not available")
        
        from pathlib import Path
        from unittest.mock import MagicMock
        
        # Mock response with empty chunks
        mock_response = MagicMock()
        mock_response.headers = {'content-length': '1000'}
        mock_response.iter_content.return_value = [b'chunk1', b'', b'chunk2', b'']  # Empty chunks
        mock_response.raise_for_status = MagicMock()
        
        # Mock session
        mock_session = MagicMock()
        mock_session.get.return_value = mock_response
        mock_requests.Session.return_value = mock_session
        
        # Mock file
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Test download
        success = downloader_module.download_file(
            "https://example.com/file.endf",
            Path("file.endf"),
            show_progress=False
        )
        
        assert success is True
        # Should only write non-empty chunks
        assert mock_file.write.call_count >= 2


class TestDownloadParallelExtended:
    """Extended tests for _download_parallel function."""
    
    @patch('smrforge.data_downloader.REQUESTS_AVAILABLE', True)
    @patch('smrforge.data_downloader.download_file')
    @patch('smrforge.data_downloader.NuclearDataCache._validate_endf_file')
    def test_download_parallel_with_progress_bar(self, mock_validate, mock_download):
        """Test _download_parallel with progress bar (tqdm available or not)."""
        if not DATA_DOWNLOADER_AVAILABLE:
            pytest.skip("Data downloader module not available")
        
        from pathlib import Path
        
        mock_download.return_value = True
        mock_validate.return_value = True
        
        nuclides = [Nuclide(Z=92, A=235), Nuclide(Z=92, A=238)]
        download_tasks = [
            (nuclide, Path(f"test_{nuclide.A}.endf"), ["http://example.com/file.endf"])
            for nuclide in nuclides
        ]
        stats = {"downloaded": 0, "failed": 0}
        
        downloader_module._download_parallel(
            download_tasks=download_tasks,
            stats=stats,
            session=None,
            resume=True,
            show_progress=True,
            validate=True,
            library=Library.ENDF_B_VIII_1,
            max_workers=2
        )
        
        assert stats["downloaded"] == 2
        # Download should succeed regardless of tqdm availability
    
    @patch('smrforge.data_downloader.REQUESTS_AVAILABLE', True)
    @patch('smrforge.data_downloader.download_file')
    @patch('smrforge.data_downloader.NuclearDataCache._validate_endf_file')
    @patch('pathlib.Path.unlink')
    def test_download_parallel_validation_failure(self, mock_unlink, mock_validate, mock_download):
        """Test _download_parallel with validation failures."""
        if not DATA_DOWNLOADER_AVAILABLE:
            pytest.skip("Data downloader module not available")
        
        from pathlib import Path
        
        # First URL fails validation, second succeeds
        mock_download.return_value = True
        mock_validate.side_effect = [False, True]  # First fails, second succeeds
        
        nuclides = [Nuclide(Z=92, A=235)]
        download_tasks = [
            (nuclides[0], Path("test.endf"), ["http://url1.com/file.endf", "http://url2.com/file.endf"])
        ]
        stats = {"downloaded": 0, "failed": 0}
        
        downloader_module._download_parallel(
            download_tasks=download_tasks,
            stats=stats,
            session=None,
            resume=True,
            show_progress=False,
            validate=True,
            library=Library.ENDF_B_VIII_1,
            max_workers=1
        )
        
        # Should succeed after trying second URL
        assert stats["downloaded"] == 1
        assert stats["failed"] == 0
    
    @patch('smrforge.data_downloader.REQUESTS_AVAILABLE', True)
    @patch('smrforge.data_downloader.download_file')
    def test_download_parallel_all_fail(self, mock_download):
        """Test _download_parallel when all downloads fail."""
        if not DATA_DOWNLOADER_AVAILABLE:
            pytest.skip("Data downloader module not available")
        
        from pathlib import Path
        
        mock_download.return_value = False  # All downloads fail
        
        nuclides = [Nuclide(Z=92, A=235)]
        download_tasks = [
            (nuclides[0], Path("test.endf"), ["http://url1.com/file.endf"])
        ]
        stats = {"downloaded": 0, "failed": 0}
        
        downloader_module._download_parallel(
            download_tasks=download_tasks,
            stats=stats,
            session=None,
            resume=True,
            show_progress=False,
            validate=False,
            library=Library.ENDF_B_VIII_1,
            max_workers=1
        )
        
        assert stats["downloaded"] == 0
        assert stats["failed"] == 1
    
    @patch('smrforge.data_downloader.REQUESTS_AVAILABLE', True)
    @patch('smrforge.data_downloader.download_file')
    @patch('smrforge.data_downloader._cache_successful_source')
    def test_download_parallel_caches_successful_source(self, mock_cache, mock_download):
        """Test _download_parallel caches successful source URL."""
        if not DATA_DOWNLOADER_AVAILABLE:
            pytest.skip("Data downloader module not available")
        
        from pathlib import Path
        
        mock_download.return_value = True
        
        nuclides = [Nuclide(Z=92, A=235)]
        test_url = "http://example.com/file.endf"
        download_tasks = [
            (nuclides[0], Path("test.endf"), [test_url])
        ]
        stats = {"downloaded": 0, "failed": 0}
        
        downloader_module._download_parallel(
            download_tasks=download_tasks,
            stats=stats,
            session=None,
            resume=True,
            show_progress=False,
            validate=False,
            library=Library.ENDF_B_VIII_1,
            max_workers=1
        )
        
        assert stats["downloaded"] == 1
        mock_cache.assert_called_once_with(test_url, Library.ENDF_B_VIII_1)
    
    @patch('smrforge.data_downloader.REQUESTS_AVAILABLE', True)
    @patch('smrforge.data_downloader.TQDM_AVAILABLE', False)
    @patch('smrforge.data_downloader.download_file')
    def test_download_parallel_no_tqdm(self, mock_download):
        """Test _download_parallel when tqdm is not available."""
        if not DATA_DOWNLOADER_AVAILABLE:
            pytest.skip("Data downloader module not available")
        
        from pathlib import Path
        
        mock_download.return_value = True
        
        nuclides = [Nuclide(Z=92, A=235)]
        download_tasks = [
            (nuclides[0], Path("test.endf"), ["http://example.com/file.endf"])
        ]
        stats = {"downloaded": 0, "failed": 0}
        
        # Should work without tqdm
        downloader_module._download_parallel(
            download_tasks=download_tasks,
            stats=stats,
            session=None,
            resume=True,
            show_progress=True,  # Request progress but tqdm not available
            validate=False,
            library=Library.ENDF_B_VIII_1,
            max_workers=1
        )
        
        assert stats["downloaded"] == 1


class TestDownloadPreprocessedLibraryExtended:
    """Extended tests for download_preprocessed_library function."""
    
    @patch('smrforge.data_downloader.download_endf_data')
    @patch('smrforge.data_downloader.REQUESTS_AVAILABLE', True)
    def test_download_preprocessed_library_with_nuclide_list(self, mock_download):
        """Test download_preprocessed_library with nuclide list."""
        if not DATA_DOWNLOADER_AVAILABLE:
            pytest.skip("Data downloader module not available")
        
        mock_download.return_value = {
            "downloaded": 2,
            "skipped": 0,
            "failed": 0,
            "total": 2
        }
        
        nuclides = [Nuclide(Z=92, A=235), Nuclide(Z=92, A=238)]
        
        result = downloader_module.download_preprocessed_library(
            library=Library.ENDF_B_VIII_1,
            nuclides=nuclides,
            output_dir=Path("test_dir"),
            show_progress=False
        )
        
        assert isinstance(result, dict)
        mock_download.assert_called_once()
        call_kwargs = mock_download.call_args[1]
        assert call_kwargs['nuclides'] == nuclides


class TestDownloadEndfDataCoverage90:
    """Tests to push data_downloader coverage toward 90%."""

    @patch('smrforge.data_downloader.REQUESTS_AVAILABLE', False)
    def test_download_endf_data_requests_unavailable_raises(self):
        """download_endf_data raises ImportError when requests not available."""
        if not DATA_DOWNLOADER_AVAILABLE:
            pytest.skip("Data downloader module not available")
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ImportError, match="requests"):
                downloader_module.download_endf_data(
                    library=Library.ENDF_B_VIII_1,
                    output_dir=Path(tmpdir),
                    nuclides=[Nuclide(Z=92, A=235)],
                    show_progress=False,
                )

    @patch('smrforge.data_downloader.REQUESTS_AVAILABLE', True)
    @patch('smrforge.data_downloader.download_file')
    @patch('smrforge.data_downloader.NuclearDataCache._validate_endf_file')
    def test_download_endf_data_default_uses_common_smr(self, mock_validate, mock_download):
        """When no nuclides/isotopes/elements/nuclide_set, uses common_smr and logs warning."""
        if not DATA_DOWNLOADER_AVAILABLE:
            pytest.skip("Data downloader module not available")
        mock_download.return_value = True
        mock_validate.return_value = True
        with tempfile.TemporaryDirectory() as tmpdir:
            result = downloader_module.download_endf_data(
                library=Library.ENDF_B_VIII_1,
                output_dir=Path(tmpdir),
                nuclides=None,
                isotopes=None,
                elements=None,
                nuclide_set=None,
                show_progress=False,
                validate=False,
            )
            assert isinstance(result, dict)
            assert result["total"] > 0
            assert "downloaded" in result

    @patch('smrforge.data_downloader.REQUESTS_AVAILABLE', True)
    def test_expand_elements_to_nuclides_unknown_element_skipped(self):
        """_expand_elements_to_nuclides with unknown element skips it and returns empty for that element."""
        if not DATA_DOWNLOADER_AVAILABLE:
            pytest.skip("Data downloader module not available")
        nuclides = downloader_module._expand_elements_to_nuclides(["Xx"], Library.ENDF_B_VIII_1)
        assert nuclides == []
        # Mixed invalid + valid: invalid skipped, valid expanded
        nuclides_mixed = downloader_module._expand_elements_to_nuclides(["Xx", "U"], Library.ENDF_B_VIII_1)
        assert isinstance(nuclides_mixed, list)
        assert len(nuclides_mixed) > 0
        assert all(n.Z == 92 for n in nuclides_mixed)

    @patch('smrforge.data_downloader.REQUESTS_AVAILABLE', True)
    @patch('smrforge.data_downloader.download_file')
    def test_download_endf_data_organize_called_after_downloads(self, mock_download):
        """When organize=True and some downloads succeed, organize_bulk_endf_downloads is called."""
        if not DATA_DOWNLOADER_AVAILABLE:
            pytest.skip("Data downloader module not available")
        mock_download.return_value = True
        with patch('smrforge.data_downloader.organize_bulk_endf_downloads') as mock_organize:
            mock_organize.return_value = {"files_organized": 1}
            with tempfile.TemporaryDirectory() as tmpdir:
                out = Path(tmpdir)
                result = downloader_module.download_endf_data(
                    library=Library.ENDF_B_VIII_1,
                    nuclides=[Nuclide(Z=92, A=235)],
                    output_dir=out,
                    organize=True,
                    show_progress=False,
                    validate=False,
                )
                if result.get("downloaded", 0) > 0:
                    mock_organize.assert_called_once()

    @patch('smrforge.data_downloader.REQUESTS_AVAILABLE', True)
    @patch('smrforge.data_downloader.download_file')
    def test_download_endf_data_organize_uses_viii0_for_endf_b_viii(self, mock_download):
        """When library=ENDF_B_VIII and organize=True with downloads, organize uses library_version VIII.0."""
        if not DATA_DOWNLOADER_AVAILABLE:
            pytest.skip("Data downloader module not available")
        mock_download.return_value = True
        with patch('smrforge.data_downloader.organize_bulk_endf_downloads') as mock_organize:
            mock_organize.return_value = {"files_organized": 1}
            with tempfile.TemporaryDirectory() as tmpdir:
                out = Path(tmpdir)
                downloader_module.download_endf_data(
                    library=Library.ENDF_B_VIII,
                    nuclides=[Nuclide(Z=92, A=235)],
                    output_dir=out,
                    organize=True,
                    show_progress=False,
                    validate=False,
                )
                if mock_organize.called:
                    call_kw = mock_organize.call_args[1]
                    assert call_kw.get("library_version") == "VIII.0"

    @patch('smrforge.data_downloader.REQUESTS_AVAILABLE', True)
    @patch('smrforge.data_downloader.download_endf_data')
    def test_download_preprocessed_library_nuclides_list_calls_download_endf_data(self, mock_download):
        """download_preprocessed_library with nuclides list calls download_endf_data with nuclides kwarg."""
        if not DATA_DOWNLOADER_AVAILABLE:
            pytest.skip("Data downloader module not available")
        mock_download.return_value = {"downloaded": 2, "skipped": 0, "failed": 0, "total": 2}
        nuclides = [Nuclide(Z=92, A=235), Nuclide(Z=92, A=238)]
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir)
            downloader_module.download_preprocessed_library(
                library=Library.ENDF_B_VIII_1,
                nuclides=nuclides,
                output_dir=out,
                show_progress=False,
            )
            mock_download.assert_called_once()
            call_kw = mock_download.call_args[1]
            assert call_kw.get("nuclides") == nuclides
            assert "nuclide_set" not in call_kw or call_kw.get("nuclide_set") is None


class TestHelperFunctionsAdditional:
    """Additional edge case tests for helper functions."""
    
    def test_parse_isotope_string_edge_cases(self):
        """Test _parse_isotope_string with various edge cases."""
        if not DATA_DOWNLOADER_AVAILABLE:
            pytest.skip("Data downloader module not available")
        
        # Test whitespace handling
        result = downloader_module._parse_isotope_string("  U235  ")
        assert result is not None
        assert result.Z == 92
        assert result.A == 235
        
        # Test lowercase symbol (may or may not work depending on regex)
        result = downloader_module._parse_isotope_string("u235")
        # May return None if regex requires uppercase, which is fine
        if result is not None:
            assert result.Z == 92
        
        # Test invalid format (numbers first)
        result = downloader_module._parse_isotope_string("235U")
        assert result is None
        
        # Test only letters
        result = downloader_module._parse_isotope_string("Uranium")
        assert result is None
        
        # Test only numbers
        result = downloader_module._parse_isotope_string("235")
        assert result is None
        
        # Test metastable with uppercase M (may or may not work depending on implementation)
        result = downloader_module._parse_isotope_string("U239M1")
        if result is not None:
            assert result.m == 1
        
        # Test metastable without number (may default to m1 or return None)
        result = downloader_module._parse_isotope_string("U239m")
        if result is not None:
            assert result.m >= 0  # Should have metastable state if parsed
    
    def test_expand_elements_to_nuclides_edge_cases(self):
        """Test _expand_elements_to_nuclides with edge cases."""
        if not DATA_DOWNLOADER_AVAILABLE:
            pytest.skip("Data downloader module not available")
        
        # Test unknown element
        nuclides = downloader_module._expand_elements_to_nuclides(["Xx"], Library.ENDF_B_VIII_1)
        assert nuclides == []
        
        # Test element not in common isotopes dict
        nuclides = downloader_module._expand_elements_to_nuclides(["He"], Library.ENDF_B_VIII_1)
        # Should return empty list or minimal list
        assert isinstance(nuclides, list)
        
        # Test mixed valid/invalid elements
        nuclides = downloader_module._expand_elements_to_nuclides(["U", "Xx", "Pu"], Library.ENDF_B_VIII_1)
        assert isinstance(nuclides, list)
        assert len(nuclides) > 0
        z_values = {nuclide.Z for nuclide in nuclides}
        assert 92 in z_values  # Uranium
        assert 94 in z_values  # Plutonium

    def test_expand_elements_to_nuclides_element_not_in_common_isotopes(self):
        """Test _expand_elements_to_nuclides with element in SYMBOL_TO_Z but not in common_isotopes."""
        if not DATA_DOWNLOADER_AVAILABLE:
            pytest.skip("Data downloader module not available")
        # Nitrogen (N) is in SYMBOL_TO_Z but not in data_downloader common_isotopes dict
        nuclides = downloader_module._expand_elements_to_nuclides(["N"], Library.ENDF_B_VIII_1)
        assert isinstance(nuclides, list)
        assert len(nuclides) == 0
    
    def test_get_nndc_url_fallback_edge_cases(self):
        """Test _get_nndc_url fallback behavior."""
        if not DATA_DOWNLOADER_AVAILABLE:
            pytest.skip("Data downloader module not available")
        
        nuclide = Nuclide(Z=92, A=235)
        
        # Test unsupported library (should fallback to IAEA)
        url = downloader_module._get_nndc_url(nuclide, Library.JEFF_33)
        assert isinstance(url, str)
        # Should fallback to IAEA URL
        assert "iaea" in url.lower() or "jeff" in url.lower()
        
        # Test JENDL-5 (should fallback)
        url = downloader_module._get_nndc_url(nuclide, Library.JENDL_5)
        assert isinstance(url, str)
        assert "iaea" in url.lower() or "jendl" in url.lower()
    
    def test_cache_successful_source_edge_cases(self):
        """Test _cache_successful_source with edge cases."""
        if not DATA_DOWNLOADER_AVAILABLE:
            pytest.skip("Data downloader module not available")
        
        # Clear cache first
        downloader_module._source_cache.clear()
        
        # Test URL that doesn't match either pattern (should not crash)
        downloader_module._cache_successful_source(
            "https://example.com/file.endf",
            Library.ENDF_B_VIII_1
        )
        # Should not add to cache
        assert Library.ENDF_B_VIII_1.value not in downloader_module._source_cache
        
        # Test URL with partial match
        downloader_module._cache_successful_source(
            "https://www.nndc.bnl.gov/other/path/file.endf",
            Library.ENDF_B_VIII_1
        )
        # Should cache as nndc
        assert downloader_module._source_cache.get(Library.ENDF_B_VIII_1.value) == "nndc"
    
    @patch('smrforge.data_downloader.REQUESTS_AVAILABLE', True)
    @patch('smrforge.data_downloader.requests')
    @patch('builtins.open', create=True)
    def test_download_file_error_handling(self, mock_open, mock_requests):
        """Test download_file error handling paths."""
        if not DATA_DOWNLOADER_AVAILABLE:
            pytest.skip("Data downloader module not available")
        
        from pathlib import Path
        from unittest.mock import MagicMock
        
        # Test HTTP error (404)
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")
        mock_session = MagicMock()
        mock_session.get.return_value = mock_response
        mock_requests.Session.return_value = mock_session
        
        success = downloader_module.download_file(
            "https://example.com/file.endf",
            Path("file.endf"),
            session=mock_session,
            show_progress=False
        )
        assert success is False
        
        # Test network timeout
        mock_session.get.side_effect = Exception("Connection timeout")
        
        success = downloader_module.download_file(
            "https://example.com/file.endf",
            Path("file.endf"),
            session=mock_session,
            show_progress=False
        )
        assert success is False
    
    @patch('smrforge.data_downloader.REQUESTS_AVAILABLE', True)
    @patch('smrforge.data_downloader.requests')
    @patch('builtins.open', create=True)
    def test_download_file_resume_edge_cases(self, mock_open, mock_requests):
        """Test download_file resume functionality edge cases."""
        if not DATA_DOWNLOADER_AVAILABLE:
            pytest.skip("Data downloader module not available")
        
        from pathlib import Path
        from unittest.mock import MagicMock
        
        # Mock existing file
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.stat') as mock_stat:
                mock_stat.return_value.st_size = 100
                
                # Mock response with Range header support
                mock_response = MagicMock()
                mock_response.headers = {'content-length': '900', 'content-range': 'bytes 100-999/1000'}
                mock_response.iter_content.return_value = [b'chunk1', b'chunk2']
                mock_response.raise_for_status = MagicMock()
                
                mock_session = MagicMock()
                mock_session.get.return_value = mock_response
                mock_requests.Session.return_value = mock_session
                
                # Mock file
                mock_file = MagicMock()
                mock_open.return_value.__enter__.return_value = mock_file
                mock_open.return_value.__exit__ = MagicMock(return_value=False)
                
                # Test resume with existing file
                success = downloader_module.download_file(
                    "https://example.com/file.endf",
                    Path("file.endf"),
                    resume=True,
                    show_progress=False,
                    session=mock_session
                )
                assert success is True
                # Should use append mode
                assert mock_open.call_args[0][1] == "ab"
                
                # Check that Range header was set
                call_kwargs = mock_session.get.call_args[1]
                assert "Range" in call_kwargs.get("headers", {})
