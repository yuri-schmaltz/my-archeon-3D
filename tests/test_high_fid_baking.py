import sys
from unittest.mock import MagicMock, AsyncMock, patch
import tempfile
import os
import trimesh
from fastapi.testclient import TestClient

# Mock heavy deps
sys.modules["hy3dgen.manager"] = MagicMock()
sys.modules["hy3dgen.inference"] = MagicMock()

import hy3dgen.api.routes as routes
routes.get_manager = MagicMock()

# Mock blender utils
mock_blender = MagicMock()
mock_blender.is_blender_available.return_value = True
# Mock bake_mesh_maps to return dummy files
async def mock_bake(h, l, maps):
    res = {}
    for m in maps:
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tmp.write(b"dummy_map")
        tmp.close()
        res[m] = tmp.name
    return res
mock_blender.bake_mesh_maps = mock_bake
sys.modules["hy3dgen.meshops.blender_utils"] = mock_blender

from hy3dgen.apps.api_server import create_app

def create_temp_mesh(name="mesh"):
    mesh = trimesh.creation.box()
    tmp = tempfile.NamedTemporaryFile(suffix=".glb", delete=False)
    mesh.export(tmp.name)
    tmp.close()
    return tmp.name

def test_high_fidelity_baking_ops():
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

    # 1. Prepare Meshes
    high_poly = create_temp_mesh("high")
    low_poly = create_temp_mesh("low")
    
    high_uri = f"file://{high_poly}"
    low_uri = f"file://{low_poly}"

    # 2. Construct Payload
    payload = {
        "request_id": "bake_test_01",
        "mode": "mesh_ops",
        "input": {
            "source_meshes": [
                {"mesh_id": "high_poly", "uri": high_uri, "format": "glb"},
                {"mesh_id": "low_poly", "uri": low_uri, "format": "glb"}
            ]
        },
        "operations": [
            {
                "op_id": "bake1", 
                "type": "texture_bake", 
                "target": {"mesh_id": "low_poly"}, 
                "params": {
                    "high_mesh_id": "high_poly",
                    "maps": ["normal", "ao"]
                }
            }
        ],
        "constraints": { "target_formats": ["glb"] },
        "output": { "artifact_prefix": "baked_asset", "return_preview_renders": False }
    }

    # 3. Submit
    resp = client.post("/v1/jobs", json=payload)
    assert resp.status_code == 200
    
    # 4. Poll
    import time
    for _ in range(20):
        r = client.get("/v1/jobs/bake_test_01")
        d = r.json()
        if d["status"] == "completed": break
        if d["status"] == "failed": raise RuntimeError(f"Job failed: {d['error']}")
        time.sleep(0.1)
        
    assert d["status"] == "completed"
    
    # 5. Verify Artifacts
    artifacts = d["artifacts"]
    map_types_found = set()
    for art in artifacts:
        if art["type"] == "textures":
            mtype = art["metadata"].get("map_type")
            if mtype: map_types_found.add(mtype)
            
    assert "normal" in map_types_found
    assert "ao" in map_types_found
    print(f"Baking test passed! Found maps: {map_types_found}")
    
    os.unlink(high_poly)
    os.unlink(low_poly)

if __name__ == "__main__":
    try:
        test_high_fidelity_baking_ops()
        print("PASS")
    except Exception as e:
        print(f"FAIL: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
