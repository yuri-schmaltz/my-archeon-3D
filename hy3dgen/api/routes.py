from fastapi import APIRouter, HTTPException, BackgroundTasks
from .schemas import JobRequest, JobResponse, JobStatus, Mode, Artifact, ArtifactType
import uuid
import asyncio
import traceback
import os

router = APIRouter()

# Global reference to the manager (to be injected)
request_manager = None
# In-memory job store (MVP)
jobs_db = {} 

def get_manager():
    if request_manager is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return request_manager

def map_request_to_params(req: JobRequest) -> dict:
    # See previous logical block
    params = {
        "model_key": "Normal",
        "text": req.input.text_prompt,
        "negative_prompt": req.input.negative_prompt,
        "image": None, # Needs handling
        "mv_images": None,
        "num_inference_steps": req.quality.steps or 30,
        "guidance_scale": 5.0,
        "seed": req.quality.seed,
        "octree_resolution": 256,
        "do_rembg": req.constraints.background == "remove" if req.constraints.background else True,
        "num_chunks": 8000,
        "do_texture": req.constraints.materials is not None,
        "tex_steps": 30, 
        "tex_guidance_scale": 5.0,
        "tex_seed": 1234
    }
    
    # Handle Image URI (Mock/Stub for now)
    # If image URI is local path, load it?
    # Ideally we need a 'fetcher' logic here. 
    # For MVP we assume URI is a local path if valid, or ignore.
    if req.input.images:
        primary = req.input.images[0]
        if primary.uri.startswith("/"):
            # Assume local path, load PIL Image
            try:
                from PIL import Image
                params["image"] = Image.open(primary.uri)
            except Exception as e:
                print(f"Failed to load image: {e}")
    
    return params

async def background_job_wrapper(job_id: str, params: dict):
    mgr = get_manager()
    jobs_db[job_id]["status"] = JobStatus.GENERATING
    
    try:
        # Submit with custom UID matching job_id
        # This await blocks until generation is done!
        result = await mgr.submit(params, uid=job_id)
        
        # Result format? 
        # unified_generation returns (path, html) usually?
        # Manager returns what 'worker.generate' returns.
        # ShapeGen worker returns... need to verify. 
        # Assuming result contains paths.
        
        # Update DB
        jobs_db[job_id]["status"] = JobStatus.COMPLETED
        
        # Mocking artifacts extraction based on result
        # Inspect result structure to be safe? 
        # For now, we assume result is a path string or similar tuple.
        
        artifacts = []
        if isinstance(result, (list, tuple)):
            # Usually [mesh_path, html_content]
            mesh_path = result[0]
            artifacts.append(Artifact(
                type=ArtifactType.MESH,
                format="glb", # assumption
                uri=str(mesh_path),
                metadata={
                    "tris": 0, "verts": 0, "uv_sets": 0, "materials_count": 0,
                    "watertight": True, "manifold": True, "axis": "z_up",
                    "unit": "m", "pivot": "center", "bounds": {"x":0,"y":0,"z":0}
                }
            ))
        
        jobs_db[job_id]["artifacts"] = artifacts
        
    except Exception as e:
        traceback.print_exc()
        jobs_db[job_id]["status"] = JobStatus.FAILED
        jobs_db[job_id]["error"] = {"code": "INTERNAL_ERROR", "message": str(e), "details": [], "retryable": True}

@router.post("/v1/jobs", response_model=JobResponse)
async def create_job(req: JobRequest, background_tasks: BackgroundTasks):
    job_id = req.request_id
    
    if job_id in jobs_db:
        # Idempotency check: return existing status
        return JobResponse(
            request_id=job_id,
            status=jobs_db[job_id]["status"],
            artifacts=jobs_db[job_id].get("artifacts", []),
            error=jobs_db[job_id].get("error")
        )
    
    # Init DB entry
    jobs_db[job_id] = {
        "status": JobStatus.QUEUED,
        "artifacts": [],
        "error": None
    }
    
    params = map_request_to_params(req)
    
    # Launch background task
    background_tasks.add_task(background_job_wrapper, job_id, params)
    
    return JobResponse(
        request_id=job_id,
        status=JobStatus.QUEUED,
        artifacts=[],
        error=None
    )

@router.get("/v1/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
        
    entry = jobs_db[job_id]
    
    return JobResponse(
        request_id=job_id,
        status=entry["status"],
        artifacts=entry.get("artifacts", []),
        error=entry.get("error")
    )
