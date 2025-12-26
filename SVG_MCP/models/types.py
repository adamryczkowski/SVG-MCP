"""Pydantic models for SVG-MCP structured output."""

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field


class ViewBox(BaseModel):
    """SVG viewBox representation."""

    x: float = Field(description="X coordinate of the viewBox origin")
    y: float = Field(description="Y coordinate of the viewBox origin")
    width: float = Field(description="Width of the viewBox")
    height: float = Field(description="Height of the viewBox")


class ValidationError(BaseModel):
    """Represents a single validation error."""

    line: int | None = Field(
        default=None, description="Line number where error occurred"
    )
    column: int | None = Field(
        default=None, description="Column number where error occurred"
    )
    message: str = Field(description="Error message")
    context: str | None = Field(default=None, description="Context around the error")
    suggestion: str | None = Field(
        default=None, description="Suggested fix for the error"
    )


class SVGInfo(BaseModel):
    """Information about an SVG document."""

    element_count: int = Field(description="Total number of elements in the SVG")
    viewbox: ViewBox | None = Field(
        default=None, description="ViewBox of the SVG if present"
    )
    width: str | None = Field(default=None, description="Width attribute of the SVG")
    height: str | None = Field(default=None, description="Height attribute of the SVG")
    has_namespace: bool = Field(description="Whether the SVG has the correct namespace")
    namespaces: dict[str, str] = Field(
        default_factory=dict, description="Namespaces declared in the SVG"
    )


class ValidationResult(BaseModel):
    """Result of SVG validation."""

    valid: bool = Field(description="Whether the SVG is valid")
    errors: list[ValidationError] = Field(
        default_factory=list, description="List of errors found"
    )
    warnings: list[ValidationError] = Field(
        default_factory=list, description="List of warnings found"
    )
    info: SVGInfo | None = Field(
        default=None, description="SVG information if parsing succeeded"
    )


class CoordinateMapping(BaseModel):
    """Mapping between SVG coordinates and pixel coordinates."""

    svg_viewbox: ViewBox = Field(description="The SVG viewBox used for rendering")
    pixel_bounds: ViewBox = Field(description="The pixel bounds of the rendered image")
    scale_x: float = Field(description="Scale factor from SVG to pixels (X axis)")
    scale_y: float = Field(description="Scale factor from SVG to pixels (Y axis)")

    def svg_to_pixel(self, svg_x: float, svg_y: float) -> tuple[float, float]:
        """Convert SVG coordinates to pixel coordinates."""
        pixel_x = (svg_x - self.svg_viewbox.x) * self.scale_x + self.pixel_bounds.x
        pixel_y = (svg_y - self.svg_viewbox.y) * self.scale_y + self.pixel_bounds.y
        return pixel_x, pixel_y

    def pixel_to_svg(self, pixel_x: float, pixel_y: float) -> tuple[float, float]:
        """Convert pixel coordinates to SVG coordinates."""
        svg_x = (pixel_x - self.pixel_bounds.x) / self.scale_x + self.svg_viewbox.x
        svg_y = (pixel_y - self.pixel_bounds.y) / self.scale_y + self.svg_viewbox.y
        return svg_x, svg_y


class RenderResult(BaseModel):
    """Result of SVG rendering."""

    success: bool = Field(description="Whether rendering succeeded")
    output_path: str | None = Field(default=None, description="Path to the output file")
    dimensions: ViewBox | None = Field(
        default=None, description="Dimensions of the output image"
    )
    coordinate_mapping: CoordinateMapping | None = Field(
        default=None, description="Coordinate mapping for the rendered image"
    )
    error: str | None = Field(
        default=None, description="Error message if rendering failed"
    )


class BoundingBox(BaseModel):
    """Bounding box for a changed region in a diff."""

    x: int = Field(description="X coordinate of the bounding box")
    y: int = Field(description="Y coordinate of the bounding box")
    width: int = Field(description="Width of the bounding box")
    height: int = Field(description="Height of the bounding box")
    description: str | None = Field(
        default=None, description="Description of the change"
    )


