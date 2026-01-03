# SVG Linter and Formatter Enhancement Plan for SVG-MCP

**Date:** 30 December 2025
**Author:** AI Assistant
**Status:** Draft

---

## Executive Summary

This document compares the current SVG-MCP project capabilities with the recommended SVG formatter/linter tools (Scour, svglint, SVGO) and proposes enhancements to achieve feature parity or better.

---

## Current SVG-MCP Capabilities

### Validation (`SVGValidator`)
- ✅ XML syntax validation using lxml
- ✅ SVG namespace checking
- ✅ Embedded image detection (base64 data URIs) - **error**
- ✅ Relative image path detection - **error**
- ✅ Deprecated xlink:href attribute detection - **warning**
- ✅ Line number and column reporting for errors
- ✅ Contextual suggestions for fixes
- ✅ SVG metadata extraction (element count, viewBox, dimensions, namespaces)

### Rendering (`SVGRenderer`)
- ✅ SVG to PNG conversion using CairoSVG
- ✅ Custom dimensions (width, height, scale)
- ✅ Zoom rectangle support
- ✅ Coordinate mapping between SVG and pixel coordinates

### Visual Diff (`SVGDiffer`)
- ✅ Pixel-level comparison using pixelmatch
- ✅ Multiple diff modes (overlay, side-by-side, difference, highlight, checkerboard)
- ✅ Multiple color schemes (default, high_contrast, colorblind_safe, subtle, neon)
- ✅ Bounding box detection for changed regions

### Editing (`svg_edit`)
- ✅ Line-based file editing (replace, insert, delete)
- ✅ Post-edit validation

---

## Comparison with External Tools

### Scour (Python SVG Optimizer)

| Feature | Scour | SVG-MCP | Gap |
|---------|-------|---------|-----|
| Precision control (`--set-precision`) | ✅ | ❌ | **Missing** |
| Color simplification (`#RRGGBB` → `#RGB`) | ✅ | ❌ | **Missing** |
| Style to XML attribute conversion | ✅ | ❌ | **Missing** |
| Group collapsing | ✅ | ❌ | **Missing** |
| Group creation for common attributes | ✅ | ❌ | **Missing** |
| Editor data removal (Inkscape, Sodipodi, AI) | ✅ | ❌ | **Missing** |
| Unreferenced defs removal | ✅ | ❌ | **Missing** |
| Renderer workarounds (librsvg) | ✅ | ❌ | **Missing** |
| XML prolog stripping | ✅ | ❌ | **Missing** |
| Title/description/metadata removal | ✅ | ❌ | **Missing** |
| Comment stripping | ✅ | ❌ | **Missing** |
| Raster embedding/disabling | ✅ | ❌ | **Missing** |
| ViewBox creation | ✅ | ❌ | **Missing** |
| Indentation control | ✅ | ❌ | **Missing** |
| ID stripping/shortening | ✅ | ❌ | **Missing** |
| ID protection (lists, prefixes) | ✅ | ❌ | **Missing** |
| Flowtext error detection | ✅ | ❌ | **Missing** |
| Inkscape compatibility | ✅ Built-in | ✅ Uses CairoSVG | Partial |

### svglint (Node.js SVG Linter)

| Feature | svglint | SVG-MCP | Gap |
|---------|---------|---------|-----|
| XML validation | ✅ fast-xml-parser | ✅ lxml | ✅ Equivalent |
| Element rules (`elm`) | ✅ | ❌ | **Missing** |
| Attribute rules (`attr`) | ✅ | ❌ | **Missing** |
| Attribute ordering validation | ✅ | ❌ | **Missing** |
| Attribute whitelisting | ✅ | ❌ | **Missing** |
| Custom rules support | ✅ | ❌ | **Missing** |
| External rules (npm packages) | ✅ | ❌ | **Missing** |
| Pre-commit hooks | ✅ | ❌ | **Missing** |
| CLI interface | ✅ | ✅ | ✅ Equivalent |
| Programmatic API | ✅ | ✅ | ✅ Equivalent |
| Glob ignore patterns | ✅ | ❌ | **Missing** |
| Fixtures for expensive computations | ✅ | ❌ | **Missing** |

