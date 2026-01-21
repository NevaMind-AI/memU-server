#!/usr/bin/env python3
"""Check configuration files for hardcoded credentials."""

import re
import sys
from pathlib import Path

# Patterns that indicate hardcoded credentials
CREDENTIAL_PATTERNS = [
    # Database URLs with actual credentials
    (r"postgresql://[^$@{}][^@]*:[^$@{}][^@]*@", "PostgreSQL URL with hardcoded credentials"),
    (r"mysql://[^$@{}][^@]*:[^$@{}][^@]*@", "MySQL URL with hardcoded credentials"),
    (r"mongodb://[^$@{}][^@]*:[^$@{}][^@]*@", "MongoDB URL with hardcoded credentials"),
    # Common password/key patterns (not in comments)
    (r'^[^#]*password\s*=\s*["\'](?!\$\{)[^"\'].*["\']', "Hardcoded password"),
    (r'^[^#]*api[_-]?key\s*=\s*["\'](?!\$\{)[^"\'].*["\']', "Hardcoded API key"),
    (r'^[^#]*secret\s*=\s*["\'](?!\$\{)[^"\'].*["\']', "Hardcoded secret"),
]

# File patterns to check
CONFIG_FILES = [
    "*.ini",
    "*.conf",
    "*.config",
    "*.cfg",
    "*.yaml",
    "*.yml",
    "*.toml",
    ".env.example",
]


def check_file_for_credentials(filepath: Path) -> list[tuple[int, str]]:
    """Check a file for hardcoded credentials."""
    issues = []
    try:
        with open(filepath, encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                # Skip comment-only lines
                if line.strip().startswith("#"):
                    continue

                for pattern, description in CREDENTIAL_PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE):
                        issues.append((line_num, f"{description}: {line.strip()[:80]}..."))
    except Exception as e:
        print(f"Warning: Could not check {filepath}: {e}")

    return issues


def main():
    """Main function."""
    root = Path(".")
    errors = []

    for pattern in CONFIG_FILES:
        for filepath in root.rglob(pattern):
            # Skip .venv and other ignored directories
            if any(part in filepath.parts for part in [".venv", "venv", ".git", "__pycache__", "node_modules"]):
                continue

            file_issues = check_file_for_credentials(filepath)
            if file_issues:
                errors.append((filepath, file_issues))

    if errors:
        print("❌ Hardcoded credentials detected in configuration files:")
        for filepath, issues in errors:
            print(f"\n  {filepath}:")
            for line_num, description in issues:
                print(f"    Line {line_num}: {description}")
        print(
            "\n💡 Hint: Use environment variable placeholders like ${VAR_NAME} "
            "or ${DATABASE_USER} instead of hardcoded values."
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
