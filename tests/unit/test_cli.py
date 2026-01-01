"""Unit tests for CLI module.

Tests for the Click-based CLI interface of SVG-MCP.
"""

import json
from pathlib import Path

from click.testing import CliRunner

from SVG_MCP import __version__
from SVG_MCP.cli import cli


class TestCLIBasic:
    """Tests for basic CLI functionality."""

    def test_cli_version(self) -> None:
        """Test --version shows version (C001)."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert "svg-mcp" in result.output.lower()
        assert __version__ in result.output

    def test_cli_help(self) -> None:
        """Test --help shows help (C002)."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "SVG-MCP" in result.output
        assert "validate" in result.output
        assert "render" in result.output
        assert "diff" in result.output
        assert "serve" in result.output
        assert "info" in result.output


class TestCLIValidate:
    """Tests for the validate command."""

    def test_cli_validate_valid(self, valid_fixtures_dir: Path) -> None:
        """Test validate command with valid SVG (C003)."""
        runner = CliRunner()
        svg_path = valid_fixtures_dir / "minimal.svg"

        result = runner.invoke(cli, ["validate", str(svg_path)])

        assert result.exit_code == 0
        assert "✓" in result.output or "valid" in result.output.lower()

    def test_cli_validate_invalid(self, invalid_fixtures_dir: Path) -> None:
        """Test validate command with invalid SVG (C004)."""
        runner = CliRunner()
        svg_path = invalid_fixtures_dir / "malformed.svg"

        result = runner.invoke(cli, ["validate", str(svg_path)])

        assert result.exit_code == 1
        assert "✗" in result.output or "invalid" in result.output.lower()

    def test_cli_validate_json_format(self, valid_fixtures_dir: Path) -> None:
        """Test validate command with JSON output format."""
        runner = CliRunner()
        svg_path = valid_fixtures_dir / "minimal.svg"

        result = runner.invoke(cli, ["validate", str(svg_path), "--format", "json"])

        assert result.exit_code == 0
        # Should be valid JSON
        data = json.loads(result.output)
        assert "valid" in data
        assert data["valid"] is True

    def test_cli_validate_json_format_invalid(self, invalid_fixtures_dir: Path) -> None:
        """Test validate command with JSON output for invalid SVG."""
        runner = CliRunner()
        svg_path = invalid_fixtures_dir / "malformed.svg"

        result = runner.invoke(cli, ["validate", str(svg_path), "--format", "json"])

        assert result.exit_code == 1
        data = json.loads(result.output)
        assert data["valid"] is False
        assert len(data["errors"]) > 0

    def test_cli_validate_shows_element_count(self, valid_fixtures_dir: Path) -> None:
        """Test validate command shows element count for valid SVG."""
        runner = CliRunner()
        svg_path = valid_fixtures_dir / "minimal.svg"

        result = runner.invoke(cli, ["validate", str(svg_path)])

        assert result.exit_code == 0
        assert "Elements:" in result.output

    def test_cli_validate_shows_viewbox(self, valid_fixtures_dir: Path) -> None:
        """Test validate command shows viewBox for valid SVG."""
        runner = CliRunner()
        svg_path = valid_fixtures_dir / "minimal.svg"

        result = runner.invoke(cli, ["validate", str(svg_path)])

        assert result.exit_code == 0
        assert "ViewBox:" in result.output

    def test_cli_validate_nonexistent_file(self) -> None:
        """Test validate command with nonexistent file."""
        runner = CliRunner()

        result = runner.invoke(cli, ["validate", "nonexistent.svg"])

        assert result.exit_code != 0

    def test_cli_validate_help(self) -> None:
        """Test validate command help."""
        runner = CliRunner()

        result = runner.invoke(cli, ["validate", "--help"])

        assert result.exit_code == 0
        assert "Validate an SVG file" in result.output


