import sys
from unittest.mock import MagicMock, AsyncMock
import tempfile
import os
import trimesh
from fastapi.testclient import TestClient
from PIL import Image
import numpy as np

# Mock heavy deps
sys.modules["hy3dgen.manager"] = MagicMock()
sys.modules["hy3dgen.inference"] = MagicMock()

# Mock the texture model specifically
mock_inf_pipe = MagicMock()
mock_tex_pipe = MagicMock()
mock_inf_pipe.pipeline_tex = mock_tex_pipe

import hy3dgen.api.routes as routes
routes.get_manager = MagicMock()
routes.get_manager().get_worker = AsyncMock(return_value=mock_inf_pipe)

from hy3dgen.apps.api_server import create_app

def create_temp_mesh():
    mesh = trimesh.creation.box()
    tmp = tempfile.NamedTemporaryFile(suffix=".glb", delete=False)
    mesh.export(tmp.name)
    tmp.close()
    return tmp.name

def create_temp_image():
    img = Image.new("RGB", (64, 64), (255, 255, 255))
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    img.save(tmp.name)
    tmp.close()
    return tmp.name

def test_auto_texture_ops():
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

    # 1. Prepare Mesh and Image
    mesh_path = create_temp_mesh()
    img_path = create_temp_image()
    mesh_uri = f"file://{mesh_path}"
    img_uri = f"file://{img_path}"

    # 2. Mock PaintPipeline behavior
    def mock_paint(mesh, image, **kwargs):
        textured = mesh.copy()
        img = Image.new("RGB", (64, 64), (255, 0, 0))
        textured.visual = trimesh.visual.TextureVisuals(
            uv=np.zeros((len(mesh.vertices), 2)),
            image=img
        )
        return textured
    
    mock_tex_pipe.side_effect = mock_paint

    # 3. Construct Payload
    payload = {
        "request_id": "tex_test_01",
        "mode": "mesh_ops",
        "input": {
            "source_meshes": [{"mesh_id": "box", "uri": mesh_uri, "format": "glb"}],
            "aux_inputs": {
                "reference_images": [{"image_id": "ref", "uri": img_uri, "role": "reference"}]
            }
        },
        "operations": [
            {"op_id": "tex1", "type": "auto_texture", "target": {"mesh_id": "box"}, "params": {"steps": 10}}
        ],
        "constraints": { "target_formats": ["glb"] },
        "output": { "artifact_prefix": "tex_out", "return_preview_renders": False }
    }

    # 4. Submit
    resp = client.post("/v1/jobs", json=payload)
    assert resp.status_code == 200
    
    # 5. Poll
    import time
    for _ in range(20):
        r = client.get("/v1/jobs/tex_test_01")
        d = r.json()
        if d["status"] == "completed": break
        if d["status"] == "failed": raise RuntimeError(f"Job failed: {d['error']}")
        time.sleep(0.1)
        
    assert d["status"] == "completed"
    print("Auto-texture test passed!")
    
    os.unlink(mesh_path)
    os.unlink(img_path)

if __name__ == "__main__":
    try:
        test_auto_texture_ops()
        print("PASS")
    except Exception as e:
        print(f"FAIL: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
