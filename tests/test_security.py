import unittest
import os
import sys
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
import base64

# Mock dependencies
sys.modules['torch'] = MagicMock()
sys.modules['torch'].cuda.CudaError = Exception # Fix for except clause
sys.modules['trimesh'] = MagicMock()
sys.modules['rembg'] = MagicMock()
sys.modules['diffusers'] = MagicMock()
sys.modules['transformers'] = MagicMock()
sys.modules['PIL'] = MagicMock()
sys.modules['hy3dgen.shapegen.utils'] = MagicMock()
sys.modules['hy3dgen.rembg'] = MagicMock()
sys.modules['hy3dgen.texgen'] = MagicMock()
sys.modules['hy3dgen.text2image'] = MagicMock()
sys.modules['hy3dgen.shapegen'] = MagicMock()
sys.modules['prometheus_client'] = MagicMock()

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set env vars for auth *before* importing app if needed, 
# although our implementation reads env at request time.
os.environ["API_USERNAME"] = "testuser"
os.environ["API_PASSWORD"] = "testpass"

from api_server import app

class TestSecurity(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_auth_required(self):
        """Test that /generate requires auth."""
        response = self.client.post("/generate", json={"text": "foo"})
        self.assertEqual(response.status_code, 401)

    def test_auth_success(self):
        """Test that correct credentials work."""
        with patch('api_server.request_manager') as mock_rm:
            # Mock submit to return a fake result
            async def fake_submit(*args, **kwargs):
                return {'uid': 'test-uid', 'fake_result': True}
            
            mock_rm.submit = MagicMock(side_effect=fake_submit)
             
            response = self.client.post(
                "/generate", 
                json={"text": "foo"}, 
                auth=("testuser", "testpass")
            )
            # Should be 500 or 200 depending on flow, but definitely not 401
            # Actually, since we mocked everything, it might hit logic inside generate
            # But the auth check happens before.
            self.assertNotEqual(response.status_code, 401)

if __name__ == '__main__':
    unittest.main()