class TestCLIRender:
    """Tests for the render command."""

    def test_cli_render(self, valid_fixtures_dir: Path, tmp_output_dir: Path) -> None:
        """Test render command works (C005)."""
        runner = CliRunner()
        svg_path = valid_fixtures_dir / "minimal.svg"
        output_path = tmp_output_dir / "output.png"

        result = runner.invoke(cli, ["render", str(svg_path), str(output_path)])

        assert result.exit_code == 0
        assert "✓" in result.output or "Rendered" in result.output
        assert output_path.exists()

    def test_cli_render_with_dimensions(
        self, valid_fixtures_dir: Path, tmp_output_dir: Path
    ) -> None:
        """Test render command with width and height options."""
        runner = CliRunner()
        svg_path = valid_fixtures_dir / "minimal.svg"
        output_path = tmp_output_dir / "output_sized.png"

        result = runner.invoke(
            cli,
            [
                "render",
                str(svg_path),
                str(output_path),
                "--width",
                "200",
                "--height",
                "200",
            ],
        )

        assert result.exit_code == 0
        assert output_path.exists()

    def test_cli_render_with_scale(
        self, valid_fixtures_dir: Path, tmp_output_dir: Path
    ) -> None:
        """Test render command with scale option."""
        runner = CliRunner()
        svg_path = valid_fixtures_dir / "minimal.svg"
        output_path = tmp_output_dir / "output_scaled.png"

        result = runner.invoke(
            cli,
            ["render", str(svg_path), str(output_path), "--scale", "2.0"],
        )

        assert result.exit_code == 0
        assert output_path.exists()

    def test_cli_render_nonexistent_file(self, tmp_output_dir: Path) -> None:
        """Test render command with nonexistent input file."""
        runner = CliRunner()
        output_path = tmp_output_dir / "output.png"

        result = runner.invoke(cli, ["render", "nonexistent.svg", str(output_path)])

        assert result.exit_code != 0

    def test_cli_render_help(self) -> None:
        """Test render command help."""
        runner = CliRunner()

        result = runner.invoke(cli, ["render", "--help"])

        assert result.exit_code == 0
        assert "Render SVG to PNG" in result.output
        assert "--width" in result.output
        assert "--height" in result.output
        assert "--scale" in result.output


class TestCLIDiff:
    """Tests for the diff command."""

    def test_cli_diff(self, pairs_fixtures_dir: Path, tmp_output_dir: Path) -> None:
        """Test diff command works (C006)."""
        runner = CliRunner()
        svg1_path = pairs_fixtures_dir / "rect_original.svg"
        svg2_path = pairs_fixtures_dir / "rect_moved.svg"
        output_path = tmp_output_dir / "diff.png"

        result = runner.invoke(
            cli,
            ["diff", str(svg1_path), str(svg2_path), "-o", str(output_path)],
        )

        assert result.exit_code == 0
        assert output_path.exists()

    def test_cli_diff_identical(
        self, pairs_fixtures_dir: Path, tmp_output_dir: Path
    ) -> None:
        """Test diff command with identical SVGs."""
        runner = CliRunner()
        svg_path = pairs_fixtures_dir / "rect_original.svg"
        output_path = tmp_output_dir / "diff_identical.png"

        result = runner.invoke(
            cli,
            ["diff", str(svg_path), str(svg_path), "-o", str(output_path)],
        )

        assert result.exit_code == 0
        assert "identical" in result.output.lower()

    def test_cli_diff_with_mode(
        self, pairs_fixtures_dir: Path, tmp_output_dir: Path
    ) -> None:
        """Test diff command with different modes."""
        runner = CliRunner()
        svg1_path = pairs_fixtures_dir / "rect_original.svg"
        svg2_path = pairs_fixtures_dir / "rect_moved.svg"
        output_path = tmp_output_dir / "diff_side_by_side.png"

        result = runner.invoke(
            cli,
            [
                "diff",
                str(svg1_path),
                str(svg2_path),
                "-o",
                str(output_path),
                "--mode",
                "side_by_side",
            ],
        )

        assert result.exit_code == 0
        assert output_path.exists()

    def test_cli_diff_with_color_scheme(
        self, pairs_fixtures_dir: Path, tmp_output_dir: Path
    ) -> None:
        """Test diff command with color scheme option."""
        runner = CliRunner()
        svg1_path = pairs_fixtures_dir / "rect_original.svg"
        svg2_path = pairs_fixtures_dir / "rect_moved.svg"
        output_path = tmp_output_dir / "diff_colorblind.png"

        result = runner.invoke(
            cli,
            [
                "diff",
                str(svg1_path),
                str(svg2_path),
                "-o",
                str(output_path),
                "--color-scheme",
                "colorblind_safe",
            ],
        )

        assert result.exit_code == 0
        assert output_path.exists()

    def test_cli_diff_with_threshold(
        self, pairs_fixtures_dir: Path, tmp_output_dir: Path
    ) -> None:
        """Test diff command with threshold option."""
        runner = CliRunner()
        svg1_path = pairs_fixtures_dir / "rect_original.svg"
        svg2_path = pairs_fixtures_dir / "rect_moved.svg"
        output_path = tmp_output_dir / "diff_threshold.png"

        result = runner.invoke(
            cli,
            [
                "diff",
                str(svg1_path),
                str(svg2_path),
                "-o",
                str(output_path),
                "--threshold",
                "0.05",
            ],
        )

        assert result.exit_code == 0
        assert output_path.exists()

    def test_cli_diff_shows_statistics(
        self, pairs_fixtures_dir: Path, tmp_output_dir: Path
    ) -> None:
        """Test diff command shows diff statistics."""
        runner = CliRunner()
        svg1_path = pairs_fixtures_dir / "rect_original.svg"
        svg2_path = pairs_fixtures_dir / "rect_moved.svg"
        output_path = tmp_output_dir / "diff_stats.png"

        result = runner.invoke(
            cli,
            ["diff", str(svg1_path), str(svg2_path), "-o", str(output_path)],
        )

        assert result.exit_code == 0
        # Should show pixel count and percentage
        assert (
            "pixels" in result.output.lower() or "difference" in result.output.lower()
        )

    def test_cli_diff_help(self) -> None:
        """Test diff command help."""
        runner = CliRunner()

        result = runner.invoke(cli, ["diff", "--help"])

        assert result.exit_code == 0
        assert "Compare two SVG files" in result.output
        assert "--output" in result.output
        assert "--threshold" in result.output
        assert "--mode" in result.output
        assert "--color-scheme" in result.output


