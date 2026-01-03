# SVG Linter and Formatter Implementation Plan

> **Note:** This plan includes Node.js provisioning for svglint support.
> **Recommended approach:** Use Spack for Python + mise for Node.js (Option C - Hybrid).
> This avoids long Node.js build times while maintaining Python version control.

**Date:** 30 December 2025
**Option:** B - Best of Both Worlds (Scour + svglint + Scour-as-Linter)
**Status:** Implementation Plan

---

## Overview

This implementation plan integrates three complementary approaches:

1. **Scour** (Python) - SVG optimization with Inkscape compatibility
2. **svglint** (Node.js) - Configurable SVG linting rules
3. **Scour-as-Linter** (Python) - Use Scour's safe mode to detect Inkscape compatibility issues

The key insight is that Scour can be run in "safe mode" (no modifications) to **detect** issues that would cause problems in Inkscape/librsvg, without actually modifying the file. This provides a Python-native Inkscape compatibility checker.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         SVG-MCP Server                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │ svg_validate │  │ svg_optimize │  │      svg_lint            │  │
│  │   (existing) │  │    (new)     │  │       (new)              │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────────┘  │
│         │                 │                      │                  │
│         ▼                 ▼                      ▼                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │ SVGValidator │  │ SVGOptimizer │  │      SVGLinter           │  │
│  │   (lxml)     │  │   (Scour)    │  │  (Scour + svglint)       │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘  │
│                                              │                      │
│                           ┌──────────────────┼──────────────────┐  │
│                           ▼                  ▼                  ▼  │
│                    ┌────────────┐    ┌────────────┐    ┌──────────┐│
│                    │ScourLinter │    │ svglint    │    │ Custom   ││
│                    │(Inkscape)  │    │ (Node.js)  │    │ Rules    ││
│                    └────────────┘    └────────────┘    └──────────┘│
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Scour-as-Linter (ScourLinter)

The key innovation is using Scour in "dry-run" mode to detect issues:

```python
class ScourLinter:
    """Use Scour to detect Inkscape compatibility issues."""

    def lint(self, content: str) -> list[LintIssue]:
        """
        Run Scour in safe mode and compare output.

        If Scour would make changes, those changes indicate
        potential compatibility issues.
        """
        issues = []

        # Run Scour with safe options (minimal changes)
        safe_output = scour.scourString(content, options={
            'set_precision': 8,  # High precision (lossless)
            'disable_simplify_colors': True,
            'disable_style_to_xml': True,
            'disable_group_collapsing': True,
            'keep_editor_data': True,
            'keep_unreferenced_defs': True,
            'renderer_workaround': True,  # Apply librsvg fixes
        })

        # Detect specific issues by analyzing what Scour would change
        issues.extend(self._detect_flowtext(content))
        issues.extend(self._detect_renderer_issues(content, safe_output))
        issues.extend(self._detect_namespace_issues(content))
        issues.extend(self._detect_precision_issues(content))

        return issues

    def _detect_flowtext(self, content: str) -> list[LintIssue]:
        """Detect non-standard flowtext (Inkscape-specific, not rendered by browsers)."""
        if '<flowRoot' in content or '<flowPara' in content:
            return [LintIssue(
                severity='error',
                code='inkscape/flowtext',
                message='Non-standard flowtext detected. Will not render in browsers or librsvg.',
                suggestion='Convert flowtext to regular text in Inkscape: Text → Convert to Text',
            )]
        return []

    def _detect_renderer_issues(self, content: str, safe_output: str) -> list[LintIssue]:
        """Detect issues that Scour's renderer workarounds would fix."""
        issues = []

        # Check for librsvg-specific issues
        # (Scour applies workarounds for these)
        if content != safe_output:
            # Analyze the diff to identify specific issues
            pass

        return issues
```

### 2. svglint Integration

svglint runs as a subprocess (Node.js) with a Python wrapper:

