"""
Template-based reactor design library.

Provides reusable, parameterized reactor design templates for
rapid design iteration and sharing.
"""

import json
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from ..utils.logging import get_logger
from ..validation.models import ReactorSpecification

logger = get_logger("smrforge.workflows.templates")


@dataclass
class ReactorTemplate:
    """
    Parameterized reactor design template.

    Attributes:
        name: Template name
        description: Template description
        version: Template version
        base_preset: Base preset name (optional)
        parameters: Dictionary of parameter definitions with defaults
                   Format: {"param_name": {"default": value, "type": str, "description": str}}
        metadata: Additional metadata (tags, author, etc.)
    """

    name: str
    description: str = ""
    version: str = "1.0.0"
    base_preset: Optional[str] = None
    parameters: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary."""
        return asdict(self)

    def instantiate(self, **kwargs) -> Dict[str, Any]:
        """
        Instantiate template with given parameter values.

        Args:
            **kwargs: Parameter values (overrides defaults)

        Returns:
            Dictionary suitable for create_reactor()
        """
        config = {}

        # Start with base preset if specified
        if self.base_preset:
            config["name"] = self.base_preset

        # Apply default parameters
        for param_name, param_def in self.parameters.items():
            if param_name not in kwargs:
                config[param_name] = param_def.get("default")
            else:
                config[param_name] = kwargs[param_name]

        # Apply overrides
        config.update(kwargs)

        return config

    def validate(self) -> List[str]:
        """
        Validate template structure.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        if not self.name:
            errors.append("Template name is required")

        for param_name, param_def in self.parameters.items():
            if "default" not in param_def:
                errors.append(f"Parameter '{param_name}' missing default value")
            if "type" not in param_def:
                errors.append(f"Parameter '{param_name}' missing type")

        return errors

    def save(self, file_path: Path):
        """Save template to file (JSON or YAML)."""
        file_path = Path(file_path)
        data = self.to_dict()

        if file_path.suffix.lower() in [".yaml", ".yml"]:
            with open(file_path, "w") as f:
                yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
        else:
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)

        logger.info(f"Saved template to {file_path}")

    @classmethod
    def load(cls, file_path: Path) -> "ReactorTemplate":
        """Load template from file."""
        file_path = Path(file_path)

        if file_path.suffix.lower() in [".yaml", ".yml"]:
            with open(file_path) as f:
                data = yaml.safe_load(f)
        else:
            with open(file_path) as f:
                data = json.load(f)

        return cls(**data)

    @classmethod
    def from_preset(
        cls, preset_name: str, name: Optional[str] = None
    ) -> "ReactorTemplate":
        """
        Create template from preset design.

        Args:
            preset_name: Name of preset design
            name: Template name (default: preset name)

        Returns:
            ReactorTemplate instance
        """
        import smrforge as smr
        from smrforge.convenience import get_preset

        preset = get_preset(preset_name)

        # Extract parameters from preset
        parameters = {}
        if hasattr(preset, "enrichment"):
            parameters["enrichment"] = {
                "default": float(preset.enrichment),
                "type": "float",
                "description": "Fuel enrichment (0-1)",
            }
        if hasattr(preset, "power_thermal"):
            parameters["power_mw"] = {
                "default": float(preset.power_thermal / 1e6),
                "type": "float",
                "description": "Thermal power (MW)",
            }

        return cls(
            name=name or preset_name,
            description=f"Template based on {preset_name} preset",
            base_preset=preset_name,
            parameters=parameters,
            metadata={"source_preset": preset_name},
        )


class TemplateLibrary:
    """
    Template library manager.

    Provides template storage, search, and management.
    """

    def __init__(self, library_dir: Optional[Path] = None):
        """
        Initialize template library.

        Args:
            library_dir: Directory for template storage (default: ~/.smrforge/templates)
        """
        if library_dir is None:
            library_dir = Path.home() / ".smrforge" / "templates"

        self.library_dir = Path(library_dir)
        self.library_dir.mkdir(parents=True, exist_ok=True)

    def save_template(self, template: ReactorTemplate):
        """Save template to library."""
        file_path = self.library_dir / f"{template.name}.json"
        template.save(file_path)

    def load_template(self, name: str) -> ReactorTemplate:
        """Load template from library."""
        file_path = self.library_dir / f"{name}.json"
        if not file_path.exists():
            raise FileNotFoundError(f"Template '{name}' not found in library")
        return ReactorTemplate.load(file_path)

    def list_templates(self) -> List[str]:
        """List all templates in library."""
        return [f.stem for f in self.library_dir.glob("*.json")]

    def delete_template(self, name: str):
        """Delete template from library."""
        file_path = self.library_dir / f"{name}.json"
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Deleted template '{name}'")
        else:
            raise FileNotFoundError(f"Template '{name}' not found")
