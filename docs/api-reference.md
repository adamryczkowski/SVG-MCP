# SVG-MCP API Reference

This document provides a complete reference for all MCP tools, resources, and CLI commands provided by SVG-MCP.

## MCP Tools

### svg_validate

Validate SVG syntax and return detailed error information.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `content` | string | Yes | SVG content as a string |

#### Returns

```json
{
  "valid": true,
  "errors": [],
  "warnings": [],
  "info": {
    "element_count": 42,
    "viewbox": {
      "x": 0,
      "y": 0,
      "width": 100,
      "height": 100
    },
    "width": "100",
    "height": "100",
    "has_namespace": true,
    "namespaces": ["http://www.w3.org/2000/svg"]
  }
}
```

#### Error Response

```json
{
  "valid": false,
  "errors": [
    {
      "line": 5,
      "column": 12,
      "message": "error parsing attribute name",
      "context": "  <rect width=\"100\" height=",
      "suggestion": "Check for missing closing quote"
    }
  ],
  "warnings": [],
  "info": null
}
```

#### Example Usage

```python
# MCP client example
result = await client.call_tool("svg_validate", {
    "content": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100" fill="red"/></svg>'
})
```

---

### svg_render

Render SVG to PNG with specified parameters.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `content` | string | Yes | - | SVG content as a string |
| `output_path` | string | Yes | - | Path to save the output PNG file |
| `width` | int | No | null | Output width in pixels |
| `height` | int | No | null | Output height in pixels |
| `scale` | float | No | null | Scale factor for rendering |
| `zoom_x` | float | No | null | X coordinate of zoom rectangle |
| `zoom_y` | float | No | null | Y coordinate of zoom rectangle |
| `zoom_width` | float | No | null | Width of zoom rectangle |
| `zoom_height` | float | No | null | Height of zoom rectangle |

#### Returns

```json
{
  "success": true,
  "output_path": "/path/to/output.png",
  "dimensions": {
    "width": 800,
    "height": 600
  },
  "coordinate_mapping": {
    "svg_viewbox": {
      "x": 0,
      "y": 0,
      "width": 100,
      "height": 100
    },
    "pixel_bounds": {
      "x": 0,
      "y": 0,
      "width": 800,
      "height": 600
    },
    "scale_x": 8.0,
    "scale_y": 6.0
  },
  "error": null
}
```

#### Error Response

```json
{
  "success": false,
  "output_path": null,
  "dimensions": null,
  "coordinate_mapping": null,
  "error": "Failed to render SVG: invalid syntax at line 5"
}
```

#### Zoom Rectangle

To render a specific region of the SVG, provide all four zoom parameters:

```python
result = await client.call_tool("svg_render", {
    "content": svg_content,
    "output_path": "/tmp/zoomed.png",
    "zoom_x": 10,
    "zoom_y": 10,
    "zoom_width": 50,
    "zoom_height": 50,
    "width": 400,
    "height": 400
})
```

---

### svg_diff

Compare two SVG files visually and produce a diff image.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `content1` | string | Yes | - | First SVG content |
| `content2` | string | Yes | - | Second SVG content |
| `output_path` | string | Yes | - | Path to save the diff image |
| `mode` | string | No | "overlay" | Diff visualization mode |
| `color_scheme` | string | No | "default" | Color scheme for visualization |
| `width` | int | No | null | Render width for comparison |
| `height` | int | No | null | Render height for comparison |
| `threshold` | float | No | 0.1 | Pixel difference threshold (0.0 to 1.0) |

#### Diff Modes

| Mode | Description |
|------|-------------|
| `overlay` | Tint and blend both images (default, recommended for AI agents) |
| `side_by_side` | Place both SVGs side by side with highlighted differences |
| `difference` | Show absolute pixel difference with amplification |
| `highlight` | Dimmed base with bright highlights on changes |
| `checkerboard` | Alternating regions from both SVGs |

#### Color Schemes

| Scheme | Description |
|--------|-------------|
| `default` | Cyan/Magenta overlay - high contrast for AI agents |
| `high_contrast` | Maximum contrast - black/white with red highlights |
| `colorblind_safe` | Optimized for deuteranopia/protanopia |
| `subtle` | Subtle differences for minor changes |
| `neon` | Bright neon colors for maximum visibility |

#### Returns

```json
{
  "identical": false,
  "diff_pixel_count": 1234,
  "diff_percentage": 0.15,
  "diff_image_path": "/path/to/diff.png",
  "bounding_boxes": [
    {
      "x": 10,
      "y": 20,
      "width": 50,
      "height": 30,
      "description": "Changed region 1"
    }
  ],
  "diff_mode_used": "overlay",
  "color_scheme_used": "default"
}
```

