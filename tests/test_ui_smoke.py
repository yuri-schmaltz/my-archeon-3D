import os
import sys
import threading
import time
import requests
import unittest
from unittest.mock import MagicMock, patch

# Mock heavy dependencies to allow starting the app without GPUs or models
sys.modules["hy3dgen.manager"] = MagicMock()
sys.modules["hy3dgen.inference"] = MagicMock()
sys.modules["hy3dgen.shapegen.utils"] = MagicMock()
sys.modules["trimesh"] = MagicMock()
sys.modules["diffusers"] = MagicMock()
sys.modules["transformers"] = MagicMock()
sys.modules["torch"] = MagicMock()
sys.modules["numba"] = MagicMock()

from hy3dgen.apps.gradio_app import build_app, request_manager
import gradio as gr
from fastapi import FastAPI
import uvicorn

class TestUISmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # We need to mock request_manager since it's global in gradio_app
        import hy3dgen.apps.gradio_app as gradio_app
        gradio_app.request_manager = MagicMock()
        
        cls.demo = build_app()
        cls.port = 7865
        cls.host = "127.0.0.1"
        
        # Start server in a thread
        def run_server():
            print(f"Starting server on {cls.host}:{cls.port}...")
            # Minimal FastAPI setup similar to gradio_app.main()
            try:
                app = FastAPI()
                app = gr.mount_gradio_app(app, cls.demo, path="/")
                uvicorn.run(app, host=cls.host, port=cls.port, log_level="info")
            except Exception as e:
                print(f"Exception in server thread: {e}")
            
        cls.server_thread = threading.Thread(target=run_server, daemon=True)
        cls.server_thread.start()
        
        # Wait for server to start
        max_retries = 30
        for i in range(max_retries):
            try:
                resp = requests.get(f"http://{cls.host}:{cls.port}/", timeout=1)
                if resp.status_code == 200:
                    print(f"Server started on attempt {i+1}")
                    return
            except Exception as e:
                if i % 5 == 0:
                    print(f"Retry {i+1}: Server not ready yet... ({e})")
                time.sleep(1)
        
        raise RuntimeError("Server failed to start after 30 seconds")

    def test_ui_loads(self):
        """Check if the main page loads and contains expected Archeon branding."""
        resp = requests.get(f"http://{self.host}:{self.port}/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Archeon 3D Pro", resp.text)
        print("UI Load verified.")

    def test_gradio_config_endpoint(self):
        """Check if Gradio config is accessible."""
        resp = requests.get(f"http://{self.host}:{self.port}/config")
        self.assertEqual(resp.status_code, 200)
        config = resp.json()
        self.assertIn("components", config)
        print("Gradio Config verified.")

if __name__ == "__main__":
    unittest.main()
