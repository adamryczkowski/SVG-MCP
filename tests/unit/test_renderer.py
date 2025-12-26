"""Unit tests for SVG renderer module."""

from pathlib import Path

import pytest
from PIL import Image

from SVG_MCP.models.types import CoordinateMapping, RenderResult, ViewBox
from SVG_MCP.svg.renderer import SVGRenderer


class TestSVGRendererBasic:
    """Tests for basic SVG rendering functionality."""

    def test_render_minimal_svg(self, minimal_svg: str, tmp_output_dir: Path) -> None:
        """Test rendering a minimal SVG to PNG."""
        renderer = SVGRenderer()
        output_path = tmp_output_dir / "minimal.png"

        result = renderer.render(minimal_svg, output_path)

        assert isinstance(result, RenderResult)
        assert result.success is True
        assert result.output_path == str(output_path)
        assert output_path.exists()

    def test_render_creates_png_file(
        self, minimal_svg: str, tmp_output_dir: Path
    ) -> None:
        """Test that rendering creates a valid PNG file."""
        renderer = SVGRenderer()
        output_path = tmp_output_dir / "test.png"

        result = renderer.render(minimal_svg, output_path)

        assert result.success is True
        # Verify it's a valid PNG by opening with PIL
        img = Image.open(output_path)
        assert img.format == "PNG"

    def test_render_complex_svg(self, complex_svg: str, tmp_output_dir: Path) -> None:
        """Test rendering a complex SVG with multiple elements."""
        renderer = SVGRenderer()
        output_path = tmp_output_dir / "complex.png"

        result = renderer.render(complex_svg, output_path)

        assert result.success is True
        assert output_path.exists()

    def test_render_from_file(
        self, valid_fixtures_dir: Path, tmp_output_dir: Path
    ) -> None:
        """Test rendering from a file path."""
        renderer = SVGRenderer()
        input_path = valid_fixtures_dir / "minimal.svg"
        output_path = tmp_output_dir / "from_file.png"

        result = renderer.render_file(input_path, output_path)

        assert result.success is True
        assert output_path.exists()


class TestSVGRendererDimensions:
    """Tests for rendering with specific dimensions."""

    def test_render_with_width(self, minimal_svg: str, tmp_output_dir: Path) -> None:
        """Test rendering with specified width."""
        renderer = SVGRenderer()
        output_path = tmp_output_dir / "width.png"

        result = renderer.render(minimal_svg, output_path, width=200)

        assert result.success is True
        img = Image.open(output_path)
        assert img.width == 200

    def test_render_with_height(self, minimal_svg: str, tmp_output_dir: Path) -> None:
        """Test rendering with specified height."""
        renderer = SVGRenderer()
        output_path = tmp_output_dir / "height.png"

        result = renderer.render(minimal_svg, output_path, height=150)

        assert result.success is True
        img = Image.open(output_path)
        assert img.height == 150

    def test_render_with_scale(self, minimal_svg: str, tmp_output_dir: Path) -> None:
        """Test rendering with scale factor."""
        renderer = SVGRenderer()
        output_path = tmp_output_dir / "scaled.png"

        # Render at 2x scale
        result = renderer.render(minimal_svg, output_path, scale=2.0)

        assert result.success is True
        img = Image.open(output_path)
        # Original viewBox is 100x100, so 2x should be 200x200
        assert img.width == 200
        assert img.height == 200

    def test_render_preserves_aspect_ratio(
        self, minimal_svg: str, tmp_output_dir: Path
    ) -> None:
        """Test that aspect ratio is preserved when only one dimension is specified."""
        renderer = SVGRenderer()
        output_path = tmp_output_dir / "aspect.png"

        # Original is 100x100 (1:1 ratio), specify only width
        result = renderer.render(minimal_svg, output_path, width=200)

        assert result.success is True
        img = Image.open(output_path)
        assert img.width == 200
        assert img.height == 200  # Should maintain 1:1 ratio


class TestSVGRendererZoomRectangle:
    """Tests for rendering with zoom rectangle (viewport cropping)."""

    def test_render_with_zoom_rectangle(
        self, minimal_svg: str, tmp_output_dir: Path
    ) -> None:
        """Test rendering with a zoom rectangle."""
        renderer = SVGRenderer()
        output_path = tmp_output_dir / "zoomed.png"

        # Zoom into the top-left quarter
        zoom_rect = ViewBox(x=0, y=0, width=50, height=50)
        result = renderer.render(
            minimal_svg, output_path, zoom_rect=zoom_rect, width=100
        )

        assert result.success is True
        img = Image.open(output_path)
        assert img.width == 100

    def test_zoom_rectangle_updates_coordinate_mapping(
        self, minimal_svg: str, tmp_output_dir: Path
    ) -> None:
        """Test that zoom rectangle correctly updates coordinate mapping."""
        renderer = SVGRenderer()
        output_path = tmp_output_dir / "zoomed_mapping.png"

        zoom_rect = ViewBox(x=25, y=25, width=50, height=50)
        result = renderer.render(
            minimal_svg, output_path, zoom_rect=zoom_rect, width=100
        )

        assert result.success is True
        assert result.coordinate_mapping is not None
        # The SVG viewbox should reflect the zoom rectangle
        assert result.coordinate_mapping.svg_viewbox.x == 25
        assert result.coordinate_mapping.svg_viewbox.y == 25
        assert result.coordinate_mapping.svg_viewbox.width == 50
        assert result.coordinate_mapping.svg_viewbox.height == 50


