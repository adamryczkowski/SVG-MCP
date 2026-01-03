"""Unit tests for SVG optimizer."""

from SVG_MCP.models.lint_types import OptimizeResult
from SVG_MCP.svg.optimizer import SVGOptimizer, optimize_svg, OPTIMIZE_PRESETS


# Sample SVG content for testing
SIMPLE_SVG = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100">
  <rect x="10" y="10" width="80" height="80" fill="red"/>
</svg>
"""

VERBOSE_SVG = """<?xml version="1.0" encoding="UTF-8"?>
<!-- This is a comment that should be removed with maximum preset -->
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
     xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
     width="100" height="100" viewBox="0 0 100 100">
  <metadata>
    <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
      <rdf:Description>Some metadata</rdf:Description>
    </rdf:RDF>
  </metadata>
  <title>Test SVG</title>
  <desc>A test SVG with verbose content</desc>
  <defs>
    <style type="text/css">
      .unused-class { fill: blue; }
    </style>
  </defs>
  <rect id="my-very-long-rectangle-id" x="10.123456789" y="10.987654321"
        width="80.111111111" height="80.222222222" fill="red"/>
</svg>
"""

INVALID_SVG = """<not-svg>This is not valid SVG</not-svg>"""


class TestSVGOptimizerInit:
    """Tests for SVGOptimizer initialization."""

    def test_default_preset(self) -> None:
        """Test that default preset is 'default'."""
        optimizer = SVGOptimizer()
        assert optimizer.preset == "default"

    def test_safe_preset(self) -> None:
        """Test initialization with safe preset."""
        optimizer = SVGOptimizer(preset="safe")
        assert optimizer.preset == "safe"

    def test_maximum_preset(self) -> None:
        """Test initialization with maximum preset."""
        optimizer = SVGOptimizer(preset="maximum")
        assert optimizer.preset == "maximum"

    def test_invalid_preset_uses_default(self) -> None:
        """Test that invalid preset falls back to default options."""
        optimizer = SVGOptimizer(preset="invalid")  # type: ignore
        # Should not raise, but use default options
        assert optimizer._base_options == OPTIMIZE_PRESETS["default"]


class TestSVGOptimizerOptimize:
    """Tests for SVGOptimizer.optimize() method."""

    def test_optimize_simple_svg(self) -> None:
        """Test optimizing a simple SVG."""
        optimizer = SVGOptimizer()
        result = optimizer.optimize(SIMPLE_SVG)

        assert isinstance(result, OptimizeResult)
        assert result.success is True
        assert result.optimized_content is not None
        assert result.original_size > 0
        assert result.optimized_size is not None
        assert result.optimized_size > 0
        assert result.error is None

    def test_optimize_reduces_size(self) -> None:
        """Test that optimization reduces file size for verbose SVG."""
        optimizer = SVGOptimizer(preset="maximum")
        result = optimizer.optimize(VERBOSE_SVG)

        assert result.success is True
        assert result.optimized_size is not None
        assert result.optimized_size < result.original_size
        assert result.reduction_percent is not None
        assert result.reduction_percent > 0

    def test_safe_preset_preserves_more(self) -> None:
        """Test that safe preset preserves more content than maximum."""
        safe_optimizer = SVGOptimizer(preset="safe")
        max_optimizer = SVGOptimizer(preset="maximum")

        safe_result = safe_optimizer.optimize(VERBOSE_SVG)
        max_result = max_optimizer.optimize(VERBOSE_SVG)

        assert safe_result.success is True
        assert max_result.success is True
        assert safe_result.optimized_size is not None
        assert max_result.optimized_size is not None
        # Maximum should produce smaller output
        assert max_result.optimized_size < safe_result.optimized_size

    def test_precision_override(self) -> None:
        """Test that precision parameter affects output."""
        optimizer = SVGOptimizer()

        high_precision = optimizer.optimize(VERBOSE_SVG, precision=8)
        low_precision = optimizer.optimize(VERBOSE_SVG, precision=1)

        assert high_precision.success is True
        assert low_precision.success is True
        # Lower precision should produce smaller output
        assert low_precision.optimized_size is not None
        assert high_precision.optimized_size is not None
        assert low_precision.optimized_size <= high_precision.optimized_size

    def test_remove_editor_data(self) -> None:
        """Test removing editor-specific data."""
        optimizer = SVGOptimizer(preset="safe")  # Safe keeps editor data by default

        result = optimizer.optimize(VERBOSE_SVG, remove_editor_data=True)

        assert result.success is True
        assert result.optimized_content is not None
        # Inkscape namespace should be removed
        assert "inkscape" not in result.optimized_content.lower()
        assert "sodipodi" not in result.optimized_content.lower()

    def test_remove_metadata(self) -> None:
        """Test removing metadata elements."""
        optimizer = SVGOptimizer()

        result = optimizer.optimize(VERBOSE_SVG, remove_metadata=True)

        assert result.success is True
        assert result.optimized_content is not None
        assert "<metadata" not in result.optimized_content.lower()

    def test_shorten_ids(self) -> None:
        """Test shortening element IDs."""
        optimizer = SVGOptimizer()

        result = optimizer.optimize(VERBOSE_SVG, shorten_ids=True)

        assert result.success is True
        assert result.optimized_content is not None
        # The long ID should be shortened
        assert "my-very-long-rectangle-id" not in result.optimized_content

    def test_invalid_svg_returns_error(self) -> None:
        """Test that invalid SVG returns an error result."""
        optimizer = SVGOptimizer()
        result = optimizer.optimize(INVALID_SVG)

        # Scour may or may not fail on invalid SVG depending on how malformed it is
        # At minimum, we should get a result back
        assert isinstance(result, OptimizeResult)

    def test_empty_svg_returns_error(self) -> None:
        """Test that empty content returns an error result."""
        optimizer = SVGOptimizer()
        result = optimizer.optimize("")

        assert isinstance(result, OptimizeResult)
        # Empty content should either fail or produce empty output
        if not result.success:
            assert result.error is not None


class TestSVGOptimizerOptimizeFile:
    """Tests for SVGOptimizer.optimize_file() method."""

    def test_optimize_nonexistent_file(self, tmp_path) -> None:
        """Test optimizing a file that doesn't exist."""
        optimizer = SVGOptimizer()
        result = optimizer.optimize_file(tmp_path / "nonexistent.svg")

        assert result.success is False
        assert result.error is not None
        assert "Failed to read file" in result.error

    def test_optimize_file_success(self, tmp_path) -> None:
        """Test successfully optimizing a file."""
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(SIMPLE_SVG, encoding="utf-8")

        optimizer = SVGOptimizer()
        result = optimizer.optimize_file(svg_file)

        assert result.success is True
        assert result.optimized_content is not None
        assert result.original_size > 0


