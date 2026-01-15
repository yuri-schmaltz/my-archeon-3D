import sys
from unittest.mock import MagicMock, AsyncMock
import numpy as np
import tempfile
import os
import trimesh
import json
import logging
from fastapi.testclient import TestClient

# Mock heavy deps
# we need to mock manager because routes.py imports 'get_manager' and fails if not set?
# actually 'get_manager' throws 503 if not set, which is fine for meshops if it doesnt call it
# but background_job_wrapper imports it.
sys.modules["hy3dgen.manager"] = MagicMock()
sys.modules["hy3dgen.inference"] = MagicMock()

from hy3dgen.apps.api_server import create_app

def create_temp_mesh():
    mesh = trimesh.creation.box()
    tmp = tempfile.NamedTemporaryFile(suffix=".glb", delete=False)
    mesh.export(tmp.name)
    tmp.close()
    return tmp.name

def test_meshops_flow():
    # Setup App
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
    print(f"Created temp mesh at {uri}")

    # 2. Construct Payload
    payload = {
        "request_id": "meshops_test_01",
        "mode": "mesh_ops",
        "input": {
            "source_meshes": [
                {"mesh_id": "box", "uri": uri, "format": "glb"}
            ]
        },
        "operations": [
            {"op_id": "op1", "type": "validate", "target": {"mesh_id": "*"}},
            {"op_id": "op2", "type": "transform", "target": {"mesh_id": "*"}, "params": {"scale": 2.0}}
        ],
        "constraints": {
            "target_formats": ["glb"],
            "materials": {"pbr": False, "texture_resolution": 1024, "maps": [], "single_material": True}, # dummy
        },
        "output": {
            "artifact_prefix": "meshops_out",
            "return_preview_renders": False
        }
    }

    # 3. Submit
    resp = client.post("/v1/jobs", json=payload)
    if resp.status_code != 200:
        raise AssertionError(f"Status {resp.status_code}: {resp.text}")
    assert resp.status_code == 200
    
    # 4. Poll
    import time
    for _ in range(10):
        r = client.get(f"/v1/jobs/meshops_test_01")
        d = r.json()
        if d["status"] == "completed":
            break
        if d["status"] == "failed":
            raise RuntimeError(f"Job failed: {d.get('error')}")
        time.sleep(0.1)
        
    assert d["status"] == "completed"
    artifacts = d["artifacts"]
    print("Job Completed. Artifacts:", len(artifacts))
    
    found_mesh = False
    found_report = False
    
    for art in artifacts:
        if art["type"] == "mesh":
            found_mesh = True
            print(f"Mesh: {art['uri']}")
        if art["type"] == "report":
            found_report = True
            print(f"Report: {art['metadata']}")

    assert found_mesh
    assert found_report
    
    # Cleanup
    os.unlink(mesh_path)

if __name__ == "__main__":
    try:
        test_meshops_flow()
        with open("meshops_result.txt", "w") as f:
            f.write("PASS")
    except BaseException as e:
        import traceback
        with open("meshops_result.txt", "w") as f:
            f.write(f"FAIL: {repr(e)}\n")
            traceback.print_exc(file=f)
        exit(1)
