"""Unit tests for SVG visual diff module."""

from pathlib import Path

from PIL import Image

from SVG_MCP.models.types import (
    BoundingBox,
    DiffColorScheme,
    DiffResult,
)
from SVG_MCP.svg.differ import SVGDiffer


class TestSVGDifferBasic:
    """Tests for basic visual diff functionality."""

    def test_diff_identical_svgs(
        self, rect_original_svg: str, tmp_output_dir: Path
    ) -> None:
        """Test diffing identical SVGs returns identical=True."""
        differ = SVGDiffer()
        output_path = tmp_output_dir / "diff_identical.png"

        result = differ.diff(rect_original_svg, rect_original_svg, output_path)

        assert isinstance(result, DiffResult)
        assert result.identical is True
        assert result.diff_pixel_count == 0
        assert result.diff_percentage == 0.0

    def test_diff_different_svgs(
        self, rect_original_svg: str, rect_moved_svg: str, tmp_output_dir: Path
    ) -> None:
        """Test diffing different SVGs returns differences."""
        differ = SVGDiffer()
        output_path = tmp_output_dir / "diff_different.png"

        result = differ.diff(rect_original_svg, rect_moved_svg, output_path)

        assert result.identical is False
        assert result.diff_pixel_count > 0
        assert result.diff_percentage > 0.0
        assert output_path.exists()

    def test_diff_creates_output_file(
        self, rect_original_svg: str, rect_moved_svg: str, tmp_output_dir: Path
    ) -> None:
        """Test that diff creates a valid PNG output file."""
        differ = SVGDiffer()
        output_path = tmp_output_dir / "diff_output.png"

        result = differ.diff(rect_original_svg, rect_moved_svg, output_path)

        assert result.diff_image_path == str(output_path)
        assert output_path.exists()
        # Verify it's a valid PNG
        img = Image.open(output_path)
        assert img.format == "PNG"

    def test_diff_from_files(
        self, pairs_fixtures_dir: Path, tmp_output_dir: Path
    ) -> None:
        """Test diffing from file paths."""
        differ = SVGDiffer()
        svg1_path = pairs_fixtures_dir / "rect_original.svg"
        svg2_path = pairs_fixtures_dir / "rect_moved.svg"
        output_path = tmp_output_dir / "diff_from_files.png"

        result = differ.diff_files(svg1_path, svg2_path, output_path)

        assert result.identical is False
        assert output_path.exists()


class TestSVGDifferModes:
    """Tests for different diff visualization modes."""

    def test_diff_mode_overlay(
        self, rect_original_svg: str, rect_moved_svg: str, tmp_output_dir: Path
    ) -> None:
        """Test overlay diff mode."""
        differ = SVGDiffer()
        output_path = tmp_output_dir / "diff_overlay.png"

        result = differ.diff(
            rect_original_svg, rect_moved_svg, output_path, mode="overlay"
        )

        assert result.diff_mode_used == "overlay"
        assert output_path.exists()

    def test_diff_mode_side_by_side(
        self, rect_original_svg: str, rect_moved_svg: str, tmp_output_dir: Path
    ) -> None:
        """Test side-by-side diff mode."""
        differ = SVGDiffer()
        output_path = tmp_output_dir / "diff_side_by_side.png"

        result = differ.diff(
            rect_original_svg, rect_moved_svg, output_path, mode="side_by_side"
        )

        assert result.diff_mode_used == "side_by_side"
        assert output_path.exists()
        # Side-by-side should be wider than single image
        img = Image.open(output_path)
        assert img.width > img.height  # Assuming square SVGs

    def test_diff_mode_difference(
        self, rect_original_svg: str, rect_moved_svg: str, tmp_output_dir: Path
    ) -> None:
        """Test difference diff mode (pixel difference)."""
        differ = SVGDiffer()
        output_path = tmp_output_dir / "diff_difference.png"

        result = differ.diff(
            rect_original_svg, rect_moved_svg, output_path, mode="difference"
        )

        assert result.diff_mode_used == "difference"
        assert output_path.exists()

    def test_diff_mode_highlight(
        self, rect_original_svg: str, rect_moved_svg: str, tmp_output_dir: Path
    ) -> None:
        """Test highlight diff mode."""
        differ = SVGDiffer()
        output_path = tmp_output_dir / "diff_highlight.png"

        result = differ.diff(
            rect_original_svg, rect_moved_svg, output_path, mode="highlight"
        )

        assert result.diff_mode_used == "highlight"
        assert output_path.exists()

    def test_diff_mode_checkerboard(
        self, rect_original_svg: str, rect_moved_svg: str, tmp_output_dir: Path
    ) -> None:
        """Test checkerboard diff mode."""
        differ = SVGDiffer()
        output_path = tmp_output_dir / "diff_checkerboard.png"

        result = differ.diff(
            rect_original_svg, rect_moved_svg, output_path, mode="checkerboard"
        )

        assert result.diff_mode_used == "checkerboard"
        assert output_path.exists()