```python
class SvglintRunner:
    """Run svglint as a subprocess."""

    def __init__(self, config_path: str | None = None):
        self.config_path = config_path
        self._check_svglint_installed()

    def _check_svglint_installed(self) -> None:
        """Verify svglint is available."""
        result = subprocess.run(
            ['npx', 'svglint', '--version'],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError("svglint not installed. Run: npm install -g svglint")

    def lint(self, content: str, rules: dict | None = None) -> list[LintIssue]:
        """Run svglint on SVG content."""
        # Write content to temp file
        with tempfile.NamedTemporaryFile(suffix='.svg', delete=False) as f:
            f.write(content.encode('utf-8'))
            temp_path = f.name

        try:
            cmd = ['npx', 'svglint', temp_path]
            if self.config_path:
                cmd.extend(['--config', self.config_path])

            result = subprocess.run(cmd, capture_output=True, text=True)
            return self._parse_output(result.stdout, result.stderr)
        finally:
            os.unlink(temp_path)
```

### 3. Unified SVGLinter

Combines all linting approaches:

```python
class SVGLinter:
    """Unified SVG linter combining multiple backends."""

    def __init__(self):
        self.scour_linter = ScourLinter()
        self.svglint_runner = SvglintRunner() if self._svglint_available() else None
        self.custom_rules: list[LintRule] = []

    def lint(
        self,
        content: str,
        *,
        use_scour: bool = True,
        use_svglint: bool = True,
        use_custom: bool = True,
        svglint_rules: dict | None = None,
    ) -> LintResult:
        """
        Lint SVG content using all available backends.

        Args:
            content: SVG content to lint
            use_scour: Run Scour-based Inkscape compatibility checks
            use_svglint: Run svglint rules (requires Node.js)
            use_custom: Run custom Python rules
            svglint_rules: Custom svglint rules configuration

        Returns:
            LintResult with all issues found
        """
        issues = []

        # 1. Scour-based Inkscape compatibility checks
        if use_scour:
            issues.extend(self.scour_linter.lint(content))

        # 2. svglint rules (if available)
        if use_svglint and self.svglint_runner:
            issues.extend(self.svglint_runner.lint(content, svglint_rules))

        # 3. Custom Python rules
        if use_custom:
            for rule in self.custom_rules:
                issues.extend(rule.check(content))

        return LintResult(
            valid=not any(i.severity == 'error' for i in issues),
            issues=issues,
        )
```

---

## New Data Models

```python
# SVG_MCP/models/lint_types.py

from enum import Enum
from pydantic import BaseModel, Field


class LintSeverity(str, Enum):
    """Severity level for lint issues."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class LintIssue(BaseModel):
    """A single lint issue found in an SVG."""

    severity: LintSeverity = Field(description="Issue severity")
    code: str = Field(description="Issue code (e.g., 'inkscape/flowtext')")
    message: str = Field(description="Human-readable description")
    line: int | None = Field(default=None, description="Line number if available")
    column: int | None = Field(default=None, description="Column number if available")
    suggestion: str | None = Field(default=None, description="Suggested fix")
    source: str = Field(default="unknown", description="Linter that found this issue")


class LintResult(BaseModel):
    """Result of linting an SVG."""

    valid: bool = Field(description="True if no errors (warnings allowed)")
    issues: list[LintIssue] = Field(default_factory=list, description="All issues found")

    @property
    def errors(self) -> list[LintIssue]:
        return [i for i in self.issues if i.severity == LintSeverity.ERROR]

    @property
    def warnings(self) -> list[LintIssue]:
        return [i for i in self.issues if i.severity == LintSeverity.WARNING]


class OptimizeResult(BaseModel):
    """Result of optimizing an SVG."""

    success: bool = Field(description="Whether optimization succeeded")
    optimized_content: str | None = Field(default=None, description="Optimized SVG content")
    original_size: int = Field(description="Original file size in bytes")
    optimized_size: int | None = Field(default=None, description="Optimized file size in bytes")
    reduction_percent: float | None = Field(default=None, description="Size reduction percentage")
    error: str | None = Field(default=None, description="Error message if failed")
    validation: dict | None = Field(default=None, description="Validation result after optimization")
```

---

## MCP Tools

### `svg_lint` Tool

