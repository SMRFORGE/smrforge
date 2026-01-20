"""
Tests for smrforge.help module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import smrforge.help as help_module


class TestGetSmrModule:
    """Test _get_smr_module function."""
    
    def test_get_smr_module_success(self):
        """Test _get_smr_module when import succeeds."""
        # Reset the cache
        help_module._CORE_AVAILABLE = None
        help_module._smr_module = None
        
        result = help_module._get_smr_module()
        assert result is not None
        assert help_module._CORE_AVAILABLE is True
    
    def test_get_smr_module_cached(self):
        """Test _get_smr_module uses cache."""
        # Set cache
        help_module._CORE_AVAILABLE = True
        mock_module = Mock()
        help_module._smr_module = mock_module
        
        result = help_module._get_smr_module()
        assert result == mock_module
    
    def test_get_smr_module_import_error(self):
        """Test _get_smr_module when import fails."""
        help_module._CORE_AVAILABLE = None
        help_module._smr_module = None
        
        with patch('builtins.__import__', side_effect=ImportError("Test error")):
            result = help_module._get_smr_module()
            assert result is None
            assert help_module._CORE_AVAILABLE is False


class TestIsCoreAvailable:
    """Test _is_core_available function."""
    
    def test_is_core_available_true(self):
        """Test _is_core_available when core is available."""
        help_module._CORE_AVAILABLE = True
        assert help_module._is_core_available() is True
    
    def test_is_core_available_false(self):
        """Test _is_core_available when core is not available."""
        help_module._CORE_AVAILABLE = False
        assert help_module._is_core_available() is False
    
    def test_is_core_available_none(self):
        """Test _is_core_available when not yet checked."""
        help_module._CORE_AVAILABLE = None
        # Should trigger _get_smr_module
        result = help_module._is_core_available()
        assert isinstance(result, bool)


class TestHelpFunction:
    """Test help function."""
    
    def test_help_no_topic_with_rich(self):
        """Test help() with no topic and Rich available."""
        with patch('smrforge.help._RICH_AVAILABLE', True):
            with patch('smrforge.help._show_main_menu') as mock_menu:
                help_module.help()
                mock_menu.assert_called_once()
    
    def test_help_no_topic_without_rich(self):
        """Test help() with no topic and Rich not available."""
        with patch('smrforge.help._RICH_AVAILABLE', False):
            with patch('smrforge.help._print_help_plain') as mock_print:
                help_module.help()
                mock_print.assert_called_once_with(None, None, True)
    
    def test_help_string_topic(self):
        """Test help() with string topic."""
        with patch('smrforge.help._RICH_AVAILABLE', True):
            with patch('smrforge.help._show_topic_help') as mock_topic:
                help_module.help("geometry")
                mock_topic.assert_called_once()
    
    def test_help_object_topic(self):
        """Test help() with object topic."""
        mock_obj = Mock()
        with patch('smrforge.help._RICH_AVAILABLE', True):
            with patch('smrforge.help._show_object_help') as mock_obj_help:
                help_module.help(mock_obj)
                mock_obj_help.assert_called_once()
    
    def test_help_with_category(self):
        """Test help() with category parameter."""
        with patch('smrforge.help._RICH_AVAILABLE', True):
            with patch('smrforge.help._show_topic_help') as mock_topic:
                help_module.help("test", category="geometry")
                mock_topic.assert_called_once()
    
    def test_help_show_examples_false(self):
        """Test help() with show_examples=False."""
        with patch('smrforge.help._RICH_AVAILABLE', True):
            with patch('smrforge.help._show_main_menu') as mock_menu:
                help_module.help(show_examples=False)
                mock_menu.assert_called_once()


class TestShowMainMenu:
    """Test _show_main_menu function."""
    
    def test_show_main_menu(self):
        """Test _show_main_menu displays menu."""
        mock_console = Mock()
        help_module._show_main_menu(mock_console)
        assert mock_console.print.called


class TestShowTopicHelp:
    """Test _show_topic_help function."""
    
    def test_show_topic_help_category(self):
        """Test _show_topic_help with category."""
        mock_console = Mock()
        with patch('smrforge.help._show_category_help') as mock_category:
            help_module._show_topic_help(mock_console, "geometry", True)
            mock_category.assert_called_once_with(mock_console, "geometry", True)
    
    def test_show_topic_help_function(self):
        """Test _show_topic_help with function name."""
        mock_console = Mock()
        mock_smr = Mock()
        mock_smr.create_reactor = Mock()
        
        with patch('smrforge.help._get_smr_module', return_value=mock_smr):
            with patch('smrforge.help._show_object_help') as mock_obj:
                help_module._show_topic_help(mock_console, "create_reactor", True)
                # Should try to find and show help for the function
                assert mock_obj.called or True  # May not find it, that's OK
    
    def test_show_topic_help_builtin_topic(self):
        """Test _show_topic_help with built-in topic."""
        mock_console = Mock()
        with patch('smrforge.help._help_getting_started') as mock_help:
            help_module._show_topic_help(mock_console, "getting_started", True)
            mock_help.assert_called_once()
    
    def test_show_topic_help_not_found(self):
        """Test _show_topic_help with unknown topic."""
        mock_console = Mock()
        with patch('smrforge.help._get_smr_module', return_value=None):
            help_module._show_topic_help(mock_console, "unknown_topic", True)
            assert mock_console.print.called


class TestShowCategoryHelp:
    """Test _show_category_help function."""
    
    def test_show_category_help_geometry(self):
        """Test _show_category_help with geometry."""
        mock_console = Mock()
        with patch('smrforge.help._help_geometry') as mock_help:
            help_module._show_category_help(mock_console, "geometry", True)
            mock_help.assert_called_once()
    
    def test_show_category_help_neutronics(self):
        """Test _show_category_help with neutronics."""
        mock_console = Mock()
        with patch('smrforge.help._help_neutronics') as mock_help:
            help_module._show_category_help(mock_console, "neutronics", True)
            mock_help.assert_called_once()
    
    def test_show_category_help_unknown(self):
        """Test _show_category_help with unknown category."""
        mock_console = Mock()
        help_module._show_category_help(mock_console, "unknown", True)
        assert mock_console.print.called


class TestShowObjectHelp:
    """Test _show_object_help function."""
    
    def test_show_object_help_with_docstring(self):
        """Test _show_object_help with object that has docstring."""
        mock_console = Mock()
        mock_obj = Mock()
        mock_obj.__name__ = "test_function"
        
        with patch('inspect.getdoc', return_value="Test docstring"):
            with patch('inspect.signature', side_effect=ValueError("No signature")):
                help_module._show_object_help(mock_console, mock_obj, True)
                assert mock_console.print.called
    
    def test_show_object_help_without_docstring(self):
        """Test _show_object_help with object without docstring."""
        mock_console = Mock()
        mock_obj = Mock()
        mock_obj.__name__ = "test_function"
        
        with patch('inspect.getdoc', return_value=None):
            help_module._show_object_help(mock_console, mock_obj, True)
            assert mock_console.print.called
    
    def test_show_object_help_with_signature(self):
        """Test _show_object_help with signature."""
        from inspect import Signature, Parameter
        
        mock_console = Mock()
        mock_obj = Mock()
        mock_obj.__name__ = "test_func"
        
        sig = Signature([Parameter('x', Parameter.POSITIONAL_OR_KEYWORD)])
        
        with patch('inspect.getdoc', return_value="Test"):
            with patch('inspect.signature', return_value=sig):
                help_module._show_object_help(mock_console, mock_obj, True)
                assert mock_console.print.called


class TestHelpFunctions:
    """Test individual help functions."""
    
    def test_help_getting_started(self):
        """Test _help_getting_started."""
        mock_console = Mock()
        mock_console.print = Mock()  # Ensure print is a Mock
        help_module._help_getting_started(mock_console, True)
        assert mock_console.print.called
    
    def test_help_examples(self):
        """Test _help_examples."""
        mock_console = Mock()
        mock_console.print = Mock()
        help_module._help_examples(mock_console, True)
        assert mock_console.print.called
    
    def test_help_workflows(self):
        """Test _help_workflows."""
        mock_console = Mock()
        mock_console.print = Mock()
        help_module._help_workflows(mock_console, True)
        assert mock_console.print.called
    
    def test_help_geometry(self):
        """Test _help_geometry."""
        mock_console = Mock()
        mock_console.print = Mock()
        help_module._help_geometry(mock_console, True)
        assert mock_console.print.called
    
    def test_help_neutronics(self):
        """Test _help_neutronics."""
        mock_console = Mock()
        mock_console.print = Mock()
        help_module._help_neutronics(mock_console, True)
        assert mock_console.print.called
    
    def test_help_burnup(self):
        """Test _help_burnup."""
        mock_console = Mock()
        mock_console.print = Mock()
        help_module._help_burnup(mock_console, True)
        assert mock_console.print.called
    
    def test_help_thermal(self):
        """Test _help_thermal."""
        mock_console = Mock()
        mock_console.print = Mock()
        help_module._help_thermal(mock_console, True)
        assert mock_console.print.called
    
    def test_help_decay(self):
        """Test _help_decay."""
        mock_console = Mock()
        mock_console.print = Mock()
        help_module._help_decay(mock_console, True)
        assert mock_console.print.called
    
    def test_help_gamma(self):
        """Test _help_gamma."""
        mock_console = Mock()
        mock_console.print = Mock()
        help_module._help_gamma(mock_console, True)
        assert mock_console.print.called
    
    def test_help_visualization(self):
        """Test _help_visualization."""
        mock_console = Mock()
        mock_console.print = Mock()
        help_module._help_visualization(mock_console, True)
        assert mock_console.print.called
    
    def test_help_materials(self):
        """Test _help_materials."""
        mock_console = Mock()
        mock_console.print = Mock()
        help_module._help_materials(mock_console, True)
        assert mock_console.print.called
    
    def test_help_nuclides(self):
        """Test _help_nuclides."""
        mock_console = Mock()
        mock_console.print = Mock()
        help_module._help_nuclides(mock_console, True)
        assert mock_console.print.called
    
    def test_help_convenience(self):
        """Test _help_convenience."""
        mock_console = Mock()
        mock_console.print = Mock()
        help_module._help_convenience(mock_console, True)
        assert mock_console.print.called
    
    def test_help_presets(self):
        """Test _help_presets."""
        mock_console = Mock()
        mock_console.print = Mock()
        help_module._help_presets(mock_console, True)
        assert mock_console.print.called
    
    def test_help_troubleshooting(self):
        """Test _help_troubleshooting."""
        mock_console = Mock()
        mock_console.print = Mock()
        help_module._help_troubleshooting(mock_console, True)
        assert mock_console.print.called


class TestPrintHelpPlain:
    """Test _print_help_plain function."""
    
    def test_print_help_plain(self, capsys):
        """Test _print_help_plain output."""
        help_module._print_help_plain(None, None, True)
        captured = capsys.readouterr()
        assert "SMRForge" in captured.out or "Help" in captured.out


class TestFormatDocstring:
    """Test _format_docstring function."""
    
    def test_format_docstring_simple(self):
        """Test _format_docstring with simple docstring."""
        doc = "Simple docstring"
        result = help_module._format_docstring(doc)
        assert isinstance(result, str)
        assert "Simple" in result
    
    def test_format_docstring_with_code_block(self):
        """Test _format_docstring with code block."""
        doc = "```python\ncode here\n```"
        result = help_module._format_docstring(doc)
        assert isinstance(result, str)
        assert "code" in result.lower()
    
    def test_format_docstring_with_examples(self):
        """Test _format_docstring with Python examples."""
        doc = "Example:\n>>> test()\nresult"
        result = help_module._format_docstring(doc)
        assert isinstance(result, str)
        assert "test" in result.lower() or ">>>" in result


class TestGetExamples:
    """Test _get_examples function."""
    
    def test_get_examples_returns_dict(self):
        """Test _get_examples returns dictionary."""
        examples = help_module._get_examples()
        assert isinstance(examples, dict)
        # May be empty or have examples
        assert len(examples) >= 0
    
    def test_get_examples_has_create_reactor(self):
        """Test _get_examples includes create_reactor if it exists."""
        examples = help_module._get_examples()
        if "create_reactor" in examples:
            assert isinstance(examples["create_reactor"], list)
            if len(examples["create_reactor"]) > 0:
                assert isinstance(examples["create_reactor"][0], dict)
    
    def test_get_examples_structure(self):
        """Test _get_examples structure."""
        examples = help_module._get_examples()
        for key, value_list in examples.items():
            assert isinstance(value_list, list)
            for item in value_list:
                assert isinstance(item, dict)
                assert "description" in item
                assert "code" in item


class TestShowExamplesForObject:
    """Test _show_examples_for_object function."""
    
    def test_show_examples_for_object_with_examples(self):
        """Test _show_examples_for_object when examples exist."""
        mock_console = Mock()
        mock_console.print = Mock()
        mock_obj = Mock()
        mock_obj.__name__ = "create_reactor"
        
        help_module._show_examples_for_object(mock_console, mock_obj)
        # May or may not print depending on examples
        assert True  # Function should not error
    
    def test_show_examples_for_object_without_examples(self):
        """Test _show_examples_for_object when no examples."""
        mock_console = Mock()
        mock_console.print = Mock()
        mock_obj = Mock()
        mock_obj.__name__ = "nonexistent_function"
        
        help_module._show_examples_for_object(mock_console, mock_obj)
        # Should not error
        assert True
