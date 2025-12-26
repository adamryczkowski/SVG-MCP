#!/usr/bin/env python3
"""
Script to add e2e testing phase to the Implementation Phases section.

This script inserts a new Phase 6 for e2e testing after Phase 5 and also
updates the pytest markers to include e2e.
"""

import re
from pathlib import Path

E2E_PHASE = """
### Phase 6: End-to-End Testing (Week 6)
- [ ] Set up e2e test infrastructure (fixtures, conftest.py)
- [ ] Implement MCP client workflow tests
- [ ] Implement CLI workflow tests
- [ ] Implement real-world scenario tests
- [ ] Create e2e test fixtures (AI-generated SVGs, complex SVGs, edge cases)
- [ ] Verify all transports work correctly (stdio, HTTP, SSE)
- [ ] Performance and memory usage validation
"""


def main():
    plan_path = Path("docs/svg-mcp-plan.md")

    if not plan_path.exists():
        print(f"Error: {plan_path} not found")
        return 1

    content = plan_path.read_text()

    # Find the location to insert (after Phase 5, before Dependencies Update)
    pattern = r"(### Phase 5: CLI & Polish \(Week 5\)\n- \[ \] Implement Click CLI\n- \[ \] Add documentation\n- \[ \] Performance optimization\n- \[ \] Final testing and bug fixes\n)"

    if not re.search(pattern, content):
        print("Error: Could not find Phase 5 section")
        return 1

    # Insert the e2e phase after Phase 5
    new_content = re.sub(pattern, r"\1" + E2E_PHASE, content)

    # Also update the pytest markers to include e2e
    old_markers = """markers = [
        "unit: Unit tests",
        "integration: Integration tests",
        "slow: Slow tests (rendering, etc.)",
    ]"""

    new_markers = """markers = [
        "unit: Unit tests",
        "integration: Integration tests",
        "e2e: End-to-end tests",
        "slow: Slow tests (rendering, etc.)",
    ]"""

    new_content = new_content.replace(old_markers, new_markers)

    plan_path.write_text(new_content)
    print(f"Successfully added e2e phase and updated pytest markers in {plan_path}")
    return 0


if __name__ == "__main__":
    exit(main())
