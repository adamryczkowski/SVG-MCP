"""Pydantic models for SVG linting and optimization."""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class LintSeverity(str, Enum):
    """Severity level for lint issues."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class LintIssue(BaseModel):
    """A single lint issue found in an SVG."""

    severity: LintSeverity = Field(description="Issue severity")
    code: str = Field(description="Issue code (e.g., 'inkscape/flowtext')")
    message: str = Field(description="Human-readable description")
    line: int | None = Field(default=None, description="Line number if available")
    column: int | None = Field(default=None, description="Column number if available")
    suggestion: str | None = Field(default=None, description="Suggested fix")
    source: str = Field(default="unknown", description="Linter that found this issue")

    def __str__(self) -> str:
        """Return a human-readable string representation."""
        location = ""
        if self.line is not None:
            location = f" (line {self.line}"
            if self.column is not None:
                location += f", col {self.column}"
            location += ")"
        return f"[{self.severity.value.upper()}] {self.code}{location}: {self.message}"


class LintResult(BaseModel):
    """Result of linting an SVG."""

    valid: bool = Field(description="True if no errors (warnings allowed)")
    issues: list[LintIssue] = Field(
        default_factory=list, description="All issues found"
    )

    @property
    def errors(self) -> list[LintIssue]:
        """Return only error-level issues."""
        return [i for i in self.issues if i.severity == LintSeverity.ERROR]

    @property
    def warnings(self) -> list[LintIssue]:
        """Return only warning-level issues."""
        return [i for i in self.issues if i.severity == LintSeverity.WARNING]

    @property
    def infos(self) -> list[LintIssue]:
        """Return only info-level issues."""
        return [i for i in self.issues if i.severity == LintSeverity.INFO]

    @property
    def error_count(self) -> int:
        """Return the number of errors."""
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        """Return the number of warnings."""
        return len(self.warnings)


class OptimizeResult(BaseModel):
    """Result of optimizing an SVG."""

    success: bool = Field(description="Whether optimization succeeded")
    optimized_content: str | None = Field(
        default=None, description="Optimized SVG content"
    )
    original_size: int = Field(description="Original file size in bytes")
    optimized_size: int | None = Field(
        default=None, description="Optimized file size in bytes"
    )
    reduction_percent: float | None = Field(
        default=None, description="Size reduction percentage"
    )
    error: str | None = Field(default=None, description="Error message if failed")
    validation: dict | None = Field(
        default=None, description="Validation result after optimization"
    )

    @property
    def bytes_saved(self) -> int | None:
        """Return the number of bytes saved."""
        if self.optimized_size is not None:
            return self.original_size - self.optimized_size
        return None


# Optimization preset type
OptimizePreset = Literal["safe", "default", "maximum"]

# Lint preset type
LintPreset = Literal["relaxed", "default", "strict", "inkscape"]
