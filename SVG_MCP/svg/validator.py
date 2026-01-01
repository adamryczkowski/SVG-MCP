"""SVG validation module using lxml."""

import re
from pathlib import Path
from typing import Any

from lxml import etree  # pyright: ignore[reportAttributeAccessIssue]

from SVG_MCP.models.types import SVGInfo, ValidationError, ValidationResult
from SVG_MCP.svg.utils import parse_viewbox

# SVG namespace
SVG_NAMESPACE = "http://www.w3.org/2000/svg"
SVG_NAMESPACE_MAP = {"svg": SVG_NAMESPACE}
XLINK_NAMESPACE = "http://www.w3.org/1999/xlink"

# Pattern to detect base64 embedded images
BASE64_DATA_URI_PATTERN = re.compile(r"^data:image/[^;]+;base64,", re.IGNORECASE)


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

            # Check for embedded images (base64 data URIs)
            # This is an error because embedded images bloat the SVG file size
            # and overwhelm AI context windows
            embedded_image_errors = self._check_embedded_images(root, content)
            errors.extend(embedded_image_errors)

            # If there are embedded image errors, the SVG is invalid
            is_valid = len(errors) == 0

            return ValidationResult(
                valid=is_valid, errors=errors, warnings=warnings, info=info
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
        viewbox = parse_viewbox(root.get("viewBox"))

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

    def _check_embedded_images(self, root: Any, content: str) -> list[ValidationError]:
        """Check for embedded images (base64 data URIs) in the SVG.

        Embedded images cause SVG files to explode in size, overwhelming
        the context of AI readers. Images should be linked, not embedded.

        Args:
            root: lxml root element.
            content: Original SVG content for line number extraction.

        Returns:
            List of ValidationError for each embedded image found.
        """
        errors: list[ValidationError] = []
        content_lines = content.split("\n")

        # Find all image elements (both namespaced and non-namespaced)
        for element in root.iter():
            tag = element.tag
            # Skip comments and other non-element nodes (their tag is a function)
            if not isinstance(tag, str):
                continue
            local_name = tag.split("}")[-1] if "}" in tag else tag

            if local_name == "image":
                # Check href attribute (SVG 2.0)
                href = element.get("href")
                # Check xlink:href attribute (SVG 1.1)
                xlink_href = element.get(f"{{{XLINK_NAMESPACE}}}href")

                # Check both href variants for embedded data
                for attr_name, attr_value in [
                    ("href", href),
                    ("xlink:href", xlink_href),
                ]:
                    if attr_value and BASE64_DATA_URI_PATTERN.match(attr_value):
                        # Try to find the line number
                        line_num = self._find_element_line(element, content_lines)

                        # Calculate approximate size of embedded data
                        data_size = len(attr_value)
                        size_kb = data_size / 1024

                        errors.append(
                            ValidationError(
                                line=line_num,
                                column=None,
                                message=(
                                    f"Embedded image detected ({attr_name} attribute, "
                                    f"~{size_kb:.1f} KB). Embedded images bloat SVG file "
                                    "size and overwhelm AI context windows."
                                ),
                                suggestion=(
                                    "Use a linked image instead: replace the base64 data URI "
                                    "with a relative or absolute file path (e.g., "
                                    f'{attr_name}="images/photo.png")'
                                ),
                            )
                        )

        return errors

    def _find_element_line(self, element: Any, content_lines: list[str]) -> int | None:
        """Try to find the line number of an element in the content.

        Args:
            element: lxml element to find.
            content_lines: List of content lines.

        Returns:
            Line number (1-based) or None if not found.
        """
        # lxml elements have sourceline attribute when parsed
        if hasattr(element, "sourceline") and element.sourceline is not None:
            return element.sourceline

        # Fallback: try to find by tag name (less accurate)
        tag = element.tag
        local_name = tag.split("}")[-1] if "}" in tag else tag

        for i, line in enumerate(content_lines, 1):
            if f"<{local_name}" in line or f"<svg:{local_name}" in line:
                return i

        return None
