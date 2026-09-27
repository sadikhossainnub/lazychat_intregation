#!/usr/bin/env python3
"""
Build Script for LazyChat Integration - Source Code Protection
--------------------------------------------------------------
Compiles all Python source files to .pyc bytecode for distribution.

This approach:
1. Hides source logic inside compiled bytecode  
2. Works natively with Frappe (no third-party runtime needed)

Usage:
    python3 build_protected.py [--remove-sources]

Options:
    --remove-sources   Delete .py source files after compilation (for deployment)
"""

import os
import sys
import py_compile
import shutil
import glob
import compileall

APP_DIR = os.path.dirname(os.path.abspath(__file__))
PACKAGE_DIR = os.path.join(APP_DIR, "lazychat_intregation")

# Files that MUST remain as plaintext .py (Frappe requires them for hooks/setup)
KEEP_AS_SOURCE = {
    "__init__.py",
    "hooks.py",
    "modules.txt",
    "setup.py",
    "pyproject.toml",
}

# Subdirectories to skip during compilation
SKIP_DIRS = {
    "__pycache__",
}


def compile_package(package_dir: str, remove_sources: bool = False) -> int:
    """Compile all .py files in package_dir to .pyc bytecode."""
    compiled = 0
    errors = 0

    for root, dirs, files in os.walk(package_dir):
        # Skip pycache dirs
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        rel_root = os.path.relpath(root, package_dir)
        for fname in files:
            if not fname.endswith(".py"):
                continue

            src_path = os.path.join(root, fname)
            rel_path = os.path.join(rel_root, fname) if rel_root != "." else fname

            # Compile to __pycache__
            try:
                py_compile.compile(src_path, doraise=True)
                compiled += 1
            except py_compile.PyCompileError as e:
                print(f"  ❌ Compile Error: {rel_path}: {e}")
                errors += 1
                continue

            # Optionally remove source files (only non-essential ones)
            if remove_sources and fname not in KEEP_AS_SOURCE:
                os.remove(src_path)

    return compiled, errors


def build(remove_sources: bool = False):
    print(f"--> LazyChat Source Protection Build")
    print(f"    Package: {PACKAGE_DIR}")
    print(f"    Remove sources: {remove_sources}")
    print()

    compiled, errors = compile_package(PACKAGE_DIR, remove_sources=remove_sources)

    if errors > 0:
        print(f"\n❌ Build FAILED with {errors} errors.")
        sys.exit(1)

    print(f"\n✅ Compiled {compiled} Python files to bytecode.")
    if remove_sources:
        print("   Source .py files removed from non-essential modules.")

    print("""
Next steps:
- Deploy the compiled package. Python will load .pyc files automatically.
""")


if __name__ == "__main__":
    remove = "--remove-sources" in sys.argv
    build(remove_sources=remove)
