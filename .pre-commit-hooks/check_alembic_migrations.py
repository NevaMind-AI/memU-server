#!/usr/bin/env python3
"""Check Alembic migration files for empty upgrades/downgrades."""

import ast
import sys
from pathlib import Path


def check_migration_file(filepath: Path) -> tuple[bool, str]:
    """Check if migration file has actual content."""
    try:
        with open(filepath, encoding="utf-8") as f:
            tree = ast.parse(f.read())

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name in ("upgrade", "downgrade"):
                    # Check if function body is just 'pass' or comments
                    body = [
                        n
                        for n in node.body
                        if not isinstance(n, (ast.Pass, ast.Expr))
                        or (isinstance(n, ast.Expr) and not isinstance(n.value, ast.Constant))
                    ]
                    if not body:
                        return (
                            False,
                            f"{filepath}: {node.name}() is empty (only pass statements)",
                        )
        return True, ""
    except Exception as e:
        return False, f"{filepath}: Error parsing file: {e}"


def main():
    """Main function."""
    alembic_versions = Path("alembic/versions")
    if not alembic_versions.exists():
        return 0

    migration_files = [f for f in alembic_versions.glob("*.py") if f.name != "__init__.py"]

    errors = []
    for migration_file in migration_files:
        is_valid, error = check_migration_file(migration_file)
        if not is_valid:
            errors.append(error)

    if errors:
        print("❌ Empty Alembic migrations detected:")
        for error in errors:
            print(f"  - {error}")
        print(
            "\n💡 Hint: Make sure your models are imported in alembic/env.py "
            "before running 'alembic revision --autogenerate'"
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