---

### svg_edit

Edit SVG file with validation feedback.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `file_path` | string | Yes | - | Path to the SVG file to edit |
| `operation` | string | Yes | - | Operation: "replace", "insert", or "delete" |
| `content` | string | No | "" | New content for replace/insert operations |
| `line_start` | int | No | 1 | Start line number (1-based) |
| `line_end` | int | No | null | End line for replace/delete (optional) |
| `validate_after` | bool | No | true | Whether to validate after edit |

#### Operations

| Operation | Description |
|-----------|-------------|
| `replace` | Replace lines from line_start to line_end with content |
| `insert` | Insert content at line_start |
| `delete` | Delete lines from line_start to line_end |

#### Returns

```json
{
  "success": true,
  "validation": {
    "valid": true,
    "errors": [],
    "warnings": [],
    "info": { ... }
  },
  "error": null
}
```

---

## MCP Resources

### svg://file/{path}

Access SVG file content as a resource.

#### Usage

```python
content = await client.read_resource("svg://file/path/to/file.svg")
```

#### Returns

The raw SVG file content as a string.

---

### svg://preview/{path}

Get a rendered preview of an SVG file as base64-encoded PNG.

#### Usage

```python
preview = await client.read_resource("svg://preview/path/to/file.svg")
# Returns: "data:image/png;base64,iVBORw0KGgo..."
```

#### Returns

A data URL containing the base64-encoded PNG preview (256px width).

---

## CLI Commands

### svg-mcp serve

Start the MCP server.

```bash
# Start with stdio transport (default)
svg-mcp serve

# Start with SSE transport
svg-mcp serve --transport sse --port 8080 --host localhost
```

#### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--transport` | stdio | Transport protocol: stdio or sse |
| `--port` | 8080 | Port for SSE transport |
| `--host` | localhost | Host for SSE transport |

---

### svg-mcp validate

Validate an SVG file.

```bash
# Text output (default)
svg-mcp validate input.svg

# JSON output
svg-mcp validate input.svg --format json
```

#### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `SVG_FILE` | Yes | Path to the SVG file to validate |

#### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--format` | text | Output format: text or json |

#### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | SVG is valid |
| 1 | SVG is invalid |
| 2 | File not found or other error |

---

### svg-mcp render

Render SVG to PNG.

```bash
# Basic render
svg-mcp render input.svg output.png

# With dimensions
svg-mcp render input.svg output.png --width 800 --height 600

# With scale
svg-mcp render input.svg output.png --scale 2.0
```

#### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `SVG_FILE` | Yes | Path to the input SVG file |
| `OUTPUT_FILE` | Yes | Path to the output PNG file |

#### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--width` | null | Output width in pixels |
| `--height` | null | Output height in pixels |
| `--scale` | 1.0 | Scale factor |

---

### svg-mcp diff

Compare two SVG files visually.

```bash
# Basic diff
svg-mcp diff file1.svg file2.svg

# With custom output
svg-mcp diff file1.svg file2.svg -o comparison.png

# With mode and color scheme
svg-mcp diff file1.svg file2.svg --mode side_by_side --color-scheme colorblind_safe
```

#### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `SVG1` | Yes | Path to the first SVG file |
| `SVG2` | Yes | Path to the second SVG file |

#### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--output`, `-o` | diff.png | Output diff image path |
| `--threshold` | 0.1 | Diff threshold (0.0 to 1.0) |
| `--mode` | overlay | Diff visualization mode |
| `--color-scheme` | default | Color scheme for visualization |

---

### svg-mcp info

Show information about SVG-MCP.

```bash
svg-mcp info
```

Displays version information, available MCP tools, and resources.

---

## Python API

### SVGValidator

```python
from SVG_MCP.svg.validator import SVGValidator

validator = SVGValidator()

# Validate SVG content
result = validator.validate('<svg xmlns="http://www.w3.org/2000/svg">...</svg>')
print(result.valid)  # True or False
print(result.errors)  # List of ValidationError
print(result.info)  # SVGInfo with element_count, viewbox, etc.

# Validate from file
result = validator.validate_file(Path("input.svg"))
```

### SVGRenderer

```python
from SVG_MCP.svg.renderer import SVGRenderer
from SVG_MCP.models.types import ViewBox

renderer = SVGRenderer()

# Basic render
result = renderer.render(svg_content, "output.png")

# Render with dimensions
result = renderer.render(svg_content, "output.png", width=800, height=600)

# Render with zoom
zoom = ViewBox(x=10, y=10, width=50, height=50)
result = renderer.render(svg_content, "output.png", zoom_rect=zoom)

# Render from file
result = renderer.render_file(Path("input.svg"), Path("output.png"))
```

