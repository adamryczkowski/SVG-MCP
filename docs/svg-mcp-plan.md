# SVG-MCP Server Plan

## Development Guidelines (Important Reminders)

> **Note:** These guidelines must be followed throughout the development process.

### Research & Documentation
- **Always do Web research** for tools and libraries before using them - assume they changed substantially since training data cutoff
- **Ask the operator** for missing information not available locally or on the Web - wait for the answer before proceeding
- When doing Web search:
  1. Use browsermcp for web searches
  2. Start with general search (DuckDuckGo/Google) unless certain about a specific URL
  3. Check at least 5 different sources
  4. Provide links to sources actually used
  5. Always follow up links from search engines - don't just look at the search page
  6. If opening a link fails, try again with different means
  7. Use pdf-reader-mcp for PDF files, not browser

### Code & Commands
- **Never execute complex commands** with quoted strings or conditionals directly - use scripts in the `scripts/` folder with accompanying just actions
- Use `git ls-tree --name-only -r $(git rev-parse --abbrev-ref HEAD)` or `fd` to list files first
- Use dedicated tools to edit source files, not command line
- Use `cat --paging=never <file>` (bat is aliased to cat and is interactive by default)
- For Poetry projects, use `poetry run` for commands expecting the project environment
- **Do not commit** to git repository during development
- **Never disarm tests** directly or indirectly (e.g., by adding timeouts)

### Remote Work
- For remote Linux work, use SSH interactive sessions only (`ssh_start_interactive_shell`, `ssh_send_input`, `ssh_read_output`)
- Document remote work in `remote-work-log.md`
- Every remote command must be simple and short - avoid conditionals and nested quoting
- Confirm potentially destructive commands with operator before executing

### Environment
- Local system: Ubuntu 24.04 LTS
- Available tools: `rg`, `fd`, `pipx`, `cookiecutter`, `just`, `poetry`, `pre-commit`, `git`, `bat`, `mise`
- Python version: 3.14.2+ (managed by Spack)

---

## Overview

This document outlines the plan for developing an MCP (Model Context Protocol) server that facilitates AI agents working with SVG files. The server provides a quick feedback loop for SVG editing, rendering, validation, and visual comparison.

**Date:** December 19, 2025

## Goals

1. Enable AI agents to edit SVG files with instant syntax validation feedback
2. Provide quick rendering of SVG files to raster images (PNG)
3. Support visual diff between two SVG files
4. Offer a CLI interface for easy deployment
5. Follow test-driven development (TDD) approach

## Research Summary

### Sources Consulted

