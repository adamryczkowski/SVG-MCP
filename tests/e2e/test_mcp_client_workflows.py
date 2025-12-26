"""End-to-end tests for MCP client workflows.

These tests simulate real MCP client interactions with the server,
validating complete workflows from connection to result verification.
"""

from pathlib import Path

import pytest

from SVG_MCP.server import (
    _impl_svg_diff,
    _impl_svg_edit,
    _impl_svg_file_resource,
    _impl_svg_preview_resource,
    _impl_svg_render,
    _impl_svg_validate,
)


@pytest.mark.e2e
class TestFullValidationWorkflow:
    """E001: Test complete validation workflow."""

    def test_full_validation_workflow_valid_svg(self, simple_svg: str) -> None:
        """Test validating a valid SVG through the complete workflow."""
        # Step 1: Send SVG for validation
        result = _impl_svg_validate(content=simple_svg)

        # Step 2: Verify structured response
        assert isinstance(result, dict)
        assert result["valid"] is True
        assert result["errors"] == []
        assert result["info"] is not None

        # Step 3: Verify metadata is present
        assert result["info"]["element_count"] > 0
        assert result["info"]["viewbox"] is not None

    def test_full_validation_workflow_invalid_svg(self, invalid_svg: str) -> None:
        """Test validating an invalid SVG with error details."""
        # Step 1: Send invalid SVG for validation
        result = _impl_svg_validate(content=invalid_svg)

        # Step 2: Verify error response
        assert result["valid"] is False
        assert len(result["errors"]) > 0

        # Step 3: Verify error has actionable information
        error = result["errors"][0]
        assert "message" in error
        # Line number should be present for syntax errors
        assert error.get("line") is not None or error.get("message") is not None


@pytest.mark.e2e
class TestFullRenderWorkflow:
    """E002: Test complete render workflow."""

    def test_full_render_workflow(self, simple_svg: str, temp_workspace: Path) -> None:
        """Test rendering SVG to PNG through complete workflow."""
        output_path = temp_workspace / "rendered.png"

        # Step 1: Send render request
        result = _impl_svg_render(
            content=simple_svg,
            output_path=str(output_path),
            width=200,
            height=200,
        )

        # Step 2: Verify success response
        assert result["success"] is True
        assert result["output_path"] == str(output_path)

        # Step 3: Verify output file exists
        assert output_path.exists()

        # Step 4: Verify dimensions
        assert result["dimensions"]["width"] == 200
        assert result["dimensions"]["height"] == 200

        # Step 5: Verify coordinate mapping
        assert result["coordinate_mapping"] is not None
        assert "svg_viewbox" in result["coordinate_mapping"]


@pytest.mark.e2e
class TestFullDiffWorkflow:
    """E003: Test complete diff workflow."""

    def test_full_diff_workflow(
        self,
        svg_pair_original: str,
        svg_pair_modified: str,
        temp_workspace: Path,
    ) -> None:
        """Test comparing two SVGs through complete workflow."""
        output_path = temp_workspace / "diff.png"

        # Step 1: Send diff request
        result = _impl_svg_diff(
            content1=svg_pair_original,
            content2=svg_pair_modified,
            output_path=str(output_path),
            mode="overlay",
            color_scheme="default",
        )

        # Step 2: Verify response structure
        assert isinstance(result, dict)
        assert "identical" in result
        assert "diff_pixel_count" in result
        assert "diff_percentage" in result

        # Step 3: Verify differences detected
        assert result["identical"] is False
        assert result["diff_pixel_count"] > 0

        # Step 4: Verify diff image created
        assert output_path.exists()

        # Step 5: Verify mode and scheme used
        assert result["diff_mode_used"] == "overlay"
        assert result["color_scheme_used"] == "default"