### SVGO (Node.js SVG Optimizer)

| Feature | SVGO | SVG-MCP | Gap |
|---------|------|---------|-----|
| Plugin architecture | ✅ | ❌ | **Missing** |
| Multipass optimization | ✅ | ❌ | **Missing** |
| removeDoctype | ✅ | ❌ | **Missing** |
| removeXMLProcInst | ✅ | ❌ | **Missing** |
| removeComments | ✅ | ❌ | **Missing** |
| removeMetadata | ✅ | ❌ | **Missing** |
| removeEditorsNSData | ✅ | ❌ | **Missing** |
| cleanupAttrs | ✅ | ❌ | **Missing** |
| mergeStyles | ✅ | ❌ | **Missing** |
| inlineStyles | ✅ | ❌ | **Missing** |
| minifyStyles | ✅ | ❌ | **Missing** |
| cleanupIds | ✅ | ❌ | **Missing** |
| removeUselessDefs | ✅ | ❌ | **Missing** |
| cleanupNumericValues | ✅ | ❌ | **Missing** |
| convertColors | ✅ | ❌ | **Missing** |
| removeUnknownsAndDefaults | ✅ | ❌ | **Missing** |
| removeNonInheritableGroupAttrs | ✅ | ❌ | **Missing** |
| removeUselessStrokeAndFill | ✅ | ❌ | **Missing** |
| cleanupEnableBackground | ✅ | ❌ | **Missing** |
| removeHiddenElems | ✅ | ❌ | **Missing** |
| removeEmptyText | ✅ | ❌ | **Missing** |
| convertShapeToPath | ✅ | ❌ | **Missing** |
| convertEllipseToCircle | ✅ | ❌ | **Missing** |
| moveElemsAttrsToGroup | ✅ | ❌ | **Missing** |
| moveGroupAttrsToElems | ✅ | ❌ | **Missing** |
| collapseGroups | ✅ | ❌ | **Missing** |
| convertPathData | ✅ | ❌ | **Missing** |
| convertTransform | ✅ | ❌ | **Missing** |
| removeEmptyAttrs | ✅ | ❌ | **Missing** |
| removeEmptyContainers | ✅ | ❌ | **Missing** |
| removeUnusedNS | ✅ | ❌ | **Missing** |
| mergePaths | ✅ | ❌ | **Missing** |
| sortAttrs | ✅ | ❌ | **Missing** |
| sortDefsChildren | ✅ | ❌ | **Missing** |
| removeDesc | ✅ | ❌ | **Missing** |
| Custom plugins | ✅ | ❌ | **Missing** |

---

## Gap Analysis Summary

### SVG-MCP Strengths (Unique Features)
1. **Visual feedback loop** - Rendering and visual diff for AI agents
2. **Coordinate mapping** - SVG ↔ pixel coordinate translation
3. **MCP integration** - Native integration with AI assistants
4. **Embedded image detection** - Specific to AI context window concerns
5. **Relative path warnings** - Inkscape/librsvg compatibility checks

### SVG-MCP Weaknesses (Missing Features)

#### Critical (Required for Parity)
1. **No SVG optimization/formatting** - Cannot reduce file size
2. **No element/attribute linting rules** - Cannot enforce SVG structure
3. **No configurable rule system** - Cannot customize validation

#### Important (Recommended)
4. **No editor metadata cleanup** - Cannot remove Inkscape/AI data
5. **No ID management** - Cannot strip/shorten IDs
6. **No style optimization** - Cannot inline/minify CSS
7. **No path optimization** - Cannot simplify path data
8. **No numeric precision control** - Cannot reduce coordinate precision

#### Nice to Have
9. **No pre-commit hook support** - Cannot integrate with git workflows
10. **No plugin architecture** - Cannot extend with custom optimizations

---

## Recommended Enhancement Strategy

### Option A: Integrate Scour (Recommended for Inkscape Compatibility)

**Rationale:** Scour is already integrated into Inkscape and is written in Python, making it easy to integrate with SVG-MCP.

