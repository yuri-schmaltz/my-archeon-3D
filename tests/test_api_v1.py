
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

# Mock dependencies before importing routes
# We must mock hy3dgen.manager to avoid GPU initialization
mock_manager_module = MagicMock()
sys.modules["hy3dgen.manager"] = mock_manager_module

# Now import app
from hy3dgen.apps.api_server import create_app
from hy3dgen.api.schemas import JobRequest, JobStatus

from unittest.mock import MagicMock, patch, AsyncMock

# ... (imports)

# Create a dummy app with mocked components
@pytest.fixture
def client():
    # Mock classes
    with patch("hy3dgen.apps.api_server.ModelManager"), \
         patch("hy3dgen.apps.api_server.PriorityRequestManager") as MockReqMgr, \
         patch("hy3dgen.api.routes.download_image_as_pil") as MockDownload:
        
        # Mock download to return a dummy image
        MockDownload.return_value = MagicMock() 

        # Setup Request Manager Mock
        mock_req_mgr = MockReqMgr.return_value
        
        # Make async methods awaitable AND compatible with create_task
        async def noop(): pass
        mock_req_mgr.start.side_effect = noop
        mock_req_mgr.stop.side_effect = noop
        
        mock_req_mgr.create_job = AsyncMock(return_value={"request_id": "test_txt_01", "status": "queued"})
        mock_req_mgr.get_job = AsyncMock()
        
        # Initialize App
        app, _ = create_app(MagicMock(low_vram_mode=False, device="cpu"))
        
        # Inject mocks AND Reset DB
        from hy3dgen.api import routes
        routes.request_manager = mock_req_mgr
        routes.jobs_db = {} # Reset for clean state
        
        # Pre-seed DB for get_job test
        routes.jobs_db["valid_job"] = {
            "status": JobStatus.COMPLETED,
            "artifacts": [],
            "error": None
        }

        with TestClient(app) as c:
            yield c

def test_system_health(client):
    """Test the health check endpoint."""
    response = client.get("/v1/system/health")
    assert response.status_code == 200
    assert response.json() == {"status": "online", "version": "1.0.0"}

def test_create_job_text_to_3d_valid(client):
    """Test happy path for text-to-3d job creation."""
    payload = {
        "request_id": "test_txt_01",
        "mode": "text_to_3d",
        "input": {
            "text_prompt": "A beautiful chair"
        },
        "quality": {
            "preset": "standard",
            "steps": 30,
            "seed": 123,
            "determinism": "best_effort"
        },
        "constraints": { "target_formats": ["glb"] },
        "postprocess": { "cleanup": True, "retopo": False, "decimate": False, "bake_textures": False, "remove_hidden": False, "fix_normals": False, "generate_collision": False },
        "batch": { "enabled": False },
        "output": { "artifact_prefix": "chair", "return_preview_renders": False }
    }
    
    response = client.post("/v1/jobs", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["request_id"] == "test_txt_01"
    assert data["status"] == "queued"

def test_create_job_image_to_3d_valid(client):
    """Test happy path for image-to-3d job creation."""
    payload = {
        "request_id": "test_img_01",
        "mode": "image_to_3d",
        "input": {
            "images": [
                {
                    "image_id": "ref1",
                    "uri": "file:///tmp/image.png",
                    "role": "reference"
                }
            ]
        },
        "quality": {
            "preset": "standard",
            "steps": 30,
            "seed": 123,
            "determinism": "best_effort"
        },
        "constraints": { "target_formats": ["glb"] },
        "postprocess": { "cleanup": True, "retopo": False, "decimate": False, "bake_textures": False, "remove_hidden": False, "fix_normals": False, "generate_collision": False },
        "batch": { "enabled": False },
        "output": { "artifact_prefix": "img3d", "return_preview_renders": False }
    }
    
    response = client.post("/v1/jobs", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "queued"

def test_create_job_invalid_schema(client):
    """Test schema validation failure."""
    # Missing 'quality', 'constraints' etc
    payload = {
        "request_id": "bad_req",
        "mode": "text_to_3d",
        "input": {} 
    }
    response = client.post("/v1/jobs", json=payload)
    assert response.status_code == 422

def test_get_job_status(client):
    """Test polling a job status."""
    # Depends on 'valid_job' being seeded in fixture
    response = client.get("/v1/jobs/valid_job")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"

def test_get_job_not_found(client):
    """Test polling a non-existent job."""
    response = client.get("/v1/jobs/unknown_id")
    assert response.status_code == 404