```python
@mcp.tool
def svg_lint(
    content: Annotated[str, Field(description="SVG content to lint")],
    preset: Annotated[str, Field(description="Lint preset: 'strict', 'default', 'relaxed', 'inkscape'")] = "default",
    use_scour: Annotated[bool, Field(description="Run Scour-based Inkscape compatibility checks")] = True,
    use_svglint: Annotated[bool, Field(description="Run svglint rules (requires Node.js)")] = True,
    element_rules: Annotated[dict | None, Field(description="Custom element rules")] = None,
    attribute_rules: Annotated[dict | None, Field(description="Custom attribute rules")] = None,
) -> dict:
    """Lint SVG content with configurable rules.

    This tool combines multiple linting backends:
    1. Scour-based Inkscape/librsvg compatibility checks
    2. svglint configurable element/attribute rules
    3. Built-in SVG-MCP validation rules

    Presets:
    - 'relaxed': Basic XML validity only
    - 'default': Standard checks + Inkscape compatibility
    - 'strict': All checks + required viewBox, title, etc.
    - 'inkscape': Focus on Inkscape/librsvg compatibility

    Args:
        content: SVG content to lint
        preset: Lint preset to use
        use_scour: Enable Scour-based Inkscape checks
        use_svglint: Enable svglint rules (requires Node.js)
        element_rules: Custom element presence/count rules
        attribute_rules: Custom attribute value/order rules

    Returns:
        A dictionary containing:
        - valid: Whether the SVG passed linting (no errors)
        - issues: List of all issues found
        - errors: Count of errors
        - warnings: Count of warnings
    """
    return _impl_svg_lint(
        content, preset, use_scour, use_svglint, element_rules, attribute_rules
    )
```

### `svg_optimize` Tool

```python
@mcp.tool
def svg_optimize(
    content: Annotated[str, Field(description="SVG content to optimize")],
    preset: Annotated[str, Field(description="Optimization preset: 'safe', 'default', 'maximum'")] = "default",
    precision: Annotated[int, Field(description="Coordinate precision (1-8)")] = 5,
    remove_editor_data: Annotated[bool, Field(description="Remove Inkscape/Sodipodi/AI metadata")] = True,
    remove_metadata: Annotated[bool, Field(description="Remove <metadata> elements")] = False,
    remove_comments: Annotated[bool, Field(description="Remove XML comments")] = False,
    remove_titles: Annotated[bool, Field(description="Remove <title> elements")] = False,
    remove_descriptions: Annotated[bool, Field(description="Remove <desc> elements")] = False,
    enable_viewboxing: Annotated[bool, Field(description="Convert width/height to viewBox")] = False,
    shorten_ids: Annotated[bool, Field(description="Shorten element IDs")] = False,
    strip_ids: Annotated[bool, Field(description="Remove unreferenced IDs")] = False,
    indent: Annotated[str, Field(description="Indentation: 'none', 'space', 'tab'")] = "space",
    no_line_breaks: Annotated[bool, Field(description="Remove line breaks (minify)")] = False,
    validate_after: Annotated[bool, Field(description="Validate after optimization")] = True,
) -> dict:
    """Optimize SVG content to reduce file size.

    Uses Scour (Inkscape's built-in optimizer) for safe, lossless optimization.

    Presets:
    - 'safe': Conservative - keeps editor data, high precision
    - 'default': Balanced - removes editor data, standard precision
    - 'maximum': Aggressive - removes everything, low precision, minified

    Args:
        content: SVG content to optimize
        preset: Optimization preset (overridden by explicit options)
        precision: Number of significant digits for coordinates (1-8)
        remove_editor_data: Remove Inkscape/Sodipodi/Adobe Illustrator metadata
        remove_metadata: Remove <metadata> elements
        remove_comments: Remove XML comments
        remove_titles: Remove <title> elements
        remove_descriptions: Remove <desc> elements
        enable_viewboxing: Convert width/height to viewBox
        shorten_ids: Shorten element IDs to reduce size
        strip_ids: Remove unreferenced IDs
        indent: Indentation style
        no_line_breaks: Remove line breaks for minification
        validate_after: Run validation on optimized output

    Returns:
        A dictionary containing:
        - success: Whether optimization succeeded
        - optimized_content: The optimized SVG content
        - original_size: Original file size in bytes
        - optimized_size: Optimized file size in bytes
        - reduction_percent: Size reduction percentage
        - validation: Validation result if validate_after is True
    """
    return _impl_svg_optimize(
        content, preset, precision, remove_editor_data, remove_metadata,
        remove_comments, remove_titles, remove_descriptions, enable_viewboxing,
        shorten_ids, strip_ids, indent, no_line_breaks, validate_after
    )
```

---

## Lint Presets

### `relaxed`
```python
PRESET_RELAXED = {
    'use_scour': False,
    'use_svglint': False,
    'use_custom': True,
    'rules': {
        'xml_valid': True,
        'namespace_warning': True,
    }
}
```