class TestCLIServe:
    """Tests for the serve command."""

    def test_cli_serve_help(self) -> None:
        """Test serve command help (C007 partial - can't fully test server start)."""
        runner = CliRunner()

        result = runner.invoke(cli, ["serve", "--help"])

        assert result.exit_code == 0
        assert "Start the MCP server" in result.output
        assert "--transport" in result.output
        assert "--port" in result.output
        assert "--host" in result.output

    def test_cli_serve_transport_options(self) -> None:
        """Test serve command shows transport options."""
        runner = CliRunner()

        result = runner.invoke(cli, ["serve", "--help"])

        assert result.exit_code == 0
        assert "stdio" in result.output
        assert "sse" in result.output


class TestCLIInfo:
    """Tests for the info command."""

    def test_cli_info(self) -> None:
        """Test info command shows information."""
        runner = CliRunner()

        result = runner.invoke(cli, ["info"])

        assert result.exit_code == 0
        assert "SVG-MCP" in result.output
        assert "Version" in result.output
        assert __version__ in result.output

    def test_cli_info_shows_tools(self) -> None:
        """Test info command lists available tools."""
        runner = CliRunner()

        result = runner.invoke(cli, ["info"])

        assert result.exit_code == 0
        assert "svg_validate" in result.output
        assert "svg_render" in result.output
        assert "svg_diff" in result.output
        assert "svg_edit" in result.output

    def test_cli_info_shows_resources(self) -> None:
        """Test info command lists available resources."""
        runner = CliRunner()

        result = runner.invoke(cli, ["info"])

        assert result.exit_code == 0
        assert "svg://file" in result.output
        assert "svg://preview" in result.output


class TestCLIErrorHandling:
    """Tests for CLI error handling."""

    def test_cli_unknown_command(self) -> None:
        """Test CLI handles unknown command gracefully."""
        runner = CliRunner()

        result = runner.invoke(cli, ["unknown_command"])

        assert result.exit_code != 0

    def test_cli_missing_required_argument(self) -> None:
        """Test CLI handles missing required argument."""
        runner = CliRunner()

        result = runner.invoke(cli, ["validate"])

        assert result.exit_code != 0
        assert "Missing argument" in result.output or "Usage:" in result.output

    def test_cli_invalid_option(self) -> None:
        """Test CLI handles invalid option."""
        runner = CliRunner()

        result = runner.invoke(cli, ["validate", "--invalid-option", "value"])

        assert result.exit_code != 0


class TestCLIExitCodes:
    """Tests for CLI exit codes."""

    def test_exit_code_success(self, valid_fixtures_dir: Path) -> None:
        """Test exit code 0 for successful validation."""
        runner = CliRunner()
        svg_path = valid_fixtures_dir / "minimal.svg"

        result = runner.invoke(cli, ["validate", str(svg_path)])

        assert result.exit_code == 0

    def test_exit_code_validation_failure(self, invalid_fixtures_dir: Path) -> None:
        """Test exit code 1 for validation failure."""
        runner = CliRunner()
        svg_path = invalid_fixtures_dir / "malformed.svg"

        result = runner.invoke(cli, ["validate", str(svg_path)])

        assert result.exit_code == 1

    def test_exit_code_file_not_found(self) -> None:
        """Test exit code for file not found."""
        runner = CliRunner()

        result = runner.invoke(cli, ["validate", "nonexistent.svg"])

        assert result.exit_code != 0