class TestSVGDifferColorSchemes:
    """Tests for different color schemes."""

    def test_diff_with_default_scheme(
        self, rect_original_svg: str, rect_moved_svg: str, tmp_output_dir: Path
    ) -> None:
        """Test diff with default color scheme."""
        differ = SVGDiffer()
        output_path = tmp_output_dir / "diff_default_scheme.png"

        result = differ.diff(
            rect_original_svg, rect_moved_svg, output_path, color_scheme="default"
        )

        assert result.color_scheme_used == "default"

    def test_diff_with_high_contrast_scheme(
        self, rect_original_svg: str, rect_moved_svg: str, tmp_output_dir: Path
    ) -> None:
        """Test diff with high contrast color scheme."""
        differ = SVGDiffer()
        output_path = tmp_output_dir / "diff_high_contrast.png"

        result = differ.diff(
            rect_original_svg, rect_moved_svg, output_path, color_scheme="high_contrast"
        )

        assert result.color_scheme_used == "high_contrast"

    def test_diff_with_colorblind_safe_scheme(
        self, rect_original_svg: str, rect_moved_svg: str, tmp_output_dir: Path
    ) -> None:
        """Test diff with colorblind-safe color scheme."""
        differ = SVGDiffer()
        output_path = tmp_output_dir / "diff_colorblind.png"

        result = differ.diff(
            rect_original_svg,
            rect_moved_svg,
            output_path,
            color_scheme="colorblind_safe",
        )

        assert result.color_scheme_used == "colorblind_safe"

    def test_diff_with_subtle_scheme(
        self, rect_original_svg: str, rect_moved_svg: str, tmp_output_dir: Path
    ) -> None:
        """Test diff with subtle color scheme."""
        differ = SVGDiffer()
        output_path = tmp_output_dir / "diff_subtle.png"

        result = differ.diff(
            rect_original_svg, rect_moved_svg, output_path, color_scheme="subtle"
        )

        assert result.color_scheme_used == "subtle"

    def test_diff_with_neon_scheme(
        self, rect_original_svg: str, rect_moved_svg: str, tmp_output_dir: Path
    ) -> None:
        """Test diff with neon color scheme."""
        differ = SVGDiffer()
        output_path = tmp_output_dir / "diff_neon.png"

        result = differ.diff(
            rect_original_svg, rect_moved_svg, output_path, color_scheme="neon"
        )

        assert result.color_scheme_used == "neon"

    def test_diff_with_custom_scheme(
        self, rect_original_svg: str, rect_moved_svg: str, tmp_output_dir: Path
    ) -> None:
        """Test diff with custom color scheme."""
        custom_scheme = DiffColorScheme(
            name="custom",
            description="Custom test scheme",
            image1_tint=(255, 0, 0),
            image2_tint=(0, 0, 255),
        )
        differ = SVGDiffer()
        output_path = tmp_output_dir / "diff_custom.png"

        result = differ.diff(
            rect_original_svg,
            rect_moved_svg,
            output_path,
            color_scheme=custom_scheme,
        )

        assert result.color_scheme_used == "custom"