### `default`
```python
PRESET_DEFAULT = {
    'use_scour': True,
    'use_svglint': True,
    'use_custom': True,
    'rules': {
        'xml_valid': True,
        'namespace_required': True,
        'embedded_images': 'error',
        'relative_paths': 'error',
        'deprecated_xlink': 'warning',
        'flowtext': 'error',
    }
}
```

### `strict`
```python
PRESET_STRICT = {
    'use_scour': True,
    'use_svglint': True,
    'use_custom': True,
    'rules': {
        'xml_valid': True,
        'namespace_required': True,
        'viewbox_required': True,
        'title_required': True,
        'embedded_images': 'error',
        'relative_paths': 'error',
        'deprecated_xlink': 'error',
        'flowtext': 'error',
        'inline_styles': 'warning',
        'attribute_order': True,
    }
}
```

### `inkscape`
```python
PRESET_INKSCAPE = {
    'use_scour': True,
    'use_svglint': False,
    'use_custom': True,
    'rules': {
        'xml_valid': True,
        'flowtext': 'error',
        'renderer_workarounds': True,
        'librsvg_compatibility': True,
    }
}
```

---

## Optimization Presets

### `safe`
```python
OPTIMIZE_SAFE = {
    'precision': 8,
    'remove_editor_data': False,
    'remove_metadata': False,
    'remove_comments': False,
    'remove_titles': False,
    'remove_descriptions': False,
    'enable_viewboxing': False,
    'shorten_ids': False,
    'strip_ids': False,
    'indent': 'space',
    'no_line_breaks': False,
}
```

### `default`
```python
OPTIMIZE_DEFAULT = {
    'precision': 5,
    'remove_editor_data': True,
    'remove_metadata': False,
    'remove_comments': False,
    'remove_titles': False,
    'remove_descriptions': False,
    'enable_viewboxing': False,
    'shorten_ids': False,
    'strip_ids': False,
    'indent': 'space',
    'no_line_breaks': False,
}
```

### `maximum`
```python
OPTIMIZE_MAXIMUM = {
    'precision': 3,
    'remove_editor_data': True,
    'remove_metadata': True,
    'remove_comments': True,
    'remove_titles': True,
    'remove_descriptions': True,
    'enable_viewboxing': True,
    'shorten_ids': True,
    'strip_ids': True,
    'indent': 'none',
    'no_line_breaks': True,
}
```

---

## File Structure

```
SVG_MCP/
├── __init__.py
├── server.py                    # Add new tools
├── cli.py                       # Add new CLI commands
├── models/
│   ├── __init__.py
│   ├── types.py                 # Existing types
│   └── lint_types.py            # NEW: Lint-specific types
├── svg/
│   ├── __init__.py
│   ├── validator.py             # Existing validator
│   ├── renderer.py              # Existing renderer
│   ├── differ.py                # Existing differ
│   ├── utils.py                 # Existing utils
│   ├── optimizer.py             # NEW: Scour wrapper
│   ├── linter.py                # NEW: Unified linter
│   ├── scour_linter.py          # NEW: Scour-as-linter
│   └── svglint_runner.py        # NEW: svglint subprocess wrapper
└── presets/
    ├── __init__.py
    ├── lint_presets.py          # NEW: Lint presets
    └── optimize_presets.py      # NEW: Optimization presets
```

---

## Dependencies

### Python Dependencies (pyproject.toml)

```toml
[tool.poetry.dependencies]
python = "^3.11"
# Existing dependencies...
scour = "^0.38.2"  # NEW: SVG optimizer
```

### Optional Node.js Dependencies

For svglint support (optional), Node.js must be available. See the **Node.js Provisioning** section below for details on how to set up Node.js using Spack.

Once Node.js is available:
```bash
npm install -g svglint
```

The system will gracefully degrade if svglint is not installed:
- `svg_lint` will work with Scour-based checks only
- A warning will be logged about missing svglint

---

## Node.js Provisioning

This section describes how to provision Node.js for svglint support. The project already uses Spack for Python; Node.js can be added to the same environment.

### Option A: Add Node.js to Spack Environment

The project already has a `spack.yaml` that provisions Python 3.14.2. To add Node.js:

#### 1. Update `spack.yaml`

