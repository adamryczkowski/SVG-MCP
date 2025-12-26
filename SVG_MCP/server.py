"""MCP server implementation for SVG operations.

This module provides an MCP server with tools for SVG validation,
rendering, and visual diff operations.
"""

import base64
import tempfile
from pathlib import Path
from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from SVG_MCP.models.types import (
    ViewBox,
)
from SVG_MCP.svg.differ import SVGDiffer
from SVG_MCP.svg.renderer import SVGRenderer
from SVG_MCP.svg.validator import SVGValidator

# Create the FastMCP server
mcp = FastMCP(
    "SVG-MCP",
    instructions="MCP server for SVG file operations - validation, rendering, and visual diff",
)

# Initialize the SVG processing components
_validator = SVGValidator()
_renderer = SVGRenderer()
_differ = SVGDiffer()


# ============================================================================
# Implementation Functions (for testing)
# ============================================================================


def _impl_svg_validate(content: str) -> dict:
    """Implementation of svg_validate tool.

    Args:
        content: SVG content as a string.

    Returns:
        A dictionary containing validation results.
    """
    result = _validator.validate(content)
    return result.model_dump()


def _impl_svg_render(
    content: str,
    output_path: str,
    width: int | None = None,
    height: int | None = None,
    scale: float | None = None,
    zoom_x: float | None = None,
    zoom_y: float | None = None,
    zoom_width: float | None = None,
    zoom_height: float | None = None,
) -> dict:
    """Implementation of svg_render tool.

    Args:
        content: SVG content as a string.
        output_path: Path to save the output PNG file.
        width: Output width in pixels (optional).
        height: Output height in pixels (optional).
        scale: Scale factor for rendering (optional).
        zoom_x: X coordinate of zoom rectangle (optional).
        zoom_y: Y coordinate of zoom rectangle (optional).
        zoom_width: Width of zoom rectangle (optional).
        zoom_height: Height of zoom rectangle (optional).

    Returns:
        A dictionary containing render results.
    """
    # Build zoom rectangle if all parameters are provided
    zoom_rect = None
    if all(v is not None for v in [zoom_x, zoom_y, zoom_width, zoom_height]):
        zoom_rect = ViewBox(
            x=zoom_x,  # type: ignore
            y=zoom_y,  # type: ignore
            width=zoom_width,  # type: ignore
            height=zoom_height,  # type: ignore
        )

    result = _renderer.render(
        content,
        output_path,
        width=width,
        height=height,
        scale=scale,
        zoom_rect=zoom_rect,
    )
    return result.model_dump()


def _impl_svg_diff(
    content1: str,
    content2: str,
    output_path: str,
    mode: str = "overlay",
    color_scheme: str = "default",
    width: int | None = None,
    height: int | None = None,
    threshold: float = 0.1,
) -> dict:
    """Implementation of svg_diff tool.

    Args:
        content1: First SVG content.
        content2: Second SVG content.
        output_path: Path to save the diff image.
        mode: Diff visualization mode (default: "overlay").
        color_scheme: Color scheme for visualization (default: "default").
        width: Render width for comparison (optional).
        height: Render height for comparison (optional).
        threshold: Pixel difference threshold (default: 0.1).

    Returns:
        A dictionary containing diff results.
    """
    result = _differ.diff(
        content1,
        content2,
        output_path,
        mode=mode,  # type: ignore
        color_scheme=color_scheme,
        width=width,
        height=height,
        threshold=threshold,
    )
    return result.model_dump()


