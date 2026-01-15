import sys
import unittest
from unittest.mock import MagicMock, AsyncMock, patch
import os
import asyncio
import tempfile
from fastapi import HTTPException

# Mock dependencies
sys.modules["hy3dgen.manager"] = MagicMock()
sys.modules["hy3dgen.inference"] = MagicMock()

from hy3dgen.api.utils import download_file
from hy3dgen.meshops.blender_utils import convert_blend_to_glb

class TestSecurityAndResilience(unittest.IsolatedAsyncioTestCase):
    
    async def test_path_traversal_protection(self):
        # Attempt to read a file outside allowed zones (e.g., /etc/passwd simulation)
        # Using a path that is definitely outside our current workspace and not in /tmp
        malicious_uri = "file:///etc/hostname" 
        
        with self.assertRaises(PermissionError) as cm:
            await download_file(malicious_uri)
        
        self.assertIn("Access to /etc/hostname is restricted", str(cm.exception))
        print("Path Traversal protection verified!")

    async def test_allowed_path_access(self):
        # Verify that files in /tmp are still accessible
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp.write(b"safe_content")
            tmp_path = tmp.name
        
        try:
            content = await download_file(f"file://{tmp_path}")
            self.assertEqual(content, b"safe_content")
            print("Allowed zone access verified!")
        finally:
            if os.path.exists(tmp_path): os.unlink(tmp_path)

    @patch("hy3dgen.meshops.blender_utils.is_blender_available", return_value=True)
    @patch("asyncio.create_subprocess_exec")
    async def test_blender_timeout(self, mock_exec, mock_avail):
        # Simulate a process that never finishes
        mock_process = AsyncMock()
        async def slow_communicate():
            await asyncio.sleep(10) # Longer than we want to wait in this test
            return b"", b""
            
        mock_process.communicate = slow_communicate
        mock_exec.return_value = mock_process
        
        # We'll reduce the timeout for the test to make it fast
        # but the logic is the same: asyncio.wait_for will raise TimeoutError
        with patch("hy3dgen.meshops.blender_utils.asyncio.wait_for", side_effect=asyncio.TimeoutError):
            with self.assertRaises(RuntimeError) as cm:
                await convert_blend_to_glb("/tmp/fake.blend")
            self.assertEqual(str(cm.exception), "Blender conversion timed out")
            print("Blender timeout handling verified!")

if __name__ == "__main__":
    unittest.main()