### SVGDiffer

```python
from SVG_MCP.svg.differ import SVGDiffer

differ = SVGDiffer()

# Basic diff
result = differ.diff(svg1_content, svg2_content, "diff.png")
print(result.identical)  # True or False
print(result.diff_percentage)  # 0.0 to 100.0
print(result.bounding_boxes)  # List of changed regions

# Diff with options
result = differ.diff(
    svg1_content,
    svg2_content,
    "diff.png",
    mode="side_by_side",
    color_scheme="colorblind_safe",
    threshold=0.05
)

# Diff from files
result = differ.diff_files("file1.svg", "file2.svg", "diff.png")
```

---

## Data Types

All data types are Pydantic `BaseModel` classes, providing automatic validation and serialization.

### ValidationResult

```python
from pydantic import BaseModel, Field

class ValidationResult(BaseModel):
    """Result of SVG validation."""
    valid: bool = Field(description="Whether the SVG is valid")
    errors: list[ValidationError] = Field(default_factory=list, description="List of validation errors")
    warnings: list[ValidationError] = Field(default_factory=list, description="List of validation warnings")
    info: SVGInfo | None = Field(default=None, description="SVG metadata if valid")
```

### ValidationError

```python
class ValidationError(BaseModel):
    """Details about a validation error or warning."""
    line: int | None = Field(default=None, description="Line number where error occurred")
    column: int | None = Field(default=None, description="Column number where error occurred")
    message: str = Field(description="Error message")
    context: str | None = Field(default=None, description="Source context around the error")
    suggestion: str | None = Field(default=None, description="Suggested fix")
```

### SVGInfo

```python
class SVGInfo(BaseModel):
    """Metadata extracted from a valid SVG."""
    element_count: int = Field(description="Total number of elements in the SVG")
    viewbox: ViewBox | None = Field(default=None, description="SVG viewBox if present")
    width: str | None = Field(default=None, description="SVG width attribute")
    height: str | None = Field(default=None, description="SVG height attribute")
    has_namespace: bool = Field(description="Whether SVG has proper namespace")
    namespaces: dict[str, str] = Field(default_factory=dict, description="Namespace prefix to URI mapping")
```

### ViewBox

```python
class ViewBox(BaseModel):
    """SVG viewBox coordinates."""
    x: float = Field(description="X coordinate of viewBox origin")
    y: float = Field(description="Y coordinate of viewBox origin")
    width: float = Field(description="Width of viewBox")
    height: float = Field(description="Height of viewBox")
```

### RenderResult

```python
class RenderResult(BaseModel):
    """Result of SVG rendering operation."""
    success: bool = Field(description="Whether rendering succeeded")
    output_path: str | None = Field(default=None, description="Path to output file if successful")
    dimensions: ViewBox | None = Field(default=None, description="Output image dimensions")
    coordinate_mapping: CoordinateMapping | None = Field(default=None, description="SVG to pixel coordinate mapping")
    error: str | None = Field(default=None, description="Error message if failed")
```

### CoordinateMapping

```python
class CoordinateMapping(BaseModel):
    """Mapping between SVG coordinates and pixel coordinates."""
    svg_viewbox: ViewBox = Field(description="SVG viewBox coordinates")
    pixel_bounds: ViewBox = Field(description="Pixel bounds of rendered image")
    scale_x: float = Field(description="Horizontal scale factor")
    scale_y: float = Field(description="Vertical scale factor")
```

### DiffResult

```python
class DiffResult(BaseModel):
    """Result of visual diff comparison."""
    identical: bool = Field(description="Whether the two SVGs are visually identical")
    diff_pixel_count: int = Field(description="Number of differing pixels")
    diff_percentage: float = Field(description="Percentage of pixels that differ")
    diff_image_path: str | None = Field(default=None, description="Path to diff image")
    bounding_boxes: list[BoundingBox] = Field(default_factory=list, description="Regions with changes")
    diff_mode_used: str = Field(description="Diff visualization mode used")
    color_scheme_used: str = Field(description="Color scheme used")
```

### BoundingBox

```python
class BoundingBox(BaseModel):
    """Bounding box for a region of interest."""
    x: int = Field(description="X coordinate of top-left corner")
    y: int = Field(description="Y coordinate of top-left corner")
    width: int = Field(description="Width of bounding box")
    height: int = Field(description="Height of bounding box")
    description: str | None = Field(default=None, description="Description of the region")
```