@pytest.mark.e2e
class TestEditValidateRenderCycle:
    """E004: Test complete edit → validate → render cycle."""

    def test_edit_validate_render_cycle(
        self, temp_workspace: Path, simple_svg: str
    ) -> None:
        """Test the complete AI agent workflow: edit, validate, render."""
        # Step 1: Create initial SVG file
        svg_file = temp_workspace / "editable.svg"
        svg_file.write_text(simple_svg)

        # Step 2: Edit the file (change color)
        edit_result = _impl_svg_edit(
            file_path=str(svg_file),
            operation="replace",
            content='  <rect width="100" height="100" fill="blue"/>',
            line_start=2,
            line_end=2,
            validate_after=True,
        )

        assert edit_result["success"] is True
        assert edit_result["validation"]["valid"] is True

        # Step 3: Validate the edited file
        edited_content = svg_file.read_text()
        validate_result = _impl_svg_validate(content=edited_content)
        assert validate_result["valid"] is True

        # Step 4: Render the edited file
        output_path = temp_workspace / "edited_render.png"
        render_result = _impl_svg_render(
            content=edited_content,
            output_path=str(output_path),
        )

        assert render_result["success"] is True
        assert output_path.exists()


@pytest.mark.e2e
class TestIterativeEditingSession:
    """E005: Test multiple sequential edits with validation."""

    def test_iterative_editing_session(
        self, temp_workspace: Path, simple_svg: str
    ) -> None:
        """Test multiple edits in sequence, validating after each."""
        svg_file = temp_workspace / "iterative.svg"
        svg_file.write_text(simple_svg)

        # Edit 1: Add a circle
        result1 = _impl_svg_edit(
            file_path=str(svg_file),
            operation="insert",
            content='  <circle cx="50" cy="50" r="25" fill="green"/>',
            line_start=3,
            validate_after=True,
        )
        assert result1["success"] is True
        assert result1["validation"]["valid"] is True

        # Edit 2: Add a text element
        result2 = _impl_svg_edit(
            file_path=str(svg_file),
            operation="insert",
            content='  <text x="50" y="90" text-anchor="middle">Hello</text>',
            line_start=4,
            validate_after=True,
        )
        assert result2["success"] is True
        assert result2["validation"]["valid"] is True

        # Edit 3: Modify the rect
        result3 = _impl_svg_edit(
            file_path=str(svg_file),
            operation="replace",
            content='  <rect width="80" height="80" x="10" y="10" fill="purple"/>',
            line_start=2,
            line_end=2,
            validate_after=True,
        )
        assert result3["success"] is True
        assert result3["validation"]["valid"] is True

        # Verify final state
        final_content = svg_file.read_text()
        assert "circle" in final_content
        assert "text" in final_content
        assert "purple" in final_content


@pytest.mark.e2e
class TestLargeSvgHandling:
    """E007: Test handling of large SVG files."""

    def test_large_svg_handling(self, large_svg: str, temp_workspace: Path) -> None:
        """Test complete workflow with a large SVG (1000+ elements)."""
        # Step 1: Validate large SVG
        validate_result = _impl_svg_validate(content=large_svg)
        assert validate_result["valid"] is True
        assert validate_result["info"]["element_count"] >= 1000

        # Step 2: Render large SVG
        output_path = temp_workspace / "large_render.png"
        render_result = _impl_svg_render(
            content=large_svg,
            output_path=str(output_path),
            width=800,
        )
        assert render_result["success"] is True
        assert output_path.exists()


@pytest.mark.e2e
class TestErrorRecoveryWorkflow:
    """E008: Test graceful error recovery."""

    def test_error_recovery_workflow(
        self, invalid_svg: str, simple_svg: str, temp_workspace: Path
    ) -> None:
        """Test that client can recover from validation errors."""
        # Step 1: Try to validate invalid SVG
        result1 = _impl_svg_validate(content=invalid_svg)
        assert result1["valid"] is False

        # Step 2: Try to render invalid SVG (should fail gracefully)
        output_path = temp_workspace / "invalid_render.png"
        render_result = _impl_svg_render(
            content=invalid_svg,
            output_path=str(output_path),
        )
        assert render_result["success"] is False
        assert render_result["error"] is not None

        # Step 3: Recover by using valid SVG
        result2 = _impl_svg_validate(content=simple_svg)
        assert result2["valid"] is True

        # Step 4: Successfully render valid SVG
        output_path2 = temp_workspace / "valid_render.png"
        render_result2 = _impl_svg_render(
            content=simple_svg,
            output_path=str(output_path2),
        )
        assert render_result2["success"] is True


