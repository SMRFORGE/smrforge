"""
Tests for template-based reactor design library.

Tests cover:
- ReactorTemplate creation from preset
- Template instantiation with parameters
- Template validation
- Template I/O (save/load JSON/YAML)
- TemplateLibrary CRUD operations
"""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from smrforge.workflows.templates import ReactorTemplate, TemplateLibrary


class TestReactorTemplate:
    """Tests for ReactorTemplate class."""

    def test_to_dict(self):
        """Test template to dictionary conversion."""
        template = ReactorTemplate(
            name="test_template",
            description="Test template",
            version="1.0.0",
            base_preset="valar-10",
            parameters={
                "enrichment": {
                    "default": 0.195,
                    "type": "float",
                    "description": "Enrichment",
                }
            },
        )

        data = template.to_dict()

        assert data["name"] == "test_template"
        assert data["description"] == "Test template"
        assert data["base_preset"] == "valar-10"
        assert "enrichment" in data["parameters"]

    def test_instantiate_defaults(self):
        """Test template instantiation with default parameters."""
        template = ReactorTemplate(
            name="test_template",
            base_preset="valar-10",
            parameters={
                "enrichment": {
                    "default": 0.195,
                    "type": "float",
                    "description": "Enrichment",
                },
                "power_mw": {"default": 10.0, "type": "float", "description": "Power"},
            },
        )

        config = template.instantiate()

        assert config["name"] == "valar-10"
        assert config["enrichment"] == 0.195
        assert config["power_mw"] == 10.0

    def test_instantiate_with_overrides(self):
        """Test template instantiation with parameter overrides."""
        template = ReactorTemplate(
            name="test_template",
            base_preset="valar-10",
            parameters={
                "enrichment": {
                    "default": 0.195,
                    "type": "float",
                    "description": "Enrichment",
                }
            },
        )

        config = template.instantiate(enrichment=0.25, power_mw=15.0)

        assert config["enrichment"] == 0.25  # Override
        assert config["power_mw"] == 15.0  # New parameter

    def test_instantiate_no_base_preset(self):
        """Test template instantiation without base preset."""
        template = ReactorTemplate(
            name="test_template",
            parameters={"enrichment": {"default": 0.195, "type": "float"}},
        )

        config = template.instantiate()

        assert "name" not in config
        assert config["enrichment"] == 0.195

    def test_validate_valid(self):
        """Test template validation with valid template."""
        template = ReactorTemplate(
            name="test_template",
            parameters={
                "enrichment": {
                    "default": 0.195,
                    "type": "float",
                    "description": "Enrichment",
                }
            },
        )

        errors = template.validate()
        assert len(errors) == 0

    def test_validate_missing_name(self):
        """Test template validation with missing name."""
        template = ReactorTemplate(
            name="", parameters={"enrichment": {"default": 0.195, "type": "float"}}
        )

        errors = template.validate()
        assert len(errors) > 0
        assert any("name is required" in e.lower() for e in errors)

    def test_validate_missing_default(self):
        """Test template validation with missing default value."""
        template = ReactorTemplate(
            name="test_template",
            parameters={"enrichment": {"type": "float"}},  # Missing default
        )

        errors = template.validate()
        assert len(errors) > 0
        assert any("missing default" in e.lower() for e in errors)

    def test_validate_missing_type(self):
        """Test template validation with missing type."""
        template = ReactorTemplate(
            name="test_template",
            parameters={"enrichment": {"default": 0.195}},  # Missing type
        )

        errors = template.validate()
        assert len(errors) > 0
        assert any("missing type" in e.lower() for e in errors)

    def test_save_json(self, tmp_path):
        """Test saving template to JSON."""
        template = ReactorTemplate(
            name="test_template",
            description="Test",
            parameters={"enrichment": {"default": 0.195, "type": "float"}},
        )

        output_file = tmp_path / "template.json"
        template.save(output_file)

        assert output_file.exists()
        with open(output_file) as f:
            data = json.load(f)
        assert data["name"] == "test_template"

    def test_save_yaml(self, tmp_path):
        """Test saving template to YAML."""
        template = ReactorTemplate(
            name="test_template",
            parameters={"enrichment": {"default": 0.195, "type": "float"}},
        )

        output_file = tmp_path / "template.yaml"
        template.save(output_file)

        assert output_file.exists()
        with open(output_file) as f:
            data = yaml.safe_load(f)
        assert data["name"] == "test_template"

    def test_load_json(self, tmp_path):
        """Test loading template from JSON."""
        template_data = {
            "name": "test_template",
            "description": "Test",
            "version": "1.0.0",
            "parameters": {"enrichment": {"default": 0.195, "type": "float"}},
        }

        template_file = tmp_path / "template.json"
        with open(template_file, "w") as f:
            json.dump(template_data, f)

        template = ReactorTemplate.load(template_file)

        assert template.name == "test_template"
        assert "enrichment" in template.parameters

    def test_load_yaml(self, tmp_path):
        """Test loading template from YAML."""
        template_data = {
            "name": "test_template",
            "parameters": {"enrichment": {"default": 0.195, "type": "float"}},
        }

        template_file = tmp_path / "template.yaml"
        with open(template_file, "w") as f:
            yaml.safe_dump(template_data, f)

        template = ReactorTemplate.load(template_file)

        assert template.name == "test_template"

    def test_from_preset(self):
        """Test creating template from preset."""
        mock_preset = Mock()
        mock_preset.enrichment = 0.195
        mock_preset.power_thermal = 10e6

        # Patch get_preset in the convenience module, creating it if it doesn't exist
        import smrforge.convenience

        with patch.object(
            smrforge.convenience, "get_preset", return_value=mock_preset, create=True
        ):
            template = ReactorTemplate.from_preset("valar-10", name="my_template")

            assert template.name == "my_template"
            assert template.base_preset == "valar-10"
            assert "enrichment" in template.parameters
            assert "power_mw" in template.parameters
            assert template.parameters["enrichment"]["default"] == 0.195

    def test_from_preset_default_name(self):
        """Test creating template from preset with default name."""
        mock_preset = Mock()
        mock_preset.enrichment = 0.195
        mock_preset.power_thermal = 10e6  # Add power_thermal to avoid division error

        # Patch get_preset in the convenience module, creating it if it doesn't exist
        import smrforge.convenience

        with patch.object(
            smrforge.convenience, "get_preset", return_value=mock_preset, create=True
        ):
            template = ReactorTemplate.from_preset("valar-10")

            assert template.name == "valar-10"
            assert template.base_preset == "valar-10"


