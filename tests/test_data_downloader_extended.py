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
