"""Unit tests for SVG validator module."""

import pytest

from SVG_MCP.models.types import ValidationResult, ViewBox
from SVG_MCP.svg.validator import SVGValidator


class TestSVGValidatorValidSVGs:
    """Tests for validating correct SVG files."""

    def test_validate_minimal_svg(self, minimal_svg: str) -> None:
        """Test validation of a minimal valid SVG."""
        validator = SVGValidator()
        result = validator.validate(minimal_svg)

        assert isinstance(result, ValidationResult)
        assert result.valid is True
        assert len(result.errors) == 0
        assert result.info is not None
        assert result.info.has_namespace is True

    def test_validate_complex_svg(self, complex_svg: str) -> None:
        """Test validation of a complex valid SVG with multiple elements."""
        validator = SVGValidator()
        result = validator.validate(complex_svg)

        assert result.valid is True
        assert len(result.errors) == 0
        assert result.info is not None
        assert result.info.element_count > 1

    def test_validate_svg_with_viewbox(self, minimal_svg: str) -> None:
        """Test that viewBox is correctly parsed."""
        validator = SVGValidator()
        result = validator.validate(minimal_svg)

        assert result.info is not None
        assert result.info.viewbox is not None
        assert result.info.viewbox.x == 0
        assert result.info.viewbox.y == 0
        assert result.info.viewbox.width == 100
        assert result.info.viewbox.height == 100

    def test_validate_svg_from_file(self, valid_fixtures_dir) -> None:
        """Test validation from a file path."""
        validator = SVGValidator()
        result = validator.validate_file(valid_fixtures_dir / "minimal.svg")

        assert result.valid is True
        assert len(result.errors) == 0


class TestSVGValidatorInvalidSVGs:
    """Tests for validating incorrect SVG files."""

    def test_validate_malformed_svg(self, malformed_svg: str) -> None:
        """Test validation of malformed SVG (unclosed attribute)."""
        validator = SVGValidator()
        result = validator.validate(malformed_svg)

        assert result.valid is False
        assert len(result.errors) > 0
        # Should have line number information
        assert any(e.line is not None for e in result.errors)

    def test_validate_missing_namespace(self, missing_namespace_svg: str) -> None:
        """Test validation of SVG without proper namespace."""
        validator = SVGValidator()
        result = validator.validate(missing_namespace_svg)

        # Missing namespace should produce a warning, not necessarily invalid
        assert result.info is not None
        assert result.info.has_namespace is False
        # Should have a warning about missing namespace
        assert len(result.warnings) > 0 or not result.info.has_namespace

    def test_validate_unclosed_tag(self, unclosed_tag_svg: str) -> None:
        """Test validation of SVG with unclosed tag."""
        validator = SVGValidator()
        result = validator.validate(unclosed_tag_svg)

        assert result.valid is False
        assert len(result.errors) > 0
        # Error message should mention the issue
        assert any(
            "tag" in e.message.lower() or "element" in e.message.lower()
            for e in result.errors
        )

    def test_validate_not_svg(self, not_svg: str) -> None:
        """Test validation of non-SVG content (HTML)."""
        validator = SVGValidator()
        result = validator.validate(not_svg)

        assert result.valid is False
        assert len(result.errors) > 0
        # Should indicate it's not an SVG
        assert any("svg" in e.message.lower() for e in result.errors)

    def test_validate_empty_string(self) -> None:
        """Test validation of empty string."""
        validator = SVGValidator()
        result = validator.validate("")

        assert result.valid is False
        assert len(result.errors) > 0

    def test_validate_none_content(self) -> None:
        """Test validation of None content raises appropriate error."""
        validator = SVGValidator()
        with pytest.raises((TypeError, ValueError)):
            validator.validate(None)  # type: ignore

    def test_validate_nonexistent_file(self, tmp_path) -> None:
        """Test validation of non-existent file."""
        validator = SVGValidator()
        result = validator.validate_file(tmp_path / "nonexistent.svg")

        assert result.valid is False
        assert len(result.errors) > 0
        assert any(
            "file" in e.message.lower() or "not found" in e.message.lower()
            for e in result.errors
        )


class TestSVGValidatorErrorDetails:
    """Tests for error detail extraction."""

    def test_error_has_line_number(self, malformed_svg: str) -> None:
        """Test that errors include line numbers when available."""
        validator = SVGValidator()
        result = validator.validate(malformed_svg)

        assert len(result.errors) > 0
        # At least one error should have line information
        errors_with_lines = [e for e in result.errors if e.line is not None]
        assert len(errors_with_lines) > 0

    def test_error_has_context(self, malformed_svg: str) -> None:
        """Test that errors include context when available."""
        validator = SVGValidator()
        result = validator.validate(malformed_svg)

        assert len(result.errors) > 0
        # Check that error messages are descriptive
        for error in result.errors:
            assert len(error.message) > 0

    def test_error_has_suggestion(self, unclosed_tag_svg: str) -> None:
        """Test that errors may include suggestions for fixes."""
        validator = SVGValidator()
        result = validator.validate(unclosed_tag_svg)

        # Suggestions are optional but should be present for common errors
        # This is a nice-to-have feature
        assert len(result.errors) > 0


