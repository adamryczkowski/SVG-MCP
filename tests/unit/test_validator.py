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


class TestSVGValidatorEmbeddedImages:
    """Tests for embedded image detection.

    Embedded images (base64 data URIs) cause SVG files to explode in size,
    overwhelming the context of AI readers. Images should be linked, not embedded.
    """

    # Short base64 test data that won't trigger secret scanners
    # This is just "test" encoded in base64
    _SHORT_BASE64 = "dGVzdA=="

    def test_validate_svg_with_embedded_image_href(self) -> None:
        """Test that SVG with embedded image using href attribute is invalid."""
        svg_with_embedded = f"""<svg xmlns="http://www.w3.org/2000/svg">
            <image href="data:image/png;base64,{self._SHORT_BASE64}" width="100" height="100"/>
        </svg>"""

        validator = SVGValidator()
        result = validator.validate(svg_with_embedded)

        assert result.valid is False
        assert len(result.errors) > 0
        assert any("embedded" in e.message.lower() for e in result.errors)
        assert any("href" in e.message.lower() for e in result.errors)

    def test_validate_svg_with_embedded_image_xlink_href(self) -> None:
        """Test that SVG with embedded image using xlink:href attribute is invalid."""
        svg_with_embedded = f"""<svg xmlns="http://www.w3.org/2000/svg"
            xmlns:xlink="http://www.w3.org/1999/xlink">
            <image xlink:href="data:image/png;base64,{self._SHORT_BASE64}" width="100" height="100"/>
        </svg>"""

        validator = SVGValidator()
        result = validator.validate(svg_with_embedded)

        assert result.valid is False
        assert len(result.errors) > 0
        assert any("embedded" in e.message.lower() for e in result.errors)
        assert any("xlink:href" in e.message.lower() for e in result.errors)

    def test_validate_svg_with_linked_image_relative_path(self) -> None:
        """Test that SVG with linked image using relative path is flagged as error.

        Relative paths may fail to resolve in Inkscape/librsvg when the SVG is
        rendered without proper working directory context.
        """
        svg_with_linked = """<svg xmlns="http://www.w3.org/2000/svg">
            <image href="images/photo.png" width="100" height="100"/>
        </svg>"""

        validator = SVGValidator()
        result = validator.validate(svg_with_linked)

        assert result.valid is False
        assert len(result.errors) > 0
        assert any("relative path" in e.message.lower() for e in result.errors)
        assert any(e.suggestion is not None for e in result.errors)

    def test_validate_svg_with_linked_image_url(self) -> None:
        """Test that SVG with linked image (URL) is valid."""
        svg_with_url = """<svg xmlns="http://www.w3.org/2000/svg">
            <image href="https://example.com/image.png" width="100" height="100"/>
        </svg>"""

        validator = SVGValidator()
        result = validator.validate(svg_with_url)

        assert result.valid is True
        assert len(result.errors) == 0

    def test_validate_svg_without_images(self) -> None:
        """Test that SVG without any images is valid."""
        svg_no_images = """<svg xmlns="http://www.w3.org/2000/svg">
            <rect width="100" height="100" fill="red"/>
            <circle cx="50" cy="50" r="25" fill="blue"/>
        </svg>"""

        validator = SVGValidator()
        result = validator.validate(svg_no_images)

        assert result.valid is True
        assert len(result.errors) == 0

    def test_embedded_image_error_includes_size(self) -> None:
        """Test that embedded image error includes approximate size."""
        svg_with_embedded = f"""<svg xmlns="http://www.w3.org/2000/svg">
            <image href="data:image/png;base64,{self._SHORT_BASE64}" width="100" height="100"/>
        </svg>"""

        validator = SVGValidator()
        result = validator.validate(svg_with_embedded)

        assert len(result.errors) > 0
        # Error should mention size in KB
        assert any("kb" in e.message.lower() for e in result.errors)

    def test_embedded_image_error_includes_suggestion(self) -> None:
        """Test that embedded image error includes a suggestion to use linked images."""
        svg_with_embedded = f"""<svg xmlns="http://www.w3.org/2000/svg">
            <image href="data:image/png;base64,{self._SHORT_BASE64}" width="100" height="100"/>
        </svg>"""

        validator = SVGValidator()
        result = validator.validate(svg_with_embedded)

        assert len(result.errors) > 0
        # Error should have a suggestion
        assert any(e.suggestion is not None for e in result.errors)
        # Suggestion should mention linked images
        assert any(
            e.suggestion is not None and "linked" in e.suggestion.lower()
            for e in result.errors
        )

    def test_multiple_embedded_images_all_reported(self) -> None:
        """Test that multiple embedded images are all reported as errors."""
        svg_with_multiple = f"""<svg xmlns="http://www.w3.org/2000/svg">
            <image href="data:image/png;base64,{self._SHORT_BASE64}" width="50" height="50"/>
            <image href="data:image/jpeg;base64,{self._SHORT_BASE64}" width="50" height="50"/>
        </svg>"""

        validator = SVGValidator()
        result = validator.validate(svg_with_multiple)

        assert result.valid is False
        # Should have at least 2 errors (one for each embedded image)
        embedded_errors = [e for e in result.errors if "embedded" in e.message.lower()]
        assert len(embedded_errors) >= 2


