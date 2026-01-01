"""End-to-end tests for CLI workflows.

These tests validate complete CLI workflows from command invocation
to output verification.
"""

import json
import subprocess
from pathlib import Path

import pytest
from click.testing import CliRunner

from SVG_MCP import __version__
from SVG_MCP.cli import cli


@pytest.mark.e2e
class TestCliValidateWorkflow:
    """E020: Test CLI validate command workflow."""

    def test_cli_validate_valid_svg(
        self, cli_runner: CliRunner, temp_workspace: Path, simple_svg: str
    ) -> None:
        """Test validating a valid SVG file via CLI."""
        # Create test file
        svg_file = temp_workspace / "valid.svg"
        svg_file.write_text(simple_svg)

        # Run validate command
        result = cli_runner.invoke(cli, ["validate", str(svg_file)])

        # Verify success
        assert result.exit_code == 0
        assert "✓" in result.output or "valid" in result.output.lower()

    def test_cli_validate_invalid_svg(
        self, cli_runner: CliRunner, temp_workspace: Path, invalid_svg: str
    ) -> None:
        """Test validating an invalid SVG file via CLI."""
        # Create test file
        svg_file = temp_workspace / "invalid.svg"
        svg_file.write_text(invalid_svg)

        # Run validate command
        result = cli_runner.invoke(cli, ["validate", str(svg_file)])

        # Verify failure
        assert result.exit_code == 1
        assert "✗" in result.output or "invalid" in result.output.lower()


@pytest.mark.e2e
class TestCliRenderWorkflow:
    """E021: Test CLI render command workflow."""

    def test_cli_render_basic(
        self, cli_runner: CliRunner, temp_workspace: Path, simple_svg: str
    ) -> None:
        """Test basic rendering via CLI."""
        svg_file = temp_workspace / "render_test.svg"
        svg_file.write_text(simple_svg)
        output_file = temp_workspace / "output.png"

        result = cli_runner.invoke(cli, ["render", str(svg_file), str(output_file)])

        assert result.exit_code == 0
        assert output_file.exists()
        assert "✓" in result.output or "Rendered" in result.output

    def test_cli_render_with_dimensions(
        self, cli_runner: CliRunner, temp_workspace: Path, simple_svg: str
    ) -> None:
        """Test rendering with specific dimensions."""
        svg_file = temp_workspace / "render_dims.svg"
        svg_file.write_text(simple_svg)
        output_file = temp_workspace / "output_dims.png"

        result = cli_runner.invoke(
            cli,
            [
                "render",
                str(svg_file),
                str(output_file),
                "--width",
                "400",
                "--height",
                "300",
            ],
        )

        assert result.exit_code == 0
        assert output_file.exists()

    def test_cli_render_with_scale(
        self, cli_runner: CliRunner, temp_workspace: Path, simple_svg: str
    ) -> None:
        """Test rendering with scale factor."""
        svg_file = temp_workspace / "render_scale.svg"
        svg_file.write_text(simple_svg)
        output_file = temp_workspace / "output_scale.png"

        result = cli_runner.invoke(
            cli,
            ["render", str(svg_file), str(output_file), "--scale", "2.0"],
        )

        assert result.exit_code == 0
        assert output_file.exists()


@pytest.mark.e2e
class TestCliDiffWorkflow:
    """E022: Test CLI diff command workflow."""

    def test_cli_diff_basic(
        self,
        cli_runner: CliRunner,
        temp_workspace: Path,
        svg_pair_original: str,
        svg_pair_modified: str,
    ) -> None:
        """Test basic diff via CLI."""
        svg1 = temp_workspace / "original.svg"
        svg2 = temp_workspace / "modified.svg"
        svg1.write_text(svg_pair_original)
        svg2.write_text(svg_pair_modified)
        output = temp_workspace / "diff.png"

        result = cli_runner.invoke(
            cli, ["diff", str(svg1), str(svg2), "-o", str(output)]
        )

        assert result.exit_code == 0
        assert output.exists()

    def test_cli_diff_identical(
        self, cli_runner: CliRunner, temp_workspace: Path, simple_svg: str
    ) -> None:
        """Test diff of identical SVGs."""
        svg1 = temp_workspace / "same1.svg"
        svg2 = temp_workspace / "same2.svg"
        svg1.write_text(simple_svg)
        svg2.write_text(simple_svg)
        output = temp_workspace / "diff_same.png"

        result = cli_runner.invoke(
            cli, ["diff", str(svg1), str(svg2), "-o", str(output)]
        )

        assert result.exit_code == 0
        assert "identical" in result.output.lower()

    def test_cli_diff_with_mode(
        self,
        cli_runner: CliRunner,
        temp_workspace: Path,
        svg_pair_original: str,
        svg_pair_modified: str,
    ) -> None:
        """Test diff with specific mode."""
        svg1 = temp_workspace / "mode1.svg"
        svg2 = temp_workspace / "mode2.svg"
        svg1.write_text(svg_pair_original)
        svg2.write_text(svg_pair_modified)
        output = temp_workspace / "diff_mode.png"

        result = cli_runner.invoke(
            cli,
            ["diff", str(svg1), str(svg2), "-o", str(output), "--mode", "side_by_side"],
        )

        assert result.exit_code == 0
        assert output.exists()


@pytest.mark.e2e
class TestCliBatchValidation:
    """E023: Test batch validation of multiple files."""

    def test_cli_batch_validation(
        self, cli_runner: CliRunner, temp_workspace: Path, simple_svg: str
    ) -> None:
        """Test validating multiple SVG files in sequence."""
        # Create multiple test files
        files = []
        for i in range(3):
            svg_file = temp_workspace / f"batch_{i}.svg"
            svg_file.write_text(simple_svg)
            files.append(svg_file)

        # Validate each file
        all_passed = True
        for svg_file in files:
            result = cli_runner.invoke(cli, ["validate", str(svg_file)])
            if result.exit_code != 0:
                all_passed = False

        assert all_passed


