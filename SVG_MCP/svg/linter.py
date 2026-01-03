"""Unified SVG linter combining multiple backends.

This module provides a unified interface for SVG linting that combines:
1. Scour-based Inkscape/librsvg compatibility checks
2. svglint rules (optional, requires Node.js)
3. Custom Python rules
"""

from typing import Any

from SVG_MCP.models.lint_types import LintIssue, LintPreset, LintResult, LintSeverity
from SVG_MCP.svg.scour_linter import ScourLinter
from SVG_MCP.svg.svglint_runner import SvglintRunner, svglint_available


# Lint presets configuration
LINT_PRESETS: dict[LintPreset, dict[str, Any]] = {
    "relaxed": {
        "use_scour": False,
        "use_svglint": False,
        "use_custom": True,
        "rules": {
            "xml_valid": True,
            "namespace_warning": True,
        },
    },
    "default": {
        "use_scour": True,
        "use_svglint": True,
        "use_custom": True,
        "rules": {
            "xml_valid": True,
            "namespace_required": True,
            "embedded_images": "warning",
            "relative_paths": "info",
            "deprecated_xlink": "warning",
            "flowtext": "error",
        },
    },
    "strict": {
        "use_scour": True,
        "use_svglint": True,
        "use_custom": True,
        "rules": {
            "xml_valid": True,
            "namespace_required": True,
            "viewbox_required": True,
            "title_required": True,
            "embedded_images": "error",
            "relative_paths": "warning",
            "deprecated_xlink": "error",
            "flowtext": "error",
            "inline_styles": "warning",
        },
    },
    "inkscape": {
        "use_scour": True,
        "use_svglint": False,
        "use_custom": True,
        "rules": {
            "xml_valid": True,
            "flowtext": "error",
            "renderer_workarounds": True,
            "librsvg_compatibility": True,
        },
    },
}