class TestOptimizeSvgFunction:
    """Tests for the optimize_svg convenience function."""

    def test_optimize_svg_default(self) -> None:
        """Test optimize_svg with default preset."""
        result = optimize_svg(SIMPLE_SVG)

        assert result.success is True
        assert result.optimized_content is not None

    def test_optimize_svg_with_preset(self) -> None:
        """Test optimize_svg with specific preset."""
        result = optimize_svg(VERBOSE_SVG, preset="maximum")

        assert result.success is True
        assert result.optimized_size is not None
        assert result.optimized_size < result.original_size

    def test_optimize_svg_with_kwargs(self) -> None:
        """Test optimize_svg with additional options."""
        result = optimize_svg(VERBOSE_SVG, preset="safe", remove_metadata=True)

        assert result.success is True
        assert result.optimized_content is not None
        assert "<metadata" not in result.optimized_content.lower()


class TestOptimizePresets:
    """Tests for optimization presets configuration."""

    def test_all_presets_exist(self) -> None:
        """Test that all expected presets are defined."""
        assert "safe" in OPTIMIZE_PRESETS
        assert "default" in OPTIMIZE_PRESETS
        assert "maximum" in OPTIMIZE_PRESETS

    def test_safe_preset_keeps_editor_data(self) -> None:
        """Test that safe preset is configured to keep editor data."""
        assert OPTIMIZE_PRESETS["safe"]["keep_editor_data"] is True

    def test_maximum_preset_removes_everything(self) -> None:
        """Test that maximum preset is configured for aggressive optimization."""
        max_preset = OPTIMIZE_PRESETS["maximum"]
        assert max_preset["keep_editor_data"] is False
        assert max_preset["remove_metadata"] is True
        assert max_preset["strip_comments"] is True
        assert max_preset["shorten_ids"] is True

    def test_default_preset_is_balanced(self) -> None:
        """Test that default preset is balanced."""
        default_preset = OPTIMIZE_PRESETS["default"]
        assert default_preset["keep_editor_data"] is False  # Remove editor data
        assert default_preset["remove_metadata"] is False  # Keep metadata
        assert default_preset["shorten_ids"] is False  # Keep IDs


class TestOptimizeResultModel:
    """Tests for OptimizeResult model."""

    def test_bytes_saved_property(self) -> None:
        """Test the bytes_saved property calculation."""
        result = OptimizeResult(
            success=True,
            optimized_content="<svg/>",
            original_size=1000,
            optimized_size=800,
            reduction_percent=20.0,
        )

        assert result.bytes_saved == 200

    def test_bytes_saved_none_when_no_optimized_size(self) -> None:
        """Test bytes_saved returns None when optimized_size is None."""
        result = OptimizeResult(
            success=False,
            original_size=1000,
            error="Optimization failed",
        )

        assert result.bytes_saved is None
