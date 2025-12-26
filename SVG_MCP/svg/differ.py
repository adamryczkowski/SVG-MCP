"""SVG visual diff module using pixelmatch and PIL."""

from pathlib import Path
from typing import Literal

import numpy as np
from PIL import Image
from pixelmatch.contrib.PIL import pixelmatch as pil_pixelmatch

from SVG_MCP.models.types import (
    BoundingBox,
    COLOR_SCHEMES,
    DiffColorScheme,
    DiffResult,
)
from SVG_MCP.svg.renderer import SVGRenderer


DiffModeType = Literal[
    "overlay", "side_by_side", "difference", "highlight", "checkerboard"
]


class SVGDiffer:
    """Compares two SVG files visually and generates diff images."""

    def __init__(self) -> None:
        """Initialize the SVG differ."""
        self._renderer = SVGRenderer()

    def diff(
        self,
        svg1: str,
        svg2: str,
        output_path: Path | str,
        *,
        mode: DiffModeType = "overlay",
        color_scheme: str | DiffColorScheme = "default",
        width: int | None = None,
        height: int | None = None,
        threshold: float = 0.1,
    ) -> DiffResult:
        """Compare two SVG strings and generate a diff image.

        Args:
            svg1: First SVG content.
            svg2: Second SVG content.
            output_path: Path to save the diff image.
            mode: Diff visualization mode.
            color_scheme: Color scheme name or custom DiffColorScheme.
            width: Output width in pixels.
            height: Output height in pixels.
            threshold: Pixel difference threshold (0.0 to 1.0).

        Returns:
            DiffResult with comparison results.
        """
        output_path = Path(output_path)

        # Get color scheme
        if isinstance(color_scheme, str):
            scheme = COLOR_SCHEMES.get(color_scheme, COLOR_SCHEMES["default"])
            scheme_name = color_scheme if color_scheme in COLOR_SCHEMES else "default"
        else:
            scheme = color_scheme
            scheme_name = scheme.name

        # Render both SVGs to images
        try:
            img1 = self._render_to_image(svg1, width, height)
            img2 = self._render_to_image(svg2, width, height)
        except Exception:
            return DiffResult(
                identical=False,
                diff_pixel_count=0,
                diff_percentage=0.0,
                diff_image_path=None,
                bounding_boxes=[],
                diff_mode_used=mode,
                color_scheme_used=scheme_name,
            )

        if img1 is None or img2 is None:
            return DiffResult(
                identical=False,
                diff_pixel_count=0,
                diff_percentage=0.0,
                diff_image_path=None,
                bounding_boxes=[],
                diff_mode_used=mode,
                color_scheme_used=scheme_name,
            )

        # Ensure images are the same size
        img1, img2 = self._normalize_sizes(img1, img2)

        # Create diff image based on mode
        diff_img, diff_count = self._create_diff_image(
            img1, img2, mode, scheme, threshold
        )

        # Calculate statistics
        total_pixels = img1.width * img1.height
        diff_percentage = (diff_count / total_pixels) * 100 if total_pixels > 0 else 0.0

        # Detect bounding boxes of changed regions
        bounding_boxes = self._detect_bounding_boxes(img1, img2, threshold)

        # Save output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        diff_img.save(output_path, "PNG")

        return DiffResult(
            identical=diff_count == 0,
            diff_pixel_count=diff_count,
            diff_percentage=diff_percentage,
            diff_image_path=str(output_path),
            bounding_boxes=bounding_boxes,
            diff_mode_used=mode,
            color_scheme_used=scheme_name,
        )

    def diff_files(
        self,
        svg1_path: Path | str,
        svg2_path: Path | str,
        output_path: Path | str,
        *,
        mode: DiffModeType = "overlay",
        color_scheme: str | DiffColorScheme = "default",
        width: int | None = None,
        height: int | None = None,
        threshold: float = 0.1,
    ) -> DiffResult:
        """Compare two SVG files and generate a diff image.

        Args:
            svg1_path: Path to first SVG file.
            svg2_path: Path to second SVG file.
            output_path: Path to save the diff image.
            mode: Diff visualization mode.
            color_scheme: Color scheme name or custom DiffColorScheme.
            width: Output width in pixels.
            height: Output height in pixels.
            threshold: Pixel difference threshold (0.0 to 1.0).

        Returns:
            DiffResult with comparison results.
        """
        svg1_path = Path(svg1_path)
        svg2_path = Path(svg2_path)

        # Get color scheme name for error result
        if isinstance(color_scheme, str):
            scheme_name = color_scheme if color_scheme in COLOR_SCHEMES else "default"
        else:
            scheme_name = color_scheme.name

        # Read files
        try:
            if not svg1_path.exists():
                return DiffResult(
                    identical=False,
                    diff_pixel_count=0,
                    diff_percentage=0.0,
                    diff_image_path=None,
                    bounding_boxes=[],
                    diff_mode_used=mode,
                    color_scheme_used=scheme_name,
                )
            if not svg2_path.exists():
                return DiffResult(
                    identical=False,
                    diff_pixel_count=0,
                    diff_percentage=0.0,
                    diff_image_path=None,
                    bounding_boxes=[],
                    diff_mode_used=mode,
                    color_scheme_used=scheme_name,
                )

            svg1 = svg1_path.read_text(encoding="utf-8")
            svg2 = svg2_path.read_text(encoding="utf-8")
        except Exception:
            return DiffResult(
                identical=False,
                diff_pixel_count=0,
                diff_percentage=0.0,
                diff_image_path=None,
                bounding_boxes=[],
                diff_mode_used=mode,
                color_scheme_used=scheme_name,
            )

        return self.diff(
            svg1,
            svg2,
            output_path,
            mode=mode,
            color_scheme=color_scheme,
            width=width,
            height=height,
            threshold=threshold,
        )

    def _render_to_image(
        self, svg: str, width: int | None, height: int | None
    ) -> Image.Image | None:
        """Render SVG to PIL Image.

        Args:
            svg: SVG content.
            width: Output width.
            height: Output height.

        Returns:
            PIL Image or None if rendering fails.
        """
        if not svg or not svg.strip():
            return None

        # Create a temporary buffer for rendering
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".png", delete=True) as tmp:
            tmp_path = Path(tmp.name)
            result = self._renderer.render(svg, tmp_path, width=width, height=height)
            if not result.success:
                return None
            return Image.open(tmp_path).convert("RGBA")

    def _normalize_sizes(
        self, img1: Image.Image, img2: Image.Image
    ) -> tuple[Image.Image, Image.Image]:
        """Ensure both images are the same size.

        Args:
            img1: First image.
            img2: Second image.

        Returns:
            Tuple of resized images.
        """
        if img1.size == img2.size:
            return img1, img2

        # Use the larger dimensions
        max_width = max(img1.width, img2.width)
        max_height = max(img1.height, img2.height)

        # Create new images with white background
        new_img1 = Image.new("RGBA", (max_width, max_height), (255, 255, 255, 255))
        new_img2 = Image.new("RGBA", (max_width, max_height), (255, 255, 255, 255))

        # Paste original images
        new_img1.paste(img1, (0, 0))
        new_img2.paste(img2, (0, 0))

        return new_img1, new_img2

    def _create_diff_image(
        self,
        img1: Image.Image,
        img2: Image.Image,
        mode: DiffModeType,
        scheme: DiffColorScheme,
        threshold: float,
    ) -> tuple[Image.Image, int]:
        """Create diff visualization image.

        Args:
            img1: First image.
            img2: Second image.
            mode: Visualization mode.
            scheme: Color scheme.
            threshold: Difference threshold.

        Returns:
            Tuple of (diff image, diff pixel count).
        """
        if mode == "overlay":
            return self._create_overlay_diff(img1, img2, scheme, threshold)
        elif mode == "side_by_side":
            return self._create_side_by_side_diff(img1, img2, scheme, threshold)
        elif mode == "difference":
            return self._create_difference_diff(img1, img2, scheme, threshold)
        elif mode == "highlight":
            return self._create_highlight_diff(img1, img2, scheme, threshold)
        elif mode == "checkerboard":
            return self._create_checkerboard_diff(img1, img2, scheme, threshold)
        else:
            # Default to overlay
            return self._create_overlay_diff(img1, img2, scheme, threshold)

    def _create_overlay_diff(
        self,
        img1: Image.Image,
        img2: Image.Image,
        scheme: DiffColorScheme,
        threshold: float,
    ) -> tuple[Image.Image, int]:
        """Create overlay diff visualization.

        Args:
            img1: First image.
            img2: Second image.
            scheme: Color scheme.
            threshold: Difference threshold.

        Returns:
            Tuple of (diff image, diff pixel count).
        """
        # Create diff output image
        diff_img = Image.new("RGBA", img1.size)

        # Use pixelmatch for pixel comparison
        diff_count = pil_pixelmatch(
            img1, img2, diff_img, threshold=threshold, alpha=0.1
        )

        return diff_img, diff_count

    def _create_side_by_side_diff(
        self,
        img1: Image.Image,
        img2: Image.Image,
        scheme: DiffColorScheme,
        threshold: float,
    ) -> tuple[Image.Image, int]:
        """Create side-by-side diff visualization.

        Args:
            img1: First image.
            img2: Second image.
            scheme: Color scheme.
            threshold: Difference threshold.

        Returns:
            Tuple of (diff image, diff pixel count).
        """
        # Create a diff image for counting
        diff_temp = Image.new("RGBA", img1.size)
        diff_count = pil_pixelmatch(
            img1, img2, diff_temp, threshold=threshold, alpha=0.1
        )

        # Create side-by-side image
        total_width = img1.width * 2 + 10  # 10px gap
        result = Image.new("RGBA", (total_width, img1.height), (255, 255, 255, 255))

        # Paste images
        result.paste(img1, (0, 0))
        result.paste(img2, (img1.width + 10, 0))

        return result, diff_count

    def _create_difference_diff(
        self,
        img1: Image.Image,
        img2: Image.Image,
        scheme: DiffColorScheme,
        threshold: float,
    ) -> tuple[Image.Image, int]:
        """Create pixel difference visualization.

        Args:
            img1: First image.
            img2: Second image.
            scheme: Color scheme.
            threshold: Difference threshold.

        Returns:
            Tuple of (diff image, diff pixel count).
        """
        # Convert to numpy arrays
        arr1 = np.array(img1, dtype=np.float32)
        arr2 = np.array(img2, dtype=np.float32)

        # Calculate absolute difference
        diff = np.abs(arr1 - arr2)

        # Amplify differences
        diff = np.clip(diff * scheme.diff_amplification, 0, 255).astype(np.uint8)

        # Count different pixels
        diff_mask = np.any(diff > (threshold * 255), axis=2)
        diff_count = int(np.sum(diff_mask))

        # Create result image
        result = Image.fromarray(diff, mode="RGBA")

        return result, diff_count

    def _create_highlight_diff(
        self,
        img1: Image.Image,
        img2: Image.Image,
        scheme: DiffColorScheme,
        threshold: float,
    ) -> tuple[Image.Image, int]:
        """Create highlight diff visualization.

        Args:
            img1: First image.
            img2: Second image.
            scheme: Color scheme.
            threshold: Difference threshold.

        Returns:
            Tuple of (diff image, diff pixel count).
        """
        # Create diff mask
        arr1 = np.array(img1, dtype=np.float32)
        arr2 = np.array(img2, dtype=np.float32)

        diff = np.abs(arr1 - arr2)
        diff_mask = np.any(diff > (threshold * 255), axis=2)
        diff_count = int(np.sum(diff_mask))

        # Create result with img2 as base, dimmed
        result = img2.copy()
        result_arr = np.array(result, dtype=np.float32)

        # Dim the background
        result_arr = result_arr * scheme.background_opacity

        # Highlight differences
        highlight_color = np.array(scheme.highlight_color, dtype=np.float32)
        for y in range(result_arr.shape[0]):
            for x in range(result_arr.shape[1]):
                if diff_mask[y, x]:
                    result_arr[y, x] = highlight_color

        result = Image.fromarray(
            np.clip(result_arr, 0, 255).astype(np.uint8), mode="RGBA"
        )

        return result, diff_count

    def _create_checkerboard_diff(
        self,
        img1: Image.Image,
        img2: Image.Image,
        scheme: DiffColorScheme,
        threshold: float,
    ) -> tuple[Image.Image, int]:
        """Create checkerboard diff visualization.

        Args:
            img1: First image.
            img2: Second image.
            scheme: Color scheme.
            threshold: Difference threshold.

        Returns:
            Tuple of (diff image, diff pixel count).
        """
        # Count differences first
        diff_temp = Image.new("RGBA", img1.size)
        diff_count = pil_pixelmatch(
            img1, img2, diff_temp, threshold=threshold, alpha=0.1
        )

        # Create checkerboard pattern
        arr1 = np.array(img1)
        arr2 = np.array(img2)
        result_arr = np.zeros_like(arr1)

        # Create checkerboard mask (8x8 tiles)
        tile_size = 8
        for y in range(arr1.shape[0]):
            for x in range(arr1.shape[1]):
                tile_x = x // tile_size
                tile_y = y // tile_size
                if (tile_x + tile_y) % 2 == 0:
                    result_arr[y, x] = arr1[y, x]
                else:
                    result_arr[y, x] = arr2[y, x]

        result = Image.fromarray(result_arr, mode="RGBA")

        return result, diff_count

    def _detect_bounding_boxes(
        self,
        img1: Image.Image,
        img2: Image.Image,
        threshold: float,
    ) -> list[BoundingBox]:
        """Detect bounding boxes of changed regions.

        Args:
            img1: First image.
            img2: Second image.
            threshold: Difference threshold.

        Returns:
            List of bounding boxes for changed regions.
        """
        # Convert to numpy arrays
        arr1 = np.array(img1, dtype=np.float32)
        arr2 = np.array(img2, dtype=np.float32)

        # Calculate difference mask
        diff = np.abs(arr1 - arr2)
        diff_mask = np.any(diff > (threshold * 255), axis=2)

        # If no differences, return empty list
        if not np.any(diff_mask):
            return []

        # Find connected components using simple flood fill approach
        # For simplicity, we'll find the overall bounding box of all differences
        rows = np.any(diff_mask, axis=1)
        cols = np.any(diff_mask, axis=0)

        if not np.any(rows) or not np.any(cols):
            return []

        row_indices = np.where(rows)[0]
        col_indices = np.where(cols)[0]

        min_row, max_row = row_indices[0], row_indices[-1]
        min_col, max_col = col_indices[0], col_indices[-1]

        # Create bounding box
        bbox = BoundingBox(
            x=int(min_col),
            y=int(min_row),
            width=int(max_col - min_col + 1),
            height=int(max_row - min_row + 1),
            description="Changed region",
        )

        return [bbox]
