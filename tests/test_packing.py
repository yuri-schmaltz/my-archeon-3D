import sys
from unittest.mock import MagicMock, AsyncMock
import tempfile
import os
import trimesh
from fastapi.testclient import TestClient
from PIL import Image
import numpy as np
from io import BytesIO

# Mock heavy deps
sys.modules["hy3dgen.manager"] = MagicMock()
sys.modules["hy3dgen.inference"] = MagicMock()

import hy3dgen.api.routes as routes
routes.get_manager = MagicMock()

from hy3dgen.apps.api_server import create_app

def create_temp_image(color):
    img = Image.new("RGB", (64, 64), color)
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    img.save(tmp.name)
    tmp.close()
    return tmp.name

def create_temp_mesh():
    mesh = trimesh.creation.box()
    tmp = tempfile.NamedTemporaryFile(suffix=".glb", delete=False)
    mesh.export(tmp.name)
    tmp.close()
    return tmp.name

def test_channel_packing_ops():
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

    # 1. Prepare Inputs
    mesh_path = create_temp_mesh()
    ao_path = create_temp_image((200, 200, 200)) # Grey AO
    rough_path = create_temp_image((128, 128, 128)) # Mid roughness
    
    mesh_uri = f"file://{mesh_path}"
    ao_uri = f"file://{ao_path}"
    rough_uri = f"file://{rough_path}"

    # 2. Construct Payload
    payload = {
        "request_id": "pack_test_01",
        "mode": "mesh_ops",
        "input": {
            "source_meshes": [{"mesh_id": "box", "uri": mesh_uri, "format": "glb"}],
            "aux_inputs": {
                "texture_sources": [
                    {"source_id": "ao", "uri": ao_uri, "type": "single_image", "maps": ["ao"]},
                    {"source_id": "rough", "uri": rough_uri, "type": "single_image", "maps": ["roughness"]}
                ]
            }
        },
        "operations": [
            {"op_id": "p1", "type": "channel_packing", "target": {"mesh_id": "*"}, "params": {"preset": "orm"}}
        ],
        "constraints": { "target_formats": ["glb"] },
        "output": { "artifact_prefix": "pack_out", "return_preview_renders": False }
    }

    # 3. Submit
    resp = client.post("/v1/jobs", json=payload)
    assert resp.status_code == 200
    
    # 4. Poll
    import time
    for _ in range(20):
        r = client.get("/v1/jobs/pack_test_01")
        d = r.json()
        if d["status"] == "completed": break
        if d["status"] == "failed": raise RuntimeError(f"Job failed: {d['error']}")
        time.sleep(0.1)
        
    assert d["status"] == "completed"
    
    # 5. Verify Artifacts
    artifacts = d["artifacts"]
    found_packed = False
    for art in artifacts:
        if art["type"] == "textures" and "packed_orm" in art["uri"]:
            found_packed = True
            print(f"Found packed texture: {art['uri']}")
            assert os.path.exists(art["uri"])
            
    assert found_packed
    print("Channel packing test passed!")
    
    os.unlink(mesh_path)
    os.unlink(ao_path)
    os.unlink(rough_path)

if __name__ == "__main__":
    try:
        test_channel_packing_ops()
        print("PASS")
    except Exception as e:
        print(f"FAIL: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