class TestTemplateLibrary:
    """Tests for TemplateLibrary class."""

    def test_init_default_dir(self, monkeypatch, tmp_path):
        """Test library initialization with default directory."""
        # Mock home directory
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        library = TemplateLibrary()

        expected_dir = fake_home / ".smrforge" / "templates"
        assert library.library_dir == expected_dir
        assert expected_dir.exists()

    def test_init_custom_dir(self, tmp_path):
        """Test library initialization with custom directory."""
        custom_dir = tmp_path / "custom_templates"

        library = TemplateLibrary(library_dir=custom_dir)

        assert library.library_dir == custom_dir
        assert custom_dir.exists()

    def test_save_template(self, tmp_path):
        """Test saving template to library."""
        library = TemplateLibrary(library_dir=tmp_path / "templates")

        template = ReactorTemplate(
            name="test_template",
            parameters={"enrichment": {"default": 0.195, "type": "float"}},
        )

        library.save_template(template)

        template_file = tmp_path / "templates" / "test_template.json"
        assert template_file.exists()

    def test_load_template(self, tmp_path):
        """Test loading template from library."""
        library = TemplateLibrary(library_dir=tmp_path / "templates")

        # Save a template first
        template = ReactorTemplate(
            name="test_template",
            parameters={"enrichment": {"default": 0.195, "type": "float"}},
        )
        library.save_template(template)

        # Load it back
        loaded = library.load_template("test_template")

        assert loaded.name == "test_template"
        assert "enrichment" in loaded.parameters

    def test_load_template_not_found(self, tmp_path):
        """Test loading non-existent template raises error."""
        library = TemplateLibrary(library_dir=tmp_path / "templates")

        with pytest.raises(FileNotFoundError, match="Template 'nonexistent' not found"):
            library.load_template("nonexistent")

    def test_list_templates(self, tmp_path):
        """Test listing templates in library."""
        library = TemplateLibrary(library_dir=tmp_path / "templates")

        # Save multiple templates
        for name in ["template1", "template2", "template3"]:
            template = ReactorTemplate(name=name)
            library.save_template(template)

        templates = library.list_templates()

        assert len(templates) == 3
        assert "template1" in templates
        assert "template2" in templates
        assert "template3" in templates

    def test_list_templates_empty(self, tmp_path):
        """Test listing templates in empty library."""
        library = TemplateLibrary(library_dir=tmp_path / "templates")

        templates = library.list_templates()

        assert len(templates) == 0

    def test_delete_template(self, tmp_path):
        """Test deleting template from library."""
        library = TemplateLibrary(library_dir=tmp_path / "templates")

        # Save a template
        template = ReactorTemplate(name="test_template")
        library.save_template(template)
        assert (tmp_path / "templates" / "test_template.json").exists()

        # Delete it
        library.delete_template("test_template")

        assert not (tmp_path / "templates" / "test_template.json").exists()

    def test_delete_template_not_found(self, tmp_path):
        """Test deleting non-existent template raises error."""
        library = TemplateLibrary(library_dir=tmp_path / "templates")

        with pytest.raises(FileNotFoundError, match="Template 'nonexistent' not found"):
            library.delete_template("nonexistent")
