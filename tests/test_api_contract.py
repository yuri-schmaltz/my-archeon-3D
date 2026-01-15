import sys
from unittest.mock import MagicMock, AsyncMock

# --- PRE-IMPORT MOCKING ---
mock_manager = MagicMock()
class StubModelManager:
    def __init__(self, *args, **kwargs): pass
    def register_model(self, *args, **kwargs): pass

class StubPriorityRequestManager:
    def __init__(self, *args, **kwargs): pass
    async def start(self): pass
    async def stop(self): pass
    async def submit(self, params, uid=None):
        return ["/tmp/mock_mesh.glb"]

mock_manager.ModelManager = StubModelManager
mock_manager.PriorityRequestManager = StubPriorityRequestManager
sys.modules["hy3dgen.manager"] = mock_manager

mock_inference = MagicMock()
mock_inference.InferencePipeline = MagicMock()
sys.modules["hy3dgen.inference"] = mock_inference

# Mock utils which uses httpx/PIL
mock_utils = MagicMock()
mock_utils.download_image_as_pil = AsyncMock(return_value="MockPILImage")
sys.modules["hy3dgen.api.utils"] = mock_utils

# --------------------------

from fastapi.testclient import TestClient
from hy3dgen.apps.api_server import create_app, routes_module
import time

# Create App
class MockArgs:
    model_path = "mock"
    subfolder = "mock"
    texgen_model_path = "mock"
    port = 8081
    host = "0.0.0.0"
    device = "cpu"
    low_vram_mode = True

app, _ = create_app(MockArgs())
client = TestClient(app)

def test_batch_job():
    payload = {
        "request_id": "batch_root_01",
        "schema_version": "1.0",
        "mode": "text_to_3d",
        "input": { "text_prompt": "Base prompt" },
        "constraints": { "target_format": ["glb"], "poly_budget": {"max_tris": 1000, "prefer_quads": False}, "materials": {"pbr": True, "maps":["basecolor"], "texture_resolution": 512, "single_material":True}}, 
        "quality": { "preset": "draft", "determinism": "best_effort" },
        "postprocess": { "cleanup": True, "retopo": False, "decimate": False, "bake_textures": False, "remove_hidden": False, "fix_normals": False, "generate_collision": False },
        "output": { "artifact_prefix": "out", "return_preview_renders": False },
        "batch": {
            "enabled": True,
            "items": [
                { "input": { "text_prompt": "Override 1" } },
                { "input": { "text_prompt": "Override 2" } }
            ]
        }
    }

    # Post to /v1/batches
    response = client.post("/v1/batches", json=payload)
    if response.status_code != 200:
        print(f"Batch Error: {response.text}")
        
    assert response.status_code == 200
    data = response.json()
    
    # Should return list of JobResponse
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["request_id"] == "batch_root_01_0"
    assert data[1]["request_id"] == "batch_root_01_1"

    print("Batch submittted successfully.")

if __name__ == "__main__":
    try:
        test_batch_job()
        with open("debug_result.txt", "w") as f:
            f.write("PASS")
    except Exception as e:
        with open("debug_result.txt", "w") as f:
            f.write(f"FAIL: {e}")
        print(e)
        exit(1)
