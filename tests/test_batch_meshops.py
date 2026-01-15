import sys
from unittest.mock import MagicMock, AsyncMock
import tempfile
import os
import trimesh
from fastapi.testclient import TestClient

# Mock heavy deps
sys.modules["hy3dgen.manager"] = MagicMock()
sys.modules["hy3dgen.inference"] = MagicMock()

import hy3dgen.api.routes as routes
routes.get_manager = MagicMock()

from hy3dgen.apps.api_server import create_app

def create_temp_mesh():
    mesh = trimesh.creation.uv_sphere()
    tmp = tempfile.NamedTemporaryFile(suffix=".glb", delete=False)
    mesh.export(tmp.name)
    tmp.close()
    return tmp.name

def test_batch_meshops_polymorphic():
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

    # 1. Prepare Mesh
    mesh_path = create_temp_mesh()
    uri = f"file://{mesh_path}"

    # 2. Construct Batch Payload
    payload = {
        "request_id": "batch_tex_test",
        "mode": "mesh_ops",
        "batch": {
            "enabled": True,
            "items": [
                {"input": {"source_meshes": [{"mesh_id": "s1", "uri": uri, "format": "glb"}]}},
                {"input": {"source_meshes": [{"mesh_id": "s2", "uri": uri, "format": "glb"}]}}
            ]
        },
        "input": {
            "source_meshes": [] # Base input can be empty if items override it
        },
        "operations": [
            {"op_id": "clean", "type": "cleanup", "target": {"mesh_id": "*"}, "params": {}},
            {"op_id": "scale", "type": "transform", "target": {"mesh_id": "s1"}, "params": {"scale": 2.0}, "depends_on": ["clean"]}
        ],
        "constraints": { "target_formats": ["glb"] },
        "output": { "artifact_prefix": "batch_out", "return_preview_renders": False }
    }

    # 3. Submit Batch
    resp = client.post("/v1/batches", json=payload)
    if resp.status_code != 200:
        print(f"Error 422: {resp.text}")
    assert resp.status_code == 200
    batch_responses = resp.json()
    assert len(batch_responses) == 2
    
    # 4. Poll each job
    import time
    for job_resp in batch_responses:
        jid = job_resp["request_id"]
        success = False
        for _ in range(30):
            r = client.get(f"/v1/jobs/{jid}")
            d = r.json()
            if d["status"] == "completed": 
                success = True
                break
            if d["status"] == "failed": raise RuntimeError(f"Job {jid} failed: {d['error']}")
            time.sleep(0.1)
        assert success
        print(f"Job {jid} passed!")
    
    print("Batch MeshOps test passed!")
    os.unlink(mesh_path)

if __name__ == "__main__":
    try:
        test_batch_meshops_polymorphic()
        print("PASS")
    except Exception as e:
        print(f"FAIL: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
