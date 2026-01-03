"""Unit tests for SVG linter."""

from SVG_MCP.models.lint_types import LintResult, LintSeverity
from SVG_MCP.svg.linter import LINT_PRESETS, SVGLinter, lint_svg
from SVG_MCP.svg.scour_linter import ScourLinter, lint_svg_with_scour


# Sample SVG content for testing
VALID_SVG = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100">
  <title>Test SVG</title>
  <rect x="10" y="10" width="80" height="80" fill="red"/>
</svg>
"""

FLOWTEXT_SVG = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
  <flowRoot>
    <flowRegion>
      <rect x="10" y="10" width="80" height="80"/>
    </flowRegion>
    <flowPara>This is flowtext</flowPara>
  </flowRoot>
</svg>
"""

INKSCAPE_SVG = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
     xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
     width="100" height="100">
  <rect x="10" y="10" width="80" height="80" fill="red"/>
</svg>
"""

XLINK_SVG = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:xlink="http://www.w3.org/1999/xlink"
     width="100" height="100">
  <defs>
    <rect id="myRect" x="10" y="10" width="80" height="80" fill="red"/>
  </defs>
  <use xlink:href="#myRect"/>
</svg>
"""

EMBEDDED_IMAGE_SVG = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
  <image href="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==" width="100" height="100"/>
</svg>
"""

NO_NAMESPACE_SVG = """<?xml version="1.0" encoding="UTF-8"?>
<svg width="100" height="100">
  <rect x="10" y="10" width="80" height="80" fill="red"/>
</svg>
"""

HIGH_PRECISION_SVG = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
  <rect x="10.12345678901234" y="10.98765432109876" width="80.11111111111111" height="80.22222222222222" fill="red"/>
  <circle cx="50.12345678901234" cy="50.98765432109876" r="25.11111111111111"/>
  <path d="M 10.12345678901234,10.98765432109876 L 90.12345678901234,90.98765432109876"/>
  <line x1="10.12345678901234" y1="10.98765432109876" x2="90.12345678901234" y2="90.98765432109876"/>
  <ellipse cx="50.12345678901234" cy="50.98765432109876" rx="40.11111111111111" ry="30.22222222222222"/>
  <polygon points="10.12345678901234,10.98765432109876 90.12345678901234,10.98765432109876 50.12345678901234,90.98765432109876"/>
  <polyline points="10.12345678901234,10.98765432109876 50.12345678901234,50.98765432109876 90.12345678901234,10.98765432109876"/>
  <text x="10.12345678901234" y="50.98765432109876">Text</text>
  <rect x="20.12345678901234" y="20.98765432109876" width="60.11111111111111" height="60.22222222222222" fill="blue"/>
  <rect x="30.12345678901234" y="30.98765432109876" width="40.11111111111111" height="40.22222222222222" fill="green"/>
  <rect x="40.12345678901234" y="40.98765432109876" width="20.11111111111111" height="20.22222222222222" fill="yellow"/>
</svg>
"""


class TestScourLinterInit:
    """Tests for ScourLinter initialization."""

    def test_scour_linter_init(self) -> None:
        """Test that ScourLinter initializes correctly."""
        linter = ScourLinter()
        assert linter is not None
        assert linter._safe_options is not None


class TestScourLinterFlowtext:
    """Tests for flowtext detection."""

    def test_detects_flowroot(self) -> None:
        """Test that flowRoot is detected as an error."""
        linter = ScourLinter()
        issues = linter.lint(FLOWTEXT_SVG)

        flowtext_issues = [i for i in issues if i.code == "inkscape/flowtext"]
        assert len(flowtext_issues) >= 1
        assert flowtext_issues[0].severity == LintSeverity.ERROR

    def test_valid_svg_no_flowtext(self) -> None:
        """Test that valid SVG has no flowtext issues."""
        linter = ScourLinter()
        issues = linter.lint(VALID_SVG)

        flowtext_issues = [i for i in issues if "flowtext" in i.code]
        assert len(flowtext_issues) == 0


class TestScourLinterNamespaces:
    """Tests for namespace detection."""

    def test_detects_inkscape_namespace(self) -> None:
        """Test that Inkscape namespace is detected."""
        linter = ScourLinter()
        issues = linter.lint(INKSCAPE_SVG)

        inkscape_issues = [i for i in issues if "inkscape" in i.code.lower()]
        assert len(inkscape_issues) >= 1

    def test_detects_sodipodi_namespace(self) -> None:
        """Test that Sodipodi namespace is detected."""
        linter = ScourLinter()
        issues = linter.lint(INKSCAPE_SVG)

        sodipodi_issues = [i for i in issues if "sodipodi" in i.code.lower()]
        assert len(sodipodi_issues) >= 1

    def test_detects_missing_svg_namespace(self) -> None:
        """Test that missing SVG namespace is detected."""
        linter = ScourLinter()
        issues = linter.lint(NO_NAMESPACE_SVG)

        namespace_issues = [i for i in issues if "namespace" in i.code.lower()]
        assert len(namespace_issues) >= 1