```yaml
---
# Spack environment for SVG-MCP
# This file defines system-level dependencies managed by Spack.
# See: https://spack.readthedocs.io/en/latest/environments.html
spack:
  # Root specs for this project
  specs:
    # Using @X.Y to match any patch version (e.g., 3.12 matches 3.12.12)
    # This allows Spack to pick a version with a valid checksum
    - python@3.14.2
    # Node.js for svglint (optional SVG linting)
    # Note: Node.js build requires Python < 3.14 due to removed FancyURLopener
    # (fixed in Node.js 24.3.0+, but Spack may not have it yet)
    - node-js@22 ^python@:3.13
  # Create a unified view with symlinks for easy PATH integration
  view: true
  # Prefer to deduplicate dependency trees across root specs
  concretizer:
    unify: when_possible
    reuse: true
  # Package requirements to avoid broken/future versions
  packages:
    ncurses:
      # Require exactly stable 6.5 release (avoid broken "current" snapshots with future dates)
      require: '@=6.5'
    python:
      # Constrain Python to < 3.14 for Node.js build compatibility
      # Node.js 24.2.0 and earlier use deprecated urllib.FancyURLopener
      # which was removed in Python 3.14
      require: "@:3.13"
```

**Key points:**
- Node.js 22 is the current LTS version (as of December 2025)
- The `^python@:3.13` constraint ensures Node.js builds with a compatible Python
- The `packages.python.require` constraint applies globally to the Node.js build dependency

#### 2. The `scripts/spack-ensure.sh` Script

The project already has a `scripts/spack-ensure.sh` script that:
1. Finds or installs Spack
2. Concretizes the environment from `spack.yaml`
3. Installs all packages
4. Generates `.spack-activate.sh` for environment activation

This script will automatically handle Node.js installation when `spack.yaml` is updated.

#### 3. Verify Node.js Installation

After running `just setup`, verify Node.js is available:

```bash
# Activate the Spack environment
source .spack-activate.sh

# Check Node.js
node --version  # Should show v22.x.x
npm --version   # Should show 10.x.x

# Install svglint globally
npm install -g svglint

# Verify svglint
svglint --version
```

### Option B: Use mise for Node.js (Alternative)

If you prefer not to build Node.js from source via Spack, you can use mise (formerly rtx) for binary Node.js installation.

#### 1. Create `mise.toml`

```toml
# mise.toml - Runtime version management
# See: https://mise.jdx.dev/

[tools]
# Node.js for svglint (optional SVG linting)
# Uses prebuilt binaries, much faster than Spack
node = "22"
```

#### 2. Update `justfile` to Support mise

Add a recipe to ensure mise tools are available:

```just
# Ensure mise tools are installed (Node.js for svglint)
[private]
install-mise-tools:
    #!/usr/bin/env bash
    set -euo pipefail
    if [ -f "mise.toml" ] && command -v mise >/dev/null 2>&1; then
        mise install
        eval "$(mise activate bash)"
    fi
```

Then update the `install-deps` recipe to call it:

```just
[private]
install-deps: install-poetry install-mise-tools
    # ... existing content ...
```

### Option C: Hybrid Approach (Spack Python + mise Node.js) — RECOMMENDED

For the best of both worlds:
- Use Spack for Python (required, specific version needed)
- Use mise for Node.js (optional, prebuilt binaries)

This avoids the long Node.js build time in Spack while keeping the Python version control.

#### Implementation Steps for Option C

1. **Keep existing `spack.yaml`** (Python only):
   ```yaml
   ---
   # Spack environment for SVG-MCP
   spack:
     specs:
       - python@3.14.2
     view: true
     concretizer:
       unify: when_possible
       reuse: true
     packages:
       ncurses:
         require: '@=6.5'
   ```

2. **Create `mise.toml`** for Node.js:
   ```toml
   # mise.toml - Runtime version management for Node.js
   # See: https://mise.jdx.dev/

   [tools]
   # Node.js for svglint (optional SVG linting)
   # Uses prebuilt binaries, much faster than Spack
   node = "22"
   ```

3. **Update `justfile`** to integrate mise:
   ```just
   # Ensure mise tools are installed (Node.js for svglint)
   [private]
   install-mise-tools:
       #!/usr/bin/env bash
       set -euo pipefail
       if [ -f "mise.toml" ] && command -v mise >/dev/null 2>&1; then
           echo "Installing mise tools (Node.js)..."
           mise install
       else
           echo "mise not available or mise.toml not found, skipping Node.js setup"
           echo "svglint will not be available (Scour-based linting will still work)"
       fi
   ```

