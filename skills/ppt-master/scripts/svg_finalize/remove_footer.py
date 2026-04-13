#!/usr/bin/env python3
"""Strip footer divider lines and footer content from PPT SVG pages."""

from __future__ import annotations

import re
from pathlib import Path
from xml.etree import ElementTree as ET

NUMBER_RE = re.compile(r"-?\d+(?:\.\d+)?")
ET.register_namespace("", "http://www.w3.org/2000/svg")


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _parse_float(value: str | None, default: float = 0.0) -> float:
    if not value:
        return default
    match = NUMBER_RE.search(value)
    return float(match.group()) if match else default


def _viewbox_size(root: ET.Element) -> tuple[float, float]:
    viewbox = root.get("viewBox")
    if viewbox:
        values = [_parse_float(part) for part in viewbox.replace(",", " ").split()]
        if len(values) == 4:
            return values[2], values[3]
    return _parse_float(root.get("width"), 1280.0), _parse_float(root.get("height"), 720.0)


def _path_bounds(path_data: str) -> tuple[float, float, float, float] | None:
    numbers = [float(token) for token in NUMBER_RE.findall(path_data)]
    if len(numbers) < 2:
        return None

    xs = numbers[0::2]
    ys = numbers[1::2]
    if not xs or not ys:
        return None
    return min(xs), min(ys), max(xs), max(ys)


def _element_bounds(element: ET.Element) -> tuple[float, float, float, float] | None:
    tag = _local_name(element.tag)

    if tag == "rect" or tag == "image":
        x = _parse_float(element.get("x"))
        y = _parse_float(element.get("y"))
        width = _parse_float(element.get("width"))
        height = _parse_float(element.get("height"))
        return x, y, x + width, y + height

    if tag == "line":
        x1 = _parse_float(element.get("x1"))
        y1 = _parse_float(element.get("y1"))
        x2 = _parse_float(element.get("x2"))
        y2 = _parse_float(element.get("y2"))
        return min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)

    if tag == "text":
        x = _parse_float(element.get("x"))
        y = _parse_float(element.get("y"))
        font_size = _parse_float(element.get("font-size"), 14.0)
        return x, y - font_size, x, y + font_size * 0.3

    if tag == "circle":
        cx = _parse_float(element.get("cx"))
        cy = _parse_float(element.get("cy"))
        radius = _parse_float(element.get("r"))
        return cx - radius, cy - radius, cx + radius, cy + radius

    if tag == "ellipse":
        cx = _parse_float(element.get("cx"))
        cy = _parse_float(element.get("cy"))
        rx = _parse_float(element.get("rx"))
        ry = _parse_float(element.get("ry"))
        return cx - rx, cy - ry, cx + rx, cy + ry

    if tag in {"polygon", "polyline"}:
        numbers = [float(token) for token in NUMBER_RE.findall(element.get("points", ""))]
        if len(numbers) < 2:
            return None
        xs = numbers[0::2]
        ys = numbers[1::2]
        return min(xs), min(ys), max(xs), max(ys)

    if tag == "path":
        return _path_bounds(element.get("d", ""))

    return None


def _should_remove(element: ET.Element, page_width: float, page_height: float) -> bool:
    tag = _local_name(element.tag)
    bounds = _element_bounds(element)
    if bounds is None:
        return False

    min_x, min_y, max_x, max_y = bounds
    footer_start = page_height - 72
    divider_band_start = page_height - 110
    span_x = max_x - min_x
    span_y = max_y - min_y

    if min_y >= footer_start:
        return True

    if (
        tag == "rect"
        and min_y >= divider_band_start
        and span_x >= page_width * 0.85
        and span_y <= page_height * 0.18
    ):
        return True

    if (
        min_y >= divider_band_start
        and max_y <= footer_start + 6
        and span_x >= page_width * 0.4
        and span_y <= max(8.0, page_height * 0.02)
    ):
        return True

    return False


def strip_footer_from_tree(tree: ET.ElementTree) -> int:
    """Remove footer elements from a parsed SVG tree."""
    root = tree.getroot()
    page_width, page_height = _viewbox_size(root)
    removed = 0

    for parent in list(root.iter()):
        children = list(parent)
        for child in children:
            if _should_remove(child, page_width, page_height):
                parent.remove(child)
                removed += 1

    return removed


def strip_footer_in_svg(svg_file: str | Path) -> int:
    """Remove footer elements from a single SVG file in place."""
    svg_path = Path(svg_file)
    tree = ET.parse(svg_path)
    removed = strip_footer_from_tree(tree)
    if removed:
        tree.write(svg_path, encoding="unicode", xml_declaration=False)
    return removed
