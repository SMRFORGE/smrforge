"""
Comprehensive tests for help.py to improve coverage to 75-80%.

Tests cover:
- Main help function (help())
- Category help functions (_show_category_help, _help_geometry, etc.)
- Object help functions (_show_object_help, _show_examples_for_object)
- Topic help functions (_show_topic_help)
- Error handling for missing rich library
- Edge cases (missing objects, invalid topics, etc.)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


class TestHelpFunction:
    """Test main help function."""

    def test_help_no_args(self):
        """Test help() with no arguments."""
        try:
            from smrforge.help import help
            # Should not raise - just prints
            help()
        except ImportError:
            pytest.skip("rich not available")

    def test_help_with_topic_string(self):
        """Test help() with topic as string."""
        try:
            from smrforge.help import help
            help("geometry")
        except ImportError:
            pytest.skip("rich not available")

    def test_help_with_topic_object(self):
        """Test help() with topic as object."""
        try:
            from smrforge.help import help
            from smrforge.convenience import create_reactor
            help(create_reactor)
        except ImportError:
            pytest.skip("rich not available")

    def test_help_with_category(self):
        """Test help() with category parameter."""
        try:
            from smrforge.help import help
            help("geometry", category="geometry")
        except ImportError:
            pytest.skip("rich not available")

    def test_help_with_show_examples_false(self):
        """Test help() with show_examples=False."""
        try:
            from smrforge.help import help
            help("geometry", show_examples=False)
        except ImportError:
            pytest.skip("rich not available")

    def test_help_no_rich_plain(self):
        """Test help() when rich is not available (plain text fallback)."""
        with patch('smrforge.help._RICH_AVAILABLE', False):
            from smrforge.help import help, _print_help_plain
            # Should call plain text version
            help("geometry")


class TestCategoryHelp:
    """Test category help functions."""

    def test_help_geometry(self):
        """Test geometry category help."""
        try:
            from smrforge.help import _help_geometry
            from smrforge.help import Console
            
            console = Console()
            _help_geometry(console, show_examples=True)
        except ImportError:
            pytest.skip("rich not available")

    def test_help_neutronics(self):
        """Test neutronics category help."""
        try:
            from smrforge.help import _help_neutronics
            from smrforge.help import Console
            
            console = Console()
            _help_neutronics(console, show_examples=True)
        except ImportError:
            pytest.skip("rich not available")

    def test_help_burnup(self):
        """Test burnup category help."""
        try:
            from smrforge.help import _help_burnup
            from smrforge.help import Console
            
            console = Console()
            _help_burnup(console, show_examples=True)
        except ImportError:
            pytest.skip("rich not available")

    def test_help_thermal(self):
        """Test thermal category help."""
        try:
            from smrforge.help import _help_thermal
            from smrforge.help import Console
            
            console = Console()
            _help_thermal(console, show_examples=True)
        except ImportError:
            pytest.skip("rich not available")

    def test_help_decay(self):
        """Test decay category help."""
        try:
            from smrforge.help import _help_decay
            from smrforge.help import Console
            
            console = Console()
            _help_decay(console, show_examples=True)
        except ImportError:
            pytest.skip("rich not available")

    def test_help_gamma(self):
        """Test gamma category help."""
        try:
            from smrforge.help import _help_gamma
            from smrforge.help import Console
            
            console = Console()
            _help_gamma(console, show_examples=True)
        except ImportError:
            pytest.skip("rich not available")

    def test_help_visualization(self):
        """Test visualization category help."""
        try:
            from smrforge.help import _help_visualization
            from smrforge.help import Console
            
            console = Console()
            _help_visualization(console, show_examples=True)
        except ImportError:
            pytest.skip("rich not available")

    def test_help_materials(self):
        """Test materials category help."""
        try:
            from smrforge.help import _help_materials
            from smrforge.help import Console
            
            console = Console()
            _help_materials(console, show_examples=True)
        except ImportError:
            pytest.skip("rich not available")

    def test_help_nuclides(self):
        """Test nuclides category help."""
        try:
            from smrforge.help import _help_nuclides
            from smrforge.help import Console
            
            console = Console()
            _help_nuclides(console, show_examples=True)
        except ImportError:
            pytest.skip("rich not available")

    def test_help_convenience(self):
        """Test convenience category help."""
        try:
            from smrforge.help import _help_convenience
            from smrforge.help import Console
            
            console = Console()
            _help_convenience(console, show_examples=True)
        except ImportError:
            pytest.skip("rich not available")

    def test_help_presets(self):
        """Test presets category help."""
        try:
            from smrforge.help import _help_presets
            from smrforge.help import Console
            
            console = Console()
            _help_presets(console, show_examples=True)
        except ImportError:
            pytest.skip("rich not available")

    def test_show_category_help_invalid(self):
        """Test _show_category_help with invalid category."""
        try:
            from smrforge.help import _show_category_help
            from smrforge.help import Console
            
            console = Console()
            _show_category_help(console, "invalid_category", show_examples=True)
        except ImportError:
            pytest.skip("rich not available")


class TestObjectHelp:
    """Test object help functions."""

    def test_show_object_help_function(self):
        """Test _show_object_help with a function."""
        try:
            from smrforge.help import _show_object_help
            from smrforge.help import Console
            from smrforge.convenience import create_reactor
            
            console = Console()
            _show_object_help(console, create_reactor, show_examples=True)
        except ImportError:
            pytest.skip("rich not available")

    def test_show_object_help_class(self):
        """Test _show_object_help with a class."""
        try:
            from smrforge.help import _show_object_help
            from smrforge.help import Console
            from smrforge.convenience import SimpleReactor
            
            console = Console()
            _show_object_help(console, SimpleReactor, show_examples=True)
        except ImportError:
            pytest.skip("rich not available")

    def test_show_object_help_no_docstring(self):
        """Test _show_object_help with object without docstring."""
        try:
            from smrforge.help import _show_object_help
            from smrforge.help import Console
            
            # Create mock object without docstring
            obj = Mock()
            obj.__name__ = "TestObject"
            del obj.__doc__
            
            console = Console()
            _show_object_help(console, obj, show_examples=True)
        except ImportError:
            pytest.skip("rich not available")

    def test_show_examples_for_object(self):
        """Test _show_examples_for_object."""
        try:
            from smrforge.help import _show_examples_for_object
            from smrforge.help import Console
            from smrforge.convenience import create_reactor
            
            console = Console()
            _show_examples_for_object(console, create_reactor)
        except ImportError:
            pytest.skip("rich not available")

    def test_show_examples_for_object_no_examples(self):
        """Test _show_examples_for_object with object that has no examples."""
        try:
            from smrforge.help import _show_examples_for_object
            from smrforge.help import Console
            
            # Create mock object without examples
            obj = Mock()
            obj.__name__ = "TestObjectWithoutExamples"
            
            console = Console()
            _show_examples_for_object(console, obj)
        except ImportError:
            pytest.skip("rich not available")


class TestTopicHelp:
    """Test topic help functions."""

    def test_show_topic_help_category(self):
        """Test _show_topic_help with category topic."""
        try:
            from smrforge.help import _show_topic_help
            from smrforge.help import Console
            
            console = Console()
            _show_topic_help(console, "geometry", show_examples=True)
        except ImportError:
            pytest.skip("rich not available")

    def test_show_topic_help_function_name(self):
        """Test _show_topic_help with function name."""
        try:
            from smrforge.help import _show_topic_help
            from smrforge.help import Console
            
            console = Console()
            _show_topic_help(console, "create_reactor", show_examples=True)
        except ImportError:
            pytest.skip("rich not available")

    def test_show_topic_help_builtin_topic(self):
        """Test _show_topic_help with built-in topic."""
        try:
            from smrforge.help import _show_topic_help
            from smrforge.help import Console
            
            console = Console()
            _show_topic_help(console, "getting_started", show_examples=True)
        except ImportError:
            pytest.skip("rich not available")

    def test_show_topic_help_invalid_topic(self):
        """Test _show_topic_help with invalid topic."""
        try:
            from smrforge.help import _show_topic_help
            from smrforge.help import Console
            
            console = Console()
            _show_topic_help(console, "nonexistent_topic_xyz123", show_examples=True)
        except ImportError:
            pytest.skip("rich not available")


class TestMainMenu:
    """Test main menu display."""

    def test_show_main_menu(self):
        """Test _show_main_menu."""
        try:
            from smrforge.help import _show_main_menu
            from smrforge.help import Console
            
            console = Console()
            _show_main_menu(console)
        except ImportError:
            pytest.skip("rich not available")


class TestBuiltinHelpTopics:
    """Test built-in help topics."""

    def test_help_getting_started(self):
        """Test _help_getting_started."""
        try:
            from smrforge.help import _help_getting_started
            from smrforge.help import Console
            
            console = Console()
            _help_getting_started(console, show_examples=True)
        except ImportError:
            pytest.skip("rich not available")

    def test_help_examples(self):
        """Test _help_examples."""
        try:
            from smrforge.help import _help_examples
            from smrforge.help import Console
            
            console = Console()
            _help_examples(console, show_examples=True)
        except ImportError:
            pytest.skip("rich not available")

    def test_help_workflows(self):
        """Test _help_workflows."""
        try:
            from smrforge.help import _help_workflows
            from smrforge.help import Console
            
            console = Console()
            _help_workflows(console, show_examples=True)
        except ImportError:
            pytest.skip("rich not available")

    def test_help_troubleshooting(self):
        """Test _help_troubleshooting."""
        try:
            from smrforge.help import _help_troubleshooting
            from smrforge.help import Console
            
            console = Console()
            _help_troubleshooting(console, show_examples=True)
        except ImportError:
            pytest.skip("rich not available")


class TestPlainTextFallback:
    """Test plain text fallback when rich is not available."""

    def test_print_help_plain_no_topic(self):
        """Test _print_help_plain with no topic."""
        with patch('smrforge.help._RICH_AVAILABLE', False):
            from smrforge.help import _print_help_plain
            _print_help_plain(None, None, True)

    def test_print_help_plain_with_topic(self):
        """Test _print_help_plain with topic."""
        with patch('smrforge.help._RICH_AVAILABLE', False):
            from smrforge.help import _print_help_plain
            _print_help_plain("geometry", None, True)

    def test_print_help_plain_with_category(self):
        """Test _print_help_plain with category."""
        with patch('smrforge.help._RICH_AVAILABLE', False):
            from smrforge.help import _print_help_plain
            _print_help_plain("geometry", "geometry", True)

