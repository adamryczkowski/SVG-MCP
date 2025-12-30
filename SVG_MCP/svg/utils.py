"""Shared utilities for SVG processing."""

import re

from SVG_MCP.models.types import ViewBox


def parse_viewbox(viewbox_str: str | None) -> ViewBox | None:
    """Parse viewBox attribute string.

    Args:
        viewbox_str: viewBox attribute value (e.g., "0 0 100 100").

    Returns:
        ViewBox if valid, None otherwise.

    Examples:
        >>> parse_viewbox("0 0 100 100")
        ViewBox(x=0.0, y=0.0, width=100.0, height=100.0)
        >>> parse_viewbox("10,20,30,40")
        ViewBox(x=10.0, y=20.0, width=30.0, height=40.0)
        >>> parse_viewbox(None)
        None
    """
    if not viewbox_str:
        return None

    # viewBox can be separated by spaces or commas
    parts = re.split(r"[\s,]+", viewbox_str.strip())
    if len(parts) != 4:
        return None

    try:
        x, y, width, height = map(float, parts)
        return ViewBox(x=x, y=y, width=width, height=height)
    except ValueError:
        return None
