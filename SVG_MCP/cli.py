"""CLI interface for SVG-MCP server.

This module provides a command-line interface for the SVG-MCP server
using Click.
"""

import json
import sys
from pathlib import Path

import click

from SVG_MCP import __version__
from SVG_MCP.server import create_server
from SVG_MCP.svg.differ import SVGDiffer
from SVG_MCP.svg.linter import SVGLinter
from SVG_MCP.svg.optimizer import SVGOptimizer
from SVG_MCP.svg.renderer import SVGRenderer
from SVG_MCP.svg.validator import SVGValidator


@click.group()
@click.version_option(version=__version__, prog_name="svg-mcp")
def cli() -> None:
    """SVG-MCP: MCP server for SVG file operations.

    This tool provides SVG validation, rendering, and visual diff capabilities
    both as an MCP server and as standalone CLI commands.
    """
    pass


@cli.command()
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse", "streamable-http", "http"]),
    default="stdio",
    help="Transport protocol for the MCP server.",
)
@click.option(
    "--port",
    type=int,
    default=8080,
    help="Port for HTTP/SSE transport.",
)
@click.option(
    "--host",
    type=str,
    default="127.0.0.1",
    help="Host for HTTP/SSE transport.",
)
@click.option(
    "--log-level",
    type=click.Choice(["debug", "info", "warning", "error"]),
    default="info",
    help="Log level for the server.",
)
def serve(transport: str, port: int, host: str, log_level: str) -> None:
    """Start the MCP server.

    By default, starts the server using stdio transport for use with
    MCP clients like Claude Desktop.

    For shared server mode (multiple VS Code windows connecting to one server),
    use streamable-http transport. This reduces CPU usage by avoiding multiple
    server instances.

    Examples:

        # Start with stdio transport (default)
        svg-mcp serve

        # Start with SSE transport
        svg-mcp serve --transport sse --port 8080

        # Start with Streamable HTTP transport (recommended for shared mode)
        svg-mcp serve --transport streamable-http --port 8081

        # Alias for streamable-http
        svg-mcp serve --transport http --port 8081
    """
    server = create_server()

    if transport == "stdio":
        server.run()
    elif transport == "sse":
        server.run(transport="sse", host=host, port=port, log_level=log_level)
    elif transport in ("streamable-http", "http"):
        server.run(
            transport="streamable-http", host=host, port=port, log_level=log_level
        )


@cli.command()
@click.argument("svg_file", type=click.Path(exists=True))
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "text"]),
    default="text",
    help="Output format.",
)
def validate(svg_file: str, output_format: str) -> None:
    """Validate an SVG file.

    Checks the SVG file for syntax errors and returns detailed
    information about any issues found.

    Examples:

        # Validate with text output
        svg-mcp validate input.svg

        # Validate with JSON output
        svg-mcp validate input.svg --format json
    """
    validator = SVGValidator()
    path = Path(svg_file)

    result = validator.validate_file(path)

    if output_format == "json":
        click.echo(json.dumps(result.model_dump(), indent=2))
    else:
        if result.valid:
            click.secho("✓ SVG is valid", fg="green")
            if result.info:
                click.echo(f"  Elements: {result.info.element_count}")
                if result.info.viewbox:
                    vb = result.info.viewbox
                    click.echo(f"  ViewBox: {vb.x} {vb.y} {vb.width} {vb.height}")
                if result.info.width:
                    click.echo(f"  Width: {result.info.width}")
                if result.info.height:
                    click.echo(f"  Height: {result.info.height}")
        else:
            click.secho("✗ SVG is invalid", fg="red")
            for error in result.errors:
                location = ""
                if error.line:
                    location = f" (line {error.line}"
                    if error.column:
                        location += f", column {error.column}"
                    location += ")"
                click.echo(f"  Error{location}: {error.message}")
                if error.context:
                    click.echo(f"    Context: {error.context}")
                if error.suggestion:
                    click.echo(f"    Suggestion: {error.suggestion}")

        if result.warnings:
            click.secho("\nWarnings:", fg="yellow")
            for warning in result.warnings:
                click.echo(f"  - {warning.message}")

    # Exit with error code if invalid
    if not result.valid:
        sys.exit(1)


@cli.command()
@click.argument("svg_file", type=click.Path(exists=True))
@click.argument("output_file", type=click.Path())
@click.option("--width", type=int, help="Output width in pixels.")
@click.option("--height", type=int, help="Output height in pixels.")
@click.option("--scale", type=float, default=1.0, help="Scale factor.")
def render(
    svg_file: str,
    output_file: str,
    width: int | None,
    height: int | None,
    scale: float,
) -> None:
    """Render SVG to PNG.

    Converts an SVG file to a PNG image with optional size and scale options.

    Examples:

        # Basic render
        svg-mcp render input.svg output.png

        # Render with specific dimensions
        svg-mcp render input.svg output.png --width 800 --height 600

        # Render at 2x scale
        svg-mcp render input.svg output.png --scale 2.0
    """
    renderer = SVGRenderer()
    input_path = Path(svg_file)
    output_path = Path(output_file)

    result = renderer.render_file(
        input_path,
        output_path,
        width=width,
        height=height,
        scale=scale if scale != 1.0 else None,
    )

    if result.success:
        click.secho(f"✓ Rendered to {output_path}", fg="green")
        if result.dimensions:
            click.echo(
                f"  Size: {int(result.dimensions.width)}x{int(result.dimensions.height)}"
            )
    else:
        click.secho(f"✗ Rendering failed: {result.error}", fg="red")
        sys.exit(1)