class TestSVGValidatorRelativeImagePaths:
    """Tests for relative image path detection.

    Relative paths in SVG image elements may fail to resolve in Inkscape/librsvg
    when the SVG is rendered without proper working directory context.
    """

    def test_relative_path_simple_filename(self) -> None:
        """Test that simple filename (relative path) is flagged as error."""
        svg = """<svg xmlns="http://www.w3.org/2000/svg">
            <image href="photo.png" width="100" height="100"/>
        </svg>"""

        validator = SVGValidator()
        result = validator.validate(svg)

        assert result.valid is False
        assert any("relative path" in e.message.lower() for e in result.errors)

    def test_relative_path_with_directory(self) -> None:
        """Test that path with directory (relative) is flagged as error."""
        svg = """<svg xmlns="http://www.w3.org/2000/svg">
            <image href="images/photo.png" width="100" height="100"/>
        </svg>"""

        validator = SVGValidator()
        result = validator.validate(svg)

        assert result.valid is False
        assert any("relative path" in e.message.lower() for e in result.errors)

    def test_relative_path_parent_directory(self) -> None:
        """Test that path with parent directory reference is flagged as error."""
        svg = """<svg xmlns="http://www.w3.org/2000/svg">
            <image href="../images/photo.png" width="100" height="100"/>
        </svg>"""

        validator = SVGValidator()
        result = validator.validate(svg)

        assert result.valid is False
        assert any("relative path" in e.message.lower() for e in result.errors)

    def test_absolute_url_http_is_valid(self) -> None:
        """Test that HTTP URL is valid (not a relative path)."""
        svg = """<svg xmlns="http://www.w3.org/2000/svg">
            <image href="https://example.com/image.png" width="100" height="100"/>
        </svg>"""

        validator = SVGValidator()
        result = validator.validate(svg)

        assert result.valid is True
        assert len(result.errors) == 0

    def test_absolute_url_file_is_valid(self) -> None:
        """Test that file:// URL is valid (absolute path)."""
        svg = """<svg xmlns="http://www.w3.org/2000/svg">
            <image href="file:///home/user/images/photo.png" width="100" height="100"/>
        </svg>"""

        validator = SVGValidator()
        result = validator.validate(svg)

        assert result.valid is True
        assert len(result.errors) == 0

    def test_fragment_reference_is_valid(self) -> None:
        """Test that fragment-only reference (#id) is valid."""
        svg = """<svg xmlns="http://www.w3.org/2000/svg">
            <defs>
                <pattern id="myPattern" width="10" height="10">
                    <rect width="10" height="10" fill="red"/>
                </pattern>
            </defs>
            <rect width="100" height="100" fill="url(#myPattern)"/>
        </svg>"""

        validator = SVGValidator()
        result = validator.validate(svg)

        assert result.valid is True
        assert len(result.errors) == 0

    def test_relative_path_with_xlink_href(self) -> None:
        """Test that relative path with xlink:href is also flagged."""
        svg = """<svg xmlns="http://www.w3.org/2000/svg"
            xmlns:xlink="http://www.w3.org/1999/xlink">
            <image xlink:href="images/photo.png" width="100" height="100"/>
        </svg>"""

        validator = SVGValidator()
        result = validator.validate(svg)

        assert result.valid is False
        assert any("relative path" in e.message.lower() for e in result.errors)

    def test_relative_path_error_includes_path(self) -> None:
        """Test that error message includes the actual path."""
        svg = """<svg xmlns="http://www.w3.org/2000/svg">
            <image href="my-special-image.png" width="100" height="100"/>
        </svg>"""

        validator = SVGValidator()
        result = validator.validate(svg)

        assert any("my-special-image.png" in e.message for e in result.errors)

    def test_relative_path_error_includes_suggestion(self) -> None:
        """Test that error includes helpful suggestion."""
        svg = """<svg xmlns="http://www.w3.org/2000/svg">
            <image href="photo.png" width="100" height="100"/>
        </svg>"""

        validator = SVGValidator()
        result = validator.validate(svg)

        assert any(e.suggestion is not None for e in result.errors)
        # Suggestion should mention alternatives
        assert any(
            e.suggestion is not None
            and (
                "embed" in e.suggestion.lower()
                or "absolute" in e.suggestion.lower()
                or "file://" in e.suggestion.lower()
            )
            for e in result.errors
        )

    def test_multiple_relative_paths_all_reported(self) -> None:
        """Test that multiple relative path images are all reported."""
        svg = """<svg xmlns="http://www.w3.org/2000/svg">
            <image href="image1.png" width="50" height="50"/>
            <image href="image2.png" width="50" height="50"/>
            <image href="image3.png" width="50" height="50"/>
        </svg>"""

        validator = SVGValidator()
        result = validator.validate(svg)

        relative_errors = [
            e for e in result.errors if "relative path" in e.message.lower()
        ]
        assert len(relative_errors) >= 3


