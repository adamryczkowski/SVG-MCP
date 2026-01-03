"""SVG processing modules for SVG-MCP."""

from SVG_MCP.svg.differ import SVGDiffer
from SVG_MCP.svg.linter import LINT_PRESETS, SVGLinter, lint_svg
from SVG_MCP.svg.optimizer import OPTIMIZE_PRESETS, SVGOptimizer, optimize_svg
from SVG_MCP.svg.renderer import SVGRenderer
from SVG_MCP.svg.scour_linter import ScourLinter, lint_svg_with_scour
from SVG_MCP.svg.svglint_runner import (
    SvglintRunner,
    lint_with_svglint,
    svglint_available,
)
from SVG_MCP.svg.validator import SVGValidator

__all__ = [
    "LINT_PRESETS",
    "OPTIMIZE_PRESETS",
    "ScourLinter",
    "SVGDiffer",
    "SVGLinter",
    "SVGOptimizer",
    "SVGRenderer",
    "SVGValidator",
    "SvglintRunner",
    "lint_svg",
    "lint_svg_with_scour",
    "lint_with_svglint",
    "optimize_svg",
    "svglint_available",
]
