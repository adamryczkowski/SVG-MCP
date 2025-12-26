# SVG Syntax Checker

This document describes the SVG validation and syntax checking features provided by SVG-MCP.

## Overview

The SVG Syntax Checker is a comprehensive validation tool built on top of lxml that provides:

- **XML well-formedness checking** - Ensures the SVG is valid XML
- **SVG-specific validation** - Verifies SVG structure and namespace
- **Detailed error reporting** - Line numbers, column positions, context, and suggestions
- **SVG metadata extraction** - Element counts, viewBox, dimensions, namespaces

## Validation Features

### 1. XML Well-Formedness

The checker validates that the SVG content is well-formed XML:

| Check | Description | Example Error |
|-------|-------------|---------------|
| **Tag matching** | Opening and closing tags must match | `<rect>` without `</rect>` or `/>` |
| **Proper nesting** | Elements must be properly nested | `<g><rect></g></rect>` |
| **Attribute quoting** | Attribute values must be quoted | `width=100` instead of `width="100"` |
| **Entity encoding** | Special characters must be escaped | `<` instead of `<` in text |
| **Bracket closure** | All brackets must be closed | `<rect width="100"` missing `>` |

### 2. SVG Root Element Validation

The checker verifies the root element is a valid SVG element:

```xml
<!-- ✅ Valid: Proper SVG root with namespace -->
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  ...
</svg>

<!-- ⚠️ Warning: Missing namespace (still valid but not recommended) -->
<svg viewBox="0 0 100 100">
  ...
</svg>

<!-- ❌ Invalid: Wrong root element -->
<div>
  <svg>...</svg>
</div>
```

### 3. Namespace Validation

The checker validates SVG namespace declarations:

| Namespace | URI | Status |
|-----------|-----|--------|
| SVG (default) | `http://www.w3.org/2000/svg` | Required for full compatibility |
| XLink | `http://www.w3.org/1999/xlink` | Optional, for `xlink:href` |
| Custom | Any valid URI | Allowed |

**Namespace Warnings:**
- Missing SVG namespace generates a warning (not an error)
- The SVG will still be considered valid but may not render correctly in all viewers

### 4. ViewBox Parsing

The checker extracts and validates the viewBox attribute:

```xml
<!-- ✅ Valid viewBox formats -->
<svg viewBox="0 0 100 100">      <!-- Space-separated -->
<svg viewBox="0,0,100,100">      <!-- Comma-separated -->
<svg viewBox="0 0 100 100">      <!-- Mixed whitespace -->

<!-- ❌ Invalid viewBox formats -->
<svg viewBox="0 0 100">          <!-- Missing value -->
<svg viewBox="a b c d">          <!-- Non-numeric values -->
```

**ViewBox Extraction:**
- `x` - X coordinate of the viewBox origin
- `y` - Y coordinate of the viewBox origin
- `width` - Width of the viewBox
- `height` - Height of the viewBox

### 5. Dimension Extraction

The checker extracts width and height attributes:

```xml
<svg width="800" height="600">           <!-- Numeric -->
<svg width="100%" height="100%">         <!-- Percentage -->
<svg width="10cm" height="10cm">         <!-- Units -->
<svg width="auto" height="auto">         <!-- Auto -->
```

**Note:** The checker extracts dimension values as strings without unit conversion.

### 6. Element Counting

The checker counts all elements in the SVG document:

```python
# Example output
{
    "element_count": 42,  # Total elements including root
    ...
}
```

This is useful for:
- Complexity analysis
- Performance estimation
- Comparing SVG versions

## Error Reporting

### Error Structure

Each validation error includes:

```python
class ValidationError:
    line: int | None       # Line number (1-based)
    column: int | None     # Column number (1-based)
    message: str           # Error description
    context: str | None    # Source code context
    suggestion: str | None # Suggested fix
```

### Example Error Output

