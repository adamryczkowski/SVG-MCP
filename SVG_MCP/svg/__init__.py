"""SVG processing modules for SVG-MCP."""

from SVG_MCP.svg.differ import SVGDiffer
from SVG_MCP.svg.optimizer import OPTIMIZE_PRESETS, SVGOptimizer, optimize_svg
from SVG_MCP.svg.renderer import SVGRenderer
from SVG_MCP.svg.validator import SVGValidator

__all__ = [
    "OPTIMIZE_PRESETS",
    "SVGDiffer",
    "SVGOptimizer",
    "SVGRenderer",
    "SVGValidator",
    "optimize_svg",
]
