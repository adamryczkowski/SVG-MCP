"""svglint subprocess wrapper for SVG linting.

This module provides a Python wrapper around the svglint Node.js tool,
enabling configurable SVG linting with element and attribute rules.

svglint is optional - if Node.js or svglint is not installed, the
linter will gracefully degrade to Scour-only mode.
"""

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from SVG_MCP.models.lint_types import LintIssue, LintSeverity


class SvglintRunner:
    """Run svglint as a subprocess.

    This class wraps the svglint Node.js tool, providing:
    - Availability detection (graceful degradation if not installed)
    - Temporary file handling for SVG content
    - Output parsing to LintIssue objects
    - Dynamic config generation for element/attribute rules
    """

    _available: bool | None = None
    _version: str | None = None

    @classmethod
    def is_available(cls) -> bool:
        """Check if svglint is installed and working.

        Returns:
            True if svglint can be executed, False otherwise.
        """
        if cls._available is None:
            cls._available = cls._check_svglint()
        return cls._available

    @classmethod
    def get_version(cls) -> str | None:
        """Get the svglint version if available.

        Returns:
            Version string or None if not available.
        """
        if cls._version is None and cls.is_available():
            cls._version = cls._get_version()
        return cls._version

    @classmethod
    def _check_svglint(cls) -> bool:
        """Check if svglint command works."""
        # First check if node is available
        if not shutil.which("node"):
            return False

        # Check if npx is available
        if not shutil.which("npx"):
            return False

        # Then check if svglint is installed
        try:
            result = subprocess.run(
                ["npx", "--yes", "svglint", "--version"],
                capture_output=True,
                text=True,
                timeout=60,  # npx may need to download svglint
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return False

    @classmethod
    def _get_version(cls) -> str | None:
        """Get svglint version."""
        try:
            result = subprocess.run(
                ["npx", "--yes", "svglint", "--version"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
        return None

    def __init__(self) -> None:
        """Initialize the svglint runner.

        Raises:
            RuntimeError: If svglint is not available.
        """
        if not self.is_available():
            msg = (
                "svglint not available. Install Node.js and run: npm install -g svglint"
            )
            raise RuntimeError(msg)

    def lint(
        self,
        content: str,
        *,
        element_rules: dict[str, Any] | None = None,
        attribute_rules: list[dict[str, Any]] | None = None,
        validate_xml: bool = True,
    ) -> list[LintIssue]:
        """Run svglint on SVG content.

        Args:
            content: SVG content to lint
            element_rules: Element presence/count rules (elm config)
            attribute_rules: Attribute validation rules (attr config)
            validate_xml: Whether to validate XML syntax

        Returns:
            List of lint issues found
        """
        # Create temporary directory for SVG and config
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Write SVG content to temp file
            svg_file = temp_path / "input.svg"
            svg_file.write_text(content, encoding="utf-8")

            # Generate config file
            config = self._build_config(element_rules, attribute_rules, validate_xml)
            config_file = temp_path / ".svglintrc.js"
            config_file.write_text(config, encoding="utf-8")

            # Run svglint
            try:
                result = subprocess.run(
                    ["npx", "--yes", "svglint", "--ci", str(svg_file)],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=temp_dir,
                )
                return self._parse_output(
                    result.stdout, result.stderr, result.returncode
                )
            except subprocess.TimeoutExpired:
                return [
                    LintIssue(
                        severity=LintSeverity.ERROR,
                        code="svglint/timeout",
                        message="svglint timed out after 30 seconds",
                        source="svglint",
                    )
                ]
            except (FileNotFoundError, OSError) as e:
                return [
                    LintIssue(
                        severity=LintSeverity.ERROR,
                        code="svglint/error",
                        message=f"Failed to run svglint: {e}",
                        source="svglint",
                    )
                ]

    def _build_config(
        self,
        element_rules: dict[str, Any] | None,
        attribute_rules: list[dict[str, Any]] | None,
        validate_xml: bool,
    ) -> str:
        """Build svglint config file content.

        Args:
            element_rules: Element presence/count rules
            attribute_rules: Attribute validation rules
            validate_xml: Whether to validate XML

        Returns:
            JavaScript config file content
        """
        rules: dict[str, Any] = {}

        # Add XML validation rule
        if validate_xml:
            rules["valid"] = True

        # Add element rules
        if element_rules:
            rules["elm"] = element_rules

        # Add attribute rules
        if attribute_rules:
            # Convert Python dicts to JS-compatible format
            rules["attr"] = attribute_rules

        # Generate JavaScript config
        config_json = json.dumps({"rules": rules}, indent=2)

        # Convert JSON to JavaScript module export
        return f"""/** @type {{import('svglint').Config}} */
const config = {config_json};
export default config;
"""

    def _parse_output(
        self,
        stdout: str,
        stderr: str,
        returncode: int,
    ) -> list[LintIssue]:
        """Parse svglint output into LintIssue objects.

        Args:
            stdout: Standard output from svglint
            stderr: Standard error from svglint
            returncode: Exit code from svglint

        Returns:
            List of lint issues found
        """
        issues: list[LintIssue] = []

        # If returncode is 0, no issues
        if returncode == 0:
            return issues

        # Parse output for errors
        # svglint output format varies, but typically includes:
        # - File path
        # - Rule name
        # - Error message

        combined_output = stdout + "\n" + stderr

        # Look for error patterns
        # Pattern: "rule-name: error message"
        error_pattern = re.compile(r"^\s*(\w+):\s*(.+)$", re.MULTILINE)
        for match in error_pattern.finditer(combined_output):
            rule_name = match.group(1)
            message = match.group(2).strip()

            # Skip if it's just a file path or status line
            if rule_name.lower() in ("file", "linting", "done", "error", "warning"):
                continue

            issues.append(
                LintIssue(
                    severity=LintSeverity.ERROR,
                    code=f"svglint/{rule_name}",
                    message=message,
                    source="svglint",
                )
            )

        # If we couldn't parse specific errors but returncode indicates failure
        if not issues and returncode != 0:
            # Extract any meaningful error message
            error_msg = combined_output.strip()
            if error_msg:
                # Truncate if too long
                if len(error_msg) > 500:
                    error_msg = error_msg[:500] + "..."
                issues.append(
                    LintIssue(
                        severity=LintSeverity.ERROR,
                        code="svglint/error",
                        message=error_msg,
                        source="svglint",
                    )
                )
            else:
                issues.append(
                    LintIssue(
                        severity=LintSeverity.ERROR,
                        code="svglint/unknown",
                        message="svglint reported an error but no details available",
                        source="svglint",
                    )
                )

        return issues


def svglint_available() -> bool:
    """Check if svglint is available.

    Convenience function for use in tests and conditional logic.

    Returns:
        True if svglint can be executed, False otherwise.
    """
    return SvglintRunner.is_available()


def lint_with_svglint(
    content: str,
    *,
    element_rules: dict[str, Any] | None = None,
    attribute_rules: list[dict[str, Any]] | None = None,
    validate_xml: bool = True,
) -> list[LintIssue]:
    """Convenience function to lint SVG content with svglint.

    Args:
        content: SVG content to lint
        element_rules: Element presence/count rules
        attribute_rules: Attribute validation rules
        validate_xml: Whether to validate XML syntax

    Returns:
        List of lint issues found

    Raises:
        RuntimeError: If svglint is not available.
    """
    runner = SvglintRunner()
    return runner.lint(
        content,
        element_rules=element_rules,
        attribute_rules=attribute_rules,
        validate_xml=validate_xml,
    )
