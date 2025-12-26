"""Integration tests for MCP tools."""

from pathlib import Path


from SVG_MCP.server import (
    _impl_svg_validate,
    _impl_svg_render,
    _impl_svg_diff,
    _impl_svg_edit,
    _impl_svg_file_resource,
    _impl_svg_preview_resource,
)


class TestSvgValidateTool:
    """Tests for svg_validate tool."""

    def test_validate_valid_svg(self, minimal_svg: str) -> None:
        """Test validating a valid SVG."""
        result = _impl_svg_validate(content=minimal_svg)

        assert isinstance(result, dict)
        assert result["valid"] is True
        assert result["errors"] == []
        assert result["info"] is not None
        assert result["info"]["element_count"] > 0

    def test_validate_invalid_svg(self, malformed_svg: str) -> None:
        """Test validating an invalid SVG."""
        result = _impl_svg_validate(content=malformed_svg)

        assert isinstance(result, dict)
        assert result["valid"] is False
        assert len(result["errors"]) > 0

    def test_validate_empty_svg(self) -> None:
        """Test validating empty content."""
        result = _impl_svg_validate(content="")

        assert isinstance(result, dict)
        assert result["valid"] is False

    def test_validate_returns_element_count(self, complex_svg: str) -> None:
        """Test that validation returns element count."""
        result = _impl_svg_validate(content=complex_svg)

        assert result["valid"] is True
        assert result["info"]["element_count"] > 2


class TestSvgRenderTool:
    """Tests for svg_render tool."""

    def test_render_basic(self, minimal_svg: str, tmp_output_dir: Path) -> None:
        """Test basic rendering."""
        output_path = tmp_output_dir / "render_test.png"

        result = _impl_svg_render(content=minimal_svg, output_path=str(output_path))

        assert isinstance(result, dict)
        assert result["success"] is True
        assert result["output_path"] == str(output_path)
        assert output_path.exists()

    def test_render_with_dimensions(
        self, minimal_svg: str, tmp_output_dir: Path
    ) -> None:
        """Test rendering with specific dimensions."""
        output_path = tmp_output_dir / "render_dims.png"

        result = _impl_svg_render(
            content=minimal_svg,
            output_path=str(output_path),
            width=200,
            height=200,
        )

        assert result["success"] is True
        assert result["dimensions"]["width"] == 200
        assert result["dimensions"]["height"] == 200

    def test_render_with_scale(self, minimal_svg: str, tmp_output_dir: Path) -> None:
        """Test rendering with scale factor."""
        output_path = tmp_output_dir / "render_scale.png"

        result = _impl_svg_render(
            content=minimal_svg,
            output_path=str(output_path),
            scale=2.0,
        )

        assert result["success"] is True
        # Original viewBox is 100x100, so 2x scale should be 200x200
        assert result["dimensions"]["width"] == 200
        assert result["dimensions"]["height"] == 200

    def test_render_with_zoom(self, minimal_svg: str, tmp_output_dir: Path) -> None:
        """Test rendering with zoom rectangle."""
        output_path = tmp_output_dir / "render_zoom.png"

        result = _impl_svg_render(
            content=minimal_svg,
            output_path=str(output_path),
            zoom_x=0,
            zoom_y=0,
            zoom_width=50,
            zoom_height=50,
            width=100,
        )

        assert result["success"] is True
        assert result["coordinate_mapping"]["svg_viewbox"]["width"] == 50

    def test_render_invalid_svg(self, malformed_svg: str, tmp_output_dir: Path) -> None:
        """Test rendering invalid SVG."""
        output_path = tmp_output_dir / "render_invalid.png"

        result = _impl_svg_render(content=malformed_svg, output_path=str(output_path))

        assert result["success"] is False
        assert result["error"] is not None


class TestSvgDiffTool:
    """Tests for svg_diff tool."""

    def test_diff_identical(self, rect_original_svg: str, tmp_output_dir: Path) -> None:
        """Test diffing identical SVGs."""
        output_path = tmp_output_dir / "diff_identical.png"

        result = _impl_svg_diff(
            content1=rect_original_svg,
            content2=rect_original_svg,
            output_path=str(output_path),
        )

        assert isinstance(result, dict)
        assert result["identical"] is True
        assert result["diff_pixel_count"] == 0

    def test_diff_different(
        self, rect_original_svg: str, rect_moved_svg: str, tmp_output_dir: Path
    ) -> None:
        """Test diffing different SVGs."""
        output_path = tmp_output_dir / "diff_different.png"

        result = _impl_svg_diff(
            content1=rect_original_svg,
            content2=rect_moved_svg,
            output_path=str(output_path),
        )

        assert result["identical"] is False
        assert result["diff_pixel_count"] > 0
        assert output_path.exists()

    def test_diff_with_mode(
        self, rect_original_svg: str, rect_moved_svg: str, tmp_output_dir: Path
    ) -> None:
        """Test diffing with different modes."""
        output_path = tmp_output_dir / "diff_mode.png"

        result = _impl_svg_diff(
            content1=rect_original_svg,
            content2=rect_moved_svg,
            output_path=str(output_path),
            mode="side_by_side",
        )

        assert result["diff_mode_used"] == "side_by_side"

    def test_diff_with_color_scheme(
        self, rect_original_svg: str, rect_moved_svg: str, tmp_output_dir: Path
    ) -> None:
        """Test diffing with different color schemes."""
        output_path = tmp_output_dir / "diff_scheme.png"

        result = _impl_svg_diff(
            content1=rect_original_svg,
            content2=rect_moved_svg,
            output_path=str(output_path),
            color_scheme="high_contrast",
        )

        assert result["color_scheme_used"] == "high_contrast"


