"""SVG rendering module using CairoSVG."""

from pathlib import Path

import cairosvg
from lxml import etree  # pyright: ignore[reportAttributeAccessIssue]

from SVG_MCP.models.types import CoordinateMapping, RenderResult, ViewBox


class SVGRenderer:
    """Renders SVG content to raster images (PNG)."""

    def __init__(self) -> None:
        """Initialize the SVG renderer."""
        self._parser = etree.XMLParser(recover=True)

    def render(
        self,
        content: str,
        output_path: Path | str,
        *,
        width: int | None = None,
        height: int | None = None,
        scale: float | None = None,
        zoom_rect: ViewBox | None = None,
    ) -> RenderResult:
        """Render SVG content to a PNG file.

        Args:
            content: SVG content as a string.
            output_path: Path to save the output PNG file.
            width: Output width in pixels (optional).
            height: Output height in pixels (optional).
            scale: Scale factor for rendering (optional).
            zoom_rect: ViewBox to zoom into (optional).

        Returns:
            RenderResult with rendering status and coordinate mapping.
        """
        output_path = Path(output_path)

        # Validate input
        if not content or not content.strip():
            return RenderResult(
                success=False,
                error="Empty SVG content",
            )

        try:
            # Parse SVG to extract viewBox and dimensions
            svg_info = self._extract_svg_info(content)
            if svg_info is None:
                return RenderResult(
                    success=False,
                    error="Failed to parse SVG content",
                )

            original_viewbox, svg_width, svg_height = svg_info

            # Apply zoom rectangle if specified
            if zoom_rect is not None:
                content = self._apply_zoom_rect(content, zoom_rect)
                effective_viewbox = zoom_rect
            else:
                effective_viewbox = original_viewbox

            # Calculate output dimensions
            output_width, output_height = self._calculate_dimensions(
                effective_viewbox, svg_width, svg_height, width, height, scale
            )

            # Create parent directories if needed
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Render using CairoSVG
            png_data = cairosvg.svg2png(
                bytestring=content.encode("utf-8"),
                output_width=output_width,
                output_height=output_height,
            )

            # Save to file
            if png_data is None:
                return RenderResult(
                    success=False,
                    error="CairoSVG returned no data",
                )
            output_path.write_bytes(png_data)

            # Create coordinate mapping
            pixel_bounds = ViewBox(x=0, y=0, width=output_width, height=output_height)

            if effective_viewbox is not None:
                scale_x = output_width / effective_viewbox.width
                scale_y = output_height / effective_viewbox.height
            else:
                scale_x = 1.0
                scale_y = 1.0
                effective_viewbox = ViewBox(
                    x=0, y=0, width=output_width, height=output_height
                )

            coordinate_mapping = CoordinateMapping(
                svg_viewbox=effective_viewbox,
                pixel_bounds=pixel_bounds,
                scale_x=scale_x,
                scale_y=scale_y,
            )

            return RenderResult(
                success=True,
                output_path=str(output_path),
                dimensions=pixel_bounds,
                coordinate_mapping=coordinate_mapping,
            )

        except etree.XMLSyntaxError as e:
            return RenderResult(
                success=False,
                error=f"Invalid SVG syntax: {e}",
            )
        except Exception as e:
            return RenderResult(
                success=False,
                error=f"Rendering failed: {e}",
            )

    def render_file(
        self,
        input_path: Path | str,
        output_path: Path | str,
        *,
        width: int | None = None,
        height: int | None = None,
        scale: float | None = None,
        zoom_rect: ViewBox | None = None,
    ) -> RenderResult:
        """Render SVG file to a PNG file.

        Args:
            input_path: Path to the input SVG file.
            output_path: Path to save the output PNG file.
            width: Output width in pixels (optional).
            height: Output height in pixels (optional).
            scale: Scale factor for rendering (optional).
            zoom_rect: ViewBox to zoom into (optional).

        Returns:
            RenderResult with rendering status and coordinate mapping.
        """
        input_path = Path(input_path)

        if not input_path.exists():
            return RenderResult(
                success=False,
                error=f"Input file not found: {input_path}",
            )

        try:
            content = input_path.read_text(encoding="utf-8")
            return self.render(
                content,
                output_path,
                width=width,
                height=height,
                scale=scale,
                zoom_rect=zoom_rect,
            )
        except UnicodeDecodeError as e:
            return RenderResult(
                success=False,
                error=f"Failed to read file as UTF-8: {e}",
            )
        except OSError as e:
            return RenderResult(
                success=False,
                error=f"Failed to read file: {e}",
            )

    def _extract_svg_info(
        self, content: str
    ) -> tuple[ViewBox | None, float | None, float | None] | None:
        """Extract viewBox and dimensions from SVG content.

        Args:
            content: SVG content as a string.

        Returns:
            Tuple of (viewBox, width, height) or None if parsing fails.
        """
        try:
            root = etree.fromstring(content.encode("utf-8"), parser=self._parser)
        except Exception:
            return None

        # Extract viewBox
        viewbox = None
        viewbox_str = root.get("viewBox")
        if viewbox_str:
            viewbox = self._parse_viewbox(viewbox_str)

        # Extract width and height
        width = self._parse_dimension(root.get("width"))
        height = self._parse_dimension(root.get("height"))

        return viewbox, width, height

    def _parse_viewbox(self, viewbox_str: str | None) -> ViewBox | None:
        """Parse viewBox attribute string.

        Args:
            viewbox_str: viewBox attribute value.

        Returns:
            ViewBox if valid, None otherwise.
        """
        if not viewbox_str:
            return None

        import re

        parts = re.split(r"[\s,]+", viewbox_str.strip())
        if len(parts) != 4:
            return None

        try:
            x, y, width, height = map(float, parts)
            return ViewBox(x=x, y=y, width=width, height=height)
        except ValueError:
            return None

    def _parse_dimension(self, dim_str: str | None) -> float | None:
        """Parse a dimension string (e.g., '100', '100px', '50%').

        Args:
            dim_str: Dimension string.

        Returns:
            Numeric value or None.
        """
        if not dim_str:
            return None

        # Remove common units
        dim_str = dim_str.strip()
        for unit in ["px", "pt", "em", "rem", "cm", "mm", "in"]:
            if dim_str.endswith(unit):
                dim_str = dim_str[: -len(unit)]
                break

        # Handle percentage (return None, as we can't resolve it without context)
        if dim_str.endswith("%"):
            return None

        try:
            return float(dim_str)
        except ValueError:
            return None

    def _calculate_dimensions(
        self,
        viewbox: ViewBox | None,
        svg_width: float | None,
        svg_height: float | None,
        target_width: int | None,
        target_height: int | None,
        scale: float | None,
    ) -> tuple[int, int]:
        """Calculate output dimensions based on various inputs.

        Args:
            viewbox: SVG viewBox.
            svg_width: SVG width attribute.
            svg_height: SVG height attribute.
            target_width: Requested output width.
            target_height: Requested output height.
            scale: Scale factor.

        Returns:
            Tuple of (width, height) in pixels.
        """
        # Determine base dimensions
        if viewbox is not None:
            base_width = viewbox.width
            base_height = viewbox.height
        elif svg_width is not None and svg_height is not None:
            base_width = svg_width
            base_height = svg_height
        else:
            # Default dimensions
            base_width = 100
            base_height = 100

        # Apply scale if specified
        if scale is not None:
            return int(base_width * scale), int(base_height * scale)

        # Apply target dimensions
        if target_width is not None and target_height is not None:
            return target_width, target_height

        if target_width is not None:
            # Calculate height to maintain aspect ratio
            aspect_ratio = base_height / base_width if base_width > 0 else 1
            return target_width, int(target_width * aspect_ratio)

        if target_height is not None:
            # Calculate width to maintain aspect ratio
            aspect_ratio = base_width / base_height if base_height > 0 else 1
            return int(target_height * aspect_ratio), target_height

        # Use base dimensions
        return int(base_width), int(base_height)

    def _apply_zoom_rect(self, content: str, zoom_rect: ViewBox) -> str:
        """Apply a zoom rectangle by modifying the SVG viewBox.

        Args:
            content: SVG content as a string.
            zoom_rect: ViewBox to zoom into.

        Returns:
            Modified SVG content with new viewBox.
        """
        try:
            root = etree.fromstring(content.encode("utf-8"), parser=self._parser)
        except Exception:
            return content

        # Set the new viewBox
        new_viewbox = (
            f"{zoom_rect.x} {zoom_rect.y} {zoom_rect.width} {zoom_rect.height}"
        )
        root.set("viewBox", new_viewbox)

        # Return modified SVG
        return etree.tostring(root, encoding="unicode")
