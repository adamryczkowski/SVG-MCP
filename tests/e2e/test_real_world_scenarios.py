"""End-to-end tests for real-world scenarios.

These tests simulate realistic AI agent workflows and edge cases
encountered in production.
"""

import time
from pathlib import Path

import pytest

from SVG_MCP.server import (
    _impl_svg_diff,
    _impl_svg_render,
    _impl_svg_validate,
)


@pytest.mark.e2e
class TestAiAgentSvgCreation:
    """E030: Test AI agent creating SVG from scratch."""

    def test_ai_agent_svg_creation(self, temp_workspace: Path) -> None:
        """Simulate AI agent creating SVG with iterative refinement."""
        # Step 1: AI generates initial SVG
        initial_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <rect x="10" y="10" width="180" height="180" fill="#f0f0f0" stroke="#333"/>
</svg>"""

        # Step 2: Validate initial attempt
        result1 = _impl_svg_validate(content=initial_svg)
        assert result1["valid"] is True

        # Step 3: AI refines by adding more elements
        refined_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <rect x="10" y="10" width="180" height="180" fill="#f0f0f0" stroke="#333"/>
  <circle cx="100" cy="100" r="50" fill="#4285f4"/>
  <text x="100" y="105" text-anchor="middle" fill="white" font-size="14">Hello</text>
</svg>"""

        # Step 4: Validate refined version
        result2 = _impl_svg_validate(content=refined_svg)
        assert result2["valid"] is True
        assert result2["info"]["element_count"] > result1["info"]["element_count"]

        # Step 5: Render final result
        output_path = temp_workspace / "ai_created.png"
        render_result = _impl_svg_render(
            content=refined_svg,
            output_path=str(output_path),
        )
        assert render_result["success"] is True


@pytest.mark.e2e
class TestAiAgentDebuggingWorkflow:
    """E032: Test AI agent debugging workflow."""

    def test_ai_agent_debugging_workflow(self, temp_workspace: Path) -> None:
        """Simulate AI agent receiving error, interpreting it, and fixing."""
        # Step 1: AI generates SVG with error
        broken_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect width="100" height="100" fill="red"
</svg>"""

        # Step 2: Validate and get error
        result1 = _impl_svg_validate(content=broken_svg)
        assert result1["valid"] is False
        assert len(result1["errors"]) > 0

        # Step 3: AI interprets error and fixes
        fixed_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect width="100" height="100" fill="red"/>
</svg>"""

        # Step 4: Validate fix
        result2 = _impl_svg_validate(content=fixed_svg)
        assert result2["valid"] is True

        # Step 5: Render to confirm fix works
        output_path = temp_workspace / "fixed.png"
        render_result = _impl_svg_render(
            content=fixed_svg,
            output_path=str(output_path),
        )
        assert render_result["success"] is True


@pytest.mark.e2e
class TestComplexSvgWithGradients:
    """E033: Test handling SVG with gradients, filters, masks."""

    def test_complex_svg_with_gradients(
        self, complex_svg: str, temp_workspace: Path
    ) -> None:
        """Test complete workflow with complex SVG features."""
        # Validate
        validate_result = _impl_svg_validate(content=complex_svg)
        assert validate_result["valid"] is True

        # Render
        output_path = temp_workspace / "complex.png"
        render_result = _impl_svg_render(
            content=complex_svg,
            output_path=str(output_path),
            width=400,
        )
        assert render_result["success"] is True
        assert output_path.exists()


@pytest.mark.e2e
class TestSvgWithTextAndFonts:
    """E035: Test handling SVG with text elements."""

    def test_svg_with_text_and_fonts(self, temp_workspace: Path) -> None:
        """Test SVG with various text elements."""
        svg_with_text = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 200">
  <text x="150" y="50" text-anchor="middle" font-size="24" font-weight="bold" fill="#333">
    Title Text
  </text>
  <text x="150" y="100" text-anchor="middle" font-size="16" fill="#666">
    Subtitle with different style
  </text>
  <text x="20" y="150" font-size="12" fill="#999">
    <tspan x="20" dy="0">Line 1 of multiline text</tspan>
    <tspan x="20" dy="1.2em">Line 2 of multiline text</tspan>
    <tspan x="20" dy="1.2em">Line 3 of multiline text</tspan>
  </text>
