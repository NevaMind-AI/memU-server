#!/usr/bin/env python3
"""Check Python source code for hardcoded credentials."""

import re
import sys
from pathlib import Path


def check_python_file_for_credentials(filepath: Path) -> list[tuple[int, str]]:
    """Check a Python file for hardcoded credentials."""
    issues = []
    try:
        with open(filepath, encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                # Skip comments
                if line.strip().startswith("#"):
                    continue

                # Check for database URLs with embedded credentials
                # Match patterns like: postgresql://user:pass@host
                db_url_pattern = r'["\'](?:postgresql|mysql|mongodb)(?:\+\w+)?://[^$:{}]+:[^$@{}]+@[^"\']*["\']'
                if re.search(db_url_pattern, line):
                    # Exclude patterns that use environment variables or config
                    if not re.search(r"os\.getenv|os\.environ|\$\{|\{[a-zA-Z_]", line):
                        issues.append(
                            (
                                line_num,
                                f"Database URL with hardcoded credentials: {line.strip()[:100]}...",
                            )
                        )

                # Check for explicit password assignments
                # password = "something"
                password_pattern = r'password\s*=\s*["\'][^"\']{3,}["\']'  # nosec B105
                if re.search(password_pattern, line, re.IGNORECASE):
                    # Skip if it's using environment variables
                    if not re.search(r"os\.getenv|os\.environ|getenv|environ\[", line):
                        issues.append(
                            (
                                line_num,
                                f"Hardcoded password assignment: {line.strip()[:80]}...",
                            )
                        )

                # Check for API keys in strings
                api_key_pattern = r'["\'](?:sk-|pk_live_|pk_test_)[a-zA-Z0-9]{20,}["\']'
                if re.search(api_key_pattern, line):
                    issues.append(
                        (
                            line_num,
                            f"Hardcoded API key detected: {line.strip()[:80]}...",
                        )
                    )

    except Exception as e:
        print(f"Warning: Could not check {filepath}: {e}")

    return issues


def main():
    """Main function."""
    root = Path(".")
    errors = []

    # Check all Python files in app/ directory
    for filepath in root.rglob("*.py"):
        # Skip .venv and test files
        if any(
            part in filepath.parts
            for part in [".venv", "venv", ".git", "__pycache__", "node_modules", "tests", "test_"]
        ):
            continue

        file_issues = check_python_file_for_credentials(filepath)
        if file_issues:
            errors.append((filepath, file_issues))

    if errors:
        print("❌ Hardcoded credentials detected in Python source code:")
        for filepath, issues in errors:
            print(f"\n  {filepath}:")
            for line_num, description in issues:
                print(f"    Line {line_num}: {description}")
        print('\n💡 Use os.getenv() with fallback values for development: os.getenv("DATABASE_URL", "default_value")')
        print(
            "💡 For production, ensure environment variables are set without hardcoded defaults "
            "or add validation at startup"
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
