import sys
from unittest.mock import MagicMock, AsyncMock
import asyncio
import time
import json
import httpx
from fastapi.testclient import TestClient

# --- PRE-IMPORT MOCKING ---
# Mocking heavy components to run API in test mode
mock_manager = MagicMock()
class StubModelManager:
    def __init__(self, *args, **kwargs): pass
    def register_model(self, *args, **kwargs): pass

class StubPriorityRequestManager:
    def __init__(self, *args, **kwargs): pass
    async def start(self): pass
    async def stop(self): pass
    async def submit(self, params, uid=None):
        # Simulate work
        await asyncio.sleep(0.5)
        return ["/tmp/mock_mesh.glb"]

mock_manager.ModelManager = StubModelManager
mock_manager.PriorityRequestManager = StubPriorityRequestManager
sys.modules["hy3dgen.manager"] = mock_manager

mock_inference = MagicMock()
sys.modules["hy3dgen.inference"] = mock_inference
sys.modules["trimesh"] = MagicMock()

# Mock utils
mock_utils = MagicMock()
mock_utils.download_image_as_pil = AsyncMock(return_value="MockPILImage")
sys.modules["hy3dgen.api.utils"] = mock_utils

# --------------------------

from hy3dgen.apps.api_server import create_app

class MockArgs:
    model_path = "mock"
    subfolder = "mock"
    texgen_model_path = "mock"
    port = 8085
    host = "0.0.0.0"
    device = "cpu"
    low_vram_mode = True

app, _ = create_app(MockArgs())

async def run_stress_test():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Prepare 20 concurrent requests
        payload = {
            "request_id": "stress_job_",
            "mode": "text_to_3d",
            "input": { "text_prompt": "Prompt " },
            "constraints": { "target_formats": ["glb"] },
            "quality": { "preset": "draft", "determinism": "best_effort" },
            "postprocess": { "cleanup": True, "retopo": False, "decimate": False, "bake_textures": False, "remove_hidden": False, "fix_normals": False, "generate_collision": False },
            "output": { "artifact_prefix": "out", "return_preview_renders": False },
            "batch": { "enabled": False }
        }

        async def submit_job(idx):
            p = payload.copy()
            p["request_id"] = f"stress_job_{idx}"
            p["input"]["text_prompt"] = f"Prompt {idx}"
            start = time.time()
            resp = await client.post("/v1/jobs", json=p)
            duration = time.time() - start
            return resp.status_code, duration

        print("Submitting 20 concurrent jobs...")
        start_all = time.time()
        tasks = [submit_job(i) for i in range(20)]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_all

        # 2. Analyze results
        success_count = sum(1 for status, _ in results if status == 200)
        avg_resp_time = sum(dur for _, dur in results) / len(results)

        print(f"Results: {success_count}/20 successful")
        print(f"Total submission time: {total_time:.2f}s")
        print(f"Avg response time: {avg_resp_time:.4f}s")

        if success_count < 20:
            print("FAILED: Some jobs were not queued correctly.")
            sys.exit(1)
            
        # 3. Poll for completion (Sample one)
        print("Polling for job 10...")
        for _ in range(20):
            resp = await client.get("/v1/jobs/stress_job_10")
            data = resp.json()
            if data["status"] == "completed":
                print("Job 10 completed successfully!")
                break
            await asyncio.sleep(0.5)
        else:
            print("FAILED: Job 10 did not complete in time.")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_stress_test())