class TestSVGDifferBoundingBoxes:
    """Tests for bounding box detection."""

    def test_diff_returns_bounding_boxes(
        self, rect_original_svg: str, rect_moved_svg: str, tmp_output_dir: Path
    ) -> None:
        """Test that diff returns bounding boxes for changed regions."""
        differ = SVGDiffer()
        output_path = tmp_output_dir / "diff_bbox.png"

        result = differ.diff(rect_original_svg, rect_moved_svg, output_path)

        assert len(result.bounding_boxes) > 0
        for bbox in result.bounding_boxes:
            assert isinstance(bbox, BoundingBox)
            assert bbox.width > 0
            assert bbox.height > 0

    def test_bounding_box_coordinates_valid(
        self, rect_original_svg: str, rect_moved_svg: str, tmp_output_dir: Path
    ) -> None:
        """Test that bounding box coordinates are within image bounds."""
        differ = SVGDiffer()
        output_path = tmp_output_dir / "diff_bbox_coords.png"

        result = differ.diff(
            rect_original_svg, rect_moved_svg, output_path, width=200, height=200
        )

        for bbox in result.bounding_boxes:
            assert bbox.x >= 0
            assert bbox.y >= 0
            assert bbox.x + bbox.width <= 200
            assert bbox.y + bbox.height <= 200

    def test_identical_svgs_no_bounding_boxes(
        self, rect_original_svg: str, tmp_output_dir: Path
    ) -> None:
        """Test that identical SVGs produce no bounding boxes."""
        differ = SVGDiffer()
        output_path = tmp_output_dir / "diff_no_bbox.png"

        result = differ.diff(rect_original_svg, rect_original_svg, output_path)

        assert len(result.bounding_boxes) == 0

    def test_color_change_detected(
        self, rect_original_svg: str, rect_color_changed_svg: str, tmp_output_dir: Path
    ) -> None:
        """Test that color changes are detected."""
        differ = SVGDiffer()
        output_path = tmp_output_dir / "diff_color_change.png"

        result = differ.diff(rect_original_svg, rect_color_changed_svg, output_path)

        assert result.identical is False
        assert result.diff_pixel_count > 0


class TestSVGDifferDimensions:
    """Tests for diff with specific dimensions."""

    def test_diff_with_width(
        self, rect_original_svg: str, rect_moved_svg: str, tmp_output_dir: Path
    ) -> None:
        """Test diff with specified width."""
        differ = SVGDiffer()
        output_path = tmp_output_dir / "diff_width.png"

        result = differ.diff(rect_original_svg, rect_moved_svg, output_path, width=300)

        assert result.identical is False
        img = Image.open(output_path)
        # Width depends on mode, but should be at least 300
        assert img.width >= 300

    def test_diff_with_height(
        self, rect_original_svg: str, rect_moved_svg: str, tmp_output_dir: Path
    ) -> None:
        """Test diff with specified height."""
        differ = SVGDiffer()
        output_path = tmp_output_dir / "diff_height.png"

        result = differ.diff(rect_original_svg, rect_moved_svg, output_path, height=250)

        assert result.identical is False


class TestSVGDifferErrorHandling:
    """Tests for error handling in differ."""

    def test_diff_invalid_svg1(
        self, malformed_svg: str, rect_original_svg: str, tmp_output_dir: Path
    ) -> None:
        """Test diff with invalid first SVG."""
        differ = SVGDiffer()
        output_path = tmp_output_dir / "diff_invalid1.png"

        result = differ.diff(malformed_svg, rect_original_svg, output_path)

        # Should handle gracefully - either fail or produce a result
        # The exact behavior depends on implementation
        assert isinstance(result, DiffResult)

    def test_diff_invalid_svg2(
        self, rect_original_svg: str, malformed_svg: str, tmp_output_dir: Path
    ) -> None:
        """Test diff with invalid second SVG."""
        differ = SVGDiffer()
        output_path = tmp_output_dir / "diff_invalid2.png"

        result = differ.diff(rect_original_svg, malformed_svg, output_path)

        assert isinstance(result, DiffResult)

    def test_diff_empty_svg1(
        self, rect_original_svg: str, tmp_output_dir: Path
    ) -> None:
        """Test diff with empty first SVG."""
        differ = SVGDiffer()
        output_path = tmp_output_dir / "diff_empty1.png"

        result = differ.diff("", rect_original_svg, output_path)

        assert result.identical is False or result.diff_pixel_count == 0

    def test_diff_nonexistent_file(self, tmp_output_dir: Path) -> None:
        """Test diff with non-existent file."""
        differ = SVGDiffer()
        output_path = tmp_output_dir / "diff_nonexistent.png"

        result = differ.diff_files(
            tmp_output_dir / "nonexistent1.svg",
            tmp_output_dir / "nonexistent2.svg",
            output_path,
        )

        # Should return a result indicating failure
        assert isinstance(result, DiffResult)


