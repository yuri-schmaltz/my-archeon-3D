import unittest
import os
import tempfile
import asyncio
from PIL import Image
from io import BytesIO
import httpx
from unittest.mock import patch, MagicMock, AsyncMock

# Mocking hy3dgen package for isolated testing
import sys
from unittest.mock import MagicMock
sys.modules["hy3dgen.manager"] = MagicMock()
sys.modules["hy3dgen.inference"] = MagicMock()

from hy3dgen.api.utils import download_file, download_image_as_pil

class TestUtils(unittest.IsolatedAsyncioTestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_file_path = os.path.join(self.temp_dir.name, "test.txt")
        with open(self.test_file_path, "wb") as f:
            f.write(b"hello world")
            
        self.test_image_path = os.path.join(self.temp_dir.name, "test.png")
        img = Image.new('RGB', (100, 100), color = 'red')
        img.save(self.test_image_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    async def test_download_file_local(self):
        uri = f"file://{self.test_file_path}"
        content = await download_file(uri)
        self.assertEqual(content, b"hello world")

    async def test_download_file_no_scheme(self):
        content = await download_file(self.test_file_path)
        self.assertEqual(content, b"hello world")

    async def test_download_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            await download_file("/tmp/non_existent_file_12345.txt")

    async def test_download_file_security_violation(self):
        # Assuming /etc/shadow is restricted
        with self.assertRaises(PermissionError):
            await download_file("file:///etc/shadow")

    @patch("httpx.AsyncClient.get")
    async def test_download_file_http(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.content = b"http content"
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp
        
        content = await download_file("http://example.com/file.txt")
        self.assertEqual(content, b"http content")
        mock_get.assert_called_once()

    async def test_download_image_as_pil_local(self):
        uri = f"file://{self.test_image_path}"
        img = await download_image_as_pil(uri)
        self.assertIsInstance(img, Image.Image)
        self.assertEqual(img.size, (100, 100))

    async def test_unsupported_uri(self):
        with self.assertRaises(ValueError):
            await download_file("ftp://example.com/file.txt")

if __name__ == "__main__":
    unittest.main()