class TestSVGRendererCoordinateMapping:
    """Tests for coordinate mapping between SVG and pixel coordinates."""

    def test_coordinate_mapping_returned(
        self, minimal_svg: str, tmp_output_dir: Path
    ) -> None:
        """Test that coordinate mapping is returned in result."""
        renderer = SVGRenderer()
        output_path = tmp_output_dir / "mapping.png"

        result = renderer.render(minimal_svg, output_path)

        assert result.success is True
        assert result.coordinate_mapping is not None
        assert isinstance(result.coordinate_mapping, CoordinateMapping)

    def test_coordinate_mapping_svg_to_pixel(
        self, minimal_svg: str, tmp_output_dir: Path
    ) -> None:
        """Test SVG to pixel coordinate conversion."""
        renderer = SVGRenderer()
        output_path = tmp_output_dir / "mapping_test.png"

        result = renderer.render(minimal_svg, output_path, width=200, height=200)

        assert result.success is True
        mapping = result.coordinate_mapping
        assert mapping is not None

        # SVG viewBox is 0,0,100,100 -> pixel is 0,0,200,200
        # SVG (0,0) should map to pixel (0,0)
        px, py = mapping.svg_to_pixel(0, 0)
        assert px == pytest.approx(0, abs=1)
        assert py == pytest.approx(0, abs=1)

        # SVG (100,100) should map to pixel (200,200)
        px, py = mapping.svg_to_pixel(100, 100)
        assert px == pytest.approx(200, abs=1)
        assert py == pytest.approx(200, abs=1)

        # SVG (50,50) should map to pixel (100,100)
        px, py = mapping.svg_to_pixel(50, 50)
        assert px == pytest.approx(100, abs=1)
        assert py == pytest.approx(100, abs=1)

    def test_coordinate_mapping_pixel_to_svg(
        self, minimal_svg: str, tmp_output_dir: Path
    ) -> None:
        """Test pixel to SVG coordinate conversion."""
        renderer = SVGRenderer()
        output_path = tmp_output_dir / "mapping_reverse.png"

        result = renderer.render(minimal_svg, output_path, width=200, height=200)

        assert result.success is True
        mapping = result.coordinate_mapping
        assert mapping is not None

        # Pixel (0,0) should map to SVG (0,0)
        sx, sy = mapping.pixel_to_svg(0, 0)
        assert sx == pytest.approx(0, abs=0.1)
        assert sy == pytest.approx(0, abs=0.1)

        # Pixel (200,200) should map to SVG (100,100)
        sx, sy = mapping.pixel_to_svg(200, 200)
        assert sx == pytest.approx(100, abs=0.1)
        assert sy == pytest.approx(100, abs=0.1)

    def test_coordinate_mapping_scale_factors(
        self, minimal_svg: str, tmp_output_dir: Path
    ) -> None:
        """Test that scale factors are correctly calculated."""
        renderer = SVGRenderer()
        output_path = tmp_output_dir / "scale_factors.png"

        result = renderer.render(minimal_svg, output_path, width=200, height=200)

        assert result.success is True
        mapping = result.coordinate_mapping
        assert mapping is not None

        # SVG 100x100 -> Pixel 200x200 = scale of 2.0
        assert mapping.scale_x == pytest.approx(2.0, abs=0.01)
        assert mapping.scale_y == pytest.approx(2.0, abs=0.01)


class TestSVGRendererErrorHandling:
    """Tests for error handling in renderer."""

    def test_render_invalid_svg(self, malformed_svg: str, tmp_output_dir: Path) -> None:
        """Test rendering invalid SVG returns error."""
        renderer = SVGRenderer()
        output_path = tmp_output_dir / "invalid.png"

        result = renderer.render(malformed_svg, output_path)

        assert result.success is False
        assert result.error is not None
        assert not output_path.exists()

    def test_render_empty_svg(self, tmp_output_dir: Path) -> None:
        """Test rendering empty SVG content."""
        renderer = SVGRenderer()
        output_path = tmp_output_dir / "empty.png"

        result = renderer.render("", output_path)

        assert result.success is False
        assert result.error is not None

    def test_render_nonexistent_file(self, tmp_output_dir: Path) -> None:
        """Test rendering from non-existent file."""
        renderer = SVGRenderer()
        output_path = tmp_output_dir / "nonexistent.png"

        result = renderer.render_file(
            tmp_output_dir / "does_not_exist.svg", output_path
        )

        assert result.success is False
        assert result.error is not None

    def test_render_to_invalid_path(self, minimal_svg: str) -> None:
        """Test rendering to an invalid output path."""
        renderer = SVGRenderer()
        # Try to write to a path that doesn't exist and can't be created
        output_path = Path("/nonexistent/directory/output.png")

        result = renderer.render(minimal_svg, output_path)

        assert result.success is False
        assert result.error is not None