class DiffResult(BaseModel):
    """Result of visual diff between two SVGs."""

    identical: bool = Field(description="Whether the two SVGs are visually identical")
    diff_pixel_count: int = Field(description="Number of pixels that differ")
    diff_percentage: float = Field(description="Percentage of pixels that differ")
    diff_image_path: str | None = Field(
        default=None, description="Path to the diff image"
    )
    bounding_boxes: list[BoundingBox] = Field(
        default_factory=list, description="Bounding boxes of changed regions"
    )
    diff_mode_used: str = Field(description="Diff visualization mode used")
    color_scheme_used: str = Field(
        description="Color scheme used for diff visualization"
    )


# Using dataclass for DiffColorScheme since it's a configuration object
# that doesn't need Pydantic's validation features
@dataclass
class DiffColorScheme:
    """Configuration for diff visualization colors."""

    name: str
    description: str = ""

    # For overlay mode
    image1_tint: tuple[int, int, int] = (0, 255, 255)  # Cyan
    image2_tint: tuple[int, int, int] = (255, 0, 255)  # Magenta
    unchanged_color: tuple[int, int, int] = (128, 128, 128)  # Gray

    # For highlight mode
    highlight_color: tuple[int, int, int, int] = (255, 255, 0, 200)  # Yellow with alpha
    background_opacity: float = 0.3

    # For difference mode
    diff_amplification: float = 3.0

    # Common
    threshold_color: tuple[int, int, int] = (255, 165, 0)  # Orange
    bounding_box_color: tuple[int, int, int, int] = (255, 0, 0, 255)  # Red
    bounding_box_width: int = 2


# Pre-defined color schemes
COLOR_SCHEMES: dict[str, DiffColorScheme] = {
    "default": DiffColorScheme(
        name="default",
        description="Cyan/Magenta overlay - high contrast for AI agents",
        image1_tint=(0, 255, 255),
        image2_tint=(255, 0, 255),
        unchanged_color=(128, 128, 128),
        highlight_color=(255, 255, 0, 200),
        background_opacity=0.3,
        diff_amplification=3.0,
        threshold_color=(255, 165, 0),
        bounding_box_color=(255, 0, 0, 255),
        bounding_box_width=2,
    ),
    "high_contrast": DiffColorScheme(
        name="high_contrast",
        description="Maximum contrast - black/white with red highlights",
        image1_tint=(0, 0, 0),
        image2_tint=(255, 255, 255),
        unchanged_color=(128, 128, 128),
        highlight_color=(255, 0, 0, 255),
        background_opacity=0.2,
        diff_amplification=5.0,
        threshold_color=(255, 255, 0),
        bounding_box_color=(0, 255, 0, 255),
        bounding_box_width=3,
    ),
    "colorblind_safe": DiffColorScheme(
        name="colorblind_safe",
        description="Optimized for deuteranopia/protanopia",
        image1_tint=(0, 114, 178),
        image2_tint=(230, 159, 0),
        unchanged_color=(128, 128, 128),
        highlight_color=(204, 121, 167, 200),
        background_opacity=0.3,
        diff_amplification=3.0,
        threshold_color=(86, 180, 233),
        bounding_box_color=(0, 158, 115, 255),
        bounding_box_width=2,
    ),
    "subtle": DiffColorScheme(
        name="subtle",
        description="Subtle differences for minor changes",
        image1_tint=(200, 220, 255),
        image2_tint=(255, 220, 200),
        unchanged_color=(240, 240, 240),
        highlight_color=(255, 200, 200, 150),
        background_opacity=0.5,
        diff_amplification=2.0,
        threshold_color=(200, 200, 200),
        bounding_box_color=(150, 150, 150, 200),
        bounding_box_width=1,
    ),
    "neon": DiffColorScheme(
        name="neon",
        description="Bright neon colors for maximum visibility",
        image1_tint=(0, 255, 128),
        image2_tint=(255, 0, 128),
        unchanged_color=(32, 32, 32),
        highlight_color=(255, 255, 0, 255),
        background_opacity=0.2,
        diff_amplification=4.0,
        threshold_color=(0, 255, 255),
        bounding_box_color=(255, 128, 0, 255),
        bounding_box_width=2,
    ),
}


# Diff mode type
DiffMode = Literal["overlay", "side_by_side", "difference", "highlight", "checkerboard"]
