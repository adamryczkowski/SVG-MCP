"""SVG-MCP: MCP server for SVG file operations.

This package provides SVG validation, rendering, and visual diff capabilities
both as an MCP server and as standalone Python classes.
"""

from importlib.metadata import PackageNotFoundError, version

from .server import create_server, mcp
from .svg import SVGDiffer, SVGRenderer, SVGValidator

try:
    __version__ = version("SVG_MCP")
except PackageNotFoundError:
    __version__ = "0.0.0.dev"

__all__ = [
    "SVGValidator",
    "SVGRenderer",
    "SVGDiffer",
    "create_server",
    "mcp",
    "__version__",
]
