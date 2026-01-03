"""Scour-based SVG linter for Inkscape/librsvg compatibility.

This module uses Scour in "dry-run" mode to detect issues that would
cause problems in Inkscape or librsvg renderers.
"""

import re
from typing import Any

from lxml import etree  # type: ignore[import-untyped]

from scour import scour  # type: ignore[import-untyped]
from scour.scour import sanitizeOptions  # type: ignore[import-untyped]

from SVG_MCP.models.lint_types import LintIssue, LintSeverity


# Inkscape-specific namespaces that indicate editor data
INKSCAPE_NAMESPACES = {
    "http://www.inkscape.org/namespaces/inkscape": "inkscape",
    "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd": "sodipodi",
}

# Adobe Illustrator namespaces
ADOBE_NAMESPACES = {
    "http://ns.adobe.com/AdobeIllustrator/10.0/": "ai",
    "http://ns.adobe.com/AdobeSVGViewerExtensions/3.0/": "x",
}

# Standard SVG namespaces (not issues)
STANDARD_NAMESPACES = {
    "http://www.w3.org/2000/svg": "svg",
    "http://www.w3.org/1999/xlink": "xlink",
    "http://www.w3.org/XML/1998/namespace": "xml",
    "http://www.w3.org/2000/xmlns/": "xmlns",
}


