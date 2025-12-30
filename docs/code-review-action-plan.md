# Code Review Action Plan

**Created:** December 30, 2025
**Based on:** [Code Review Findings](code-review-findings.md)
**Project:** SVG-MCP
**Scope:** Private project (not for public distribution)

## Overview

This document outlines the action plan to address the findings from the code review. The plan is organized into milestones, prioritized by severity and impact.

---

## Milestone 1: Package API Cleanup

**Priority:** Medium
**Estimated Effort:** 2 hours
**Dependencies:** None

### Task 1.1: Remove or Repurpose `core.py`

**Finding:** [#1 - Vestigial core.py Module](code-review-findings.md#finding-1-vestigial-corepy-module-with-placeholder-function)

**Actions:**
1. Evaluate if `core.py` is needed for shared utilities
2. If not needed:
   - Delete [`SVG_MCP/core.py`](../SVG_MCP/core.py)
   - Update [`SVG_MCP/__init__.py`](../SVG_MCP/__init__.py) to remove the import
3. If needed for utilities:
   - Rename to `utils.py`
   - Replace placeholder `add()` with actual shared utilities (e.g., `_parse_viewbox`)

**Acceptance Criteria:**
- [ ] No placeholder functions remain in the codebase
- [ ] Package structure reflects actual functionality

### Task 1.2: Update Package Exports

**Finding:** [#2 - `__init__.py` Exports Unrelated Function](code-review-findings.md#finding-2-__init__py-exports-unrelated-function)

**Actions:**
1. Update [`SVG_MCP/__init__.py`](../SVG_MCP/__init__.py) to export the public API:
   ```python
   from .svg import SVGValidator, SVGRenderer, SVGDiffer
   from .server import create_server, mcp

   __all__ = [
       "SVGValidator",
       "SVGRenderer",
       "SVGDiffer",
       "create_server",
       "mcp",
   ]
   ```
2. Update [`scripts/test-package.sh`](../scripts/test-package.sh) smoke test to verify actual exports

**Acceptance Criteria:**
- [ ] `from SVG_MCP import SVGValidator` works
- [ ] `from SVG_MCP import create_server` works
- [ ] Package smoke test passes with new exports

### Task 1.3: Implement Dynamic Version

**Finding:** [#3 - Hardcoded Version in CLI](code-review-findings.md#finding-3-hardcoded-version-in-cli)

**Actions:**
1. Create version utility in [`SVG_MCP/__init__.py`](../SVG_MCP/__init__.py):
   ```python
   from importlib.metadata import version, PackageNotFoundError

   try:
       __version__ = version("SVG_MCP")
   except PackageNotFoundError:
       __version__ = "0.0.0.dev"
   ```
2. Update [`SVG_MCP/cli.py`](../SVG_MCP/cli.py:20) to use dynamic version:
   ```python
   from SVG_MCP import __version__

   @click.version_option(version=__version__, prog_name="svg-mcp")
   ```
3. Update the `info` command at line 281 to use `__version__`

**Acceptance Criteria:**
- [ ] Version is defined in single location (`pyproject.toml`)
- [ ] CLI `--version` shows correct version
- [ ] `info` command shows correct version
- [ ] All tests pass

---

## Milestone 2: Code Quality Improvements

**Priority:** Low
**Estimated Effort:** 2 hours
**Dependencies:** Milestone 1

### Task 2.1: Extract Shared Utilities

**Finding:** [#8 - Duplicate `_parse_viewbox` Implementation](code-review-findings.md#finding-8-duplicate-_parse_viewbox-implementation)

**Actions:**
1. Create [`SVG_MCP/svg/utils.py`](../SVG_MCP/svg/utils.py) with shared utilities:
   ```python
   """Shared utilities for SVG processing."""
   import re
   from SVG_MCP.models.types import ViewBox

   def parse_viewbox(viewbox_str: str | None) -> ViewBox | None:
       """Parse viewBox attribute string."""
       if not viewbox_str:
           return None
       parts = re.split(r"[\s,]+", viewbox_str.strip())
       if len(parts) != 4:
           return None
       try:
           x, y, width, height = map(float, parts)
           return ViewBox(x=x, y=y, width=width, height=height)
       except ValueError:
           return None
   ```
2. Update [`SVG_MCP/svg/validator.py`](../SVG_MCP/svg/validator.py:229) to use shared utility
3. Update [`SVG_MCP/svg/renderer.py`](../SVG_MCP/svg/renderer.py:209) to use shared utility
4. Update [`SVG_MCP/svg/__init__.py`](../SVG_MCP/svg/__init__.py) to export if needed

**Acceptance Criteria:**
- [ ] Single implementation of `parse_viewbox`
- [ ] All existing tests pass
- [ ] No code duplication

### Task 2.2: Fix Resource Cleanup

**Finding:** [#7 - Potential Resource Leak in Preview Resource](code-review-findings.md#finding-7-potential-resource-leak-in-preview-resource)

**Actions:**
1. Update [`SVG_MCP/server.py`](../SVG_MCP/server.py:246) `_impl_svg_preview_resource()`:
   ```python
   def _impl_svg_preview_resource(path: str) -> str:
       file_path = Path(path)
       if not file_path.exists():
           return f"Error: File not found: {path}"

       try:
           svg_content = file_path.read_text(encoding="utf-8")
           with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
               tmp_path = tmp.name

           try:
               result = _renderer.render(svg_content, tmp_path, width=256)
               if result.success:
                   with open(tmp_path, "rb") as f:
                       png_data = f.read()
                   return f"data:image/png;base64,{base64.b64encode(png_data).decode()}"
               else:
                   return f"Error: Failed to render preview: {result.error}"
           finally:
               Path(tmp_path).unlink(missing_ok=True)

       except OSError as e:
           return f"Error: Failed to read file: {e}"
   ```

**Acceptance Criteria:**
- [ ] Temporary files are always cleaned up
- [ ] All existing tests pass
- [ ] No resource leaks

---

## Milestone 3: Minor Fixes and Polish

**Priority:** Low
**Estimated Effort:** 1 hour
**Dependencies:** None

### Task 3.1: Fix `deactivate` Warning

**Finding:** [#4 - Minor Warning in justfile](code-review-findings.md#finding-4-minor-warning-in-justfile---deactivate-command-not-found)

**Actions:**
1. Update [`justfile`](../justfile:72) install-deps recipe:
   ```bash
   # Replace:
   if [ -n "${VIRTUAL_ENV-}" ]; then
       deactivate || true
   fi

   # With:
   if [ -n "${VIRTUAL_ENV-}" ] && type deactivate &>/dev/null; then
       deactivate || true
   fi
   ```

**Acceptance Criteria:**
- [ ] No warning when running `just validate`
- [ ] Virtual environment deactivation still works when applicable

### Task 3.2: Handle Missing valgrind Script

**Finding:** [#5 - Missing valgrind-pytests.sh Script](code-review-findings.md#finding-5-missing-valgrind-pytestssh-script)

**Actions:**
Option A (Remove hook):
1. Remove the `valgrind-pytests` hook from [`.pre-commit-config.yaml`](../.pre-commit-config.yaml:54-60)

Option B (Create script):
1. Create [`scripts/valgrind-pytests.sh`](../scripts/valgrind-pytests.sh):
   ```bash
   #!/usr/bin/env bash
   set -euo pipefail
   echo "Valgrind memory check for pytest..."
   valgrind --tool=memcheck --leak-check=full \
       poetry run pytest tests/unit/ -v
   ```
2. Make executable: `chmod +x scripts/valgrind-pytests.sh`

**Recommendation:** Option A is simpler unless valgrind testing is specifically needed.

**Acceptance Criteria:**
- [ ] No broken references in pre-commit config
- [ ] Manual hook runs successfully (if Option B)

### Task 3.3: Update API Documentation

**Finding:** [#6 - Documentation Inconsistency](code-review-findings.md#finding-6-documentation-inconsistency---data-types-section)

**Actions:**
1. Update [`docs/api-reference.md`](../docs/api-reference.md:494-564) Data Types section
2. Change `@dataclass` annotations to show actual Pydantic `BaseModel` usage:
   ```python
   class ValidationResult(BaseModel):
       valid: bool = Field(description="Whether the SVG is valid")
       errors: list[ValidationError] = Field(default_factory=list)
       warnings: list[ValidationError] = Field(default_factory=list)
       info: SVGInfo | None = Field(default=None)
   ```

**Acceptance Criteria:**
- [ ] Documentation matches actual implementation
- [ ] All code examples are accurate

---

## Implementation Schedule

| Milestone | Tasks | Priority | Est. Effort | Suggested Order |
|-----------|-------|----------|-------------|-----------------|
| 1 | 1.1, 1.2, 1.3 | Medium | 2 hours | First |
| 2 | 2.1, 2.2 | Low | 2 hours | Second |
| 3 | 3.1, 3.2, 3.3 | Low | 1 hour | Third |

**Total Estimated Effort:** 5 hours

---

## Verification Checklist

After completing all milestones, verify:

- [ ] `just validate` passes with no errors or warnings
- [ ] `just test` passes with all tests
- [ ] `just test-package` passes smoke tests
- [ ] `poetry run svg-mcp --version` shows correct version
- [ ] `poetry run svg-mcp info` shows correct version
- [ ] `from SVG_MCP import SVGValidator` works in Python
- [ ] No temporary files are leaked during preview generation

---

## Notes

- All changes should be made incrementally with tests passing after each change
- Run `just validate` after each milestone to ensure no regressions
- Consider creating a PR for each milestone for easier review