4. **Update `install-deps` recipe** to call `install-mise-tools`:
   ```just
   [private]
   install-deps: install-poetry install-mise-tools
       # ... existing content ...
   ```

5. **Create `.mise-activate.sh`** for environment activation:
   ```bash
   #!/usr/bin/env bash
   # Auto-generated mise activation script
   if command -v mise >/dev/null 2>&1 && [ -f "mise.toml" ]; then
       eval "$(mise activate bash)"
   fi
   ```

6. **Update `check-node` recipe** to check both Spack and mise:
   ```just
   check-node:
       #!/usr/bin/env bash
       set -euo pipefail
       # Try Spack first
       if [ -f ".spack-activate.sh" ]; then
           source .spack-activate.sh
       fi
       # Then try mise
       if command -v mise >/dev/null 2>&1 && [ -f "mise.toml" ]; then
           eval "$(mise activate bash)"
       fi
       # Check Node.js availability
       if command -v node >/dev/null 2>&1; then
           echo "Node.js: $(node --version)"
           echo "npm: $(npm --version)"
           echo "Source: $(which node)"
           # Check svglint
           if command -v svglint >/dev/null 2>&1; then
               echo "svglint: $(svglint --version 2>/dev/null || echo 'available')"
           elif npx --yes svglint --version >/dev/null 2>&1; then
               echo "svglint: available via npx"
           else
               echo "svglint: not installed (run: npm install -g svglint)"
           fi
       else
           echo "Node.js: not available"
           echo ""
           echo "To enable svglint support with Option C (Hybrid):"
           echo "  1. Ensure mise is installed: https://mise.jdx.dev/"
           echo "  2. Run: just setup"
           echo "  3. Run: npm install -g svglint"
       fi
   ```

### Graceful Degradation

The svglint integration should gracefully degrade when Node.js is not available:

```python
# SVG_MCP/svg/svglint_runner.py

import shutil
import subprocess
from typing import Optional

class SvglintRunner:
    """Run svglint as a subprocess."""

    _available: Optional[bool] = None

    @classmethod
    def is_available(cls) -> bool:
        """Check if svglint is installed and working."""
        if cls._available is None:
            cls._available = cls._check_svglint()
        return cls._available

    @classmethod
    def _check_svglint(cls) -> bool:
        """Check if svglint command works."""
        # First check if node is available
        if not shutil.which('node'):
            return False

        # Then check if svglint is installed
        try:
            result = subprocess.run(
                ['npx', '--yes', 'svglint', '--version'],
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def __init__(self):
        if not self.is_available():
            raise RuntimeError(
                "svglint not available. Install Node.js and run: npm install -g svglint"
            )
```

### Just Actions for Node.js

Add these recipes to the `justfile`:

```just
# Check if Node.js is available (for svglint support)
check-node:
    #!/usr/bin/env bash
    set -euo pipefail
    if [ -f ".spack-activate.sh" ]; then
        source .spack-activate.sh
    fi
    if command -v node >/dev/null 2>&1; then
        echo "Node.js: $(node --version)"
        echo "npm: $(npm --version)"
        if command -v svglint >/dev/null 2>&1 || npx --yes svglint --version >/dev/null 2>&1; then
            echo "svglint: available"
        else
            echo "svglint: not installed (run: npm install -g svglint)"
        fi
    else
        echo "Node.js: not available"
        echo "svglint: not available (requires Node.js)"
        echo ""
        echo "To enable svglint support, either:"
        echo "  1. Add node-js to spack.yaml and run: just setup"
        echo "  2. Install Node.js via mise: mise install node@22"
        echo "  3. Install Node.js via system package manager"
    fi

# Install svglint globally (requires Node.js)
install-svglint:
    #!/usr/bin/env bash
    set -euo pipefail
    if [ -f ".spack-activate.sh" ]; then
        source .spack-activate.sh
    fi
    if ! command -v node >/dev/null 2>&1; then
        echo "Error: Node.js not available. See 'just check-node' for options."
        exit 1
    fi
    npm install -g svglint
    echo "svglint installed successfully"
```

### Pre-commit Hook for svglint

If svglint is available, it can be integrated into pre-commit:

#### 1. Add to `.pre-commit-config.yaml`

```yaml
# SVG linting with svglint (requires Node.js)
# This hook is optional and will be skipped if svglint is not installed
- repo: local
  hooks:
    - id: svglint
      name: svglint
      entry: bash -c 'if command -v svglint >/dev/null 2>&1; then svglint "$@"; else echo "svglint not installed, skipping"; fi' --
      language: system
      files: \.svg$
      types: [file]
```

#### 2. Alternative: Use svglint's Official Hook

svglint provides an official pre-commit hook:

```yaml
- repo: https://github.com/nickytonline/svglint-pre-commit
  rev: v0.0.1
  hooks:
    - id: svglint
```

**Note:** Research the current status of this hook before using it, as it may have changed since December 2025.

### Summary: Node.js Provisioning Checklist

| Step | Spack (Option A) | mise (Option B) | Hybrid (Option C) |
|------|------------------|-----------------|-------------------|
| 1. Update config | Edit `spack.yaml` | Create `mise.toml` | Both |
| 2. Install runtime | `just setup` | `mise install` | Both |
| 3. Activate env | `source .spack-activate.sh` | `eval "$(mise activate bash)"` | Both |
| 4. Install svglint | `npm install -g svglint` | Same | Same |
| 5. Verify | `just check-node` | Same | Same |

**Recommendation:** Use **Option C (Hybrid)** — Spack for Python + mise for Node.js. This provides the best balance of:
- **Version control**: Spack ensures the exact Python version needed
- **Fast setup**: mise uses prebuilt Node.js binaries (no compilation)
- **Simplicity**: mise is already available on the system (`mise` command)
- **Graceful degradation**: If mise is not available, svglint is simply skipped

---

## Implementation Phases

### Phase 1: Core Infrastructure (2-3 days)

1. **Add Scour dependency**
   - Add to `pyproject.toml`
   - Run `poetry lock && poetry install`

2. **Create data models**
   - Create `SVG_MCP/models/lint_types.py`
   - Add `LintIssue`, `LintResult`, `OptimizeResult`

3. **Create SVGOptimizer**
   - Create `SVG_MCP/svg/optimizer.py`
   - Implement Scour wrapper with preset support
   - Add unit tests

4. **Add `svg_optimize` MCP tool**
   - Add to `SVG_MCP/server.py`
   - Add CLI command to `SVG_MCP/cli.py`

### Phase 2: Scour-as-Linter (2-3 days)

1. **Create ScourLinter**
   - Create `SVG_MCP/svg/scour_linter.py`
   - Implement flowtext detection
   - Implement renderer workaround detection
   - Implement namespace issue detection
   - Add unit tests

2. **Create unified SVGLinter**
   - Create `SVG_MCP/svg/linter.py`
   - Integrate ScourLinter
   - Add preset support
   - Add unit tests

3. **Add `svg_lint` MCP tool (Scour-only)**
   - Add to `SVG_MCP/server.py`
   - Add CLI command to `SVG_MCP/cli.py`

### Phase 3: svglint Integration (2-3 days)

1. **Create SvglintRunner**
   - Create `SVG_MCP/svg/svglint_runner.py`
   - Implement subprocess wrapper
   - Parse svglint output
   - Add graceful degradation if not installed
   - Add integration tests

2. **Integrate with SVGLinter**
   - Add svglint backend to unified linter
   - Add element/attribute rule support
   - Add unit tests

3. **Update `svg_lint` MCP tool**
   - Add svglint options
   - Add element_rules and attribute_rules parameters

### Phase 4: Documentation & Polish (1-2 days)

1. **Update README.md**
   - Document new tools
   - Add usage examples
   - Document presets

2. **Add pre-commit hook support**
   - Create `.pre-commit-hooks.yaml`
   - Document integration

3. **Run full test suite**
   - Run `just validate`
   - Fix any issues

---

## Testing Strategy

### Unit Tests

