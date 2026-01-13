#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path

def check_root_cleanliness():
    """Checks if root directory contains files that should be in scripts/ or tests/."""
    allowed_root_files = {
        'README.md', 'LICENSE', 'CHANGELOG.md', 'CONTRIBUTING.md', 'NOTICE',
        'requirements.txt', 'setup.py', 'pytest.ini', 'Dockerfile', '.dockerignore',
        '.gitignore', '.editorconfig', '.pre-commit-config.yaml', 'docker-compose.yml',
        '.readthedocs.yaml', 'archeon_3d.py'
    }
    
    root_path = Path('.')
    files = [f for f in root_path.iterdir() if f.is_file() and not f.name.startswith('.')]
    
    violations = []
    for f in files:
        if f.name not in allowed_root_files:
            violations.append(str(f))
            
    return violations

def check_git_ignored_committed():
    """Checks if any files that should be ignored are tracked by git."""
    try:
        # Get list of tracked files
        tracked = subprocess.check_output(['git', 'ls-files'], text=True).splitlines()
        
        # Check each tracked file against git check-ignore
        ignored_but_tracked = []
        for f in tracked:
            cmd = ['git', 'check-ignore', '-q', f]
            if subprocess.run(cmd).returncode == 0:
                ignored_but_tracked.append(f)
        return ignored_but_tracked
    except Exception as e:
        print(f"Error checking git ignored files: {e}")
        return []

def main():
    print("=== Archeon 3D Repository Governance Check ===")
    
    # 1. Root Cleanliness
    print("\n[1] Checking Root Cleanliness...")
    root_violations = check_root_cleanliness()
    if root_violations:
        print("❌ Found unexpected files in root (should probably be in scripts/ or tests/):")
        for v in root_violations:
            print(f"  - {v}")
    else:
        print("✅ Root directory is clean.")
        
    # 2. Ignored but Tracked
    print("\n[2] Checking for Ignored but Tracked files...")
    ignored_vios = check_git_ignored_committed()
    if ignored_vios:
        print("❌ Found files present in .gitignore but still tracked by git:")
        for v in ignored_vios:
            print(f"  - {v}")
    else:
        print("✅ No ignored files are being tracked.")
        
    # 3. Directory Existence
    print("\n[3] Checking Directory Structure...")
    required_dirs = ['hy3dgen', 'tests', 'scripts', 'docs']
    missing_dirs = [d for d in required_dirs if not os.path.isdir(d)]
    if missing_dirs:
        print(f"❌ Missing critical directories: {missing_dirs}")
    else:
        print("✅ All critical directories exist.")

    if root_violations or ignored_vios or missing_dirs:
        print("\nSUMMARY: Governance checks FAILED. Please clean up according to recommendations.")
        sys.exit(1)
    else:
        print("\nSUMMARY: All governance checks PASSED.")
        sys.exit(0)

if __name__ == "__main__":
    main()