class TestScourLinterXlink:
    """Tests for deprecated xlink detection."""

    def test_detects_xlink_href(self) -> None:
        """Test that xlink:href is detected as deprecated."""
        linter = ScourLinter()
        issues = linter.lint(XLINK_SVG)

        xlink_issues = [i for i in issues if "xlink" in i.code.lower()]
        assert len(xlink_issues) >= 1
        assert xlink_issues[0].severity == LintSeverity.WARNING


class TestScourLinterEmbeddedImages:
    """Tests for embedded image detection."""

    def test_detects_embedded_base64_image(self) -> None:
        """Test that embedded base64 images are detected."""
        linter = ScourLinter()
        issues = linter.lint(EMBEDDED_IMAGE_SVG)

        image_issues = [i for i in issues if "embedded" in i.code.lower()]
        assert len(image_issues) >= 1


class TestScourLinterPrecision:
    """Tests for precision detection."""

    def test_detects_excessive_precision(self) -> None:
        """Test that excessive precision is detected."""
        linter = ScourLinter()
        issues = linter.lint(HIGH_PRECISION_SVG)

        precision_issues = [i for i in issues if "precision" in i.code.lower()]
        assert len(precision_issues) >= 1


class TestSVGLinterInit:
    """Tests for SVGLinter initialization."""

    def test_default_preset(self) -> None:
        """Test that default preset is 'default'."""
        linter = SVGLinter()
        assert linter.preset == "default"

    def test_relaxed_preset(self) -> None:
        """Test initialization with relaxed preset."""
        linter = SVGLinter(preset="relaxed")
        assert linter.preset == "relaxed"

    def test_strict_preset(self) -> None:
        """Test initialization with strict preset."""
        linter = SVGLinter(preset="strict")
        assert linter.preset == "strict"

    def test_inkscape_preset(self) -> None:
        """Test initialization with inkscape preset."""
        linter = SVGLinter(preset="inkscape")
        assert linter.preset == "inkscape"


class TestSVGLinterLint:
    """Tests for SVGLinter.lint() method."""

    def test_lint_valid_svg(self) -> None:
        """Test linting a valid SVG."""
        linter = SVGLinter()
        result = linter.lint(VALID_SVG)

        assert isinstance(result, LintResult)
        assert result.valid is True

    def test_lint_flowtext_svg(self) -> None:
        """Test linting SVG with flowtext."""
        linter = SVGLinter()
        result = linter.lint(FLOWTEXT_SVG)

        assert isinstance(result, LintResult)
        assert result.valid is False
        assert len(result.errors) >= 1

    def test_relaxed_preset_ignores_scour(self) -> None:
        """Test that relaxed preset doesn't run Scour checks."""
        linter = SVGLinter(preset="relaxed")
        result = linter.lint(FLOWTEXT_SVG)

        # Relaxed preset doesn't use Scour, so flowtext won't be detected
        flowtext_errors = [i for i in result.issues if "flowtext" in i.code]
        assert len(flowtext_errors) == 0

    def test_inkscape_preset_detects_flowtext(self) -> None:
        """Test that inkscape preset detects flowtext."""
        linter = SVGLinter(preset="inkscape")
        result = linter.lint(FLOWTEXT_SVG)

        assert result.valid is False
        flowtext_errors = [i for i in result.issues if "flowtext" in i.code]
        assert len(flowtext_errors) >= 1

    def test_use_scour_override(self) -> None:
        """Test that use_scour parameter overrides preset."""
        linter = SVGLinter(preset="relaxed")

        # With use_scour=True, should detect flowtext even in relaxed mode
        result = linter.lint(FLOWTEXT_SVG, use_scour=True)
        flowtext_errors = [i for i in result.issues if "flowtext" in i.code]
        assert len(flowtext_errors) >= 1


class TestSVGLinterCustomRules:
    """Tests for custom lint rules."""

    def test_strict_requires_viewbox(self) -> None:
        """Test that strict preset requires viewBox."""
        svg_no_viewbox = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
  <rect x="10" y="10" width="80" height="80" fill="red"/>
