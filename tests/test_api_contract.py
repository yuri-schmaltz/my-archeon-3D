import sys
from unittest.mock import MagicMock

# --- PRE-IMPORT MOCKING ---
# We mock heavy modules before `api_server` imports them.
# This avoids loading torch/transformers/diffusers during API logic testing.

mock_manager = MagicMock()
class StubModelManager:
    def __init__(self, *args, **kwargs): pass
    def register_model(self, *args, **kwargs): pass

class StubPriorityRequestManager:
    def __init__(self, *args, **kwargs): pass
    async def start(self): pass
    async def stop(self): pass
    async def submit(self, params, uid=None):
        # Return a mock result typical of the worker
        return ["/tmp/mock_mesh.glb"]

mock_manager.ModelManager = StubModelManager
mock_manager.PriorityRequestManager = StubPriorityRequestManager
sys.modules["hy3dgen.manager"] = mock_manager

mock_inference = MagicMock()
mock_inference.InferencePipeline = MagicMock()
sys.modules["hy3dgen.inference"] = mock_inference

# --------------------------

from fastapi.testclient import TestClient
from hy3dgen.apps.api_server import create_app, routes_module
import time

# Verify mocks worked (optional)
# print("DEBUG: Manager is", sys.modules["hy3dgen.manager"])

# Mock Args for create_app
class MockArgs:
    model_path = "mock"
    subfolder = "mock"
    texgen_model_path = "mock"
    port = 8081
    host = "0.0.0.0"
    device = "cpu"
    low_vram_mode = True

# Create App
app, _ = create_app(MockArgs())

# We need to ensure routes_module uses our StubPriorityRequestManager logic
# The create_app instantiates StubPriorityRequestManager.
# Our stub implementation of `submit` is above.

client = TestClient(app)

def test_create_and_get_job():
    payload = {
        "request_id": "test_req_fast_001",
        "schema_version": "1.0",
        "mode": "text_to_3d",
        "input": {
            "text_prompt": "Fast test",
        },
        "constraints": {
            "target_format": ["glb"],
            "poly_budget": { "max_tris": 100000, "prefer_quads": True },
            "topology": { "watertight": True, "manifold": True, "no_self_intersections": True },
            "uv": { "required": True },
            "materials": { 
                "pbr": True, 
                "texture_resolution": 1024, 
                "maps": ["basecolor"], 
                "single_material": True 
            },
            "background": "remove",
            "lod": { "generate": False, "levels": [] },
            "rigging": { "generate": False, "type": "generic" }
        },
        "quality": {
            "preset": "draft",
            "steps": 10,
            "seed": 0,
            "determinism": "best_effort",
            "text_adherence": 0.5,
            "image_adherence": 0.5
        },
        "postprocess": {
            "cleanup": True,
            "retopo": False,
            "decimate": True,
            "bake_textures": True,
            "remove_hidden": True,
            "fix_normals": True,
            "generate_collision": False,
            "mesh_simplify_target_tris": 1000
        },
        "batch": { "enabled": False, "concurrency_hint": 1 },
        "output": {
            "artifact_prefix": "fast",
            "return_preview_renders": False,
            "preview_angles_deg": []
        }
    }

    # 1. Create Job
    response = client.post("/v1/jobs", json=payload)
    if response.status_code != 200:
        print(f"Error: {response.text}")
    assert response.status_code == 200
    data = response.json()
    assert data["request_id"] == "test_req_fast_001"
    assert data["status"] == "queued"

    # 2. Poll Job
    for i in range(10):
        resp_get = client.get(f"/v1/jobs/test_req_fast_001")
        assert resp_get.status_code == 200
        status_data = resp_get.json()
        if status_data["status"] == "completed":
            print("Job Completed!")
            break
        if status_data["status"] == "failed":
            print(f"Job Failed: {status_data.get('error')}")
            break
        print(f"Polling... {status_data['status']}")
        time.sleep(0.1)
        
    assert status_data["status"] == "completed"
    assert len(status_data["artifacts"]) > 0

if __name__ == "__main__":
    try:
        test_create_and_get_job()
        with open("debug_result.txt", "w") as f:
            f.write("PASS")
    except Exception as e:
        with open("debug_result.txt", "w") as f:
            f.write(f"FAIL: {e}")
        exit(1)
