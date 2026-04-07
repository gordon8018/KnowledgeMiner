#!/usr/bin/env python
"""
Verify KnowledgeMiner 4.0 is ready for release
"""

import os
import sys
import subprocess


def check_file_exists(filepath):
    """Check if file exists"""
    if os.path.exists(filepath):
        print(f"[OK] {filepath} exists")
        return True
    else:
        print(f"[FAIL] {filepath} missing")
        return False


def run_command(cmd):
    """Run command and return success"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[OK] Command succeeded: {cmd}")
            return True
        else:
            print(f"[FAIL] Command failed: {cmd}")
            print(f"  Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"[FAIL] Command error: {cmd}")
        print(f"  Exception: {e}")
        return False


def main():
    """Run all verification checks"""
    print("Verifying KnowledgeMiner 4.0 release readiness...\n")

    checks = []

    # Check essential files
    print("Checking essential files...")
    checks.append(check_file_exists("src/__init__.py"))
    checks.append(check_file_exists("src/orchestrator.py"))
    checks.append(check_file_exists("config.yaml"))
    checks.append(check_file_exists("README.md"))
    checks.append(check_file_exists("docs/USAGE.md"))
    checks.append(check_file_exists("VERSION"))
    checks.append(check_file_exists("CHANGELOG.md"))

    # Check directory structure
    print("\nChecking directory structure...")
    checks.append(check_file_exists("src/raw/"))
    checks.append(check_file_exists("src/enhanced/"))
    checks.append(check_file_exists("src/wiki/"))
    checks.append(check_file_exists("tests/"))
    checks.append(check_file_exists("scripts/"))

    # Run tests
    print("\nRunning test suite...")
    checks.append(run_command("pytest tests/test_integration/ --quiet"))

    # Check imports
    print("\nChecking imports...")
    checks.append(run_command('python -c "from src import orchestrator"'))
    checks.append(run_command('python -c "from src.orchestrator import KnowledgeMinerOrchestrator"'))

    # Summary
    print("\n" + "="*50)
    passed = sum(checks)
    total = len(checks)

    if passed == total:
        print(f"[SUCCESS] All checks passed ({passed}/{total})")
        print("KnowledgeMiner 4.0 is ready for release!")
        return 0
    else:
        print(f"[FAILURE] Some checks failed ({passed}/{total})")
        print("Please fix issues before release")
        return 1


if __name__ == "__main__":
    sys.exit(main())
