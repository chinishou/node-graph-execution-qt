#!/usr/bin/env python
"""
Run UI tests with visible windows for debugging.

This script runs pytest with --show-ui flag enabled, allowing you to see
the actual Qt windows and operations during testing.

Usage:
    # Run all UI tests with visible windows
    python run_ui_test_visual.py

    # Run specific test with visible windows
    python run_ui_test_visual.py tests/ui/test_parameters_pane.py::TestParametersPaneEditing::test_edit_bool_parameter

    # Run with custom delay (in milliseconds)
    python run_ui_test_visual.py --delay 1000

    # Run recursion bug test
    python run_ui_test_visual.py tests/ui/test_recursion_bug.py
"""

import sys
import subprocess
import argparse


def main():
    parser = argparse.ArgumentParser(description="Run UI tests with visible windows")
    parser.add_argument(
        "test_path",
        nargs="?",
        default="tests/ui/",
        help="Path to test file or directory (default: tests/ui/)"
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=500,
        help="Delay between UI operations in milliseconds (default: 500)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "-s", "--no-capture",
        action="store_true",
        help="Don't capture stdout (shows print statements)"
    )
    parser.add_argument(
        "-k", "--keyword",
        type=str,
        help="Only run tests matching this keyword expression"
    )

    args = parser.parse_args()

    # Build pytest command
    cmd = [
        "pytest",
        args.test_path,
        "--show-ui",
        f"--ui-delay={args.delay}"
    ]

    if args.verbose:
        cmd.append("-v")

    if args.no_capture:
        cmd.append("-s")

    if args.keyword:
        cmd.extend(["-k", args.keyword])

    print(f"Running: {' '.join(cmd)}")
    print(f"UI delay: {args.delay}ms")
    print("-" * 60)

    # Run pytest
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
