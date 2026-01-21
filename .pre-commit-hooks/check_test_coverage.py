#!/usr/bin/env python3
"""Check that test coverage meets minimum threshold."""

import subprocess  # nosec B404
import sys


def check_coverage(min_coverage: int = 80) -> int:
    """
    Run pytest with coverage and check if it meets minimum threshold.

    Args:
        min_coverage: Minimum required coverage percentage (default 80%)

    Returns:
        0 if coverage meets threshold, 1 otherwise
    """
    try:
        # Run pytest with coverage
        result = subprocess.run(  # nosec B603 B607
            [
                "pytest",
                "--cov=app",
                "--cov-report=term-missing",
                f"--cov-fail-under={min_coverage}",
                "--quiet",
                "tests/",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        # Print output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)

        # Check if coverage threshold was met
        if result.returncode != 0:
            print(f"\n❌ Test coverage is below {min_coverage}%")
            print("💡 Run 'make test-cov' to see detailed coverage report")
            print("💡 Add tests to increase coverage or adjust threshold in .pre-commit-config.yaml")
            return 1

        print(f"✅ Test coverage meets minimum threshold of {min_coverage}%")
        return 0

    except FileNotFoundError:
        print("❌ pytest not found. Install dev dependencies: make dev", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Error checking coverage: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    min_threshold = int(sys.argv[1]) if len(sys.argv) > 1 else 80
    sys.exit(check_coverage(min_threshold))