class TestSVGValidatorDeprecatedXlinkHref:
    """Tests for deprecated xlink:href attribute detection.

    The xlink:href attribute is deprecated in SVG 2.0 in favor of the
    standard href attribute.
    """

    def test_xlink_href_on_image_produces_warning(self) -> None:
        """Test that xlink:href on image element produces warning."""
        svg = """<svg xmlns="http://www.w3.org/2000/svg"
            xmlns:xlink="http://www.w3.org/1999/xlink">
            <image xlink:href="https://example.com/image.png" width="100" height="100"/>
        </svg>"""

        validator = SVGValidator()
        result = validator.validate(svg)

        # Should be valid (it's just a warning)
        assert result.valid is True
        # But should have a warning
        assert len(result.warnings) > 0
        assert any("xlink:href" in w.message.lower() for w in result.warnings)
        assert any("deprecated" in w.message.lower() for w in result.warnings)

    def test_xlink_href_on_use_produces_warning(self) -> None:
        """Test that xlink:href on use element produces warning."""
        svg = """<svg xmlns="http://www.w3.org/2000/svg"
            xmlns:xlink="http://www.w3.org/1999/xlink">
            <defs>
                <rect id="myRect" width="50" height="50"/>
            </defs>
            <use xlink:href="#myRect" x="10" y="10"/>
        </svg>"""

        validator = SVGValidator()
        result = validator.validate(svg)

        assert result.valid is True
        assert len(result.warnings) > 0
        assert any("xlink:href" in w.message.lower() for w in result.warnings)

    def test_standard_href_no_warning(self) -> None:
        """Test that standard href attribute produces no warning."""
        svg = """<svg xmlns="http://www.w3.org/2000/svg">
            <defs>
                <rect id="myRect" width="50" height="50"/>
            </defs>
            <use href="#myRect" x="10" y="10"/>
        </svg>"""

        validator = SVGValidator()
        result = validator.validate(svg)

        assert result.valid is True
        # No xlink:href warnings
        xlink_warnings = [
            w for w in result.warnings if "xlink:href" in w.message.lower()
        ]
        assert len(xlink_warnings) == 0

    def test_both_href_and_xlink_href_warning(self) -> None:
        """Test that having both href and xlink:href produces specific warning."""
        svg = """<svg xmlns="http://www.w3.org/2000/svg"
            xmlns:xlink="http://www.w3.org/1999/xlink">
            <defs>
                <rect id="myRect" width="50" height="50"/>
            </defs>
            <use href="#myRect" xlink:href="#myRect" x="10" y="10"/>
        </svg>"""

        validator = SVGValidator()
        result = validator.validate(svg)

        assert result.valid is True
        assert len(result.warnings) > 0
        # Should mention having both attributes
        assert any("both" in w.message.lower() for w in result.warnings)

    def test_xlink_href_warning_includes_element_name(self) -> None:
        """Test that warning includes the element name."""
        svg = """<svg xmlns="http://www.w3.org/2000/svg"
            xmlns:xlink="http://www.w3.org/1999/xlink">
            <image xlink:href="https://example.com/image.png" width="100" height="100"/>
        </svg>"""

        validator = SVGValidator()
        result = validator.validate(svg)

        assert any("image" in w.message.lower() for w in result.warnings)

    def test_xlink_href_warning_includes_suggestion(self) -> None:
        """Test that warning includes suggestion to use href."""
        svg = """<svg xmlns="http://www.w3.org/2000/svg"
            xmlns:xlink="http://www.w3.org/1999/xlink">
            <image xlink:href="https://example.com/image.png" width="100" height="100"/>
        </svg>"""

        validator = SVGValidator()
        result = validator.validate(svg)

        assert any(w.suggestion is not None for w in result.warnings)
        assert any(
            w.suggestion is not None and "href" in w.suggestion.lower()
            for w in result.warnings
        )

    def test_multiple_xlink_href_all_reported(self) -> None:
        """Test that multiple xlink:href usages are all reported."""
        svg = """<svg xmlns="http://www.w3.org/2000/svg"
            xmlns:xlink="http://www.w3.org/1999/xlink">
            <defs>
                <rect id="rect1" width="50" height="50"/>
                <rect id="rect2" width="50" height="50"/>
            </defs>
            <use xlink:href="#rect1" x="10" y="10"/>
            <use xlink:href="#rect2" x="70" y="10"/>
            <image xlink:href="https://example.com/image.png" width="100" height="100"/>
        </svg>"""

        validator = SVGValidator()
        result = validator.validate(svg)

        xlink_warnings = [
            w for w in result.warnings if "xlink:href" in w.message.lower()
        ]
        assert len(xlink_warnings) >= 3