**Implementation:**
1. Add `scour` as a dependency in `pyproject.toml`
2. Create new `SVGOptimizer` class wrapping Scour
3. Add new MCP tool `svg_optimize` with configurable options
4. Add new MCP tool `svg_lint` with configurable rules

**Pros:**
- Python-native, easy integration
- Inkscape-compatible by design
- Well-documented options
- Lossless by default

**Cons:**
- Fewer optimization plugins than SVGO
- Less active development than SVGO

### Option B: Integrate svglint + Scour (Best of Both Worlds)

**Rationale:** Use svglint for linting rules and Scour for optimization.

**Implementation:**
1. Add `scour` as Python dependency
2. Create subprocess wrapper for `svglint` (Node.js)
3. Create unified `svg_lint` tool that combines both
4. Create `svg_optimize` tool using Scour

**Pros:**
- Best linting capabilities (svglint)
- Best Inkscape compatibility (Scour)
- Pre-commit hook support

**Cons:**
- Requires Node.js runtime for svglint
- More complex dependency management

### Option C: Native Python Implementation (Most Control)

**Rationale:** Implement linting and optimization rules natively in Python.

**Implementation:**
1. Extend `SVGValidator` with configurable linting rules
2. Create new `SVGOptimizer` class with optimization passes
3. Implement plugin architecture for custom rules
4. Port essential Scour/SVGO features

**Pros:**
- Full control over implementation
- No external dependencies
- Optimized for MCP use case

**Cons:**
- Significant development effort
- Risk of reimplementing existing functionality
- Maintenance burden

---

## Proposed Implementation Plan (Option A: Scour Integration)

### Phase 1: Scour Integration (Priority: High)

#### 1.1 Add Scour Dependency
```toml
# pyproject.toml
[tool.poetry.dependencies]
scour = "^0.38.2"
```

#### 1.2 Create SVGOptimizer Class
```python
# SVG_MCP/svg/optimizer.py
from scour import scour

class SVGOptimizer:
    """Optimizes SVG content using Scour."""

    def optimize(
        self,
        content: str,
        *,
        precision: int = 5,
        remove_editor_data: bool = True,
        remove_metadata: bool = False,
        remove_comments: bool = False,
        enable_viewboxing: bool = False,
        shorten_ids: bool = False,
        indent: str = "space",
        # ... more options
    ) -> OptimizeResult:
        """Optimize SVG content with configurable options."""
        pass
```

#### 1.3 Add MCP Tool `svg_optimize`
```python
@mcp.tool
def svg_optimize(
    content: str,
    preset: str = "default",  # "default", "safe", "maximum", "custom"
    # ... options
) -> dict:
    """Optimize SVG content to reduce file size."""
    pass
```

### Phase 2: Enhanced Linting (Priority: Medium)

#### 2.1 Extend SVGValidator with Configurable Rules
```python
class SVGLintRule:
    """Base class for linting rules."""
    pass

class ElementRule(SVGLintRule):
    """Validate element presence/count."""
    pass

class AttributeRule(SVGLintRule):
    """Validate attribute values/presence."""
    pass
```

#### 2.2 Add MCP Tool `svg_lint`
```python
@mcp.tool
def svg_lint(
    content: str,
    rules: dict | None = None,
) -> dict:
    """Lint SVG content with configurable rules."""
    pass
```

### Phase 3: Advanced Features (Priority: Low)

#### 3.1 Pre-commit Hook Support
- Create `.pre-commit-hooks.yaml` for SVG-MCP
- Document integration with pre-commit

#### 3.2 Plugin Architecture
- Design plugin interface for custom rules
- Allow external rule packages

---

## New MCP Tools Specification

### `svg_optimize`

**Purpose:** Optimize SVG content to reduce file size while preserving rendering.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `content` | string | required | SVG content to optimize |
| `preset` | string | "default" | Optimization preset: "safe", "default", "maximum" |
| `precision` | int | 5 | Number of significant digits for coordinates |
| `remove_editor_data` | bool | true | Remove Inkscape/Sodipodi/AI metadata |
| `remove_metadata` | bool | false | Remove `<metadata>` elements |
| `remove_comments` | bool | false | Remove XML comments |
| `remove_titles` | bool | false | Remove `<title>` elements |
| `remove_descriptions` | bool | false | Remove `<desc>` elements |
| `enable_viewboxing` | bool | false | Convert width/height to viewBox |
| `shorten_ids` | bool | false | Shorten element IDs |
| `strip_ids` | bool | false | Remove unreferenced IDs |
| `indent` | string | "space" | Indentation: "none", "space", "tab" |
| `no_line_breaks` | bool | false | Remove line breaks (minify) |

