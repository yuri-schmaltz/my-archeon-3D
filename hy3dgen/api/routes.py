from fastapi import APIRouter, HTTPException, BackgroundTasks
from .schemas import JobRequest, JobResponse, JobStatus, Mode, Artifact, ArtifactType, Batch
import uuid
import asyncio
import traceback
import os
from .utils import download_image_as_pil

router = APIRouter()

request_manager = None
jobs_db = {} 

def get_manager():
    if request_manager is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return request_manager

async def map_request_to_params(req: JobRequest) -> dict:
    params = {
        "model_key": "Normal", # or "Primary"
        "text": req.input.text_prompt,
        "negative_prompt": req.input.negative_prompt,
        "image": None, 
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
    
    if req.input.images:
        primary = req.input.images[0]
        try:
            pil_img = await download_image_as_pil(primary.uri)
            params["image"] = pil_img
        except Exception as e:
            print(f"Failed to load image {primary.uri}: {e}")
            raise HTTPException(status_code=400, detail=f"Failed to load image: {e}")
    
    return params

async def background_job_wrapper(job_id: str, params: dict):
    mgr = get_manager()
    jobs_db[job_id]["status"] = JobStatus.GENERATING
    
    try:
        # Submit blocks until generation is done
        result = await mgr.submit(params, uid=job_id)
        
        # Result interpretation
        # InferencePipeline.generate returns (mesh_path, glb_path_if_any??) or just path?
        # Usually it returns paths. If using Gradio wrapper it returns (path, html).
        # Internal model worker returns path string or tuple.
        # We assume it returns the mesh path (GLB/OBJ).
        
        mesh_path = None
        if isinstance(result, (list, tuple)):
            mesh_path = result[0]
        else:
            mesh_path = str(result)
            
        jobs_db[job_id]["status"] = JobStatus.COMPLETED
        
        artifacts = []
        if mesh_path and os.path.exists(mesh_path):
             artifacts.append(Artifact(
                type=ArtifactType.MESH,
                format="glb" if mesh_path.endswith(".glb") else "obj",
                uri=mesh_path,
                metadata={
                    "path": mesh_path 
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
        return JobResponse(
            request_id=job_id,
            status=jobs_db[job_id]["status"],
            artifacts=jobs_db[job_id].get("artifacts", []),
            error=jobs_db[job_id].get("error")
        )
    
    # Check if batch was intended but submitted to single endpoint? No, schema handles it.
    
    # Init DB
    jobs_db[job_id] = {
        "status": JobStatus.QUEUED,
        "artifacts": [],
        "error": None
    }
    
    try:
        params = await map_request_to_params(req)
        background_tasks.add_task(background_job_wrapper, job_id, params)
    except HTTPException as he:
        # If mapping fails (e.g. image download), fail immediately
        jobs_db[job_id]["status"] = JobStatus.FAILED
        jobs_db[job_id]["error"] = {"code": "VALIDATION_ERROR", "message": he.detail, "details": [], "retryable": False}
        return JobResponse(
            request_id=job_id,
            status=JobStatus.FAILED,
            artifacts=[],
            error=jobs_db[job_id]["error"]
        )
    
    return JobResponse(
        request_id=job_id,
        status=JobStatus.QUEUED,
        artifacts=[],
        error=None
    )

@router.post("/v1/batches")
async def create_batch(req: JobRequest, background_tasks: BackgroundTasks):
    """
    Experimental Batch Endpoint.
    The Contract defines 'batch' in JobRequest, effectively making JobRequest a potential BatchRequest.
    If 'batch.enabled' is true, we treat 'batch.items' as the payloads.
    
    However, the schemas.py defined JobRequest as a SINGLE job with a 'batch' config block.
    If the user wants to submit multiple jobs, they often send an array or a specific BatchRequest.
    
    Given the schema:
    job.batch.enabled = True
    job.batch.items = [ { "input": ... }, { "input": ... } ] (Overriding base input)
    
    We will iterate items, merge with base request, and spawn jobs.
    """
    
    if not req.batch or not req.batch.enabled:
        # Just a normal job
        return await create_job(req, background_tasks)
    
    responses = []
    
    base_id = req.request_id
    items = req.batch.items
    
    for idx, item_override in enumerate(items):
        # Construct sub-request
        # This is a shallow merge for MVP
        sub_id = f"{base_id}_{idx}"
        
        # Clone req
        sub_req = req.model_copy(deep=True)
        sub_req.request_id = sub_id
        sub_req.batch.enabled = False # Prevent recursion
        
        # Apply overrides from item dict
        # item_override might have "input": {...}
        if "input" in item_override:
            # Pydantic update or manual merge?
            # For strictness, manual merge of prompt
            if "text_prompt" in item_override["input"]:
                sub_req.input.text_prompt = item_override["input"]["text_prompt"]
            # ... support other overrides as needed
            
        # Spawn
        resp = await create_job(sub_req, background_tasks)
        responses.append(resp)
        
    return responses

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