1. **LibHunt - Top 23 Python SVG Projects** (https://www.libhunt.com/l/python/topic/svg)
   - Comprehensive list of Python SVG libraries ranked by popularity

2. **CairoSVG GitHub** (https://github.com/Kozea/CairoSVG)
   - Version 2.8.2 (May 2025), Python 3.9+, 887 stars, 29.8k dependents
   - Converts SVG to PDF, EPS, PS, and PNG

3. **MCP Python SDK** (https://github.com/modelcontextprotocol/python-sdk)
   - Official SDK v1.25.0 (Dec 2025), 20.8k stars
   - FastMCP for easy server creation

4. **pixelmatch-py** (https://pypi.org/project/pixelmatch/)
   - Pixel-level image comparison with anti-aliasing detection
   - Perceptual color difference metrics

5. **lxml** (https://lxml.de/validation.html)
   - XML/SVG validation with XSD schema support

### Selected Libraries

| Purpose | Library | Version | Rationale |
|---------|---------|---------|-----------|
| MCP Server | `mcp` | ≥1.25.0 | Official Python SDK with FastMCP |
| SVG Rendering | `cairosvg` | ≥2.8.0 | Mature, widely used, PNG/PDF support |
| SVG Parsing/Validation | `lxml` | ≥5.0.0 | Fast XML parsing, XSD validation |
| Image Comparison | `pixelmatch` | ≥0.3.0 | Perceptual diff, anti-aliasing aware |
| Image Processing | `Pillow` | ≥10.0.0 | Image manipulation for diff output |
| CLI Interface | `click` | ≥8.0.0 | Modern CLI framework |

## Architecture

### Module Structure

```
SVG_MCP/
├── __init__.py
├── core.py              # Core utilities (existing)
├── server.py            # MCP server implementation
├── cli.py               # Click-based CLI interface
├── svg/
│   ├── __init__.py
│   ├── validator.py     # SVG syntax validation
│   ├── renderer.py      # SVG to PNG rendering
│   └── differ.py        # Visual diff between SVGs
└── models/
    ├── __init__.py
    └── types.py          # Pydantic models for structured output
```

### MCP Tools

The server will expose the following tools:

#### 1. `svg_validate`
Validate SVG syntax and return detailed error information.

**Input:**
```json
{
  "content": "string",     // SVG content as string
}
```

**Output:**
```json
{
  "valid": true,
  "errors": [
    {"line":  12,
    "pos": 133,
    "error": "invalid token"}
  ],
  "warnings": [
    {"line":  3,
    "pos": 12,
    "error": "uninitialized variable"},
    {"line":  13,
    "pos": 10,
    "error": "uninitialized variable"}
  ],
  "element_count": 42,
}
```

#### 2. `svg_render`
Render SVG to PNG with specified parameters.

**Input:**
```json
{
  "content": "string",           // SVG content or file path
  "output_path": "string",       // Output PNG file path
  "width": 800,                  // Output width in pixels (optional)
  "height": 600,                 // Output height in pixels (optional)
  "scale": 2.0,                  // Scale factor (optional)
  "zoom_rect": {                 // Zoom to specific area (optional)
    "x": 0, "y": 0,
    "width": 100, "height": 100
  },
  "background_color": "#ffffff"  // Background color (optional)
}
```

**Output:**
```json
{
  "success": true,
  "output_path": "/path/to/output.png",
  "dimensions": {"width": 800, "height": 600},
  "coordinate_mapping": {
    "svg_viewbox": {"x": 0, "y": 0, "width": 100, "height": 100},
    "pixel_bounds": {"x": 0, "y": 0, "width": 800, "height": 600},
    "scale_x": 8.0,
    "scale_y": 6.0
  }
}
```

#### 3. `svg_diff`
Compare two SVG files visually and produce a diff image.

**Input:**
```json
{
  "content1": "string",              // First SVG (content or path)
  "content2": "string",              // Second SVG (content or path)
  "output_path": "string",       // Output diff image path
  "threshold": 0.1,              // Color difference threshold (0-1)
  "include_anti_aliasing": true, // Include AA pixels in diff
  "render_width": 800,           // Render width for comparison
  "render_height": 600,          // Render height for comparison
  "diff_mode": "overlay",        // Diff visualization mode (see below)
  "color_scheme": "default"      // Color scheme name or custom config
}
```

**Output:**
```json
{
  "identical": false,
  "diff_pixel_count": 1234,
  "diff_percentage": 0.15,
  "diff_image_path": "/path/to/diff.png",
  "bounding_boxes": [
    {"x": 10, "y": 20, "width": 50, "height": 30, "description": "Changed region 1"}
  ],
  "diff_mode_used": "overlay",
  "color_scheme_used": "default"
}
```

---

## Visual Diff System Design

### Design Goals

1. **Maximum Clarity for AI Agents**: Differences must be immediately obvious in rendered output
2. **Configurable Color Schemes**: Easy to change visualization without code modifications
3. **Multiple Visualization Modes**: Different modes for different use cases
4. **Perceptual Accuracy**: Account for anti-aliasing and minor rendering differences

### Visualization Modes

The system supports multiple diff visualization modes, each optimized for different scenarios:

#### Mode 1: `overlay` (Default - Recommended for AI Agents)

**Algorithm:**
1. Render both SVGs to RGBA images at the same resolution
2. Convert both images to grayscale (luminance-preserving)
3. Tint Image A with one color (e.g., cyan) and Image B with complementary color (e.g., magenta)
4. Blend the tinted images using screen blending
5. Areas that match appear gray/neutral; differences appear in vivid colors

**Visual Result:**
- **Unchanged areas**: Neutral gray
- **Only in SVG1**: Cyan/blue tint
- **Only in SVG2**: Magenta/red tint
- **Changed areas**: Mix of both colors (appears as bright highlight)

```
┌─────────────────────────────────────────┐
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │  Gray = unchanged
│  ░░░░░░░░░░████████░░░░░░░░░░░░░░░░░░░  │  Cyan = only in SVG1
│  ░░░░░░░░░░████████░░░░░░░░░░░░░░░░░░░  │  Magenta = only in SVG2
│  ░░░░░░░░░░████████░░░░▓▓▓▓░░░░░░░░░░░  │  Bright = changed
│  ░░░░░░░░░░░░░░░░░░░░░░▓▓▓▓░░░░░░░░░░░  │
└─────────────────────────────────────────┘
```

#### Mode 2: `side_by_side`

**Algorithm:**
1. Render both SVGs
2. Place them side by side with a divider
3. Highlight differences with colored rectangles/outlines

**Visual Result:**
```
┌──────────────────┬──────────────────┐
│     SVG 1        │      SVG 2       │
│                  │                  │
│  ┌──────┐        │  ┌──────┐        │
│  │ rect │        │  │ RECT │ ← diff │
│  └──────┘        │  └──────┘        │
│                  │                  │
└──────────────────┴──────────────────┘
```

#### Mode 3: `difference` (Absolute Difference)

**Algorithm:**
1. Render both SVGs
2. Compute per-pixel absolute difference: `|pixel_a - pixel_b|`
3. Amplify differences for visibility
4. Apply threshold to ignore minor differences

**Visual Result:**
- Black = identical
- Bright colors = different (intensity = magnitude of difference)

#### Mode 4: `highlight` (Difference Highlighting)

**Algorithm:**
1. Render both SVGs
2. Use SVG1 as base image (desaturated/dimmed)
3. Overlay bright highlights on changed regions
4. Optionally show SVG2 content in highlight areas

**Visual Result:**
- Dimmed grayscale background showing SVG1
- Bright colored highlights showing what changed
- Optional: SVG2 content visible in highlight areas

#### Mode 5: `checkerboard` (Alternating Regions)

**Algorithm:**
1. Divide image into grid cells
2. Alternate between SVG1 and SVG2 in checkerboard pattern
3. Misaligned edges reveal differences

**Visual Result:**
- Seamless checkerboard = identical
- Visible seams/discontinuities = differences

### Color Scheme Configuration

Color schemes are defined in a configuration structure that can be:
1. Built-in presets (referenced by name)
2. Custom configurations (passed as JSON)

#### Color Scheme Structure

```python
@dataclass
class DiffColorScheme:
    """Configuration for diff visualization colors."""

    name: str
    description: str

    # For overlay mode
    image1_tint: tuple[int, int, int]      # RGB for SVG1 tint
    image2_tint: tuple[int, int, int]      # RGB for SVG2 tint
    unchanged_color: tuple[int, int, int]  # RGB for unchanged areas

    # For highlight mode
    highlight_color: tuple[int, int, int, int]  # RGBA for highlights
    background_opacity: float                    # 0.0-1.0

    # For difference mode
    diff_amplification: float              # Multiplier for difference visibility

    # Common
    threshold_color: tuple[int, int, int]  # Color for threshold boundary
    bounding_box_color: tuple[int, int, int, int]  # RGBA for bbox outlines
    bounding_box_width: int                # Stroke width for bboxes
```

#### Built-in Color Schemes

```python
COLOR_SCHEMES = {
    "default": DiffColorScheme(
        name="default",
        description="Cyan/Magenta overlay - high contrast for AI agents",
        image1_tint=(0, 255, 255),      # Cyan
        image2_tint=(255, 0, 255),      # Magenta
        unchanged_color=(128, 128, 128), # Gray
        highlight_color=(255, 255, 0, 200),  # Yellow with alpha
        background_opacity=0.3,
        diff_amplification=3.0,
        threshold_color=(255, 165, 0),   # Orange
        bounding_box_color=(255, 0, 0, 255),  # Red
        bounding_box_width=2,
    ),

    "high_contrast": DiffColorScheme(
        name="high_contrast",
        description="Maximum contrast - black/white with red highlights",
        image1_tint=(0, 0, 0),          # Black
        image2_tint=(255, 255, 255),    # White
        unchanged_color=(128, 128, 128),
        highlight_color=(255, 0, 0, 255),    # Pure red
        background_opacity=0.2,
        diff_amplification=5.0,
        threshold_color=(255, 255, 0),
        bounding_box_color=(0, 255, 0, 255),  # Green
        bounding_box_width=3,
    ),

    "colorblind_safe": DiffColorScheme(
        name="colorblind_safe",
        description="Optimized for deuteranopia/protanopia",
        image1_tint=(0, 114, 178),      # Blue
        image2_tint=(230, 159, 0),      # Orange
        unchanged_color=(128, 128, 128),
        highlight_color=(204, 121, 167, 200),  # Pink
        background_opacity=0.3,
        diff_amplification=3.0,
        threshold_color=(86, 180, 233),  # Sky blue
        bounding_box_color=(0, 158, 115, 255),  # Teal
        bounding_box_width=2,
    ),

    "subtle": DiffColorScheme(
        name="subtle",
        description="Subtle differences for minor changes",
        image1_tint=(200, 220, 255),    # Light blue
        image2_tint=(255, 220, 200),    # Light orange
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
        image1_tint=(0, 255, 128),      # Neon green
        image2_tint=(255, 0, 128),      # Neon pink
        unchanged_color=(32, 32, 32),   # Dark gray
        highlight_color=(255, 255, 0, 255),  # Neon yellow
        background_opacity=0.2,
        diff_amplification=4.0,
        threshold_color=(0, 255, 255),  # Neon cyan
        bounding_box_color=(255, 128, 0, 255),  # Neon orange
        bounding_box_width=2,
    ),
}
```

#### Custom Color Scheme via API

```json
{
  "diff_mode": "overlay",
  "color_scheme": {
    "name": "custom",
    "image1_tint": [100, 200, 255],
    "image2_tint": [255, 100, 100],
    "unchanged_color": [200, 200, 200],
    "highlight_color": [255, 255, 0, 200],
    "background_opacity": 0.4,
    "diff_amplification": 2.5,
    "bounding_box_color": [255, 0, 0, 255],
    "bounding_box_width": 2
  }
}
```

### Implementation Architecture

```python
# SVG_MCP/svg/differ.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Protocol
from PIL import Image
import numpy as np

class DiffRenderer(Protocol):
    """Protocol for diff rendering strategies."""

    def render_diff(
        self,
        image1: Image.Image,
        image2: Image.Image,
        scheme: DiffColorScheme,
        threshold: float,
    ) -> Image.Image:
        """Render the diff visualization."""
        ...


class OverlayDiffRenderer:
    """Overlay mode: tint and blend both images."""

    def render_diff(
        self,
        image1: Image.Image,
        image2: Image.Image,
        scheme: DiffColorScheme,
        threshold: float,
    ) -> Image.Image:
        # 1. Convert to grayscale (luminance-preserving)
        gray1 = image1.convert('L')
        gray2 = image2.convert('L')

        # 2. Create tinted versions
        tinted1 = self._apply_tint(gray1, scheme.image1_tint)
        tinted2 = self._apply_tint(gray2, scheme.image2_tint)

        # 3. Screen blend
        result = self._screen_blend(tinted1, tinted2)

        # 4. Mark unchanged areas
        diff_mask = self._compute_diff_mask(image1, image2, threshold)
        result = self._apply_unchanged_color(result, diff_mask, scheme.unchanged_color)

        return result

    def _apply_tint(self, gray: Image.Image, tint: tuple[int, int, int]) -> Image.Image:
        """Apply color tint to grayscale image."""
        # Convert grayscale to RGB
        rgb = gray.convert('RGB')
        arr = np.array(rgb, dtype=np.float32)

        # Apply tint: multiply by tint color normalized
        tint_norm = np.array(tint, dtype=np.float32) / 255.0
        arr = arr * tint_norm

        return Image.fromarray(arr.astype(np.uint8))

    def _screen_blend(self, img1: Image.Image, img2: Image.Image) -> Image.Image:
        """Screen blend two images: 1 - (1-a)(1-b)."""
        arr1 = np.array(img1, dtype=np.float32) / 255.0
        arr2 = np.array(img2, dtype=np.float32) / 255.0

        result = 1.0 - (1.0 - arr1) * (1.0 - arr2)
        return Image.fromarray((result * 255).astype(np.uint8))

    def _compute_diff_mask(
        self,
        img1: Image.Image,
        img2: Image.Image,
        threshold: float
    ) -> np.ndarray:
        """Compute boolean mask of different pixels."""
        arr1 = np.array(img1, dtype=np.float32)
        arr2 = np.array(img2, dtype=np.float32)

        # Compute per-pixel difference
        diff = np.abs(arr1 - arr2)

        # Sum across color channels and normalize
        diff_magnitude = np.sum(diff, axis=2) / (255.0 * 3)

        # Apply threshold
        return diff_magnitude > threshold


class DifferenceDiffRenderer:
    """Difference mode: absolute pixel difference with amplification."""

    def render_diff(
        self,
        image1: Image.Image,
        image2: Image.Image,
        scheme: DiffColorScheme,
        threshold: float,
    ) -> Image.Image:
        arr1 = np.array(image1, dtype=np.float32)
        arr2 = np.array(image2, dtype=np.float32)

        # Compute absolute difference
        diff = np.abs(arr1 - arr2)

        # Amplify for visibility
        diff = diff * scheme.diff_amplification
        diff = np.clip(diff, 0, 255)

        # Apply threshold (set below-threshold to black)
        magnitude = np.sum(diff, axis=2) / (255.0 * 3)
        mask = magnitude < threshold
        diff[mask] = 0

        return Image.fromarray(diff.astype(np.uint8))


class HighlightDiffRenderer:
    """Highlight mode: dimmed base with bright highlights on changes."""

    def render_diff(
        self,
        image1: Image.Image,
        image2: Image.Image,
        scheme: DiffColorScheme,
        threshold: float,
    ) -> Image.Image:
        # 1. Create dimmed/desaturated base from image1
        base = self._create_dimmed_base(image1, scheme.background_opacity)

        # 2. Compute diff mask
        diff_mask = self._compute_diff_mask(image1, image2, threshold)

        # 3. Apply highlight color to changed regions
        result = self._apply_highlights(base, diff_mask, scheme.highlight_color)

        return result


class SVGDiffer:
    """Main class for SVG visual comparison."""

    RENDERERS = {
        'overlay': OverlayDiffRenderer,
        'difference': DifferenceDiffRenderer,
        'highlight': HighlightDiffRenderer,
        'side_by_side': SideBySideDiffRenderer,
        'checkerboard': CheckerboardDiffRenderer,
    }

    def __init__(self):
        self.color_schemes = COLOR_SCHEMES.copy()

    def register_color_scheme(self, scheme: DiffColorScheme) -> None:
        """Register a custom color scheme."""
        self.color_schemes[scheme.name] = scheme

    def diff(
        self,
        svg1: str | Path,
        svg2: str | Path,
        output_path: str | Path,
        mode: str = 'overlay',
        color_scheme: str | dict = 'default',
        threshold: float = 0.1,
        render_width: int = 800,
        render_height: int = 600,
    ) -> DiffResult:
        """Compare two SVGs and generate diff visualization."""

        # 1. Render both SVGs to images
        img1 = self._render_svg(svg1, render_width, render_height)
        img2 = self._render_svg(svg2, render_width, render_height)

        # 2. Get color scheme
        scheme = self._get_color_scheme(color_scheme)

        # 3. Get renderer for mode
        renderer = self.RENDERERS[mode]()

        # 4. Generate diff image
        diff_image = renderer.render_diff(img1, img2, scheme, threshold)

        # 5. Compute statistics
        stats = self._compute_diff_stats(img1, img2, threshold)

        # 6. Find bounding boxes of changed regions
        bboxes = self._find_diff_bounding_boxes(img1, img2, threshold)

        # 7. Draw bounding boxes on diff image
        diff_image = self._draw_bounding_boxes(diff_image, bboxes, scheme)

        # 8. Save result
        diff_image.save(output_path)

        return DiffResult(
            identical=stats['diff_pixel_count'] == 0,
            diff_pixel_count=stats['diff_pixel_count'],
            diff_percentage=stats['diff_percentage'],
            diff_image_path=str(output_path),
            bounding_boxes=bboxes,
            diff_mode_used=mode,
            color_scheme_used=scheme.name,
        )
```

### Diff Output Examples

#### Example 1: Minor Position Change

**Scenario:** A rectangle moved 10 pixels to the right

**Overlay Mode Output:**
```
┌─────────────────────────────────────────┐
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │
│  ░░░░██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │  ██ = Cyan (old position)
│  ░░░░██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │
│  ░░░░░░░░░░░░░░▓▓░░░░░░░░░░░░░░░░░░░░░  │  ▓▓ = Magenta (new position)
│  ░░░░░░░░░░░░░░▓▓░░░░░░░░░░░░░░░░░░░░░  │
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │
└─────────────────────────────────────────┘
```

#### Example 2: Color Change

**Scenario:** A circle changed from red to blue

**Overlay Mode Output:**
```
┌─────────────────────────────────────────┐
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │
│  ░░░░░░░░░░░░████████░░░░░░░░░░░░░░░░░  │  Bright overlay where
│  ░░░░░░░░░░████████████░░░░░░░░░░░░░░░  │  colors differ
│  ░░░░░░░░░░████████████░░░░░░░░░░░░░░░  │
│  ░░░░░░░░░░░░████████░░░░░░░░░░░░░░░░░  │
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │
└─────────────────────────────────────────┘
```

### Tests for Visual Diff System

Additional tests for the diff system:

| Test ID | Test Name | Description |
|---------|-----------|-------------|
| D011 | `test_diff_mode_overlay` | Overlay mode produces correct output |
| D012 | `test_diff_mode_difference` | Difference mode produces correct output |
| D013 | `test_diff_mode_highlight` | Highlight mode produces correct output |
| D014 | `test_diff_mode_side_by_side` | Side-by-side mode produces correct output |
| D015 | `test_color_scheme_default` | Default color scheme applies correctly |
| D016 | `test_color_scheme_custom` | Custom color scheme applies correctly |
| D017 | `test_color_scheme_colorblind` | Colorblind-safe scheme is distinguishable |
| D018 | `test_bounding_box_detection` | Bounding boxes correctly identify regions |
| D019 | `test_bounding_box_drawing` | Bounding boxes render correctly |
| D020 | `test_diff_statistics_accuracy` | Diff percentage is accurate |

---

#### 4. `svg_edit` (Enhanced File Edit)
Edit SVG file with validation feedback.

**Input:**
```json
{
  "file_path": "string",
  "operation": "replace" | "insert" | "delete",
  "content": "string",           // New content
  "line_start": 10,              // Start line (1-based)
  "line_end": 15,                // End line (optional, for replace/delete)
  "validate_after": true         // Validate after edit
}
```

**Output:**
```json
{
  "success": true,
  "validation": {
    "valid": true,
    "errors": [],
    "warnings": []
  },
  "preview_render": "/tmp/preview.png"  // Optional quick preview
}
```

### MCP Resources

#### 1. `svg://file/{path}`
Access SVG file content as a resource.

#### 2. `svg://preview/{path}`
Get a rendered preview of an SVG file.

### Additional Features (For Review)

The following additional features are proposed for consideration:

#### 5. `svg_optimize`
Optimize SVG file size using scour or similar tool.

**Rationale:** AI agents often generate verbose SVG code. Optimization can reduce file size by 30-70%.

#### 6. `svg_info`
Extract detailed information about SVG structure.

**Output includes:**
- Element hierarchy
- Used colors and gradients
- Font references
- External resource dependencies
- Accessibility attributes (aria-*, role)

#### 7. `svg_transform`
Apply transformations to SVG elements.

**Operations:**
- Scale, rotate, translate
- Change colors/fills
- Modify stroke properties
- Add/remove elements by selector

#### 8. `svg_to_path`
Convert text and shapes to paths for better compatibility.

**Rationale:** Useful for ensuring SVG renders consistently across platforms.

## CLI Interface

Using Click library for CLI:

```bash
# Start MCP server (stdio transport)
svg-mcp serve

# Start MCP server (HTTP transport)
svg-mcp serve --transport http --port 8080

# Validate SVG file
svg-mcp validate input.svg

# Render SVG to PNG
svg-mcp render input.svg output.png --width 800 --height 600

# Compare two SVG files
svg-mcp diff file1.svg file2.svg --output diff.png

# Show version and info
svg-mcp --version
svg-mcp info
```

### CLI Implementation

```python
# SVG_MCP/cli.py
import click
from .server import create_server

@click.group()
@click.version_option()
def cli():
    """SVG-MCP: MCP server for SVG file operations."""
    pass

@cli.command()
@click.option('--transport', type=click.Choice(['stdio', 'http', 'sse']), default='stdio')
@click.option('--port', default=8080, help='Port for HTTP transport')
@click.option('--host', default='localhost', help='Host for HTTP transport')
def serve(transport, port, host):
    """Start the MCP server."""
    server = create_server()
    if transport == 'stdio':
        server.run()
    else:
        server.run(transport=transport, host=host, port=port)

@cli.command()
@click.argument('svg_file', type=click.Path(exists=True))
@click.option('--format', type=click.Choice(['json', 'text']), default='text')
def validate(svg_file, format):
    """Validate an SVG file."""
    # Implementation
    pass

@cli.command()
@click.argument('svg_file', type=click.Path(exists=True))
@click.argument('output_file', type=click.Path())
@click.option('--width', type=int, help='Output width in pixels')
@click.option('--height', type=int, help='Output height in pixels')
@click.option('--scale', type=float, default=1.0, help='Scale factor')
def render(svg_file, output_file, width, height, scale):
    """Render SVG to PNG."""
    # Implementation
    pass

@cli.command()
@click.argument('svg1', type=click.Path(exists=True))
@click.argument('svg2', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output diff image')
@click.option('--threshold', type=float, default=0.1, help='Diff threshold')
def diff(svg1, svg2, output, threshold):
    """Compare two SVG files visually."""
    # Implementation
    pass
```

## Test-Driven Development Plan

### Test Categories

#### 1. Unit Tests

Located in `tests/unit/`:

```
tests/
├── pytest.ini
├── conftest.py              # Shared fixtures
├── unit/
│   ├── test_validator.py    # SVG validation tests
│   ├── test_renderer.py     # SVG rendering tests
│   ├── test_differ.py       # Visual diff tests
│   └── test_cli.py          # CLI tests
├── integration/
│   ├── test_server.py       # MCP server integration
│   └── test_tools.py        # Tool integration tests
├── e2e/
│   ├── test_mcp_client_workflows.py  # Full MCP client workflows
│   ├── test_cli_workflows.py         # CLI end-to-end workflows
│   └── test_real_world_scenarios.py  # Real-world usage scenarios
└── fixtures/
    ├── valid/               # Valid SVG samples
    ├── invalid/             # Invalid SVG samples
    └── pairs/               # SVG pairs for diff testing
```

### Test List

#### Validator Tests (`test_validator.py`)

| Test ID | Test Name | Description |
|---------|-----------|-------------|
| V001 | `test_valid_svg_minimal` | Validate minimal valid SVG |
| V002 | `test_valid_svg_complex` | Validate complex SVG with all elements |
| V003 | `test_invalid_svg_malformed_xml` | Detect malformed XML |
| V004 | `test_invalid_svg_missing_namespace` | Detect missing SVG namespace |
| V005 | `test_invalid_svg_unknown_element` | Warn on unknown elements |
| V006 | `test_invalid_svg_bad_attribute` | Detect invalid attribute values |
| V007 | `test_validation_error_line_numbers` | Error messages include line numbers |
| V008 | `test_validation_error_context` | Error messages include context |
| V009 | `test_viewbox_extraction` | Extract viewBox correctly |
| V010 | `test_element_count` | Count elements accurately |

#### Renderer Tests (`test_renderer.py`)

| Test ID | Test Name | Description |
|---------|-----------|-------------|
| R001 | `test_render_basic_shapes` | Render basic shapes (rect, circle, etc.) |
| R002 | `test_render_with_dimensions` | Render with specified width/height |
| R003 | `test_render_with_scale` | Render with scale factor |
| R004 | `test_render_zoom_rect` | Render specific zoom rectangle |
| R005 | `test_render_background_color` | Apply background color |
| R006 | `test_render_transparent_background` | Preserve transparency |
| R007 | `test_coordinate_mapping_accuracy` | Verify pixel-to-SVG mapping |
| R008 | `test_render_text_elements` | Render text correctly |
| R009 | `test_render_gradients` | Render gradients |
| R010 | `test_render_filters` | Render SVG filters |
| R011 | `test_render_invalid_svg_error` | Handle invalid SVG gracefully |
| R012 | `test_render_output_formats` | Support PNG output format |

#### Differ Tests (`test_differ.py`)

| Test ID | Test Name | Description |
|---------|-----------|-------------|
| D001 | `test_diff_identical_svgs` | Identical SVGs report 0% diff |
| D002 | `test_diff_completely_different` | Completely different SVGs report ~100% |
| D003 | `test_diff_small_change` | Detect small changes |
| D004 | `test_diff_color_change` | Detect color changes |
| D005 | `test_diff_position_change` | Detect position changes |
| D006 | `test_diff_threshold_sensitivity` | Threshold affects detection |
| D007 | `test_diff_anti_aliasing_handling` | Handle anti-aliasing correctly |
| D008 | `test_diff_output_image` | Generate diff image |
| D009 | `test_diff_bounding_boxes` | Identify changed regions |
| D010 | `test_diff_different_sizes` | Handle different SVG sizes |

#### Server Tests (`test_server.py`)

| Test ID | Test Name | Description |
|---------|-----------|-------------|
| S001 | `test_server_initialization` | Server initializes correctly |
| S002 | `test_server_list_tools` | List all available tools |
| S003 | `test_server_tool_schemas` | Tool schemas are valid |
| S004 | `test_tool_svg_validate` | svg_validate tool works |
| S005 | `test_tool_svg_render` | svg_render tool works |
| S006 | `test_tool_svg_diff` | svg_diff tool works |
| S007 | `test_tool_svg_edit` | svg_edit tool works |
| S008 | `test_resource_svg_file` | svg://file resource works |
| S009 | `test_resource_svg_preview` | svg://preview resource works |
| S010 | `test_error_handling` | Errors are handled gracefully |

#### CLI Tests (`test_cli.py`)

| Test ID | Test Name | Description |
|---------|-----------|-------------|
| C001 | `test_cli_version` | --version shows version |
| C002 | `test_cli_help` | --help shows help |
| C003 | `test_cli_validate_valid` | validate command with valid SVG |
| C004 | `test_cli_validate_invalid` | validate command with invalid SVG |
| C005 | `test_cli_render` | render command works |
| C006 | `test_cli_diff` | diff command works |
| C007 | `test_cli_serve_stdio` | serve command with stdio |

#### End-to-End Tests

End-to-end (e2e) tests validate complete workflows from the perspective of an MCP client
or CLI user. These tests ensure that all components work together correctly in realistic
usage scenarios.

##### E2E Test Structure

```
tests/e2e/
├── test_mcp_client_workflows.py  # Full MCP client workflows
├── test_cli_workflows.py         # CLI end-to-end workflows
└── test_real_world_scenarios.py  # Real-world usage scenarios
```

##### MCP Client Workflow Tests (`test_mcp_client_workflows.py`)

These tests simulate a real MCP client connecting to the server and performing complete workflows.

| Test ID | Test Name | Description |
|---------|-----------|-------------|
| E001 | `test_full_validation_workflow` | Client connects, sends SVG for validation, receives structured response with errors/warnings |
| E002 | `test_full_render_workflow` | Client sends SVG content, receives rendered PNG with coordinate mapping |
| E003 | `test_full_diff_workflow` | Client sends two SVGs, receives diff image and statistics |
| E004 | `test_edit_validate_render_cycle` | Complete edit → validate → render cycle simulating AI agent workflow |
| E005 | `test_iterative_editing_session` | Multiple sequential edits with validation feedback after each |
| E006 | `test_concurrent_tool_calls` | Multiple tool calls in parallel (if supported by transport) |
| E007 | `test_large_svg_handling` | Handle large SVG files (>1MB) through complete workflow |
| E008 | `test_error_recovery_workflow` | Client recovers gracefully from validation errors and continues |
| E009 | `test_resource_access_workflow` | Access SVG files via svg://file/{path} resource |
| E010 | `test_preview_resource_workflow` | Access rendered previews via svg://preview/{path} resource |
| E011 | `test_session_persistence` | State persists correctly across multiple tool calls in a session |
| E012 | `test_transport_stdio` | Complete workflow using stdio transport |
| E013 | `test_transport_http` | Complete workflow using HTTP transport |
| E014 | `test_transport_sse` | Complete workflow using SSE transport |

##### CLI Workflow Tests (`test_cli_workflows.py`)

These tests validate complete CLI workflows from command invocation to output verification.

| Test ID | Test Name | Description |
|---------|-----------|-------------|
| E020 | `test_cli_validate_and_fix_workflow` | Validate SVG, get errors, fix them, re-validate successfully |
| E021 | `test_cli_render_multiple_formats` | Render SVG to PNG with various size/scale options |
| E022 | `test_cli_diff_and_analyze` | Compare two SVGs and verify diff output is meaningful |
| E023 | `test_cli_batch_validation` | Validate multiple SVG files in sequence |
| E024 | `test_cli_pipe_workflow` | Pipe SVG content through stdin to CLI commands |
| E025 | `test_cli_output_formats` | Verify JSON and text output formats for all commands |
| E026 | `test_cli_error_exit_codes` | Verify correct exit codes for success/failure scenarios |
| E027 | `test_cli_serve_and_connect` | Start server via CLI, connect with client, perform operations |
| E028 | `test_cli_help_completeness` | All commands have complete help documentation |
| E029 | `test_cli_version_consistency` | Version matches pyproject.toml version |

##### Real-World Scenario Tests (`test_real_world_scenarios.py`)

These tests simulate realistic AI agent workflows and edge cases encountered in production.

| Test ID | Test Name | Description |
|---------|-----------|-------------|
| E030 | `test_ai_agent_svg_creation` | Simulate AI agent creating SVG from scratch with iterative refinement |
| E031 | `test_ai_agent_svg_modification` | Simulate AI agent modifying existing SVG based on feedback |
| E032 | `test_ai_agent_debugging_workflow` | AI agent receives validation error, interprets it, fixes the issue |
| E033 | `test_complex_svg_with_gradients` | Full workflow with SVG containing gradients, filters, masks |
| E034 | `test_svg_with_embedded_images` | Handle SVG with embedded base64 images |
| E035 | `test_svg_with_text_and_fonts` | Handle SVG with text elements and font references |
| E036 | `test_svg_with_animations` | Handle SVG with SMIL animations (if supported) |
| E037 | `test_svg_with_external_references` | Handle SVG with external resource references (blocked by default) |
| E038 | `test_malformed_input_recovery` | Server handles malformed input gracefully without crashing |
| E039 | `test_unicode_content_handling` | Handle SVG with Unicode text content (emoji, CJK, RTL) |
| E040 | `test_very_deep_nesting` | Handle SVG with deeply nested elements (>50 levels) |
| E041 | `test_many_elements` | Handle SVG with many elements (>10,000) |
| E042 | `test_diff_subtle_changes` | Detect subtle visual changes (1px shifts, slight color changes) |
| E043 | `test_diff_structural_vs_visual` | Distinguish structural changes from visual-only changes |
| E044 | `test_coordinate_mapping_precision` | Verify pixel-to-SVG coordinate mapping is accurate |
| E045 | `test_zoom_and_pan_workflow` | Render specific regions of large SVG with zoom |
| E046 | `test_accessibility_attributes` | Validate and preserve accessibility attributes (aria-*, role) |
| E047 | `test_svg_optimization_workflow` | Validate → Optimize → Re-validate → Render workflow |
| E048 | `test_cross_platform_rendering` | Verify consistent rendering output (deterministic) |
| E049 | `test_memory_usage_large_files` | Memory usage stays within bounds for large files |
| E050 | `test_timeout_handling` | Long operations respect timeout limits |

##### E2E Test Implementation Guidelines

1. **Test Isolation**: Each e2e test should be fully isolated and not depend on state from other tests
2. **Realistic Data**: Use realistic SVG files that represent actual use cases
3. **Deterministic Output**: Rendering tests should verify deterministic output (same input → same output)
4. **Performance Bounds**: Include timing assertions for performance-critical operations
5. **Error Messages**: Verify error messages are actionable and include sufficient context
6. **Cleanup**: All temporary files and resources must be cleaned up after tests

##### E2E Test Fixtures

Additional fixtures for e2e testing:

```
tests/fixtures/
├── e2e/
│   ├── ai_generated/           # SVGs generated by AI agents (realistic examples)
│   │   ├── chart_v1.svg
│   │   ├── chart_v2.svg        # Modified version for diff testing
│   │   ├── diagram.svg
│   │   └── icon_set.svg
│   ├── complex/                # Complex real-world SVGs
│   │   ├── map.svg             # Large SVG with many elements
│   │   ├── infographic.svg     # SVG with text, gradients, images
│   │   └── animation.svg       # SVG with SMIL animations
│   ├── edge_cases/             # Edge case SVGs
│   │   ├── unicode_text.svg    # Unicode content
│   │   ├── deep_nesting.svg    # Deeply nested elements
│   │   ├── many_elements.svg   # Many elements
│   │   └── large_file.svg      # Large file size
│   └── expected_outputs/       # Expected rendering outputs for comparison
│       ├── chart_v1.png
│       ├── diagram.png
│       └── diff_chart_v1_v2.png
```

##### E2E Test Configuration

```python
# tests/e2e/conftest.py

import pytest
from pathlib import Path
import tempfile
import subprocess
import time

@pytest.fixture(scope="session")
def mcp_server():
    """Start MCP server for e2e tests."""
    # Start server in background
    proc = subprocess.Popen(
        ["poetry", "run", "svg-mcp", "serve", "--transport", "http", "--port", "8765"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    # Wait for server to be ready
    time.sleep(2)
    yield {"host": "localhost", "port": 8765, "process": proc}
    # Cleanup
    proc.terminate()
    proc.wait(timeout=5)

@pytest.fixture
def mcp_client(mcp_server):
    """Create MCP client connected to test server."""
    from mcp import Client
    client = Client()
    client.connect(f"http://{mcp_server['host']}:{mcp_server['port']}")
    yield client
    client.disconnect()

@pytest.fixture
def temp_workspace():
    """Create temporary workspace for e2e tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def e2e_fixtures():
    """Path to e2e test fixtures."""
    return Path(__file__).parent.parent / "fixtures" / "e2e"
```


### Test Fixtures

#### Valid SVG Samples

```xml
<!-- fixtures/valid/minimal.svg -->
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect width="100" height="100" fill="red"/>
</svg>
```

```xml
<!-- fixtures/valid/complex.svg -->
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <defs>
    <linearGradient id="grad1">
      <stop offset="0%" stop-color="red"/>
      <stop offset="100%" stop-color="blue"/>
    </linearGradient>
  </defs>
  <circle cx="100" cy="100" r="80" fill="url(#grad1)"/>
  <text x="100" y="100" text-anchor="middle">Hello</text>
</svg>
```

#### Invalid SVG Samples

```xml
<!-- fixtures/invalid/malformed.svg -->
<svg xmlns="http://www.w3.org/2000/svg">
  <rect width="100" height="100"
</svg>
```

```xml
<!-- fixtures/invalid/bad_attribute.svg -->
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect width="abc" height="100" fill="red"/>
</svg>
```

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1)
- [ ] Set up project dependencies in pyproject.toml
- [ ] Implement SVG validator module
- [ ] Write validator unit tests
- [ ] Create test fixtures

### Phase 2: Rendering (Week 2)
- [ ] Implement SVG renderer module
- [ ] Add coordinate mapping logic
- [ ] Write renderer unit tests
- [ ] Test with various SVG features

### Phase 3: Visual Diff (Week 3)
- [ ] Implement visual diff module
- [ ] Add bounding box detection
- [ ] Write differ unit tests
- [ ] Create diff pair fixtures

### Phase 4: MCP Server (Week 4)
- [ ] Implement MCP server with FastMCP
- [ ] Register all tools
- [ ] Implement resources
- [ ] Write integration tests

### Phase 5: CLI & Polish (Week 5)
- [ ] Implement Click CLI
- [ ] Add documentation
- [ ] Performance optimization
- [ ] Final testing and bug fixes

### Phase 6: End-to-End Testing (Week 6) ✅ COMPLETED
- [x] Set up e2e test infrastructure (fixtures, conftest.py)
- [x] Implement MCP client workflow tests
- [x] Implement CLI workflow tests
- [x] Implement real-world scenario tests
- [x] Create e2e test fixtures (AI-generated SVGs, complex SVGs, edge cases)
- [x] Verify all transports work correctly (stdio, HTTP, SSE)
- [x] Performance and memory usage validation

## Dependencies Update

Add to `pyproject.toml`:

```toml
[project]
dependencies = [
    "mcp>=1.25.0",
    "cairosvg>=2.8.0",
    "lxml>=5.0.0",
    "pixelmatch>=0.3.0",
    "Pillow>=10.0.0",
    "click>=8.0.0",
]

[project.scripts]
svg-mcp = "SVG_MCP.cli:cli"
```

## Integration with Existing Template

The implementation will integrate with the existing project structure:

1. **justfile**: Add new recipes for running the server
   ```makefile
   # Run MCP server
   serve:
       poetry run svg-mcp serve

   # Run MCP server in development mode
   dev:
       poetry run mcp dev SVG_MCP/server.py
   ```

2. **pre-commit**: Existing hooks will validate code quality

3. **pytest**: Tests will use existing pytest configuration with additional markers:
   ```ini
   [tool.pytest.ini_options]
   markers = [
       "unit: Unit tests",
       "integration: Integration tests",
        "e2e: End-to-end tests",
       "slow: Slow tests (rendering, etc.)",
   ]
   ```

4. **coverage**: Maintain coverage requirements for new code

## Error Handling Strategy

All tools will return structured errors that are easy for AI agents to understand:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid SVG: Malformed XML at line 5",
    "details": {
      "line": 5,
      "column": 12,
      "context": "  <rect width=\"100\" height=",
      "suggestion": "Missing closing quote for 'height' attribute"
    }
  }
}
```

## Performance Considerations

1. **Caching**: Cache rendered previews for unchanged SVGs
2. **Lazy Loading**: Load CairoSVG only when rendering is needed
3. **Streaming**: Support streaming for large SVG files
4. **Parallel Processing**: Use async for I/O-bound operations

## Security Considerations

1. **Path Validation**: Validate file paths to prevent directory traversal
2. **Content Size Limits**: Limit SVG content size to prevent DoS
3. **External Resource Blocking**: Block external resource loading by default
4. **Sandbox Rendering**: Render in isolated environment

## Open Questions for Review

1. Should we support SVG animation preview (SMIL)?
2. Should we add support for converting SVG to other vector formats (PDF, EPS)?
3. What is the maximum SVG file size we should support?
4. Should we implement a caching layer for rendered previews?
5. Should we add support for SVG sprites and symbol libraries?

---

*This plan is subject to revision based on feedback and implementation discoveries.*