```json
{
    "valid": false,
    "errors": [
        {
            "line": 5,
            "column": 12,
            "message": "Opening and ending tag mismatch: rect line 5 and g",
            "context": "  </g>",
            "suggestion": "Check that all tags are properly closed and nested"
        }
    ],
    "warnings": [],
    "info": null
}
```

### Smart Suggestions

The checker provides context-aware suggestions based on error patterns:

| Error Pattern | Suggestion |
|---------------|------------|
| Tag mismatch | "Check that all tags are properly closed and nested" |
| Missing `>` or `/>` | "Check for missing closing bracket '>' or self-closing '/>'" |
| Unescaped `<` | "Use `<` instead of `<` in text content" |
| Unescaped `&` | "Use `&` instead of `&` in text content" |
| Attribute value error | "Check that attribute values are properly quoted" |
| Premature end | "Check that all elements are properly closed" |
| Not well-formed | "Check XML syntax: proper nesting, closed tags, quoted attributes" |

## Validation Result

### Success Response

```json
{
    "valid": true,
    "errors": [],
    "warnings": [],
    "info": {
        "element_count": 15,
        "viewbox": {
            "x": 0,
            "y": 0,
            "width": 100,
            "height": 100
        },
        "width": "800",
        "height": "600",
        "has_namespace": true,
        "namespaces": {
            "": "http://www.w3.org/2000/svg",
            "xlink": "http://www.w3.org/1999/xlink"
        }
    }
}
```

### Failure Response

```json
{
    "valid": false,
    "errors": [
        {
            "line": 3,
            "column": 15,
            "message": "Specification mandates value for attribute fill",
            "context": "  <rect fill>",
            "suggestion": "Check that attribute values are properly quoted"
        }
    ],
    "warnings": [],
    "info": null
}
```

### Warning Response (Valid with Warnings)

```json
{
    "valid": true,
    "errors": [],
    "warnings": [
        {
            "line": 1,
            "column": 1,
            "message": "SVG element is missing the standard namespace",
            "suggestion": "Add xmlns=\"http://www.w3.org/2000/svg\" to the svg element"
        }
    ],
    "info": {
        "element_count": 5,
        "has_namespace": false,
        ...
    }
}
```

## Common SVG Errors

### 1. Unclosed Tags

```xml
<!-- ❌ Error: Unclosed rect tag -->
<svg xmlns="http://www.w3.org/2000/svg">
  <rect width="100" height="100"
</svg>

<!-- ✅ Fixed -->
<svg xmlns="http://www.w3.org/2000/svg">
  <rect width="100" height="100"/>
</svg>
```

### 2. Mismatched Tags

```xml
<!-- ❌ Error: g and rect mismatch -->
<svg xmlns="http://www.w3.org/2000/svg">
  <g>
    <rect width="100" height="100"/>
  </rect>
</svg>

<!-- ✅ Fixed -->
<svg xmlns="http://www.w3.org/2000/svg">
  <g>
    <rect width="100" height="100"/>
  </g>
</svg>
```

### 3. Unquoted Attributes

```xml
<!-- ❌ Error: Unquoted attribute value -->
<svg xmlns="http://www.w3.org/2000/svg">
  <rect width=100 height="100"/>
</svg>

<!-- ✅ Fixed -->
<svg xmlns="http://www.w3.org/2000/svg">
  <rect width="100" height="100"/>
</svg>
```

### 4. Unescaped Special Characters

```xml
<!-- ❌ Error: Unescaped < in text -->
<svg xmlns="http://www.w3.org/2000/svg">
  <text>x < y</text>
</svg>

<!-- ✅ Fixed -->
<svg xmlns="http://www.w3.org/2000/svg">
  <text>x < y</text>
</svg>
```

### 5. Invalid XML Declaration

```xml
<!-- ❌ Error: XML declaration must be first -->
 <?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg">
</svg>

<!-- ✅ Fixed -->
<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg">
</svg>
```

### 6. Missing Namespace