@cli.command()
@click.argument("svg1", type=click.Path(exists=True))
@click.argument("svg2", type=click.Path(exists=True))
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default="diff.png",
    help="Output diff image path.",
)
@click.option(
    "--threshold",
    type=float,
    default=0.1,
    help="Diff threshold (0.0 to 1.0).",
)
@click.option(
    "--mode",
    type=click.Choice(
        ["overlay", "side_by_side", "difference", "highlight", "checkerboard"]
    ),
    default="overlay",
    help="Diff visualization mode.",
)
@click.option(
    "--color-scheme",
    type=click.Choice(
        ["default", "high_contrast", "colorblind_safe", "subtle", "neon"]
    ),
    default="default",
    help="Color scheme for diff visualization.",
)
def diff(
    svg1: str,
    svg2: str,
    output: str,
    threshold: float,
    mode: str,
    color_scheme: str,
) -> None:
    """Compare two SVG files visually.

    Generates a diff image highlighting the visual differences between
    two SVG files.

    Examples:

        # Basic diff
        svg-mcp diff file1.svg file2.svg

        # Diff with custom output
        svg-mcp diff file1.svg file2.svg -o comparison.png

        # Diff with side-by-side mode
        svg-mcp diff file1.svg file2.svg --mode side_by_side
    """
    differ = SVGDiffer()
    output_path = Path(output)

    result = differ.diff_files(
        svg1,
        svg2,
        output_path,
        mode=mode,  # type: ignore
        color_scheme=color_scheme,
        threshold=threshold,
    )

    if result.diff_image_path:
        if result.identical:
            click.secho("✓ SVGs are visually identical", fg="green")
        else:
            click.secho("✗ SVGs differ", fg="yellow")
            click.echo(f"  Different pixels: {result.diff_pixel_count}")
            click.echo(f"  Difference: {result.diff_percentage:.2f}%")
            click.echo(f"  Diff image: {result.diff_image_path}")
            if result.bounding_boxes:
                click.echo(f"  Changed regions: {len(result.bounding_boxes)}")
    else:
        click.secho("✗ Failed to generate diff", fg="red")
        sys.exit(1)


@cli.command()
@click.argument("svg_file", type=click.Path(exists=True))
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file path. If not specified, prints to stdout.",
)
@click.option(
    "--preset",
    type=click.Choice(["safe", "default", "maximum"]),
    default="default",
    help="Optimization preset.",
)
@click.option(
    "--precision",
    type=int,
    help="Decimal precision for coordinates (1-15).",
)
@click.option(
    "--remove-editor-data/--keep-editor-data",
    default=None,
    help="Remove/keep editor-specific data (Inkscape, etc.).",
)
@click.option(
    "--remove-metadata/--keep-metadata",
    default=None,
    help="Remove/keep metadata elements.",
)
@click.option(
    "--shorten-ids/--keep-ids",
    default=None,
    help="Shorten/keep element IDs.",
)
@click.option(
    "--indent",
    type=str,
    help="Indentation string (e.g., '  ' for 2 spaces).",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["svg", "json"]),
    default="svg",
    help="Output format (svg content or json with stats).",
)
def optimize(
    svg_file: str,
    output: str | None,
    preset: str,
    precision: int | None,
    remove_editor_data: bool | None,
    remove_metadata: bool | None,
    shorten_ids: bool | None,
    indent: str | None,
    output_format: str,
) -> None:
    """Optimize an SVG file using Scour.

    Reduces SVG file size while preserving visual appearance.

    Presets:
      - safe: Minimal changes, preserves all IDs and editor data
      - default: Balanced optimization for most use cases
      - maximum: Aggressive optimization for smallest file size

    Examples:

        # Optimize with default preset
        svg-mcp optimize input.svg -o output.svg

        # Optimize with maximum compression
        svg-mcp optimize input.svg -o output.svg --preset maximum

        # Optimize and print to stdout
        svg-mcp optimize input.svg

        # Get optimization stats as JSON
        svg-mcp optimize input.svg --format json
    """
    optimizer = SVGOptimizer(preset=preset)  # type: ignore
    input_path = Path(svg_file)

    # Build kwargs for options that were explicitly provided
    kwargs: dict = {}
    if precision is not None:
        kwargs["precision"] = precision
    if remove_editor_data is not None:
        kwargs["remove_editor_data"] = remove_editor_data
    if remove_metadata is not None:
        kwargs["remove_metadata"] = remove_metadata
    if shorten_ids is not None:
        kwargs["shorten_ids"] = shorten_ids
    if indent is not None:
        kwargs["indent"] = indent

    result = optimizer.optimize_file(input_path, **kwargs)

    if output_format == "json":
        click.echo(json.dumps(result.model_dump(), indent=2))
    elif result.success:
        if output:
            output_path = Path(output)
            output_path.write_text(result.optimized_content or "", encoding="utf-8")
            click.secho(f"✓ Optimized to {output_path}", fg="green")
            click.echo(f"  Original size: {result.original_size} bytes")
            click.echo(f"  Optimized size: {result.optimized_size} bytes")
            click.echo(f"  Reduction: {result.reduction_percent:.1f}%")
        else:
            # Print optimized SVG to stdout
            click.echo(result.optimized_content)
    else:
        click.secho(f"✗ Optimization failed: {result.error}", fg="red")
        sys.exit(1)


