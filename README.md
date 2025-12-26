# SVG-MCP

An MCP (Model Context Protocol) server that enables AI agents to work with SVG files through a quick feedback loop. Provides instant validation, rendering to PNG, and visual diff capabilities.

## What is SVG-MCP?

SVG-MCP is a specialized MCP server designed to help AI agents (like Claude, GPT-4, or other vision-capable models) create, edit, and refine SVG graphics through an iterative feedback loop. The server provides:

- **Instant SVG validation** with detailed error messages and line numbers
- **SVG to PNG rendering** with configurable dimensions and zoom
- **Visual diff comparison** between SVG versions with multiple visualization modes
- **Coordinate mapping** to translate between SVG coordinates and pixel positions

## Capabilities

### ✅ What SVG-MCP Can Do

| Feature | Description |
|---------|-------------|
| **Validate SVG** | Parse and validate SVG syntax, report errors with line numbers and context |
| **Render to PNG** | Convert SVG to PNG with custom dimensions, scale, and background color |
| **Visual Diff** | Compare two SVGs visually with overlay, side-by-side, or highlight modes |
| **Zoom Rendering** | Render specific regions of an SVG for detailed inspection |
| **Coordinate Mapping** | Map pixel coordinates to SVG coordinates and vice versa |
| **Element Counting** | Count and report SVG elements for complexity analysis |

### ❌ What SVG-MCP Cannot Do

| Limitation | Reason |
|------------|--------|
| **Edit SVG directly** | Use your IDE's file editing tools; SVG-MCP validates after edits |
| **Animate SVGs** | SMIL animations are not rendered (static frame only) |
| **Load external resources** | External images/fonts are blocked for security |
| **Convert to other formats** | Only PNG output is supported (no PDF, EPS) |
| **Optimize SVG** | No minification or optimization (planned for future) |

## Installation

### Prerequisites

- Python 3.11+ (managed by Spack or your system)
- Poetry 2.x
- just (command runner)

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/your-org/SVG-MCP.git
cd SVG-MCP

# Initialize development environment
just setup

# Verify installation
poetry run svg-mcp --version
```

### Install as a Package

```bash
# Install from source
pip install .

# Or install in development mode
pip install -e .
```

## Using with Roo Code (VS Code Extension)

### Configuration

Add SVG-MCP to your Roo Code MCP settings. Edit your VS Code settings or the MCP configuration file:

**Option 1: VS Code Settings (settings.json)**

```json
{
  "roo-cline.mcpServers": {
    "svg-mcp": {
      "command": "poetry",
      "args": ["run", "svg-mcp", "serve"],
      "cwd": "/path/to/SVG-MCP"
    }
  }
}
```

**Option 2: MCP Configuration File (~/.config/roo-cline/mcp.json)**

```json
{
  "mcpServers": {
    "svg-mcp": {
      "command": "/path/to/SVG-MCP/.venv/bin/svg-mcp",
      "args": ["serve"],
      "env": {}
    }
  }
}
```

**Option 3: Using pipx (Recommended for Global Install)**

```bash
# Install globally with pipx
pipx install /path/to/SVG-MCP

# Then configure in Roo Code
{
  "mcpServers": {
    "svg-mcp": {
      "command": "svg-mcp",
      "args": ["serve"]
    }
  }
}
```

### Verifying the Connection

After configuring, restart VS Code. You should see "svg-mcp" listed in the MCP servers panel. The following tools will be available:

- `svg_validate` - Validate SVG content
- `svg_render` - Render SVG to PNG
- `svg_diff` - Compare two SVGs visually

## MCP Tools Reference

### svg_validate

Validate SVG syntax and return detailed error information.

```json
// Input
{
  "content": "<svg xmlns='http://www.w3.org/2000/svg'>...</svg>"
}

// Output
{
  "valid": true,
  "errors": [],
  "warnings": [],
  "element_count": 42
}
```

### svg_render

Render SVG to PNG with specified parameters.

```json
// Input
{
  "content": "<svg>...</svg>",
  "output_path": "/tmp/output.png",
  "width": 800,
  "height": 600,
  "scale": 2.0,
  "background_color": "#ffffff"
}

// Output
{
  "success": true,
  "output_path": "/tmp/output.png",
  "dimensions": {"width": 800, "height": 600},
  "coordinate_mapping": {
    "svg_viewbox": {"x": 0, "y": 0, "width": 100, "height": 100},
    "scale_x": 8.0,
    "scale_y": 6.0
  }
}
```

### svg_diff

Compare two SVG files visually.

```json
// Input
{
  "content1": "<svg>...</svg>",
  "content2": "<svg>...</svg>",
  "output_path": "/tmp/diff.png",
  "diff_mode": "overlay",
  "threshold": 0.1
}

