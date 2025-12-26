"""SVG validation module using lxml."""

import re
from pathlib import Path
from typing import Any

from lxml import etree  # pyright: ignore[reportAttributeAccessIssue]

from SVG_MCP.models.types import SVGInfo, ValidationError, ValidationResult, ViewBox

# SVG namespace
SVG_NAMESPACE = "http://www.w3.org/2000/svg"
SVG_NAMESPACE_MAP = {"svg": SVG_NAMESPACE}


class SVGValidator:
    """Validates SVG content and extracts information."""

    def __init__(self) -> None:
        """Initialize the SVG validator."""
        self._parser = etree.XMLParser(
            recover=False,
            remove_comments=False,
            remove_blank_text=False,
        )

    def validate(self, content: str) -> ValidationResult:
        """Validate SVG content string.

        Args:
            content: SVG content as a string.

        Returns:
            ValidationResult with validation status and any errors.

        Raises:
            TypeError: If content is None.
            ValueError: If content is not a string.
        """
        if content is None:
            raise TypeError("SVG content cannot be None")
        if not isinstance(content, str):
            raise ValueError("SVG content must be a string")

        errors: list[ValidationError] = []
        warnings: list[ValidationError] = []
        info: SVGInfo | None = None

        # Check for empty content
        if not content.strip():
            errors.append(
                ValidationError(
                    line=1,
                    column=1,
                    message="Empty SVG content",
                    suggestion="Provide valid SVG content starting with <svg> element",
                )
            )
            return ValidationResult(
                valid=False, errors=errors, warnings=warnings, info=None
            )

        # Try to parse the XML
        try:
            # Parse the content
            root = etree.fromstring(content.encode("utf-8"), parser=self._parser)

            # Check if root element is SVG
            if not self._is_svg_element(root):
                errors.append(
                    ValidationError(
                        line=1,
                        column=1,
                        message=f"Root element is not an SVG element. Found: {root.tag}",
                        suggestion="Ensure the root element is <svg> with proper namespace",
                    )
                )
                return ValidationResult(
                    valid=False, errors=errors, warnings=warnings, info=None
                )

            # Extract SVG information
            info = self._extract_svg_info(root)

            # Check for namespace
            if not info.has_namespace:
                warnings.append(
                    ValidationError(
                        line=1,
                        column=1,
                        message="SVG element is missing the standard namespace",
                        suggestion='Add xmlns="http://www.w3.org/2000/svg" to the svg element',
                    )
                )

            return ValidationResult(
                valid=True, errors=errors, warnings=warnings, info=info
            )

        except etree.XMLSyntaxError as e:
            # Extract error details from lxml exception
            error = self._parse_xml_error(e, content)
            errors.append(error)
            return ValidationResult(
                valid=False, errors=errors, warnings=warnings, info=None
            )

    def validate_file(self, file_path: Path | str) -> ValidationResult:
        """Validate SVG file.

        Args:
            file_path: Path to the SVG file.

        Returns:
            ValidationResult with validation status and any errors.
        """
        path = Path(file_path)

        if not path.exists():
            return ValidationResult(
                valid=False,
                errors=[
                    ValidationError(
                        line=None,
                        column=None,
                        message=f"File not found: {path}",
                        suggestion="Check that the file path is correct",
                    )
                ],
                warnings=[],
                info=None,
            )

        try:
            content = path.read_text(encoding="utf-8")
            return self.validate(content)
        except UnicodeDecodeError as e:
            return ValidationResult(
                valid=False,
                errors=[
                    ValidationError(
                        line=None,
                        column=None,
                        message=f"Failed to read file as UTF-8: {e}",
                        suggestion="Ensure the file is encoded in UTF-8",
                    )
                ],
                warnings=[],
                info=None,
            )
        except OSError as e:
            return ValidationResult(
                valid=False,
                errors=[
                    ValidationError(
                        line=None,
                        column=None,
                        message=f"Failed to read file: {e}",
                        suggestion="Check file permissions and accessibility",
                    )
                ],
                warnings=[],
                info=None,
            )

    def _is_svg_element(self, element: Any) -> bool:
        """Check if element is an SVG element.

        Args:
            element: lxml element to check.

        Returns:
            True if element is an SVG element.
        """
        tag = element.tag
        # Handle namespaced tag
        if tag.startswith("{"):
            namespace = tag[1 : tag.index("}")]
            local_name = tag[tag.index("}") + 1 :]
            return namespace == SVG_NAMESPACE and local_name == "svg"
        # Handle non-namespaced tag
        return tag == "svg"

    def _extract_svg_info(self, root: Any) -> SVGInfo:
        """Extract information from SVG root element.

        Args:
            root: lxml root element.

        Returns:
            SVGInfo with extracted information.
        """
        # Count elements
        element_count = len(list(root.iter()))

        # Check namespace
        has_namespace = False
        namespaces: dict[str, str] = {}

        # Get namespaces from the root element
        if root.nsmap:
            for prefix, uri in root.nsmap.items():
                if prefix is None:
                    prefix = ""
                namespaces[prefix] = uri
                if uri == SVG_NAMESPACE:
                    has_namespace = True

        # Also check the tag itself for namespace
        if root.tag.startswith("{" + SVG_NAMESPACE + "}"):
            has_namespace = True

        # Extract viewBox
        viewbox = self._parse_viewbox(root.get("viewBox"))

        # Extract dimensions
        width = root.get("width")
        height = root.get("height")

        return SVGInfo(
            element_count=element_count,
            viewbox=viewbox,
            width=width,
            height=height,
            has_namespace=has_namespace,
            namespaces=namespaces,
        )

    def _parse_viewbox(self, viewbox_str: str | None) -> ViewBox | None:
        """Parse viewBox attribute string.

        Args:
            viewbox_str: viewBox attribute value.

        Returns:
            ViewBox if valid, None otherwise.
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

    def _parse_xml_error(
        self, error: etree.XMLSyntaxError, content: str
    ) -> ValidationError:
        """Parse lxml XMLSyntaxError into ValidationError.

        Args:
            error: lxml XMLSyntaxError exception.
            content: Original SVG content for context extraction.

        Returns:
            ValidationError with extracted details.
        """
        # Extract line and column from error
        line = error.lineno
        column = error.offset

        # Get error message
        message = str(error.msg) if error.msg else str(error)

        # Extract context from content
        context = None
        if line is not None and line > 0:
            lines = content.split("\n")
            if 0 < line <= len(lines):
                context = lines[line - 1].strip()

        # Generate suggestion based on error type
        suggestion = self._generate_suggestion(message)

        return ValidationError(
            line=line,
            column=column,
            message=message,
            context=context,
            suggestion=suggestion,
        )

    def _generate_suggestion(self, error_message: str) -> str | None:
        """Generate a suggestion based on error message.

        Args:
            error_message: Error message from parser.

        Returns:
            Suggestion string or None.
        """
        error_lower = error_message.lower()

        if "opening and ending tag mismatch" in error_lower:
            return "Check that all tags are properly closed and nested"
        if "expected '>'" in error_lower or "expected '/>'" in error_lower:
            return "Check for missing closing bracket '>' or self-closing '/>'"
        if "unescaped" in error_lower and "<" in error_lower:
            return "Use < instead of < in text content"
        if "unescaped" in error_lower and "&" in error_lower:
            return "Use & instead of & in text content"
        if "attribute" in error_lower and "value" in error_lower:
            return "Check that attribute values are properly quoted"
        if "premature end" in error_lower:
            return "Check that all elements are properly closed"
        if "not well-formed" in error_lower:
            return "Check XML syntax: proper nesting, closed tags, quoted attributes"

        return None