</svg>"""

        # Validate
        result = _impl_svg_validate(content=svg_with_text)
        assert result["valid"] is True

        # Render
        output_path = temp_workspace / "text.png"
        render_result = _impl_svg_render(
            content=svg_with_text,
            output_path=str(output_path),
        )
        assert render_result["success"] is True


@pytest.mark.e2e
class TestMalformedInputRecovery:
    """E038: Test graceful handling of malformed input."""

    def test_malformed_input_recovery(self, temp_workspace: Path) -> None:
        """Test server handles malformed input without crashing."""
        # Inputs that should definitely be invalid
        definitely_invalid = [
            "",  # Empty string
            "not xml at all",  # Plain text
            "<svg>",  # Incomplete tag
            "<html><body>Not SVG</body></html>",  # Wrong document type
        ]

        for malformed in definitely_invalid:
            # Should not crash, should return error
            result = _impl_svg_validate(content=malformed)
            assert isinstance(result, dict)
            assert result["valid"] is False, f"Expected invalid for: {malformed!r}"

    def test_lenient_validation(self, temp_workspace: Path) -> None:
        """Test that validator handles edge cases gracefully."""
        # Some inputs may be considered valid by a lenient validator
        # The key is that the server doesn't crash
        edge_cases = [
            "<svg></svg>",  # Missing namespace - may be valid
            '<svg xmlns="http://www.w3.org/2000/svg"/>',  # Self-closing - valid
        ]

        for content in edge_cases:
            result = _impl_svg_validate(content=content)
            assert isinstance(result, dict)
            # Just verify it returns a valid response structure
            assert "valid" in result
            assert "errors" in result


@pytest.mark.e2e
class TestUnicodeContentHandling:
    """E039: Test handling SVG with Unicode content."""

    def test_unicode_content_handling(
        self, svg_with_unicode: str, temp_workspace: Path
    ) -> None:
        """Test SVG with Unicode text renders correctly."""
        # Validate
        result = _impl_svg_validate(content=svg_with_unicode)
        assert result["valid"] is True

        # Render
        output_path = temp_workspace / "unicode.png"
        render_result = _impl_svg_render(
            content=svg_with_unicode,
            output_path=str(output_path),
        )
        assert render_result["success"] is True


@pytest.mark.e2e
class TestVeryDeepNesting:
    """E040: Test handling SVG with deeply nested elements."""

    def test_very_deep_nesting(
        self, deeply_nested_svg: str, temp_workspace: Path
    ) -> None:
        """Test SVG with 50 levels of nesting."""
        # Validate
        result = _impl_svg_validate(content=deeply_nested_svg)
        assert result["valid"] is True
        # Should have many elements due to nesting
        assert result["info"]["element_count"] >= 50

        # Render
        output_path = temp_workspace / "nested.png"
        render_result = _impl_svg_render(
            content=deeply_nested_svg,
            output_path=str(output_path),
        )
        assert render_result["success"] is True


@pytest.mark.e2e
class TestManyElements:
    """E041: Test handling SVG with many elements."""

    def test_many_elements(self, large_svg: str, temp_workspace: Path) -> None:
        """Test SVG with 1000+ elements."""
        # Validate
        result = _impl_svg_validate(content=large_svg)
        assert result["valid"] is True
        assert result["info"]["element_count"] >= 1000

        # Render
        output_path = temp_workspace / "many_elements.png"
        render_result = _impl_svg_render(
            content=large_svg,
            output_path=str(output_path),
        )
        assert render_result["success"] is True


@pytest.mark.e2e
class TestDiffSubtleChanges:
    """E042: Test detecting subtle visual changes."""

    def test_diff_subtle_changes(self, temp_workspace: Path) -> None:
        """Test detecting 1px shifts and slight color changes."""
        # Original
        original = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect x="10" y="10" width="80" height="80" fill="#ff0000"/>
</svg>"""

        # Subtle change: 1px shift
        shifted = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect x="11" y="10" width="80" height="80" fill="#ff0000"/>
