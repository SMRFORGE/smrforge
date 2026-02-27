"""
Template command handlers: template_create, template_modify, template_validate.
"""

import sys
from pathlib import Path

from smrforge.cli.common import _print_error, _print_success


def template_create(args):
    """Create reactor template from preset or existing design."""
    try:
        from smrforge.workflows.templates import ReactorTemplate, TemplateLibrary

        if args.from_preset:
            template = ReactorTemplate.from_preset(args.from_preset, name=args.name)
        elif args.from_file:
            import json  # pragma: no cover
            from pathlib import Path  # pragma: no cover

            with open(Path(args.from_file)) as f:  # pragma: no cover
                reactor_data = json.load(f)  # pragma: no cover
            template = ReactorTemplate(  # pragma: no cover
                name=args.name or "template",
                description=args.description or "Template from file",
                base_preset=reactor_data.get("name"),
                parameters={},
            )
        else:
            _print_error("Must specify --from-preset or --from-file")
            sys.exit(1)

        # Save template
        output_file = (
            Path(args.output) if args.output else Path(f"{template.name}.json")
        )
        template.save(output_file)  # pragma: no cover

        if args.library:  # pragma: no cover
            library = TemplateLibrary()  # pragma: no cover
            library.save_template(template)  # pragma: no cover
            _print_success(
                f"Template saved to library and {output_file}"
            )  # pragma: no cover
        else:  # pragma: no cover
            _print_success(f"Template saved to {output_file}")  # pragma: no cover

    except Exception as e:
        _print_error(f"Failed to create template: {e}")
        if args.verbose if hasattr(args, "verbose") else False:
            import traceback  # pragma: no cover

            traceback.print_exc()  # pragma: no cover
        sys.exit(1)


def template_modify(args):
    """Modify reactor template parameters."""
    try:
        from smrforge.workflows.templates import ReactorTemplate

        template = ReactorTemplate.load(Path(args.template))

        # Modify parameters
        if args.param:
            for param_spec in args.param:
                # Format: name=value
                if "=" not in param_spec:
                    _print_error(
                        f"Invalid parameter format: {param_spec}. Use name=value"
                    )  # pragma: no cover
                    sys.exit(1)  # pragma: no cover
                name, value = param_spec.split("=", 1)
                # Try to convert to number
                try:
                    value = float(value) if "." in value else int(value)
                except ValueError:  # pragma: no cover
                    pass  # pragma: no cover

                if name not in template.parameters:
                    template.parameters[name] = {
                        "default": value,
                        "type": type(value).__name__,
                        "description": "",
                    }
                else:
                    template.parameters[name]["default"] = value  # pragma: no cover

        # Save modified template
        template.save(Path(args.template))
        _print_success(f"Template modified: {args.template}")

    except Exception as e:
        _print_error(f"Failed to modify template: {e}")
        sys.exit(1)


def template_validate(args):
    """Validate reactor template."""
    try:
        from smrforge.workflows.templates import ReactorTemplate

        template = ReactorTemplate.load(Path(args.template))
        errors = template.validate()

        if errors:
            _print_error("Template validation failed:")
            for error in errors:
                _print_error(f"  - {error}")
            sys.exit(1)
        else:
            _print_success("Template is valid!")

    except Exception as e:  # pragma: no cover
        _print_error(f"Failed to validate template: {e}")  # pragma: no cover
        sys.exit(1)  # pragma: no cover
