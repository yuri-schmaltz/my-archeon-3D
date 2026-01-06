import sys
import os
import unittest
from unittest.mock import MagicMock

# Mock dependencies BEFORE importing project modules to handle missing environment
MOCK_MODULES = [
    'trimesh', 'torch', 'torch.nn', 'torch.nn.functional', 'torch.utils', 'torch.utils.data',
    'diffusers', 'diffusers.utils', 'diffusers.utils.torch_utils',
    'diffusers.utils.import_utils', 'transformers', 'einops', 'rembg', 'PIL', 
    'numpy', 'tqdm', 'gradio', 'fastapi', 'fastapi.staticfiles', 
    'fastapi.responses', 'fastapi.middleware.cors', 'uvicorn', 'yaml',
    'safetensors', 'safetensors.torch', 'skimage', 'skimage.measure', 'scipy', 'pandas',
    'torchvision', 'torchvision.transforms', 'pymeshlab', 'xatlas', 'pygltflib',
    'cv2', 'numpy.core', 'numpy.core.multiarray'
]

for mod_name in MOCK_MODULES:
    sys.modules[mod_name] = MagicMock()

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestSanity(unittest.TestCase):
    def test_api_server_import(self):
        """Test that api_server can be imported (verifies async syntax)."""
        try:
            import api_server
            print("\n[SUCCESS] api_server imported successfully.")
        except ImportError as e:
            self.fail(f"Failed to import api_server: {e}")
        except Exception as e:
            self.fail(f"Unexpected error importing api_server: {e}")

    def test_gradio_app_import(self):
        """Test that gradio_app can be imported."""
        try:
            import gradio_app
            print("\n[SUCCESS] gradio_app imported successfully.")
        except Exception as e:
            self.fail(f"Unexpected error importing gradio_app: {e}")

if __name__ == '__main__':
    unittest.main()