</svg>"""

        output_path = temp_workspace / "subtle_diff.png"
        result = _impl_svg_diff(
            content1=original,
            content2=shifted,
            output_path=str(output_path),
            threshold=0.01,  # Low threshold to catch subtle changes
        )

        # Should detect the difference
        assert result["identical"] is False
        assert result["diff_pixel_count"] > 0


@pytest.mark.e2e
class TestCoordinateMappingPrecision:
    """E044: Test pixel-to-SVG coordinate mapping accuracy."""

    def test_coordinate_mapping_precision(
        self, simple_svg: str, temp_workspace: Path
    ) -> None:
        """Verify coordinate mapping is accurate."""
        output_path = temp_workspace / "coord_test.png"

        result = _impl_svg_render(
            content=simple_svg,
            output_path=str(output_path),
            width=200,
            height=200,
        )

        assert result["success"] is True
        mapping = result["coordinate_mapping"]

        # Verify mapping structure
        assert "svg_viewbox" in mapping
        assert "pixel_bounds" in mapping
        assert "scale_x" in mapping
        assert "scale_y" in mapping

        # Verify scale factors are correct
        # Original viewBox is 100x100, output is 200x200
        assert mapping["scale_x"] == 2.0
        assert mapping["scale_y"] == 2.0


@pytest.mark.e2e
class TestZoomAndPanWorkflow:
    """E045: Test rendering specific regions with zoom."""

    def test_zoom_and_pan_workflow(self, simple_svg: str, temp_workspace: Path) -> None:
        """Test rendering zoomed region of SVG."""
        output_path = temp_workspace / "zoomed.png"

        # Render only the top-left quarter
        result = _impl_svg_render(
            content=simple_svg,
            output_path=str(output_path),
            zoom_x=0,
            zoom_y=0,
            zoom_width=50,
            zoom_height=50,
            width=200,
        )

        assert result["success"] is True
        # Verify the zoom was applied
        assert result["coordinate_mapping"]["svg_viewbox"]["width"] == 50
        assert result["coordinate_mapping"]["svg_viewbox"]["height"] == 50


@pytest.mark.e2e
@pytest.mark.slow
class TestPerformanceBounds:
    """E050: Test operations complete within time bounds."""

    def test_validation_performance(self, large_svg: str) -> None:
        """Test validation completes within reasonable time."""
        start = time.time()
        result = _impl_svg_validate(content=large_svg)
        elapsed = time.time() - start

        assert result["valid"] is True
        # Validation should complete within 5 seconds even for large SVGs
        assert elapsed < 5.0, f"Validation took {elapsed:.2f}s, expected < 5s"

    def test_render_performance(self, large_svg: str, temp_workspace: Path) -> None:
        """Test rendering completes within reasonable time."""
        output_path = temp_workspace / "perf_test.png"

        start = time.time()
        result = _impl_svg_render(
            content=large_svg,
            output_path=str(output_path),
        )
        elapsed = time.time() - start

        assert result["success"] is True
        # Rendering should complete within 10 seconds
        assert elapsed < 10.0, f"Rendering took {elapsed:.2f}s, expected < 10s"

    def test_diff_performance(self, large_svg: str, temp_workspace: Path) -> None:
        """Test diff completes within reasonable time."""
        # Create a slightly modified version
        modified = large_svg.replace('fill="#', 'fill="#0')

        output_path = temp_workspace / "diff_perf.png"

        start = time.time()
        result = _impl_svg_diff(
            content1=large_svg,
            content2=modified,
            output_path=str(output_path),
        )
        elapsed = time.time() - start

        # Verify diff completed successfully
        assert result["identical"] is False  # Modified SVG should differ
        # Diff should complete within 15 seconds
        assert elapsed < 15.0, f"Diff took {elapsed:.2f}s, expected < 15s"