class TestSVGDifferThreshold:
    """Tests for diff threshold settings."""

    def test_diff_with_threshold(
        self, rect_original_svg: str, rect_color_changed_svg: str, tmp_output_dir: Path
    ) -> None:
        """Test diff with pixel difference threshold."""
        differ = SVGDiffer()
        output_path = tmp_output_dir / "diff_threshold.png"

        # With a high threshold, small color differences might be ignored
        result = differ.diff(
            rect_original_svg,
            rect_color_changed_svg,
            output_path,
            threshold=0.5,  # 50% threshold
        )

        assert isinstance(result, DiffResult)

    def test_diff_threshold_affects_pixel_count(
        self, rect_original_svg: str, rect_color_changed_svg: str, tmp_output_dir: Path
    ) -> None:
        """Test that threshold affects diff pixel count."""
        differ = SVGDiffer()

        # Low threshold - more sensitive
        output_low = tmp_output_dir / "diff_threshold_low.png"
        result_low = differ.diff(
            rect_original_svg,
            rect_color_changed_svg,
            output_low,
            threshold=0.01,
        )

        # High threshold - less sensitive
        output_high = tmp_output_dir / "diff_threshold_high.png"
        result_high = differ.diff(
            rect_original_svg,
            rect_color_changed_svg,
            output_high,
            threshold=0.9,
        )

        # Higher threshold should result in fewer or equal diff pixels
        assert result_high.diff_pixel_count <= result_low.diff_pixel_count


class TestSVGDifferEdgeCases:
    """Tests for edge cases in differ."""

    def test_diff_circle_resize(
        self, circle_original_svg: str, circle_resized_svg: str, tmp_output_dir: Path
    ) -> None:
        """Test diffing circles with size change."""
        differ = SVGDiffer()
        output_path = tmp_output_dir / "diff_circle_resize.png"

        result = differ.diff(circle_original_svg, circle_resized_svg, output_path)

        assert result.identical is False
        assert result.diff_pixel_count > 0

    def test_diff_creates_parent_directories(
        self, rect_original_svg: str, rect_moved_svg: str, tmp_output_dir: Path
    ) -> None:
        """Test that diff creates parent directories if needed."""
        differ = SVGDiffer()
        output_path = tmp_output_dir / "nested" / "deep" / "diff.png"

        differ.diff(rect_original_svg, rect_moved_svg, output_path)

        assert output_path.exists()

    def test_diff_percentage_calculation(
        self, rect_original_svg: str, rect_moved_svg: str, tmp_output_dir: Path
    ) -> None:
        """Test that diff percentage is correctly calculated."""
        differ = SVGDiffer()
        output_path = tmp_output_dir / "diff_percentage.png"

        result = differ.diff(
            rect_original_svg, rect_moved_svg, output_path, width=100, height=100
        )

        # Percentage should be between 0 and 100
        assert 0 <= result.diff_percentage <= 100
        # Percentage should match pixel count / total pixels
        total_pixels = 100 * 100
        expected_percentage = (result.diff_pixel_count / total_pixels) * 100
        assert abs(result.diff_percentage - expected_percentage) < 0.1

    def test_diff_with_transparency(self, tmp_output_dir: Path) -> None:
        """Test diffing SVGs with transparency."""
        svg1 = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
            <rect width="50" height="50" fill="rgba(255,0,0,0.5)"/>
        </svg>"""
        svg2 = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
            <rect width="50" height="50" fill="rgba(0,0,255,0.5)"/>
        </svg>"""

        differ = SVGDiffer()
        output_path = tmp_output_dir / "diff_transparency.png"

        result = differ.diff(svg1, svg2, output_path)

        assert result.identical is False