</svg>
"""
        linter = SVGLinter(preset="strict")
        result = linter.lint(svg_no_viewbox)

        viewbox_issues = [i for i in result.issues if "viewbox" in i.code.lower()]
        assert len(viewbox_issues) >= 1

    def test_strict_requires_title(self) -> None:
        """Test that strict preset requires title."""
        svg_no_title = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100">
  <rect x="10" y="10" width="80" height="80" fill="red"/>
</svg>
"""
        linter = SVGLinter(preset="strict")
        result = linter.lint(svg_no_title)

        title_issues = [i for i in result.issues if "title" in i.code.lower()]
        assert len(title_issues) >= 1


class TestSVGLinterLintFile:
    """Tests for SVGLinter.lint_file() method."""

    def test_lint_nonexistent_file(self, tmp_path) -> None:
        """Test linting a file that doesn't exist."""
        linter = SVGLinter()
        result = linter.lint_file(str(tmp_path / "nonexistent.svg"))

        assert result.valid is False
        assert len(result.issues) >= 1
        assert result.issues[0].code == "file/read-error"

    def test_lint_file_success(self, tmp_path) -> None:
        """Test successfully linting a file."""
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(VALID_SVG, encoding="utf-8")

        linter = SVGLinter()
        result = linter.lint_file(str(svg_file))

        assert result.valid is True


class TestLintSvgFunction:
    """Tests for the lint_svg convenience function."""

    def test_lint_svg_default(self) -> None:
        """Test lint_svg with default preset."""
        result = lint_svg(VALID_SVG)

        assert result.valid is True

    def test_lint_svg_with_preset(self) -> None:
        """Test lint_svg with specific preset."""
        result = lint_svg(FLOWTEXT_SVG, preset="inkscape")

        assert result.valid is False

    def test_lint_svg_with_kwargs(self) -> None:
        """Test lint_svg with additional options."""
        result = lint_svg(FLOWTEXT_SVG, preset="relaxed", use_scour=True)

        # Should detect flowtext because use_scour=True
        flowtext_errors = [i for i in result.issues if "flowtext" in i.code]
        assert len(flowtext_errors) >= 1


class TestLintSvgWithScourFunction:
    """Tests for the lint_svg_with_scour convenience function."""

    def test_lint_svg_with_scour(self) -> None:
        """Test lint_svg_with_scour function."""
        issues = lint_svg_with_scour(FLOWTEXT_SVG)

        assert isinstance(issues, list)
        flowtext_issues = [i for i in issues if "flowtext" in i.code]
        assert len(flowtext_issues) >= 1


class TestLintPresets:
    """Tests for lint presets configuration."""

    def test_all_presets_exist(self) -> None:
        """Test that all expected presets are defined."""
        assert "relaxed" in LINT_PRESETS
        assert "default" in LINT_PRESETS
        assert "strict" in LINT_PRESETS
        assert "inkscape" in LINT_PRESETS

    def test_relaxed_preset_config(self) -> None:
        """Test relaxed preset configuration."""
        assert LINT_PRESETS["relaxed"]["use_scour"] is False

    def test_default_preset_config(self) -> None:
        """Test default preset configuration."""
        assert LINT_PRESETS["default"]["use_scour"] is True

    def test_inkscape_preset_config(self) -> None:
        """Test inkscape preset configuration."""
        assert LINT_PRESETS["inkscape"]["use_scour"] is True
        assert LINT_PRESETS["inkscape"]["use_svglint"] is False


class TestLintResultModel:
    """Tests for LintResult model."""

    def test_errors_property(self) -> None:
        """Test the errors property."""
        linter = SVGLinter()
        result = linter.lint(FLOWTEXT_SVG)

        assert len(result.errors) >= 1
        for error in result.errors:
            assert error.severity == LintSeverity.ERROR

    def test_warnings_property(self) -> None:
        """Test the warnings property."""
        linter = SVGLinter()
        result = linter.lint(XLINK_SVG)

        # xlink:href should generate a warning
        assert len(result.warnings) >= 1
        for warning in result.warnings:
            assert warning.severity == LintSeverity.WARNING

    def test_error_count_property(self) -> None:
        """Test the error_count property."""
        linter = SVGLinter()
        result = linter.lint(FLOWTEXT_SVG)

        assert result.error_count >= 1
        assert result.error_count == len(result.errors)

    def test_warning_count_property(self) -> None:
        """Test the warning_count property."""
        linter = SVGLinter()
        result = linter.lint(XLINK_SVG)

        assert result.warning_count >= 1
        assert result.warning_count == len(result.warnings)
