"""
Pro report generator: HTML from templates, PDF export with weasyprint.

Supports design and regulatory report types. Uses Jinja2 when available.
"""

from pathlib import Path
from typing import Any, Dict, Optional

from smrforge.utils.logging import get_logger

logger = get_logger("smrforge_pro.reporting.generator")


def _render_html_simple(report_type: str, data: Dict[str, Any]) -> str:
    """Render HTML without Jinja2."""
    title = data.get("title", "Report")
    sections = data.get("sections", [])
    html_parts = [
        "<!DOCTYPE html>",
        "<html><head>",
        "<meta charset='utf-8'>",
        "<style>body{font-family:sans-serif;margin:1in;line-height:1.5;}</style>",
        f"<title>{title}</title>",
        "</head><body>",
        f"<h1>{title}</h1>",
    ]
    for sec in sections:
        h = sec.get("heading", "")
        content = sec.get("content", "")
        if h:
            html_parts.append(f"<h2>{h}</h2>")
        html_parts.append(f"<p>{content}</p>")
    html_parts.append("</body></html>")
    return "\n".join(html_parts)


def _render_with_jinja(report_type: str, data: Dict[str, Any]) -> Optional[str]:
    """Render using Jinja2 if available."""
    try:
        from jinja2 import Template

        templates = {
            "design": """
<!DOCTYPE html>
<html><head><meta charset='utf-8'>
<style>body{font-family:sans-serif;margin:1in;}</style>
<title>{{ title }}</title></head>
<body><h1>{{ title }}</h1>
{% for k, v in data.items() %}
<p><strong>{{ k }}:</strong> {{ v }}</p>
{% endfor %}
</body></html>
""",
            "regulatory": """
<!DOCTYPE html>
<html><head><meta charset='utf-8'>
<style>body{font-family:sans-serif;margin:1in;}</style>
<title>{{ title }} - Regulatory</title></head>
<body><h1>{{ title }}</h1>
<p><em>Regulatory compliance report</em></p>
{% for k, v in data.items() %}
<p><strong>{{ k }}:</strong> {{ v }}</p>
{% endfor %}
</body></html>
""",
        }
        tpl = templates.get(report_type, templates["design"])
        tmpl = Template(tpl)
        return tmpl.render(
            title=data.get("title", "Report"),
            data={k: v for k, v in data.items() if k not in ("title", "sections")},
        )
    except ImportError:
        return None


class ReportGenerator:
    """
    Generate design and regulatory reports as HTML, and export to PDF.

    Uses Jinja2 for templating when available. PDF export uses weasyprint;
    if not installed, falls back to writing HTML (can be printed to PDF manually).
    """

    def generate(self, report_type: str, data: Dict[str, Any]) -> str:
        """
        Generate HTML report from template and data.

        Args:
            report_type: "design", "regulatory", or other; selects template.
            data: Dict with title, sections, and other keys to render.

        Returns:
            HTML string.
        """
        html = _render_with_jinja(report_type, data)
        if html:
            return html
        return _render_html_simple(report_type, data)

    def export_pdf(self, html_content: str, output_path: Path) -> Optional[Path]:
        """
        Export HTML content to PDF file.

        Uses weasyprint when available. If not, writes HTML to the given path
        (same filename, content is HTML; user can open in browser and Print to PDF).

        Args:
            html_content: Full HTML string.
            output_path: Output path (typically .pdf).

        Returns:
            Path to written file if successful, else None.
        """
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        try:
            from weasyprint import HTML

            out = out.with_suffix(".pdf")
            HTML(string=html_content).write_pdf(str(out))
            logger.info("PDF report saved to %s", out)
            return out
        except ImportError:
            # Fallback: write HTML to requested path so file exists; user can convert manually
            out.write_text(html_content, encoding="utf-8")
            logger.warning(
                "weasyprint not installed. HTML saved to %s. Install weasyprint for PDF export.",
                out,
            )
            return out