class ScourLinter:
    """Use Scour to detect Inkscape/librsvg compatibility issues.

    This linter runs Scour in safe mode and analyzes what changes
    it would make to detect potential compatibility issues.
    """

    def __init__(self) -> None:
        """Initialize the Scour linter."""
        self._safe_options = self._build_safe_options()

    def _build_safe_options(self) -> Any:
        """Build Scour options for safe mode (minimal changes)."""
        from types import SimpleNamespace

        opts = SimpleNamespace(
            # High precision (lossless)
            digits=8,
            cdigits=-1,  # Same as digits
            # Keep everything
            keep_editor_data=True,
            remove_metadata=False,
            strip_comments=False,
            remove_titles=False,
            remove_descriptions=False,
            enable_viewboxing=False,
            shorten_ids=False,
            strip_ids=False,
            # Formatting
            indent_type="space",
            indent_depth=1,
            newlines=True,
            strip_xml_prolog=False,
            # Apply librsvg workarounds (this is what we want to detect)
            renderer_workaround=True,
        )

        return sanitizeOptions(opts)

    def lint(self, content: str) -> list[LintIssue]:
        """Lint SVG content for Inkscape/librsvg compatibility issues.

        Args:
            content: SVG content to lint

        Returns:
            List of lint issues found
        """
        issues: list[LintIssue] = []

        # 1. Detect flowtext (Inkscape-specific, not rendered by browsers)
        issues.extend(self._detect_flowtext(content))

        # 2. Detect namespace issues
        issues.extend(self._detect_namespace_issues(content))

        # 3. Detect deprecated xlink usage
        issues.extend(self._detect_deprecated_xlink(content))

        # 4. Detect embedded images (potential issues)
        issues.extend(self._detect_embedded_images(content))

        # 5. Detect relative paths (may break when moved)
        issues.extend(self._detect_relative_paths(content))

        # 6. Detect renderer-specific issues by comparing with Scour output
        issues.extend(self._detect_renderer_issues(content))

        # 7. Detect precision issues
        issues.extend(self._detect_precision_issues(content))

        return issues

    def _detect_flowtext(self, content: str) -> list[LintIssue]:
        """Detect non-standard flowtext (Inkscape-specific).

        Flowtext is an Inkscape extension that is not part of the SVG spec
        and will not render in browsers or librsvg.
        """
        issues: list[LintIssue] = []

        # Find flowRoot elements
        flowroot_pattern = re.compile(r"<flowRoot[^>]*>", re.IGNORECASE)
        for match in flowroot_pattern.finditer(content):
            line_num = content[: match.start()].count("\n") + 1
            issues.append(
                LintIssue(
                    severity=LintSeverity.ERROR,
                    code="inkscape/flowtext",
                    message="Non-standard flowtext detected. Will not render in browsers or librsvg.",
                    line=line_num,
                    suggestion="Convert flowtext to regular text in Inkscape: Text → Convert to Text",
                    source="scour-linter",
                )
            )

        # Also check for flowPara, flowSpan, flowRegion
        for tag in ["flowPara", "flowSpan", "flowRegion", "flowDiv"]:
            pattern = re.compile(rf"<{tag}[^>]*>", re.IGNORECASE)
            for match in pattern.finditer(content):
                line_num = content[: match.start()].count("\n") + 1
                issues.append(
                    LintIssue(
                        severity=LintSeverity.WARNING,
                        code="inkscape/flowtext-element",
                        message=f"Non-standard <{tag}> element detected (part of flowtext).",
                        line=line_num,
                        suggestion="Convert flowtext to regular text in Inkscape: Text → Convert to Text",
                        source="scour-linter",
                    )
                )

        return issues

    def _detect_namespace_issues(self, content: str) -> list[LintIssue]:
        """Detect namespace-related issues."""
        issues: list[LintIssue] = []

        try:
            # Parse the SVG
            root = etree.fromstring(content.encode("utf-8"))

            # Check for editor-specific namespaces
            for ns_uri, prefix in INKSCAPE_NAMESPACES.items():
                if ns_uri in root.nsmap.values():
                    issues.append(
                        LintIssue(
                            severity=LintSeverity.INFO,
                            code=f"namespace/{prefix}",
                            message=f"Inkscape namespace '{prefix}' detected. This data is editor-specific.",
                            suggestion="Use svg_optimize with remove_editor_data=True to remove",
                            source="scour-linter",
                        )
                    )

            for ns_uri, prefix in ADOBE_NAMESPACES.items():
                if ns_uri in root.nsmap.values():
                    issues.append(
                        LintIssue(
                            severity=LintSeverity.INFO,
                            code=f"namespace/{prefix}",
                            message=f"Adobe namespace '{prefix}' detected. This data is editor-specific.",
                            suggestion="Use svg_optimize with remove_editor_data=True to remove",
                            source="scour-linter",
                        )
                    )

            # Check for missing SVG namespace
            svg_ns = "http://www.w3.org/2000/svg"
            if svg_ns not in root.nsmap.values() and root.nsmap.get(None) != svg_ns:
                issues.append(
                    LintIssue(
                        severity=LintSeverity.WARNING,
                        code="namespace/missing-svg",
                        message="SVG namespace not declared. Some renderers may not display correctly.",
                        suggestion='Add xmlns="http://www.w3.org/2000/svg" to the <svg> element',
                        source="scour-linter",
                    )
                )

        except etree.XMLSyntaxError:
            # XML parsing failed, skip namespace checks
            pass

        return issues

    def _detect_deprecated_xlink(self, content: str) -> list[LintIssue]:
        """Detect deprecated xlink:href usage.

        SVG 2 deprecates xlink:href in favor of plain href.
        """
        issues: list[LintIssue] = []

        # Find xlink:href attributes
        xlink_pattern = re.compile(r'xlink:href\s*=\s*["\']', re.IGNORECASE)
        matches = list(xlink_pattern.finditer(content))

        if matches:
            # Only report once, not for every occurrence
            line_num = content[: matches[0].start()].count("\n") + 1
            issues.append(
                LintIssue(
                    severity=LintSeverity.WARNING,
                    code="deprecated/xlink-href",
                    message=f"Deprecated xlink:href found ({len(matches)} occurrences). SVG 2 uses plain href.",
                    line=line_num,
                    suggestion="Replace xlink:href with href (supported in modern browsers)",
                    source="scour-linter",
                )
            )

        return issues

    def _detect_embedded_images(self, content: str) -> list[LintIssue]:
        """Detect embedded base64 images.

        Embedded images significantly increase file size and may cause
        issues with some renderers.
        """
        issues: list[LintIssue] = []

        # Find data: URLs in href or xlink:href
        data_url_pattern = re.compile(
            r'(?:xlink:)?href\s*=\s*["\']data:image/[^"\']+["\']', re.IGNORECASE
        )
        matches = list(data_url_pattern.finditer(content))

        if matches:
            line_num = content[: matches[0].start()].count("\n") + 1
            issues.append(
                LintIssue(
                    severity=LintSeverity.WARNING,
                    code="embedded/base64-image",
                    message=f"Embedded base64 image(s) detected ({len(matches)} occurrences). This increases file size.",
                    line=line_num,
                    suggestion="Consider using external image files for better performance",
                    source="scour-linter",
                )
            )

        return issues

    def _detect_relative_paths(self, content: str) -> list[LintIssue]:
        """Detect relative paths in href attributes.

        Relative paths may break when the SVG is moved or embedded.
        """
        issues: list[LintIssue] = []

        # Find relative paths (not starting with http, https, data, or #)
        href_pattern = re.compile(
            r'(?:xlink:)?href\s*=\s*["\'](?!https?://|data:|#)([^"\']+)["\']',
            re.IGNORECASE,
        )
        matches = list(href_pattern.finditer(content))

        if matches:
            line_num = content[: matches[0].start()].count("\n") + 1
            issues.append(
                LintIssue(
                    severity=LintSeverity.INFO,
                    code="path/relative",
                    message=f"Relative path(s) detected ({len(matches)} occurrences). May break when SVG is moved.",
                    line=line_num,
                    suggestion="Consider using absolute URLs or embedding resources",
                    source="scour-linter",
                )
            )

        return issues

    def _detect_renderer_issues(self, content: str) -> list[LintIssue]:
        """Detect issues that Scour's renderer workarounds would fix.

        This runs Scour in safe mode and compares the output to detect
        issues that would be fixed by renderer workarounds.
        """
        issues: list[LintIssue] = []

        try:
            # Run Scour with renderer workarounds
            safe_output = scour.scourString(content, self._safe_options)

            # If the output differs, there are potential renderer issues
            if content.strip() != safe_output.strip():
                # Check for specific patterns that Scour fixes

                # 1. Check for style attributes that should be presentation attributes
                if 'style="' in content and 'style="' not in safe_output:
                    issues.append(
                        LintIssue(
                            severity=LintSeverity.INFO,
                            code="renderer/style-to-attributes",
                            message="Style attributes could be converted to presentation attributes for better compatibility.",
                            suggestion="Use svg_optimize to convert style attributes",
                            source="scour-linter",
                        )
                    )

                # 2. Check for unnecessary whitespace in path data
                path_pattern = re.compile(r'd\s*=\s*["\']([^"\']+)["\']')
                original_paths = path_pattern.findall(content)
                optimized_paths = path_pattern.findall(safe_output)

                if original_paths and optimized_paths:
                    original_len = sum(len(p) for p in original_paths)
                    optimized_len = sum(len(p) for p in optimized_paths)
                    if original_len > optimized_len * 1.1:  # 10% threshold
                        issues.append(
                            LintIssue(
                                severity=LintSeverity.INFO,
                                code="renderer/path-optimization",
                                message="Path data could be optimized for smaller file size.",
                                suggestion="Use svg_optimize to optimize path data",
                                source="scour-linter",
                            )
                        )

        except Exception:
            # Scour failed, skip renderer checks
            pass

        return issues

    def _detect_precision_issues(self, content: str) -> list[LintIssue]:
        """Detect excessive precision in numeric values.

        Very high precision values increase file size without visual benefit.
        """
        issues: list[LintIssue] = []

        # Find numbers with more than 6 decimal places
        high_precision_pattern = re.compile(r"\d+\.\d{7,}")
        matches = list(high_precision_pattern.finditer(content))

        if len(matches) > 10:  # Only report if there are many
            issues.append(
                LintIssue(
                    severity=LintSeverity.INFO,
                    code="precision/excessive",
                    message=f"Excessive numeric precision detected ({len(matches)} values with 7+ decimal places).",
                    suggestion="Use svg_optimize with precision=5 to reduce file size",
                    source="scour-linter",
                )
            )

        return issues


def lint_svg_with_scour(content: str) -> list[LintIssue]:
    """Convenience function to lint SVG content with Scour.

    Args:
        content: SVG content to lint

    Returns:
        List of lint issues found
    """
    linter = ScourLinter()
    return linter.lint(content)
