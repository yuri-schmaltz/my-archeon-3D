from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from typing import Union, Dict, Any
from .schemas import JobRequest, JobResponse, JobStatus, Mode, Artifact, ArtifactType, Batch, MeshOpsRequest
import uuid
import asyncio
import traceback
import os
from .utils import download_image_as_pil
from hy3dgen.meshops.engine import MeshOpsEngine

router = APIRouter()

request_manager = None
jobs_db = {} 
meshops_engine = MeshOpsEngine()

def get_manager():
    if request_manager is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return request_manager

async def map_request_to_params(req: JobRequest) -> dict:
    params = {
        "model_key": "Normal", 
        "text": req.input.text_prompt,
        "negative_prompt": req.input.negative_prompt,
        "image": None, 
        "mv_images": None,
        "num_inference_steps": req.quality or 30, # Handle quality object or int
        "guidance_scale": 5.0,
        "seed": req.quality.seed if req.quality else 0,
        "octree_resolution": 256,
        "do_rembg": req.constraints.background == "remove" if req.constraints.background else True,
        "num_chunks": 8000,
        "do_texture": req.constraints.materials is not None,
        "tex_steps": 30, 
        "tex_guidance_scale": 5.0,
        "tex_seed": 1234
    }
    
    # Fix quality.steps if it exists
    if hasattr(req.quality, 'steps'):
        params["num_inference_steps"] = req.quality.steps
    
    if req.input.images:
        primary = req.input.images[0]
        try:
            pil_img = await download_image_as_pil(primary.uri)
            params["image"] = pil_img
        except Exception as e:
            print(f"Failed to load image {primary.uri}: {e}")
            raise HTTPException(status_code=400, detail=f"Failed to load image: {e}")
    
    return params

async def background_job_wrapper(job_id: str, params: Union[dict, MeshOpsRequest]):
    jobs_db[job_id]["status"] = JobStatus.GENERATING
    
    try:
        # MeshOps Path
        if isinstance(params, MeshOpsRequest):
            artifacts = await meshops_engine.process_async(params)
            jobs_db[job_id]["status"] = JobStatus.COMPLETED
            jobs_db[job_id]["artifacts"] = artifacts
            return

        # Inference Pipeline Path
        mgr = get_manager()
        result = await mgr.submit(params, uid=job_id)
        
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

async def _process_request_and_queue(body: Dict[str, Any], background_tasks: BackgroundTasks) -> JobResponse:
    mode = body.get("mode")
    
    # Polymorphic Parsing
    if mode == Mode.MESH_OPS:
        try:
            req = MeshOpsRequest.model_validate(body)
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"MeshOps validation failed: {e}")
    else:
        try:
            req = JobRequest.model_validate(body)
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Job validation failed: {e}")
            
    job_id = req.request_id
    
    if job_id in jobs_db:
        return JobResponse(
            request_id=job_id,
            status=jobs_db[job_id]["status"],
            artifacts=jobs_db[job_id].get("artifacts", []),
            error=jobs_db[job_id].get("error")
        )
    
    jobs_db[job_id] = {
        "status": JobStatus.QUEUED,
        "artifacts": [],
        "error": None
    }
    
    try:
        if isinstance(req, MeshOpsRequest):
            background_tasks.add_task(background_job_wrapper, job_id, req)
        else:
            params = await map_request_to_params(req)
            background_tasks.add_task(background_job_wrapper, job_id, params)
            
    except HTTPException as he:
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

@router.post("/v1/jobs", response_model=JobResponse)
async def create_job(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()
    return await _process_request_and_queue(body, background_tasks)

@router.post("/v1/batches")
async def create_batch(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()
    
    # Check for batch structure
    batch_info = body.get("batch")
    if not batch_info or not batch_info.get("enabled"):
        # Fallback to single job parsing if batch is not enabled/present
        return [await _process_request_and_queue(body, background_tasks)]
    
    responses = []
    base_id = body.get("request_id", str(uuid.uuid4()))
    items = batch_info.get("items", [])
    
    for idx, item_override in enumerate(items):
        sub_id = f"{base_id}_{idx}"
        
        # Merge override with base body
        sub_body = body.copy()
        # Deep merge would be better but simple copy + update for common fields
        sub_body["request_id"] = sub_id
        # Disable batch in sub-requests to avoid loops
        sub_body["batch"] = {"enabled": False}
        
        # Apply overrides
        if "input" in item_override:
            if "input" not in sub_body: sub_body["input"] = {}
            for k, v in item_override["input"].items():
                sub_body["input"][k] = v
                
        if "quality" in item_override:
            sub_body["quality"] = item_override["quality"]

        resp = await _process_request_and_queue(sub_body, background_tasks)
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