class SVGLinter:
    """Unified SVG linter combining multiple backends."""

    def __init__(self, preset: LintPreset = "default") -> None:
        """Initialize the linter with a preset.

        Args:
            preset: Lint preset to use ('relaxed', 'default', 'strict', 'inkscape')
        """
        self.preset = preset
        self._preset_config = LINT_PRESETS.get(preset, LINT_PRESETS["default"])
        self._scour_linter = ScourLinter()
        self._svglint_available: bool | None = None

    def lint(
        self,
        content: str,
        *,
        use_scour: bool | None = None,
        use_svglint: bool | None = None,
        use_custom: bool | None = None,
        element_rules: dict[str, Any] | None = None,
        attribute_rules: list[dict[str, Any]] | None = None,
    ) -> LintResult:
        """Lint SVG content using all available backends.

        Args:
            content: SVG content to lint
            use_scour: Run Scour-based Inkscape compatibility checks
                      (None = use preset default)
            use_svglint: Run svglint rules (requires Node.js)
                        (None = use preset default)
            use_custom: Run custom Python rules
                       (None = use preset default)
            element_rules: Custom element rules for svglint (elm config)
            attribute_rules: Custom attribute rules for svglint (attr config)

        Returns:
            LintResult with all issues found
        """
        issues: list[LintIssue] = []

        # Determine which backends to use
        _use_scour = (
            use_scour if use_scour is not None else self._preset_config["use_scour"]
        )
        _use_svglint = (
            use_svglint
            if use_svglint is not None
            else self._preset_config["use_svglint"]
        )
        _use_custom = (
            use_custom if use_custom is not None else self._preset_config["use_custom"]
        )

        # 1. Scour-based Inkscape compatibility checks
        if _use_scour:
            scour_issues = self._scour_linter.lint(content)
            issues.extend(scour_issues)

        # 2. svglint rules (if available)
        if _use_svglint and self._is_svglint_available():
            svglint_issues = self._run_svglint(
                content,
                element_rules=element_rules,
                attribute_rules=attribute_rules,
            )
            issues.extend(svglint_issues)

        # 3. Custom Python rules
        if _use_custom:
            custom_issues = self._run_custom_rules(content)
            issues.extend(custom_issues)

        # Determine if valid (no errors)
        has_errors = any(i.severity == LintSeverity.ERROR for i in issues)

        return LintResult(
            valid=not has_errors,
            issues=issues,
        )

    def lint_file(self, file_path: str) -> LintResult:
        """Lint an SVG file.

        Args:
            file_path: Path to the SVG file

        Returns:
            LintResult with all issues found
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
            return self.lint(content)
        except OSError as e:
            return LintResult(
                valid=False,
                issues=[
                    LintIssue(
                        severity=LintSeverity.ERROR,
                        code="file/read-error",
                        message=f"Failed to read file: {e}",
                        source="linter",
                    )
                ],
            )

    def _is_svglint_available(self) -> bool:
        """Check if svglint is available.

        This is cached after the first check.
        """
        if self._svglint_available is None:
            self._svglint_available = svglint_available()
        return self._svglint_available

    def _run_svglint(
        self,
        content: str,
        *,
        element_rules: dict[str, Any] | None = None,
        attribute_rules: list[dict[str, Any]] | None = None,
    ) -> list[LintIssue]:
        """Run svglint on the content.

        Args:
            content: SVG content to lint
            element_rules: Custom element rules for svglint
            attribute_rules: Custom attribute rules for svglint

        Returns:
            List of issues from svglint
        """
        try:
            runner = SvglintRunner()
            return runner.lint(
                content,
                element_rules=element_rules,
                attribute_rules=attribute_rules,
            )
        except RuntimeError:
            # svglint not available
            return []

    def _run_custom_rules(self, content: str) -> list[LintIssue]:
        """Run custom Python-based lint rules.

        Args:
            content: SVG content to lint

        Returns:
            List of issues from custom rules
        """
        issues: list[LintIssue] = []
        rules = self._preset_config.get("rules", {})

        # Check for viewBox requirement (strict preset)
        if rules.get("viewbox_required"):
            if "viewBox" not in content and "viewbox" not in content.lower():
                issues.append(
                    LintIssue(
                        severity=LintSeverity.WARNING,
                        code="svg/missing-viewbox",
                        message="SVG is missing viewBox attribute. This may cause scaling issues.",
                        suggestion="Add a viewBox attribute to the <svg> element",
                        source="custom-rules",
                    )
                )

        # Check for title requirement (strict preset)
        if rules.get("title_required"):
            if "<title>" not in content.lower():
                issues.append(
                    LintIssue(
                        severity=LintSeverity.WARNING,
                        code="a11y/missing-title",
                        message="SVG is missing <title> element. This affects accessibility.",
                        suggestion="Add a <title> element as the first child of <svg>",
                        source="custom-rules",
                    )
                )

        # Check for inline styles (strict preset)
        if rules.get("inline_styles") == "warning":
            import re

            style_count = len(re.findall(r'style\s*=\s*["\']', content))
            if style_count > 5:  # Only warn if there are many
                issues.append(
                    LintIssue(
                        severity=LintSeverity.WARNING,
                        code="style/inline-styles",
                        message=f"Many inline style attributes detected ({style_count}). Consider using CSS classes.",
                        suggestion="Use <style> element or external CSS for better maintainability",
                        source="custom-rules",
                    )
                )

        return issues


def lint_svg(
    content: str,
    preset: LintPreset = "default",
    *,
    use_scour: bool | None = None,
    use_svglint: bool | None = None,
    use_custom: bool | None = None,
    element_rules: dict[str, Any] | None = None,
    attribute_rules: list[dict[str, Any]] | None = None,
) -> LintResult:
    """Convenience function to lint SVG content.

    Args:
        content: SVG content to lint
        preset: Lint preset ('relaxed', 'default', 'strict', 'inkscape')
        use_scour: Run Scour-based Inkscape compatibility checks
        use_svglint: Run svglint rules (requires Node.js)
        use_custom: Run custom Python rules
        element_rules: Custom element rules for svglint
        attribute_rules: Custom attribute rules for svglint

    Returns:
        LintResult with all issues found
    """
    linter = SVGLinter(preset=preset)
    return linter.lint(
        content,
        use_scour=use_scour,
        use_svglint=use_svglint,
        use_custom=use_custom,
        element_rules=element_rules,
        attribute_rules=attribute_rules,
    )
