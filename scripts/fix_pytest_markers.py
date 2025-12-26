#!/usr/bin/env python3
"""
Script to update pytest markers to include e2e marker.
"""

from pathlib import Path


def main():
    plan_path = Path("docs/svg-mcp-plan.md")

    if not plan_path.exists():
        print(f"Error: {plan_path} not found")
        return 1

    content = plan_path.read_text()

    # Match the exact indentation from the file (3 spaces for ini content)
    old_markers = """   markers = [
        "unit: Unit tests",
        "integration: Integration tests",
        "slow: Slow tests (rendering, etc.)",
    ]"""

    new_markers = """   markers = [
        "unit: Unit tests",
        "integration: Integration tests",
        "e2e: End-to-end tests",
        "slow: Slow tests (rendering, etc.)",
    ]"""

    if old_markers in content:
        new_content = content.replace(old_markers, new_markers)
        plan_path.write_text(new_content)
        print(f"Successfully updated pytest markers in {plan_path}")
        return 0
    elif "e2e: End-to-end tests" in content:
        print("Pytest markers already include e2e marker")
        return 0
    else:
        print("Error: Could not find pytest markers section with expected format")
        # Try a more flexible approach using regex
        import re

        pattern = (
            r'(markers = \[\s*"unit: Unit tests",\s*"integration: Integration tests",)'
        )
        replacement = r'\1\n        "e2e: End-to-end tests",'
        new_content, count = re.subn(pattern, replacement, content)
        if count > 0:
            plan_path.write_text(new_content)
            print(f"Successfully updated pytest markers using regex in {plan_path}")
            return 0
        print("Regex approach also failed")
        return 1


if __name__ == "__main__":
    exit(main())