```xml
<!-- ⚠️ Warning: Missing namespace -->
<svg viewBox="0 0 100 100">
  <rect width="100" height="100"/>
</svg>

<!-- ✅ Better: With namespace -->
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect width="100" height="100"/>
</svg>
```

## Usage Examples

### Via MCP Tool

```json
// Request
{
    "tool": "svg_validate",
    "arguments": {
        "content": "<svg xmlns='http://www.w3.org/2000/svg'><rect/></svg>"
    }
}

// Response
{
    "valid": true,
    "errors": [],
    "warnings": [],
    "info": {
        "element_count": 2,
        "viewbox": null,
        "width": null,
        "height": null,
        "has_namespace": true,
        "namespaces": {"": "http://www.w3.org/2000/svg"}
    }
}
```

### Via CLI

```bash
# Validate a file
svg-mcp validate input.svg

# Validate with JSON output
svg-mcp validate input.svg --format json

# Validate from stdin
cat input.svg | svg-mcp validate -
```

### Via Python API

```python
from SVG_MCP.svg.validator import SVGValidator

validator = SVGValidator()

# Validate string content
result = validator.validate('<svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>')
print(f"Valid: {result.valid}")
print(f"Element count: {result.info.element_count}")

# Validate file
result = validator.validate_file("input.svg")
if not result.valid:
    for error in result.errors:
        print(f"Line {error.line}: {error.message}")
        if error.suggestion:
            print(f"  Suggestion: {error.suggestion}")
```

## Limitations

### What the Checker Does NOT Validate

| Not Checked | Reason |
|-------------|--------|
| **SVG 1.1/2.0 schema compliance** | Would require XSD validation, adds complexity |
| **Attribute value semantics** | `width="abc"` is syntactically valid XML |
| **CSS validity** | Inline styles are not parsed |
| **Path data syntax** | `d` attribute content not validated |
| **Color format validity** | `fill="not-a-color"` is not detected |
| **Reference validity** | `url(#missing)` references not checked |
| **External resource availability** | External files not fetched |

### Future Enhancements (Planned)

- [ ] SVG element whitelist validation
- [ ] Attribute value type checking (numbers, colors, etc.)
- [ ] Path data syntax validation
- [ ] CSS property validation
- [ ] Reference integrity checking
- [ ] Accessibility attribute validation (aria-*, role)
- [ ] Best practices linting (e.g., missing viewBox)

## Error Codes Reference

| Code | Category | Description |
|------|----------|-------------|
| `XML_SYNTAX` | Parsing | XML is not well-formed |
| `NOT_SVG` | Structure | Root element is not `<svg>` |
| `EMPTY_CONTENT` | Content | SVG content is empty |
| `FILE_NOT_FOUND` | I/O | File does not exist |
| `ENCODING_ERROR` | I/O | File is not valid UTF-8 |
| `READ_ERROR` | I/O | Cannot read file |

## Performance

The validator is designed for fast feedback:

| Operation | Typical Time |
|-----------|--------------|
| Small SVG (<1KB) | <1ms |
| Medium SVG (10KB) | <5ms |
| Large SVG (100KB) | <20ms |
| Very large SVG (1MB) | <100ms |

**Note:** Times are approximate and depend on SVG complexity and system performance.

## Integration with Rendering

The validation result includes information useful for rendering:

```python
result = validator.validate(svg_content)

if result.valid and result.info:
    # Use viewBox for coordinate mapping
    if result.info.viewbox:
        print(f"ViewBox: {result.info.viewbox.width}x{result.info.viewbox.height}")

    # Check dimensions for output sizing
    if result.info.width and result.info.height:
        print(f"Dimensions: {result.info.width}x{result.info.height}")

    # Verify namespace for compatibility
    if not result.info.has_namespace:
        print("Warning: Missing namespace may cause rendering issues")
```

## See Also

- [README.md](../README.md) - Project overview and installation
- [svg-mcp-plan.md](svg-mcp-plan.md) - Development plan and architecture