def _impl_svg_edit(
    file_path: str,
    operation: str,
    content: str = "",
    line_start: int = 1,
    line_end: int | None = None,
    validate_after: bool = True,
) -> dict:
    """Implementation of svg_edit tool.

    Args:
        file_path: Path to the SVG file to edit.
        operation: Operation type: "replace", "insert", or "delete".
        content: New content for replace/insert operations.
        line_start: Start line number (1-based).
        line_end: End line number for replace/delete (optional).
        validate_after: Whether to validate after edit (default: True).

    Returns:
        A dictionary containing edit results.
    """
    path = Path(file_path)

    # Check if file exists
    if not path.exists():
        return {
            "success": False,
            "error": f"File not found: {file_path}",
            "validation": None,
        }

    try:
        # Read the file
        lines = path.read_text(encoding="utf-8").split("\n")

        # Validate line numbers
        if line_start < 1 or line_start > len(lines) + 1:
            return {
                "success": False,
                "error": f"Invalid line_start: {line_start}. File has {len(lines)} lines.",
                "validation": None,
            }

        # Set default line_end
        if line_end is None:
            line_end = line_start

        # Perform the operation
        if operation == "replace":
            # Replace lines from line_start to line_end with content
            new_lines = content.split("\n")
            lines = lines[: line_start - 1] + new_lines + lines[line_end:]
        elif operation == "insert":
            # Insert content at line_start
            new_lines = content.split("\n")
            lines = lines[: line_start - 1] + new_lines + lines[line_start - 1 :]
        elif operation == "delete":
            # Delete lines from line_start to line_end
            lines = lines[: line_start - 1] + lines[line_end:]
        else:
            return {
                "success": False,
                "error": f"Invalid operation: {operation}. Use 'replace', 'insert', or 'delete'.",
                "validation": None,
            }

        # Write the file
        new_content = "\n".join(lines)
        path.write_text(new_content, encoding="utf-8")

        # Validate if requested
        validation_result = None
        if validate_after:
            validation_result = _validator.validate(new_content).model_dump()

        return {
            "success": True,
            "validation": validation_result,
            "error": None,
        }

    except OSError as e:
        return {
            "success": False,
            "error": f"Failed to edit file: {e}",
            "validation": None,
        }


def _impl_svg_file_resource(path: str) -> str:
    """Implementation of svg://file/{path} resource.

    Args:
        path: Path to the SVG file.

    Returns:
        SVG file content as a string.
    """
    file_path = Path(path)
    if not file_path.exists():
        return f"Error: File not found: {path}"

    try:
        return file_path.read_text(encoding="utf-8")
    except OSError as e:
        return f"Error: Failed to read file: {e}"


def _impl_svg_preview_resource(path: str) -> str:
    """Implementation of svg://preview/{path} resource.

    Args:
        path: Path to the SVG file.

    Returns:
        Base64-encoded PNG preview or error message.
    """
    file_path = Path(path)
    if not file_path.exists():
        return f"Error: File not found: {path}"

    try:
        svg_content = file_path.read_text(encoding="utf-8")

        # Render to a temporary file
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name

        result = _renderer.render(svg_content, tmp_path, width=256)

        if result.success:
            # Read and encode the PNG
            with open(tmp_path, "rb") as f:
                png_data = f.read()
            # Clean up
            Path(tmp_path).unlink()
            return f"data:image/png;base64,{base64.b64encode(png_data).decode()}"
        else:
            return f"Error: Failed to render preview: {result.error}"

    except OSError as e:
        return f"Error: Failed to read file: {e}"


# ============================================================================
# MCP Tools
# ============================================================================


@mcp.tool
def svg_validate(
    content: Annotated[str, Field(description="SVG content as a string")],
) -> dict:
    """Validate SVG syntax and return detailed error information.

    This tool validates SVG content and returns structured information about
    any errors or warnings found, along with metadata about the SVG structure.

    Args:
        content: SVG content as a string.

    Returns:
        A dictionary containing:
        - valid: Whether the SVG is valid
        - errors: List of errors found (with line numbers and suggestions)
        - warnings: List of warnings found
        - info: SVG metadata (element count, viewBox, dimensions, namespaces)
    """
    return _impl_svg_validate(content)


@mcp.tool
def svg_render(
    content: Annotated[str, Field(description="SVG content as a string")],
    output_path: Annotated[str, Field(description="Output PNG file path")],
    width: Annotated[int | None, Field(description="Output width in pixels")] = None,
    height: Annotated[int | None, Field(description="Output height in pixels")] = None,
    scale: Annotated[
        float | None, Field(description="Scale factor for rendering")
    ] = None,
    zoom_x: Annotated[
        float | None, Field(description="Zoom rectangle X coordinate")
    ] = None,
    zoom_y: Annotated[
        float | None, Field(description="Zoom rectangle Y coordinate")
    ] = None,
    zoom_width: Annotated[
        float | None, Field(description="Zoom rectangle width")
    ] = None,
    zoom_height: Annotated[
        float | None, Field(description="Zoom rectangle height")
    ] = None,
) -> dict:
    """Render SVG to PNG with specified parameters.

    This tool renders SVG content to a PNG image file with optional
    dimension, scale, and zoom parameters.

    Args:
        content: SVG content as a string.
        output_path: Path to save the output PNG file.
        width: Output width in pixels (optional).
        height: Output height in pixels (optional).
        scale: Scale factor for rendering (optional).
        zoom_x: X coordinate of zoom rectangle (optional).
        zoom_y: Y coordinate of zoom rectangle (optional).
        zoom_width: Width of zoom rectangle (optional).
        zoom_height: Height of zoom rectangle (optional).

    Returns:
        A dictionary containing:
        - success: Whether rendering succeeded
        - output_path: Path to the output file
        - dimensions: Output image dimensions
        - coordinate_mapping: Mapping between SVG and pixel coordinates
        - error: Error message if rendering failed
    """
    return _impl_svg_render(
        content,
        output_path,
        width,
        height,
        scale,
        zoom_x,
        zoom_y,
        zoom_width,
        zoom_height,
    )