**Returns:**
```json
{
  "success": true,
  "optimized_content": "<svg>...</svg>",
  "original_size": 12345,
  "optimized_size": 8765,
  "reduction_percent": 29.0,
  "validation": { ... }
}
```

### `svg_lint`

**Purpose:** Lint SVG content with configurable rules.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `content` | string | required | SVG content to lint |
| `rules` | object | null | Custom linting rules |
| `preset` | string | "default" | Rule preset: "strict", "default", "relaxed" |

**Rules Object Format:**
```json
{
  "elements": {
    "svg": 1,
    "svg > title": 1,
    "svg > path": [1, 10],
    "script": false
  },
  "attributes": {
    "svg": {
      "xmlns": "http://www.w3.org/2000/svg",
      "viewBox": "/^\\d+ \\d+ \\d+ \\d+$/",
      "whitelist": true,
      "order": true
    }
  }
}
```

**Returns:**
```json
{
  "valid": true,
  "errors": [],
  "warnings": [],
  "info": { ... }
}
```

---

## Presets

### Optimization Presets

#### `safe` (Conservative)
- Keep editor data
- Keep metadata
- Keep comments
- Precision: 8
- No ID changes

#### `default` (Balanced)
- Remove editor data
- Keep metadata
- Keep comments
- Precision: 5
- No ID changes

#### `maximum` (Aggressive)
- Remove editor data
- Remove metadata
- Remove comments
- Remove titles/descriptions
- Precision: 3
- Shorten IDs
- No line breaks

### Linting Presets

#### `relaxed`
- XML validity only
- Namespace warning

#### `default`
- XML validity
- Namespace check
- Embedded image detection
- Relative path detection
- Deprecated xlink:href warning

#### `strict`
- All default rules
- Required viewBox
- Required title
- No inline styles
- Attribute ordering

---

## Migration Path

### Backward Compatibility
- Existing `svg_validate` tool remains unchanged
- New tools are additive, not replacements
- Default behavior matches current validation

### Deprecation Plan
- None required - all changes are additions

---

## Testing Strategy

### Unit Tests
- Test each optimization option independently
- Test linting rules with valid/invalid SVGs
- Test presets produce expected results

### Integration Tests
- Test optimization + validation pipeline
- Test with real-world SVG files (Inkscape, AI, web)

### E2E Tests
- Test MCP tool invocation
- Test with AI agent workflows

---

## Timeline Estimate

| Phase | Effort | Duration |
|-------|--------|----------|
| Phase 1: Scour Integration | Medium | 2-3 days |
| Phase 2: Enhanced Linting | Medium | 2-3 days |
| Phase 3: Advanced Features | Low | 1-2 days |
| Documentation | Low | 1 day |
| **Total** | | **6-9 days** |

---

## Sources Consulted

1. https://github.com/scour-project/scour - Scour GitHub repository
2. https://github.com/scour-project/scour/wiki/Documentation - Scour documentation
3. https://github.com/simple-icons/svglint - svglint GitHub repository
4. https://github.com/svg/svgo - SVGO GitHub repository
5. https://svgo.dev/docs/preset-default/ - SVGO default plugins documentation

---

## Conclusion

SVG-MCP currently provides excellent **validation** and **visual feedback** capabilities but lacks **optimization** and **configurable linting** features that tools like Scour, svglint, and SVGO provide.

The recommended approach is to **integrate Scour** as a Python dependency for optimization capabilities, while extending the existing `SVGValidator` with configurable linting rules inspired by svglint.

This approach provides:
1. **Inkscape compatibility** (Scour is Inkscape's built-in optimizer)
2. **Python-native integration** (no Node.js dependency)
3. **Minimal development effort** (leverage existing tools)
4. **Comprehensive feature set** (optimization + linting)