class TestSvgEditTool:
    """Tests for svg_edit tool."""

    def test_edit_replace(self, tmp_output_dir: Path, minimal_svg: str) -> None:
        """Test replacing lines in SVG file."""
        # Create a test file
        test_file = tmp_output_dir / "edit_test.svg"
        test_file.write_text(minimal_svg)

        result = _impl_svg_edit(
            file_path=str(test_file),
            operation="replace",
            content='  <rect width="50" height="50" fill="blue"/>',
            line_start=2,
            line_end=2,
        )

        assert result["success"] is True
        assert result["validation"]["valid"] is True

        # Verify the file was modified
        new_content = test_file.read_text()
        assert "blue" in new_content

    def test_edit_insert(self, tmp_output_dir: Path, minimal_svg: str) -> None:
        """Test inserting lines in SVG file."""
        test_file = tmp_output_dir / "edit_insert.svg"
        test_file.write_text(minimal_svg)

        result = _impl_svg_edit(
            file_path=str(test_file),
            operation="insert",
            content='  <circle cx="50" cy="50" r="25" fill="green"/>',
            line_start=2,
        )

        assert result["success"] is True
        # The file should now have more elements
        new_content = test_file.read_text()
        assert "circle" in new_content

    def test_edit_delete(self, tmp_output_dir: Path, minimal_svg: str) -> None:
        """Test deleting lines in SVG file."""
        test_file = tmp_output_dir / "edit_delete.svg"
        test_file.write_text(minimal_svg)

        # Get original line count
        original_lines = minimal_svg.split("\n")
        original_count = len(original_lines)

        result = _impl_svg_edit(
            file_path=str(test_file),
            operation="delete",
            line_start=2,
            line_end=2,
        )

        assert result["success"] is True

        # Verify line was deleted
        new_content = test_file.read_text()
        new_count = len(new_content.split("\n"))
        assert new_count < original_count

    def test_edit_nonexistent_file(self, tmp_output_dir: Path) -> None:
        """Test editing non-existent file."""
        result = _impl_svg_edit(
            file_path=str(tmp_output_dir / "nonexistent.svg"),
            operation="replace",
            content="test",
            line_start=1,
        )

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_edit_invalid_operation(
        self, tmp_output_dir: Path, minimal_svg: str
    ) -> None:
        """Test invalid operation."""
        test_file = tmp_output_dir / "edit_invalid_op.svg"
        test_file.write_text(minimal_svg)

        result = _impl_svg_edit(
            file_path=str(test_file),
            operation="invalid",
            content="test",
            line_start=1,
        )

        assert result["success"] is False
        assert "invalid operation" in result["error"].lower()

    def test_edit_without_validation(
        self, tmp_output_dir: Path, minimal_svg: str
    ) -> None:
        """Test editing without validation."""
        test_file = tmp_output_dir / "edit_no_validate.svg"
        test_file.write_text(minimal_svg)

        result = _impl_svg_edit(
            file_path=str(test_file),
            operation="replace",
            content='  <rect width="50" height="50" fill="blue"/>',
            line_start=2,
            line_end=2,
            validate_after=False,
        )

        assert result["success"] is True
        assert result["validation"] is None


class TestSvgFileResource:
    """Tests for svg://file/{path} resource."""

    def test_file_resource_exists(self, tmp_output_dir: Path, minimal_svg: str) -> None:
        """Test reading existing file."""
        test_file = tmp_output_dir / "resource_test.svg"
        test_file.write_text(minimal_svg)

        result = _impl_svg_file_resource(str(test_file))

        assert result == minimal_svg

    def test_file_resource_not_exists(self, tmp_output_dir: Path) -> None:
        """Test reading non-existent file."""
        result = _impl_svg_file_resource(str(tmp_output_dir / "nonexistent.svg"))

        assert "Error" in result
        assert "not found" in result.lower()


class TestSvgPreviewResource:
    """Tests for svg://preview/{path} resource."""

    def test_preview_resource_exists(
        self, tmp_output_dir: Path, minimal_svg: str
    ) -> None:
        """Test previewing existing file."""
        test_file = tmp_output_dir / "preview_test.svg"
        test_file.write_text(minimal_svg)

        result = _impl_svg_preview_resource(str(test_file))

        assert result.startswith("data:image/png;base64,")

    def test_preview_resource_not_exists(self, tmp_output_dir: Path) -> None:
        """Test previewing non-existent file."""
        result = _impl_svg_preview_resource(str(tmp_output_dir / "nonexistent.svg"))

        assert "Error" in result
        assert "not found" in result.lower()