@pytest.mark.e2e
class TestResourceAccessWorkflow:
    """E009: Test svg://file/{path} resource access."""

    def test_resource_access_workflow(
        self, temp_workspace: Path, simple_svg: str
    ) -> None:
        """Test accessing SVG files via resource URI."""
        # Step 1: Create a test file
        svg_file = temp_workspace / "resource_test.svg"
        svg_file.write_text(simple_svg)

        # Step 2: Access via resource
        content = _impl_svg_file_resource(str(svg_file))

        # Step 3: Verify content matches
        assert content == simple_svg

    def test_resource_access_nonexistent(self, temp_workspace: Path) -> None:
        """Test error handling for nonexistent resource."""
        result = _impl_svg_file_resource(str(temp_workspace / "nonexistent.svg"))
        assert "Error" in result
        assert "not found" in result.lower()


@pytest.mark.e2e
class TestPreviewResourceWorkflow:
    """E010: Test svg://preview/{path} resource access."""

    def test_preview_resource_workflow(
        self, temp_workspace: Path, simple_svg: str
    ) -> None:
        """Test getting rendered preview via resource URI."""
        # Step 1: Create a test file
        svg_file = temp_workspace / "preview_test.svg"
        svg_file.write_text(simple_svg)

        # Step 2: Get preview via resource
        result = _impl_svg_preview_resource(str(svg_file))

        # Step 3: Verify base64 PNG data URL
        assert result.startswith("data:image/png;base64,")
        # Verify it's valid base64 (should be decodable)
        import base64

        base64_data = result.replace("data:image/png;base64,", "")
        decoded = base64.b64decode(base64_data)
        # PNG files start with specific magic bytes
        assert decoded[:8] == b"\x89PNG\r\n\x1a\n"


@pytest.mark.e2e
class TestSessionPersistence:
    """E011: Test state persistence across multiple tool calls."""

    def test_session_persistence(self, temp_workspace: Path, simple_svg: str) -> None:
        """Test that file changes persist across tool calls."""
        svg_file = temp_workspace / "persistent.svg"
        svg_file.write_text(simple_svg)

        # Call 1: Edit file
        _impl_svg_edit(
            file_path=str(svg_file),
            operation="replace",
            content='  <rect width="50" height="50" fill="green"/>',
            line_start=2,
            line_end=2,
        )

        # Call 2: Read file via resource (should see changes)
        content = _impl_svg_file_resource(str(svg_file))
        assert "green" in content
        assert 'width="50"' in content

        # Call 3: Validate (should validate the modified content)
        result = _impl_svg_validate(content=content)
        assert result["valid"] is True


@pytest.mark.e2e
class TestDiffModes:
    """Test different diff visualization modes."""

    @pytest.mark.parametrize(
        "mode",
        ["overlay", "side_by_side", "difference", "highlight", "checkerboard"],
    )
    def test_diff_modes(
        self,
        mode: str,
        svg_pair_original: str,
        svg_pair_modified: str,
        temp_workspace: Path,
    ) -> None:
        """Test each diff mode produces valid output."""
        output_path = temp_workspace / f"diff_{mode}.png"

        result = _impl_svg_diff(
            content1=svg_pair_original,
            content2=svg_pair_modified,
            output_path=str(output_path),
            mode=mode,
        )

        assert result["diff_mode_used"] == mode
        assert output_path.exists()


@pytest.mark.e2e
class TestColorSchemes:
    """Test different color schemes for diff visualization."""

    @pytest.mark.parametrize(
        "scheme",
        ["default", "high_contrast", "colorblind_safe", "subtle", "neon"],
    )
    def test_color_schemes(
        self,
        scheme: str,
        svg_pair_original: str,
        svg_pair_modified: str,
        temp_workspace: Path,
    ) -> None:
        """Test each color scheme produces valid output."""
        output_path = temp_workspace / f"diff_{scheme}.png"

        result = _impl_svg_diff(
            content1=svg_pair_original,
            content2=svg_pair_modified,
            output_path=str(output_path),
            color_scheme=scheme,
        )

        assert result["color_scheme_used"] == scheme
        assert output_path.exists()
