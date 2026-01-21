#!/usr/bin/env python3
"""Check Makefile commands for common issues."""

import re
import sys
from pathlib import Path


def check_makefile_commands(makefile_path: str = "Makefile") -> int:
    """
    Check Makefile for deprecated or incorrect command patterns.

    Args:
        makefile_path: Path to the Makefile

    Returns:
        0 if all checks pass, 1 if issues found
    """
    makefile = Path(makefile_path)
    if not makefile.exists():
        print(f"⚠️  Makefile not found at {makefile_path}")
        return 0

    content = makefile.read_text()
    issues = []

    # Check for deprecated uv pip install patterns
    deprecated_patterns = [
        (
            r'uv\s+pip\s+install\s+-e\s+"?\.\[.*?\]"?',
            "uv pip install -e '.[extras]' is deprecated with PEP 735 dependency-groups",
            "Use 'uv sync' or 'uv sync --group <group>' instead",
        ),
    ]

    for pattern, message, suggestion in deprecated_patterns:
        matches = re.finditer(pattern, content, re.MULTILINE)
        for match in matches:
            # Find line number
            line_num = content[: match.start()].count("\n") + 1
            issues.append(
                {
                    "line": line_num,
                    "match": match.group(),
                    "message": message,
                    "suggestion": suggestion,
                }
            )

    if issues:
        print("❌ Found issues in Makefile:")
        for issue in issues:
            print(f"\n  Line {issue['line']}: {issue['match']}")
            print(f"  ⚠️  {issue['message']}")
            print(f"  💡 {issue['suggestion']}")
        return 1

    print("✅ Makefile commands look good")
    return 0


if __name__ == "__main__":
    sys.exit(check_makefile_commands())
