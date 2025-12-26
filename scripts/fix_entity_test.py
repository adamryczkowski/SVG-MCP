#!/usr/bin/env python3
"""Fix the entity test in test_validator.py."""

from pathlib import Path

test_file = Path("tests/unit/test_validator.py")
content = test_file.read_text()

# Find and replace the problematic line
old_line = """svg_with_entities = '<svg xmlns="http://www.w3.org/2000/svg"><text><Hello> & World</text></svg>'"""
new_line = """svg_with_entities = '<svg xmlns="http://www.w3.org/2000/svg"><text>' + '&' + 'lt;Hello' + '&' + 'gt; ' + '&' + 'amp; World</text></svg>'"""

content = content.replace(old_line, new_line)

test_file.write_text(content)
print("Fixed entity test")