// Output
{
  "identical": false,
  "diff_pixel_count": 1234,
  "diff_percentage": 0.15,
  "diff_image_path": "/tmp/diff.png",
  "bounding_boxes": [
    {"x": 10, "y": 20, "width": 50, "height": 30}
  ]
}
```

## Use Cases

### 1. Visual Feedback Loop with Vision-Capable AI

The primary use case for SVG-MCP is enabling a visual feedback loop where an AI model can:

1. **Generate SVG code** based on a description
2. **Validate the SVG** to catch syntax errors immediately
3. **Render to PNG** and view the result
4. **Iterate and refine** based on visual feedback

**Example Workflow:**

```
User: "Create an SVG icon of a house with a red roof"

AI Agent:
1. Generates initial SVG code
2. Calls svg_validate → catches missing xmlns
3. Fixes the error, calls svg_validate → valid
4. Calls svg_render → produces house.png
5. [Vision model analyzes the image]
6. "The roof looks orange, not red. Adjusting..."
7. Modifies fill color, calls svg_render again
8. [Vision model confirms] "The roof is now red"
9. Done!
```

### 2. Iterative SVG Refinement

When creating complex SVGs, the AI can use the diff tool to track changes:

```
1. Create initial version → render as v1.png
2. Make modifications
3. Call svg_diff(v1, v2) → see exactly what changed
4. Verify changes are correct
5. Continue iterating
```

### 3. Debugging SVG Rendering Issues

When an SVG doesn't render as expected:

```
1. Validate SVG → check for syntax errors
2. Render at high resolution → inspect details
3. Use zoom_rect to focus on problem areas
4. Get coordinate mapping → understand scale issues
```

### 4. Batch SVG Processing

For processing multiple SVGs:

```
1. Validate all SVGs in a directory
2. Render thumbnails for preview
3. Compare versions to detect changes
```

## Visual Diff Modes

SVG-MCP supports multiple diff visualization modes:

### Overlay Mode (Default)
- Unchanged areas appear gray
- SVG1-only content appears cyan
- SVG2-only content appears magenta
- Changed areas appear as bright highlights

### Side-by-Side Mode
- Both SVGs rendered next to each other
- Difference regions highlighted with boxes

### Highlight Mode
- Base image shown dimmed
- Changes highlighted in bright colors

### Difference Mode
- Pure pixel difference visualization
- Black = identical, bright = different

## CLI Usage

SVG-MCP also provides a command-line interface:

```bash
# Start MCP server (stdio transport)
svg-mcp serve

# Start with HTTP transport
svg-mcp serve --transport http --port 8080

# Validate an SVG file
svg-mcp validate input.svg

# Render SVG to PNG
svg-mcp render input.svg output.png --width 800 --height 600

# Compare two SVGs
svg-mcp diff old.svg new.svg --output diff.png
```

## Development

### Running Tests

```bash
# Run all tests
just test

# Run with coverage
just test-cov

# Run specific test category
poetry run pytest -m unit
poetry run pytest -m integration
poetry run pytest -m e2e
```

### Code Quality

```bash
# Run all pre-commit hooks
just validate

# Format code
just format

# Type checking
just typecheck
```

### Building

```bash
# Build wheel
just package

# Clean build artifacts
just clean
```

## Project Structure

```
SVG-MCP/
├── SVG_MCP/
│   ├── __init__.py
│   ├── server.py          # MCP server implementation
│   ├── cli.py             # CLI interface
│   ├── svg/
│   │   ├── validator.py   # SVG validation
│   │   ├── renderer.py    # SVG to PNG rendering
│   │   └── differ.py      # Visual diff
│   └── models/
│       └── types.py       # Pydantic models
├── tests/
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   ├── e2e/               # End-to-end tests
│   └── fixtures/          # Test SVG files
├── docs/
│   └── svg-mcp-plan.md    # Development plan
├── pyproject.toml
├── justfile
└── README.md
```

## Dependencies

| Library | Purpose |
|---------|---------|
| mcp | MCP Python SDK |
| cairosvg | SVG to PNG rendering |
| lxml | XML/SVG parsing and validation |
| pixelmatch | Pixel-level image comparison |
| Pillow | Image manipulation |
| click | CLI framework |

## Security Considerations

- **External resources are blocked** by default to prevent SSRF attacks
- **File paths are validated** to prevent directory traversal
- **Content size limits** prevent denial-of-service attacks
- **Rendering is sandboxed** to isolate potentially malicious SVGs

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please read the development plan in `docs/svg-mcp-plan.md` for architecture details and implementation guidelines.
