#!/usr/bin/env python3
"""
Script to add comprehensive e2e tests section to svg-mcp-plan.md.

This script inserts a new section describing end-to-end tests after the CLI Tests
section and before the Test Fixtures section.
"""

import re
from pathlib import Path

E2E_TESTS_SECTION = '''
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

'''


def main():
    plan_path = Path("docs/svg-mcp-plan.md")

    if not plan_path.exists():
        print(f"Error: {plan_path} not found")
        return 1

    content = plan_path.read_text()

    # Find the location to insert (after CLI Tests table, before Test Fixtures)
    # Look for the pattern: "| C007 | ... |\n\n### Test Fixtures"
    pattern = r"(\| C007 \| `test_cli_serve_stdio` \| serve command with stdio \|\n)"

    if not re.search(pattern, content):
        print("Error: Could not find insertion point (C007 test row)")
        return 1

    # Insert the e2e tests section after the CLI tests table
    new_content = re.sub(pattern, r"\1" + E2E_TESTS_SECTION, content)

    plan_path.write_text(new_content)
    print(f"Successfully added e2e tests section to {plan_path}")
    return 0


if __name__ == "__main__":
    exit(main())
