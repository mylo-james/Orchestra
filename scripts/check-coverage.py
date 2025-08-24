#!/usr/bin/env python3
"""Coverage check script for CI/CD pipeline."""

import subprocess
import sys
from pathlib import Path


def main():
    """Run coverage check with 90% minimum threshold."""
    print("🔍 Checking code coverage (minimum 90%)...")

    try:
        # Run pytest with coverage (redirect stderr to eliminate SDK logging noise)
        result = subprocess.run(
            [
                "poetry",
                "run",
                "pytest",
                "--cov=orchestra",
                "--cov-fail-under=90",
                "--cov-report=term-missing",
                "--quiet",
            ],
            cwd=Path(__file__).parent.parent,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )

        if result.returncode == 0:
            print("✅ Coverage check passed (≥90%)")

            # Extract coverage percentage from output
            for line in result.stdout.split("\n"):
                if "TOTAL" in line and "%" in line:
                    print(f"📊 {line.strip()}")

            return 0
        else:
            print("❌ Coverage check failed (<90%)")
            print("\nCoverage report:")
            print(result.stdout)

            if result.stderr:
                print("\nErrors:")
                print(result.stderr)

            return 1

    except Exception as e:
        print(f"❌ Coverage check error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
