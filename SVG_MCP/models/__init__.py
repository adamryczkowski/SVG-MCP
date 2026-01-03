"""Pydantic models for SVG-MCP structured output."""

from .lint_types import (
    LintIssue,
    LintPreset,
    LintResult,
    LintSeverity,
    OptimizePreset,
    OptimizeResult,
)
from .types import (
    BoundingBox,
    CoordinateMapping,
    DiffColorScheme,
    DiffResult,
    RenderResult,
    SVGInfo,
    ValidationError,
    ValidationResult,
    ViewBox,
)

__all__ = [
    "BoundingBox",
    "CoordinateMapping",
    "DiffColorScheme",
    "DiffResult",
    "LintIssue",
    "LintPreset",
    "LintResult",
    "LintSeverity",
    "OptimizePreset",
    "OptimizeResult",
    "RenderResult",
    "SVGInfo",
    "ValidationError",
    "ValidationResult",
    "ViewBox",
]