```python
# tests/unit/test_optimizer.py
class TestSVGOptimizer:
    def test_optimize_removes_editor_data(self):
        """Editor data should be removed by default."""
        svg = '<svg xmlns="http://www.w3.org/2000/svg" inkscape:version="1.0">...</svg>'
        result = optimizer.optimize(svg)
        assert 'inkscape:version' not in result.optimized_content

    def test_optimize_safe_preserves_editor_data(self):
        """Safe preset should preserve editor data."""
        svg = '<svg xmlns="http://www.w3.org/2000/svg" inkscape:version="1.0">...</svg>'
        result = optimizer.optimize(svg, preset='safe')
        assert 'inkscape:version' in result.optimized_content

    def test_optimize_reduces_size(self):
        """Optimization should reduce file size."""
        result = optimizer.optimize(large_svg)
        assert result.optimized_size < result.original_size


# tests/unit/test_scour_linter.py
class TestScourLinter:
    def test_detects_flowtext(self):
        """Flowtext should be detected as an error."""
        svg = '<svg><flowRoot>...</flowRoot></svg>'
        result = linter.lint(svg)
        assert any(i.code == 'inkscape/flowtext' for i in result.issues)

    def test_valid_svg_passes(self):
        """Valid SVG should pass linting."""
        svg = '<svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>'
        result = linter.lint(svg)
        assert result.valid


# tests/unit/test_svglint_runner.py
class TestSvglintRunner:
    @pytest.mark.skipif(not svglint_available(), reason="svglint not installed")
    def test_element_rules(self):
        """Element rules should be enforced."""
        svg = '<svg><title>Test</title></svg>'
        result = runner.lint(svg, rules={'elm': {'svg > title': 1}})
        assert result.valid
```

### Integration Tests

```python
# tests/integration/test_lint_optimize_pipeline.py
class TestLintOptimizePipeline:
    def test_lint_then_optimize(self):
        """Linting should pass after optimization."""
        svg = load_fixture('complex.svg')

        # Optimize
        opt_result = optimizer.optimize(svg)
        assert opt_result.success

        # Lint optimized output
        lint_result = linter.lint(opt_result.optimized_content)
        assert lint_result.valid
```

### E2E Tests

```python
# tests/e2e/test_mcp_tools.py
class TestMCPTools:
    def test_svg_lint_tool(self):
        """svg_lint MCP tool should work."""
        result = svg_lint(content=valid_svg, preset='default')
        assert result['valid'] is True

    def test_svg_optimize_tool(self):
        """svg_optimize MCP tool should work."""
        result = svg_optimize(content=large_svg, preset='default')
        assert result['success'] is True
        assert result['reduction_percent'] > 0
```

---

## CLI Commands

```bash
# Lint an SVG file
svg-mcp lint input.svg
svg-mcp lint input.svg --preset strict
svg-mcp lint input.svg --preset inkscape

# Optimize an SVG file
svg-mcp optimize input.svg -o output.svg
svg-mcp optimize input.svg -o output.svg --preset maximum
svg-mcp optimize input.svg -o output.svg --precision 3 --no-line-breaks

# Combined lint + optimize
svg-mcp check input.svg  # Lint only, no changes
svg-mcp fix input.svg -o output.svg  # Lint + optimize
```

---

## Timeline

| Phase | Tasks | Duration |
|-------|-------|----------|
| Phase 1 | Core Infrastructure | 2-3 days |
| Phase 2 | Scour-as-Linter | 2-3 days |
| Phase 3 | svglint Integration | 2-3 days |
| Phase 4 | Documentation & Polish | 1-2 days |
| **Total** | | **7-11 days** |

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| svglint not installed | Medium | Graceful degradation to Scour-only |
| Scour API changes | Low | Pin version, add version check |
| Node.js not available | Medium | Make svglint optional |
| Performance issues | Low | Cache Scour options, batch processing |

---

## Success Criteria

1. ✅ `svg_lint` detects Inkscape compatibility issues (flowtext, etc.)
2. ✅ `svg_lint` supports configurable element/attribute rules
3. ✅ `svg_optimize` reduces file size without breaking rendering
4. ✅ All existing tests pass
5. ✅ New tests cover all new functionality
6. ✅ Documentation updated
7. ✅ `just validate` passes

---

## Conclusion

This implementation plan provides a comprehensive approach to adding SVG linting and optimization to SVG-MCP:

1. **Scour** provides Python-native SVG optimization with Inkscape compatibility
2. **Scour-as-Linter** provides Inkscape compatibility checking without modifying files
3. **svglint** provides configurable element/attribute rules (optional, requires Node.js)

The combination ensures that SVG-MCP can both **detect** issues (linting) and **fix** them (optimization), with a focus on Inkscape/librsvg compatibility.