@cli.command()
@click.argument("svg_file", type=click.Path(exists=True))
@click.option(
    "--preset",
    type=click.Choice(["relaxed", "default", "strict", "inkscape"]),
    default="default",
    help="Lint preset.",
)
@click.option(
    "--use-scour/--no-scour",
    default=None,
    help="Enable/disable Scour-based Inkscape compatibility checks.",
)
@click.option(
    "--use-svglint/--no-svglint",
    default=None,
    help="Enable/disable svglint rules (requires Node.js).",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format.",
)
def lint(
    svg_file: str,
    preset: str,
    use_scour: bool | None,
    use_svglint: bool | None,
    output_format: str,
) -> None:
    """Lint an SVG file for issues.

    Checks the SVG file for compatibility issues, best practices,
    and potential problems.

    Presets:
      - relaxed: Basic XML validity only
      - default: Standard checks + Inkscape compatibility
      - strict: All checks + required viewBox, title, etc.
      - inkscape: Focus on Inkscape/librsvg compatibility

    Examples:

        # Lint with default preset
        svg-mcp lint input.svg

        # Lint with strict preset
        svg-mcp lint input.svg --preset strict

        # Lint focusing on Inkscape compatibility
        svg-mcp lint input.svg --preset inkscape

        # Get lint results as JSON
        svg-mcp lint input.svg --format json
    """
    linter = SVGLinter(preset=preset)  # type: ignore
    input_path = Path(svg_file)

    # Build kwargs for options that were explicitly provided
    kwargs: dict = {}
    if use_scour is not None:
        kwargs["use_scour"] = use_scour
    if use_svglint is not None:
        kwargs["use_svglint"] = use_svglint

    result = linter.lint_file(str(input_path), **kwargs)

    if output_format == "json":
        click.echo(json.dumps(result.model_dump(), indent=2))
    else:
        if result.valid:
            click.secho("✓ SVG passed linting", fg="green")
        else:
            click.secho("✗ SVG has issues", fg="red")

        # Group issues by severity
        errors = [i for i in result.issues if i.severity.value == "error"]
        warnings = [i for i in result.issues if i.severity.value == "warning"]
        infos = [i for i in result.issues if i.severity.value == "info"]

        if errors:
            click.secho(f"\nErrors ({len(errors)}):", fg="red")
            for issue in errors:
                location = f" (line {issue.line})" if issue.line else ""
                click.echo(f"  [{issue.code}]{location}: {issue.message}")
                if issue.suggestion:
                    click.echo(f"    → {issue.suggestion}")

        if warnings:
            click.secho(f"\nWarnings ({len(warnings)}):", fg="yellow")
            for issue in warnings:
                location = f" (line {issue.line})" if issue.line else ""
                click.echo(f"  [{issue.code}]{location}: {issue.message}")
                if issue.suggestion:
                    click.echo(f"    → {issue.suggestion}")

        if infos:
            click.secho(f"\nInfo ({len(infos)}):", fg="blue")
            for issue in infos:
                location = f" (line {issue.line})" if issue.line else ""
                click.echo(f"  [{issue.code}]{location}: {issue.message}")
                if issue.suggestion:
                    click.echo(f"    → {issue.suggestion}")

        if not result.issues:
            click.echo("  No issues found.")

    # Exit with error code if not valid
    if not result.valid:
        sys.exit(1)


@cli.command()
def info() -> None:
    """Show information about SVG-MCP.

    Displays version information and available features.
    """
    click.echo("SVG-MCP Server")
    click.echo("==============")
    click.echo()
    click.echo(f"Version: {__version__}")
    click.echo()
    click.echo("Available MCP Tools:")
    click.echo("  - svg_validate: Validate SVG syntax")
    click.echo("  - svg_render: Render SVG to PNG")
    click.echo("  - svg_diff: Compare two SVGs visually")
    click.echo("  - svg_edit: Edit SVG files with validation")
    click.echo("  - svg_optimize: Optimize SVG using Scour")
    click.echo("  - svg_lint: Lint SVG for issues")
    click.echo()
    click.echo("Available MCP Resources:")
    click.echo("  - svg://file/{path}: Access SVG file content")
    click.echo("  - svg://preview/{path}: Get rendered preview")
    click.echo()
    click.echo("For more information, run: svg-mcp --help")


if __name__ == "__main__":
    cli()
