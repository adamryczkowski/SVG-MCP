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
| **Optimize SVG** | Reduce file size with Scour (Inkscape's optimizer) while preserving appearance |
| **Lint SVG** | Check for Inkscape/librsvg compatibility issues, enforce element/attribute rules |

### ❌ What SVG-MCP Cannot Do

| Limitation | Reason |
|------------|--------|
| **Edit SVG directly** | Use your IDE's file editing tools; SVG-MCP validates after edits |
| **Animate SVGs** | SMIL animations are not rendered (static frame only) |
| **Load external resources** | External images/fonts are blocked for security |
| **Convert to other formats** | Only PNG output is supported (no PDF, EPS) |

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

MCP server configurations in Roo Code can be managed at two levels:

- **Global Configuration**: Stored in `mcp_settings.json`, applies across all workspaces
- **Project-level Configuration**: Stored in `.roo/mcp.json` within your project's root directory

### Option 1: Using pipx (Recommended)

Install SVG-MCP globally with pipx, then configure Roo Code to use it:

```bash
# Install globally with pipx
pipx install .

# Or install from a specific path
pipx install /path/to/SVG-MCP
```

Then add the following to your Roo Code MCP settings (click the MCP Servers icon in Roo Code, then "Edit Global MCP" or "Edit Project MCP"):

```json
{
  "mcpServers": {
    "svg-mcp": {
      "command": "svg-mcp",
      "args": ["serve"]
    }
  }
}
```

### Option 2: Using mise (Runtime Version Manager)

If you use [mise](https://mise.jdx.dev/) to manage Python versions:

```json
{
  "mcpServers": {
    "svg-mcp": {
      "command": "mise",
      "args": ["x", "--", "svg-mcp", "serve"]
    }
  }
}
```

### Option 3: Direct Path to Virtual Environment

If you prefer to run from a local development installation:

```json
{
  "mcpServers": {
    "svg-mcp": {
      "command": "/path/to/SVG-MCP/.venv/bin/svg-mcp",
      "args": ["serve"]
    }
  }
}
```

### Option 4: Using Poetry (Development)

For development with Poetry:

```json
{
  "mcpServers": {
    "svg-mcp": {
      "command": "poetry",
      "args": ["run", "svg-mcp", "serve"],
      "cwd": "/path/to/SVG-MCP"
    }
  }
}
```

### Option 5: Shared HTTP Server (Recommended for Multiple Windows)

If you have multiple VS Code windows open, each one spawns its own MCP server process,
which can consume significant CPU (~1.3% per instance). To reduce CPU usage, run a
single shared server that all windows connect to:

**Step 1: Start the shared server**

```bash
# Using just (recommended)
just serve-http

# Or directly with poetry
poetry run svg-mcp serve --transport streamable-http --port 8081

# Or install as a systemd user service for automatic startup
just install-systemd-service
systemctl --user enable svg-mcp
systemctl --user start svg-mcp
```

**Step 2: Configure VS Code to use the shared server**

```json
{
  "mcpServers": {
    "svg-mcp": {
      "type": "streamable-http",
      "url": "http://127.0.0.1:8081/mcp"
    }
  }
}
```

**Benefits:**
- Reduces CPU usage from ~20% (14 instances) to ~1.3% (1 instance)
- Faster startup (server is already running)
- Easier monitoring and management

**Note:** The shared server must be running before VS Code can connect to it.
Use the systemd service for automatic startup on login.

### Configuration Options

Each server configuration supports these parameters:

| Parameter | Description |
|-----------|-------------|
| `command` | The executable to run (e.g., `svg-mcp`, `python`, `poetry`) |
| `args` | Array of arguments to pass to the command |
| `cwd` | Working directory for the server process (optional) |
| `env` | Environment variables for the server process (optional) |
| `alwaysAllow` | Array of tool names to auto-approve (optional) |
| `disabled` | Set to `true` to disable this server (optional) |

### Verifying the Connection

1. Open VS Code with Roo Code extension installed
2. Click the MCP Servers icon (⚡) in the Roo Code panel
3. You should see "svg-mcp" listed with a green status indicator
4. The following tools will be available:
   - `svg_validate` - Validate SVG content
   - `svg_render` - Render SVG to PNG
   - `svg_diff` - Compare two SVGs visually
   - `svg_edit` - Edit SVG files with validation
   - `svg_optimize` - Optimize SVG to reduce file size
   - `svg_lint` - Lint SVG for compatibility issues

### Troubleshooting

If the server doesn't connect:

1. **Check the server is installed**: Run `svg-mcp --version` in your terminal
2. **Check the path**: Ensure the command path is correct for your installation method
3. **Check logs**: Look at the Roo Code output panel for error messages
4. **Restart the server**: Use the restart button next to the server in the MCP settings

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

### svg_optimize

Optimize SVG content to reduce file size using Scour (Inkscape's built-in optimizer).

```json
// Input
{
  "content": "<svg xmlns='http://www.w3.org/2000/svg'>...</svg>",
  "preset": "default",
  "precision": 5,
  "remove_editor_data": true
}

// Output
{
  "success": true,
  "optimized_content": "<svg xmlns='http://www.w3.org/2000/svg'>...</svg>",
  "original_size": 5432,
  "optimized_size": 2156,
  "size_reduction_percent": 60.3,
  "preset_used": "default"
}
```

**Optimization Presets:**

| Preset | Description |
|--------|-------------|
| `safe` | Conservative - preserves all IDs and editor data, high precision |
| `default` | Balanced - removes editor data, standard precision (5 digits) |
| `maximum` | Aggressive - removes everything, low precision, minified output |

**Options:**

| Option | Type | Description |
|--------|------|-------------|
| `precision` | int | Decimal precision for coordinates (1-15) |
| `remove_editor_data` | bool | Remove Inkscape/Sodipodi/Adobe metadata |
| `remove_metadata` | bool | Remove `<metadata>` elements |
| `shorten_ids` | bool | Shorten element IDs to reduce size |
| `indent` | string | Indentation string (e.g., `"  "` or `"\t"`) |

### svg_lint

Lint SVG content for compatibility issues and enforce rules.

```json
// Input
{
  "content": "<svg xmlns='http://www.w3.org/2000/svg'>...</svg>",
  "preset": "default",
  "use_scour": true,
  "use_svglint": true,
  "element_rules": {"svg > title": 1},
  "attribute_rules": [{"rule::selector": "svg", "viewBox": true}]
}

// Output
{
  "valid": true,
  "issues": [
    {
      "severity": "warning",
      "code": "deprecated/xlink-href",
      "message": "Deprecated xlink:href found. SVG 2 uses plain href.",
      "line": 5,
      "suggestion": "Replace xlink:href with href"
    }
  ],
  "error_count": 0,
  "warning_count": 1
}
```

**Lint Presets:**

| Preset | Description |
|--------|-------------|
| `relaxed` | Basic XML validity only |
| `default` | Standard checks + Inkscape compatibility |
| `strict` | All checks + required viewBox, title, accessibility |
| `inkscape` | Focus on Inkscape/librsvg compatibility |

**Scour-based Checks (Python, always available):**

- Flowtext detection (Inkscape-specific, won't render in browsers)
- Namespace issues (Inkscape, Sodipodi, Adobe namespaces)
- Deprecated xlink:href usage
- Embedded base64 images
- Relative paths that may break
- Renderer-specific issues
- Excessive numeric precision

**svglint Checks (Node.js, optional):**

Requires Node.js and svglint. See [Optional: svglint Setup](#optional-svglint-setup).

- Element rules: Enforce element presence/count with CSS selectors
- Attribute rules: Validate attribute values and order
- XML validation

**Element Rules Example:**

```json
{
  "element_rules": {
    "svg": 1,           // Exactly 1 <svg> element
    "svg > title": 1,   // Exactly 1 <title> as direct child
    "svg > path": true, // At least 1 <path>
    "script": false     // No <script> elements allowed
  }
}
```

**Attribute Rules Example:**

```json
{
  "attribute_rules": [
    {
      "rule::selector": "svg",
      "xmlns": "http://www.w3.org/2000/svg",
      "viewBox": true,
      "rule::whitelist": true
    }
  ]
}
```

## Optional: svglint Setup

The `svg_lint` tool can optionally use [svglint](https://github.com/simple-icons/svglint) for advanced element and attribute rules. This requires Node.js.

### Using mise (Recommended)

```bash
# Install Node.js via mise
mise install node@22

# Install svglint globally
npm install -g svglint

# Verify installation
svglint --version
```

### Using System Node.js

```bash
# Install svglint globally
npm install -g svglint

# Or use npx (no global install needed)
npx svglint --version
```

### Graceful Degradation

If Node.js or svglint is not installed:
- The `svg_lint` tool will still work with Scour-based checks
- `element_rules` and `attribute_rules` will be ignored
- A warning will be logged about missing svglint

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

# Optimize an SVG file
svg-mcp optimize input.svg -o output.svg --preset default
svg-mcp optimize input.svg -o output.svg --precision 3 --remove-editor-data

# Lint an SVG file
svg-mcp lint input.svg --preset strict
svg-mcp lint input.svg --preset inkscape
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
│   │   ├── differ.py      # Visual diff
│   │   ├── optimizer.py   # SVG optimization (Scour wrapper)
│   │   ├── linter.py      # Unified SVG linter
│   │   ├── scour_linter.py    # Scour-based compatibility checks
│   │   └── svglint_runner.py  # svglint subprocess wrapper
│   └── models/
│       ├── types.py       # Pydantic models
│       └── lint_types.py  # Lint/optimize result models
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
| scour | SVG optimization and cleanup (Inkscape's optimizer) |

### Optional Dependencies

| Library | Purpose |
|---------|---------|
| svglint (Node.js) | Advanced element/attribute rules enforcement |

## Security Considerations

- **External resources are blocked** by default to prevent SSRF attacks
- **File paths are validated** to prevent directory traversal
- **Content size limits** prevent denial-of-service attacks
- **Rendering is sandboxed** to isolate potentially malicious SVGs

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please read the development plan in `docs/svg-mcp-plan.md` for architecture details and implementation guidelines.
