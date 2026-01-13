# DEPRECATED: Este script utilitário está marcado como suspeito de não ser mais utilizado. Favor revisar antes de remover.
#!/usr/bin/env python3
"""
Check for synchronization between setup.py and requirements.txt

This script ensures that dependencies declared in setup.py are consistent
with those in requirements.txt (excluding dev dependencies).

Usage:
    python scripts/check_dep_sync.py

Exit codes:
    0 - Dependencies are in sync
    1 - Dependencies are out of sync
"""

import re
import sys
from pathlib import Path


def extract_setup_deps():
    """Extract dependencies from setup.py"""
    setup_file = Path("setup.py")
    if not setup_file.exists():
        print("ERROR: setup.py not found")
        return None
    
    content = setup_file.read_text()
    
    # Extract install_requires list
    match = re.search(r'install_requires=\[(.*?)\]', content, re.DOTALL)
    if not match:
        print("ERROR: Could not find install_requires in setup.py")
        return None
    
    deps_text = match.group(1)
    
    # Extract package names (ignore version specifiers)
    deps = set()
    for line in deps_text.split('\n'):
        line = line.strip().strip(',').strip("'\"")
        if line and not line.startswith('#'):
            # Remove version specifiers (>=, ==, etc.)
            pkg = re.split(r'[><=!]', line)[0].strip()
            deps.add(pkg)
    
    return deps


def extract_requirements_deps():
    """Extract dependencies from requirements.txt (excluding dev deps)"""
    req_file = Path("requirements.txt")
    if not req_file.exists():
        print("ERROR: requirements.txt not found")
        return None
    
    deps = set()
    for line in req_file.read_text().split('\n'):
        line = line.strip()
        if line and not line.startswith('#'):
            # Remove version specifiers
            pkg = re.split(r'[><=!]', line)[0].strip()
            deps.add(pkg)
    
    return deps


def main():
    print("Checking dependency synchronization between setup.py and requirements.txt...")
    print()
    
    setup_deps = extract_setup_deps()
    req_deps = extract_requirements_deps()
    
    if setup_deps is None or req_deps is None:
        return 1
    
    # Find differences
    only_in_setup = setup_deps - req_deps
    only_in_requirements = req_deps - setup_deps
    
    if not only_in_setup and not only_in_requirements:
        print("✓ Dependencies are in sync!")
        return 0
    
    print("⚠️  Dependency mismatch detected!")
    print()
    
    if only_in_setup:
        print("Packages in setup.py but NOT in requirements.txt:")
        for pkg in sorted(only_in_setup):
            print(f"  - {pkg}")
        print()
    
    if only_in_requirements:
        print("Packages in requirements.txt but NOT in setup.py:")
        for pkg in sorted(only_in_requirements):
            print(f"  - {pkg}")
        print()
    
    print("Note: requirements.txt may include additional packages for")
    print("deployment/Docker that are not needed as install dependencies.")
    print("This is acceptable if intentional (e.g., torch, pydantic).")
    print()
    print("If this is expected, you can suppress this warning.")
    
    return 1


if __name__ == "__main__":
    sys.exit(main())