@mcp.tool
def svg_diff(
    content1: Annotated[str, Field(description="First SVG content")],
    content2: Annotated[str, Field(description="Second SVG content")],
    output_path: Annotated[str, Field(description="Output diff image path")],
    mode: Annotated[
        str,
        Field(
            description="Diff visualization mode: overlay, side_by_side, difference, highlight, checkerboard"
        ),
    ] = "overlay",
    color_scheme: Annotated[
        str,
        Field(
            description="Color scheme: default, high_contrast, colorblind_safe, subtle, neon"
        ),
    ] = "default",
    width: Annotated[
        int | None, Field(description="Render width for comparison")
    ] = None,
    height: Annotated[
        int | None, Field(description="Render height for comparison")
    ] = None,
    threshold: Annotated[
        float, Field(description="Pixel difference threshold (0.0 to 1.0)")
    ] = 0.1,
) -> dict:
    """Compare two SVG files visually and produce a diff image.

    This tool renders both SVGs and compares them pixel by pixel,
    generating a visual diff image that highlights the differences.

    Args:
        content1: First SVG content.
        content2: Second SVG content.
        output_path: Path to save the diff image.
        mode: Diff visualization mode (default: "overlay").
        color_scheme: Color scheme for visualization (default: "default").
        width: Render width for comparison (optional).
        height: Render height for comparison (optional).
        threshold: Pixel difference threshold (default: 0.1).

    Returns:
        A dictionary containing:
        - identical: Whether the two SVGs are visually identical
        - diff_pixel_count: Number of pixels that differ
        - diff_percentage: Percentage of pixels that differ
        - diff_image_path: Path to the diff image
        - bounding_boxes: Bounding boxes of changed regions
        - diff_mode_used: Diff visualization mode used
        - color_scheme_used: Color scheme used
    """
    return _impl_svg_diff(
        content1, content2, output_path, mode, color_scheme, width, height, threshold
    )


@mcp.tool
def svg_edit(
    file_path: Annotated[str, Field(description="Path to the SVG file to edit")],
    operation: Annotated[
        str, Field(description="Operation: replace, insert, or delete")
    ],
    content: Annotated[
        str, Field(description="New content for replace/insert operations")
    ] = "",
    line_start: Annotated[int, Field(description="Start line (1-based)")] = 1,
    line_end: Annotated[
        int | None, Field(description="End line for replace/delete (optional)")
    ] = None,
    validate_after: Annotated[bool, Field(description="Validate after edit")] = True,
) -> dict:
    """Edit SVG file with validation feedback.

    This tool allows editing SVG files with line-based operations
    and provides validation feedback after the edit.

    Args:
        file_path: Path to the SVG file to edit.
        operation: Operation type: "replace", "insert", or "delete".
        content: New content for replace/insert operations.
        line_start: Start line number (1-based).
        line_end: End line number for replace/delete (optional).
        validate_after: Whether to validate after edit (default: True).

    Returns:
        A dictionary containing:
        - success: Whether the edit succeeded
        - validation: Validation result if validate_after is True
        - error: Error message if edit failed
    """
    return _impl_svg_edit(
        file_path, operation, content, line_start, line_end, validate_after
    )


# ============================================================================
# MCP Resources
# ============================================================================


@mcp.resource("svg://file/{path}")
def svg_file_resource(path: str) -> str:
    """Access SVG file content as a resource.

    Args:
        path: Path to the SVG file.

    Returns:
        SVG file content as a string.
    """
    return _impl_svg_file_resource(path)


@mcp.resource("svg://preview/{path}")
def svg_preview_resource(path: str) -> str:
    """Get a rendered preview of an SVG file as base64-encoded PNG.

    Args:
        path: Path to the SVG file.

    Returns:
        Base64-encoded PNG data URL or error message.
    """
    return _impl_svg_preview_resource(path)


# ============================================================================
# Server Factory
# ============================================================================


def create_server() -> FastMCP:
    """Create and return the MCP server instance.

    Returns:
        The configured FastMCP server instance.
    """
    return mcp
