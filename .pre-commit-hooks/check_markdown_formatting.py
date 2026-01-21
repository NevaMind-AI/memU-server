#!/usr/bin/env python3
"""Check Markdown files for formatting issues."""

import re
import sys
from pathlib import Path


def check_markdown_file(filepath: Path) -> list[tuple[int, str]]:
    """Check a Markdown file for common formatting issues."""
    issues = []
    try:
        content = filepath.read_text(encoding="utf-8")
        lines = content.split("\n")

        for line_num, line in enumerate(lines, 1):
            # Check for escaped backticks in code fences
            if re.match(r"^\\`\\`\\`", line):
                issues.append(
                    (
                        line_num,
                        f"Escaped code fence (\\`\\`\\`) should be unescaped (```): {line[:50]}",
                    )
                )

            # Check for inconsistent code fence markers
            if re.match(r"^`{3,}[^`]", line) or re.match(r"^`{3,}$", line):
                # This is a proper code fence, check if previous/next lines have escaped ones
                pass

        # Check for duplicate content blocks (same 5+ consecutive lines)
        seen_blocks = {}
        block_size = 5
        for i in range(len(lines) - block_size):
            block = tuple(lines[i : i + block_size])
            # Skip empty blocks
            if all(not line.strip() for line in block):
                continue

            block_str = "\n".join(block)
            if block in seen_blocks and block_str.strip():
                issues.append(
                    (
                        i + 1,
                        f"Duplicate content block found (also at line {seen_blocks[block]})",
                    )
                )
            else:
                seen_blocks[block] = i + 1

    except Exception as e:
        print(f"Warning: Could not check {filepath}: {e}")

    return issues


def main():
    """Main function."""
    root = Path(".")
    errors = []

    for filepath in root.rglob("*.md"):
        # Skip .venv and other ignored directories
        if any(part in filepath.parts for part in [".venv", "venv", ".git", "__pycache__", "node_modules"]):
            continue

        file_issues = check_markdown_file(filepath)
        if file_issues:
            errors.append((filepath, file_issues))

    if errors:
        print("❌ Markdown formatting issues detected:")
        for filepath, issues in errors:
            print(f"\n  {filepath}:")
            for line_num, description in issues:
                print(f"    Line {line_num}: {description}")
        print("\n💡 Fix escaped code fences by replacing \\`\\`\\` with ```")
        print("💡 Remove duplicate content blocks to keep documentation concise")
        return 1

    print("✅ Markdown files look good")
    return 0


if __name__ == "__main__":
    sys.exit(main())
