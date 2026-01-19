#!/bin/bash
echo "AEGIS SECURITY SCANNER - Archeon 3D"
echo "====================================="

# 1. Check for basic vulnerabilities in code
echo "[*] Running Bandit SAST..."
bandit -r hy3dgen -ll -ii

# 2. Check for safety dependencies
echo "[*] Checking Dependencies..."
if [ -f "requirements.lock" ]; then
    pip-audit -r requirements.lock
else
    pip-audit -r requirements.txt
fi

# 3. Generate SBOM
echo "[*] Generating SBOM..."
cyclonedx-py requirements.lock --output sbom.json --force

# 4. Run Security Unit Tests
echo "[*] Running Security Gates..."
pytest tests/test_security.py

echo "Security Check Complete."