@pytest.mark.e2e
class TestCliOutputFormats:
    """E025: Test different output formats."""

    def test_cli_validate_json_output(
        self, cli_runner: CliRunner, temp_workspace: Path, simple_svg: str
    ) -> None:
        """Test JSON output format for validate command."""
        svg_file = temp_workspace / "json_test.svg"
        svg_file.write_text(simple_svg)

        result = cli_runner.invoke(cli, ["validate", str(svg_file), "--format", "json"])

        assert result.exit_code == 0
        # Verify output is valid JSON
        output_data = json.loads(result.output)
        assert "valid" in output_data
        assert output_data["valid"] is True

    def test_cli_validate_text_output(
        self, cli_runner: CliRunner, temp_workspace: Path, simple_svg: str
    ) -> None:
        """Test text output format for validate command."""
        svg_file = temp_workspace / "text_test.svg"
        svg_file.write_text(simple_svg)

        result = cli_runner.invoke(cli, ["validate", str(svg_file), "--format", "text"])

        assert result.exit_code == 0
        # Text output should have human-readable content
        assert "✓" in result.output or "valid" in result.output.lower()


@pytest.mark.e2e
class TestCliErrorExitCodes:
    """E026: Test correct exit codes for various scenarios."""

    def test_cli_success_exit_code(
        self, cli_runner: CliRunner, temp_workspace: Path, simple_svg: str
    ) -> None:
        """Test exit code 0 for successful operations."""
        svg_file = temp_workspace / "success.svg"
        svg_file.write_text(simple_svg)

        result = cli_runner.invoke(cli, ["validate", str(svg_file)])
        assert result.exit_code == 0

    def test_cli_validation_failure_exit_code(
        self, cli_runner: CliRunner, temp_workspace: Path, invalid_svg: str
    ) -> None:
        """Test exit code 1 for validation failure."""
        svg_file = temp_workspace / "failure.svg"
        svg_file.write_text(invalid_svg)

        result = cli_runner.invoke(cli, ["validate", str(svg_file)])
        assert result.exit_code == 1

    def test_cli_file_not_found_exit_code(
        self, cli_runner: CliRunner, temp_workspace: Path
    ) -> None:
        """Test exit code for file not found."""
        result = cli_runner.invoke(
            cli, ["validate", str(temp_workspace / "nonexistent.svg")]
        )
        assert result.exit_code != 0


@pytest.mark.e2e
class TestCliHelpCompleteness:
    """E028: Test CLI help documentation."""

    def test_cli_main_help(self, cli_runner: CliRunner) -> None:
        """Test main CLI help."""
        result = cli_runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "SVG-MCP" in result.output
        assert "validate" in result.output
        assert "render" in result.output
        assert "diff" in result.output
        assert "serve" in result.output

    def test_cli_validate_help(self, cli_runner: CliRunner) -> None:
        """Test validate command help."""
        result = cli_runner.invoke(cli, ["validate", "--help"])

        assert result.exit_code == 0
        assert "SVG" in result.output.upper()
        assert "--format" in result.output

    def test_cli_render_help(self, cli_runner: CliRunner) -> None:
        """Test render command help."""
        result = cli_runner.invoke(cli, ["render", "--help"])

        assert result.exit_code == 0
        assert "--width" in result.output
        assert "--height" in result.output
        assert "--scale" in result.output

    def test_cli_diff_help(self, cli_runner: CliRunner) -> None:
        """Test diff command help."""
        result = cli_runner.invoke(cli, ["diff", "--help"])

        assert result.exit_code == 0
        assert "--output" in result.output or "-o" in result.output
        assert "--mode" in result.output
        assert "--threshold" in result.output

    def test_cli_serve_help(self, cli_runner: CliRunner) -> None:
        """Test serve command help."""
        result = cli_runner.invoke(cli, ["serve", "--help"])

        assert result.exit_code == 0
        assert "--transport" in result.output
        assert "--port" in result.output


@pytest.mark.e2e
class TestCliVersionConsistency:
    """E029: Test version consistency."""

    def test_cli_version_matches_pyproject(self, cli_runner: CliRunner) -> None:
        """Test that CLI version matches pyproject.toml version."""
        result = cli_runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        # Version should be in output
        assert __version__ in result.output

    def test_cli_info_command(self, cli_runner: CliRunner) -> None:
        """Test info command shows version and features."""
        result = cli_runner.invoke(cli, ["info"])

        assert result.exit_code == 0
        assert "SVG-MCP" in result.output
        assert "Version" in result.output or __version__ in result.output
        assert "svg_validate" in result.output
        assert "svg_render" in result.output
        assert "svg_diff" in result.output


@pytest.mark.e2e
@pytest.mark.slow
class TestCliServeAndConnect:
    """E027: Test starting server via CLI and connecting."""

    def test_cli_serve_starts(self, temp_workspace: Path) -> None:
        """Test that serve command starts the server.

        Note: This test starts the server briefly and then terminates it.
        """
        import signal
        import time

        # Start server in subprocess
        proc = subprocess.Popen(
            [
                "poetry",
                "run",
                "svg-mcp",
                "serve",
                "--transport",
                "sse",
                "--port",
                "8766",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path(__file__).parent.parent.parent,
        )

        try:
            # Wait briefly for server to start
            time.sleep(2)

            # Check if process is still running (server started successfully)
            assert proc.poll() is None, "Server process terminated unexpectedly"

        finally:
            # Clean up
            proc.send_signal(signal.SIGTERM)
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
