import unittest
import os
import tempfile
import asyncio
from unittest.mock import MagicMock

# Mock dependencies
import sys
sys.modules["hy3dgen.manager"] = MagicMock()
sys.modules["hy3dgen.inference"] = MagicMock()

from hy3dgen.api.utils import download_file

class TestSecurityHardening(unittest.IsolatedAsyncioTestCase):
    
    async def test_pt_complex_traversal(self):
        """Test ../ style traversal."""
        # Our allowed zones are os.getcwd() and /tmp
        # Try to go from /tmp to /etc
        payload = "file:///tmp/../etc/passwd"
        with self.assertRaises(PermissionError):
            await download_file(payload)
        print("Complex traversal (..) blocked.")

    async def test_pt_absolute_path_outside(self):
        """Test absolute paths outside allowed zones."""
        payload = "file:///root/.ssh/id_rsa"
        with self.assertRaises(PermissionError):
            await download_file(payload)
        print("Absolute path outside blocked.")

    async def test_pt_empty_scheme_traversal(self):
        """Test relative path traversal without scheme."""
        # Current directory is allowed, but we try to go up
        payload = "../../../etc/hostname"
        with self.assertRaises(PermissionError):
            await download_file(payload)
        print("No-scheme traversal blocked.")

    async def test_pt_symlink_attack(self):
        """Test if symlinks can bypass protection."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create a symlink in /tmp pointing to /etc/hostname
            link_path = os.path.join(tmp_dir, "malicious_link")
            try:
                os.symlink("/etc/hostname", link_path)
            except OSError:
                # Might fail if no permission to symlink
                self.skipTest("Cannot create symlinks in this environment")
                
            # Current implementation uses os.path.realpath(parsed.path)
            # which resolves the link to /etc/hostname and THEN checks allowed prefixes.
            # So the prefix check will fail and raise PermissionError.
            
            with self.assertRaises(PermissionError, msg="Symlink bypass detected!"):
                await download_file(f"file://{link_path}")
            print("Symlink bypass protection verified!")

if __name__ == "__main__":
    unittest.main()