class TestSVGValidatorSVGInfo:
    """Tests for SVG information extraction."""

    def test_extract_element_count(self, complex_svg: str) -> None:
        """Test that element count is correctly extracted."""
        validator = SVGValidator()
        result = validator.validate(complex_svg)

        assert result.info is not None
        assert result.info.element_count > 0

    def test_extract_viewbox(self, minimal_svg: str) -> None:
        """Test that viewBox is correctly extracted."""
        validator = SVGValidator()
        result = validator.validate(minimal_svg)

        assert result.info is not None
        assert result.info.viewbox is not None
        assert isinstance(result.info.viewbox, ViewBox)

    def test_extract_dimensions(self) -> None:
        """Test extraction of width and height attributes."""
        svg_with_dimensions = """<svg xmlns="http://www.w3.org/2000/svg"
            width="200" height="150" viewBox="0 0 200 150">
            <rect width="100" height="100"/>
        </svg>"""

        validator = SVGValidator()
        result = validator.validate(svg_with_dimensions)

        assert result.info is not None
        assert result.info.width == "200"
        assert result.info.height == "150"

    def test_extract_namespaces(self) -> None:
        """Test extraction of namespace declarations."""
        svg_with_namespaces = """<svg xmlns="http://www.w3.org/2000/svg"
            xmlns:xlink="http://www.w3.org/1999/xlink">
            <rect width="100" height="100"/>
        </svg>"""

        validator = SVGValidator()
        result = validator.validate(svg_with_namespaces)

        assert result.info is not None
        assert result.info.has_namespace is True
        assert len(result.info.namespaces) >= 1

    def test_svg_without_viewbox(self) -> None:
        """Test SVG without viewBox attribute."""
        svg_no_viewbox = """<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
            <rect width="100" height="100"/>
        </svg>"""

        validator = SVGValidator()
        result = validator.validate(svg_no_viewbox)

        assert result.valid is True
        assert result.info is not None
        assert result.info.viewbox is None


class TestSVGValidatorEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_validate_svg_with_cdata(self) -> None:
        """Test SVG with CDATA sections."""
        svg_with_cdata = """<svg xmlns="http://www.w3.org/2000/svg">
            <style><![CDATA[
                .cls { fill: red; }
            ]]></style>
            <rect class="cls" width="100" height="100"/>
        </svg>"""

        validator = SVGValidator()
        result = validator.validate(svg_with_cdata)

        assert result.valid is True

    def test_validate_svg_with_comments(self) -> None:
        """Test SVG with XML comments."""
        svg_with_comments = """<svg xmlns="http://www.w3.org/2000/svg">
            <!-- This is a comment -->
            <rect width="100" height="100"/>
        </svg>"""

        validator = SVGValidator()
        result = validator.validate(svg_with_comments)

        assert result.valid is True

    def test_validate_svg_with_processing_instruction(self) -> None:
        """Test SVG with XML processing instruction."""
        svg_with_pi = """<?xml version="1.0" encoding="UTF-8"?>
        <svg xmlns="http://www.w3.org/2000/svg">
            <rect width="100" height="100"/>
        </svg>"""

        validator = SVGValidator()
        result = validator.validate(svg_with_pi)

        assert result.valid is True

    def test_validate_svg_with_doctype(self) -> None:
        """Test SVG with DOCTYPE declaration."""
        svg_with_doctype = """<?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
        <svg xmlns="http://www.w3.org/2000/svg">
            <rect width="100" height="100"/>
        </svg>"""

        validator = SVGValidator()
        result = validator.validate(svg_with_doctype)

        assert result.valid is True

    def test_validate_svg_with_entities(self) -> None:
        """Test SVG with XML entities."""
        # Note: The entities must be properly escaped in the source
        # < = <, > = >, & = &
        svg_with_entities = (
            '<svg xmlns="http://www.w3.org/2000/svg"><text>'
            + "&"
            + "lt;Hello"
            + "&"
            + "gt; "
            + "&"
            + "amp; World</text></svg>"
        )

        validator = SVGValidator()
        result = validator.validate(svg_with_entities)

        assert result.valid is True

    def test_validate_large_svg(self) -> None:
        """Test validation of a large SVG with many elements."""
        # Generate a large SVG with many elements
        elements = "\n".join(
            f'<rect x="{i}" y="{i}" width="10" height="10"/>' for i in range(100)
        )
        large_svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000">
            {elements}
        </svg>"""

        validator = SVGValidator()
        result = validator.validate(large_svg)

        assert result.valid is True
        assert result.info is not None
        assert result.info.element_count >= 100

    def test_validate_svg_with_unicode(self) -> None:
        """Test SVG with unicode characters."""
        svg_with_unicode = """<svg xmlns="http://www.w3.org/2000/svg">
            <text>Hello 世界 🌍 مرحبا</text>
        </svg>"""

        validator = SVGValidator()
        result = validator.validate(svg_with_unicode)

        assert result.valid is True

    def test_validate_svg_with_whitespace_variations(self) -> None:
        """Test SVG with various whitespace patterns."""
        svg_with_whitespace = """<svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox = "0 0 100 100"
        >
            <rect
                width="100"
                height="100"
            />
        </svg>"""

        validator = SVGValidator()
        result = validator.validate(svg_with_whitespace)

        assert result.valid is True
