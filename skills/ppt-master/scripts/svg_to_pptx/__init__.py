"""svg_to_pptx — backward-compatible package name for final export commands."""

from .html_slideshow import export_html_slideshow, main

try:
    from .drawingml_converter import convert_svg_to_slide_shapes
    from .pptx_builder import create_pptx_with_native_svg
except Exception:  # pragma: no cover - optional legacy imports
    convert_svg_to_slide_shapes = None  # type: ignore[assignment]
    create_pptx_with_native_svg = None  # type: ignore[assignment]

__all__ = ["main", "export_html_slideshow"]
if convert_svg_to_slide_shapes is not None:
    __all__.append("convert_svg_to_slide_shapes")
if create_pptx_with_native_svg is not None:
    __all__.append("create_pptx_with_native_svg")
