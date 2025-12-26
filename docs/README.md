# SVG-MCP Documentation

Welcome to the SVG-MCP documentation. This directory contains detailed documentation for the SVG-MCP server.

## Contents

### [API Reference](api-reference.md)

Complete reference for all MCP tools, resources, CLI commands, and Python API:

- **MCP Tools**: `svg_validate`, `svg_render`, `svg_diff`, `svg_edit`
- **MCP Resources**: `svg://file/{path}`, `svg://preview/{path}`
- **CLI Commands**: `serve`, `validate`, `render`, `diff`, `info`
- **Python API**: `SVGValidator`, `SVGRenderer`, `SVGDiffer`
- **Data Types**: All Pydantic models and dataclasses

### [Development Plan](svg-mcp-plan.md)

The original development plan including:

- Architecture overview
- Module structure
- Test-driven development plan
- Implementation phases
- Visual diff system design

### [SVG Syntax Checker](svg-syntax-checker.md)

Notes on SVG syntax validation and common issues.

## Quick Start

### Installation

```bash
# Clone and setup
git clone https://github.com/your-org/SVG-MCP.git
cd SVG-MCP
just setup

# Verify installation
poetry run svg-mcp --version
```

### Using with MCP Clients

Add to your MCP client configuration:

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

### CLI Usage

```bash
# Validate an SVG
svg-mcp validate input.svg

# Render to PNG
svg-mcp render input.svg output.png --width 800

# Compare two SVGs
svg-mcp diff old.svg new.svg -o diff.png
```

## Architecture Overview

```
SVG-MCP/
├── SVG_MCP/
│   ├── server.py          # MCP server with FastMCP
│   ├── cli.py             # Click-based CLI
│   ├── svg/
│   │   ├── validator.py   # lxml-based validation
│   │   ├── renderer.py    # CairoSVG rendering
│   │   └── differ.py      # Pillow/pixelmatch diff
│   └── models/
│       └── types.py       # Pydantic models
├── tests/
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── fixtures/          # Test SVG files
└── docs/                  # Documentation
```

## Key Features

| Feature | Description |
|---------|-------------|
| **Validation** | Parse and validate SVG with detailed error messages |
| **Rendering** | Convert SVG to PNG with dimensions, scale, and zoom |
| **Visual Diff** | Compare SVGs with multiple visualization modes |
| **Coordinate Mapping** | Map between SVG and pixel coordinates |
| **MCP Integration** | Full MCP server with tools and resources |
| **CLI** | Standalone command-line interface |

## Dependencies

| Library | Version | Purpose |
|---------|---------|---------|
| fastmcp | ≥2.0.0 | MCP server framework |
| cairosvg | ≥2.8.0 | SVG to PNG rendering |
| lxml | ≥6.0.0 | XML/SVG parsing |
| pixelmatch | ≥0.3.0 | Pixel comparison |
| Pillow | ≥12.0.0 | Image manipulation |
| click | ≥8.3.0 | CLI framework |

## Contributing

See the main [README.md](../README.md) for contribution guidelines and the [development plan](svg-mcp-plan.md) for implementation details.