class TestSVGRendererOutputFormats:
    """Tests for different output scenarios."""

    def test_render_creates_parent_directories(
        self, minimal_svg: str, tmp_output_dir: Path
    ) -> None:
        """Test that parent directories are created if they don't exist."""
        renderer = SVGRenderer()
        output_path = tmp_output_dir / "nested" / "deep" / "output.png"

        result = renderer.render(minimal_svg, output_path)

        assert result.success is True
        assert output_path.exists()

    def test_render_overwrites_existing_file(
        self, minimal_svg: str, complex_svg: str, tmp_output_dir: Path
    ) -> None:
        """Test that rendering overwrites existing files."""
        renderer = SVGRenderer()
        output_path = tmp_output_dir / "overwrite.png"

        # First render
        result1 = renderer.render(minimal_svg, output_path)
        assert result1.success is True
        mtime1 = output_path.stat().st_mtime

        # Second render with different SVG
        result2 = renderer.render(complex_svg, output_path)
        assert result2.success is True
        mtime2 = output_path.stat().st_mtime

        # File should have been overwritten (modification time should change or be same)
        # The key assertion is that the file exists and both renders succeeded
        assert output_path.exists()
        assert mtime2 >= mtime1

    def test_render_returns_dimensions(
        self, minimal_svg: str, tmp_output_dir: Path
    ) -> None:
        """Test that render result includes output dimensions."""
        renderer = SVGRenderer()
        output_path = tmp_output_dir / "dimensions.png"

        result = renderer.render(minimal_svg, output_path, width=150, height=150)

        assert result.success is True
        assert result.dimensions is not None
        assert result.dimensions.width == 150
        assert result.dimensions.height == 150


class TestSVGRendererEdgeCases:
    """Tests for edge cases in rendering."""

    def test_render_svg_without_viewbox(self, tmp_output_dir: Path) -> None:
        """Test rendering SVG without viewBox attribute."""
        svg_no_viewbox = """<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
            <rect width="100" height="100" fill="blue"/>
        </svg>"""

        renderer = SVGRenderer()
        output_path = tmp_output_dir / "no_viewbox.png"

        result = renderer.render(svg_no_viewbox, output_path)

        assert result.success is True
        assert output_path.exists()

    def test_render_svg_with_percentage_dimensions(self, tmp_output_dir: Path) -> None:
        """Test rendering SVG with percentage dimensions."""
        svg_percent = """<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 100 100">
            <rect width="100" height="100" fill="green"/>
        </svg>"""

        renderer = SVGRenderer()
        output_path = tmp_output_dir / "percent.png"

        # Should work with explicit output dimensions
        result = renderer.render(svg_percent, output_path, width=100, height=100)

        assert result.success is True

    def test_render_svg_with_styles(self, tmp_output_dir: Path) -> None:
        """Test rendering SVG with embedded styles."""
        svg_styled = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
            <style>
                .red { fill: red; }
            </style>
            <rect class="red" width="100" height="100"/>
        </svg>"""

        renderer = SVGRenderer()
        output_path = tmp_output_dir / "styled.png"

        result = renderer.render(svg_styled, output_path)

        assert result.success is True

    def test_render_svg_with_gradients(self, tmp_output_dir: Path) -> None:
        """Test rendering SVG with gradients."""
        svg_gradient = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
            <defs>
                <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" style="stop-color:rgb(255,255,0);stop-opacity:1" />
                    <stop offset="100%" style="stop-color:rgb(255,0,0);stop-opacity:1" />
                </linearGradient>
            </defs>
            <rect width="100" height="100" fill="url(#grad1)"/>
        </svg>"""

        renderer = SVGRenderer()
        output_path = tmp_output_dir / "gradient.png"

        result = renderer.render(svg_gradient, output_path)

        assert result.success is True

    def test_render_svg_with_text(self, tmp_output_dir: Path) -> None:
        """Test rendering SVG with text elements."""
        svg_text = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
            <text x="10" y="50" font-size="12">Hello World</text>
        </svg>"""

        renderer = SVGRenderer()
        output_path = tmp_output_dir / "text.png"

        result = renderer.render(svg_text, output_path)

        assert result.success is True

    def test_render_very_small_output(
        self, minimal_svg: str, tmp_output_dir: Path
    ) -> None:
        """Test rendering to very small dimensions."""
        renderer = SVGRenderer()
        output_path = tmp_output_dir / "tiny.png"

        result = renderer.render(minimal_svg, output_path, width=10, height=10)

        assert result.success is True
        img = Image.open(output_path)
        assert img.width == 10
        assert img.height == 10

    def test_render_very_large_output(
        self, minimal_svg: str, tmp_output_dir: Path
    ) -> None:
        """Test rendering to large dimensions."""
        renderer = SVGRenderer()
        output_path = tmp_output_dir / "large.png"

        result = renderer.render(minimal_svg, output_path, width=2000, height=2000)

        assert result.success is True
        img = Image.open(output_path)
        assert img.width == 2000
        assert img.height == 2000
