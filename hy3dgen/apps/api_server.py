# Hunyuan 3D is licensed under the TENCENT HUNYUAN NON-COMMERCIAL LICENSE AGREEMENT
# except for the third-party components listed below.
# Hunyuan 3D does not impose any additional limitations beyond what is outlined
# in the repsective licenses of these third-party components.
# Users must comply with all terms and conditions of original licenses of these third-party
# components and must ensure that the usage of the third party components adheres to
# all relevant laws and regulations.

# For avoidance of doubts, Hunyuan 3D means the large language models and
# their software and algorithms, including trained model weights, parameters (including
# optimizer states), machine-learning model code, inference-enabling code, training-enabling code,
# fine-tuning enabling code and other elements of the foregoing made publicly available
# by Tencent in accordance with TENCENT HUNYUAN COMMUNITY LICENSE AGREEMENT.

"""
A model worker executes the model.
"""
import argparse
import asyncio
import base64
import logging
import logging.handlers
import os
import sys
import tempfile
import threading
import traceback
import uuid
from io import BytesIO

import torch
import trimesh
import uvicorn
from PIL import Image
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
from typing import Optional, Union
from hy3dgen.manager import PriorityRequestManager, ModelManager
from hy3dgen.inference import InferencePipeline
import prometheus_client
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

from hy3dgen.shapegen.utils import get_logger
from hy3dgen.rembg import BackgroundRemover
logger = get_logger("api_server")

server_error_msg = "**NETWORK ERROR DUE TO HIGH TRAFFIC. PLEASE REGENERATE OR REFRESH THIS PAGE.**"
moderation_msg = "YOUR INPUT VIOLATES OUR CONTENT MODERATION GUIDELINES. PLEASE TRY AGAIN."

SAVE_DIR = 'gradio_cache'

worker_id = str(uuid.uuid4())[:6]

# Metrics
REQUEST_COUNT = Counter('app_request_count', 'Total application requests', ['method', 'endpoint', 'http_status'])
REQUEST_LATENCY = Histogram('app_request_latency_seconds', 'Request latency', ['endpoint'])
GENERATION_COUNT = Counter('app_generation_total', 'Total generations', ['status'])

# Global Manager
request_manager = None
rembg_processor = None

def load_image_from_base64(image):
    return Image.open(BytesIO(base64.b64decode(image)))

def apply_rembg(image):
    """Apply background removal to image if needed"""
    global rembg_processor
    if rembg_processor is None:
        rembg_processor = BackgroundRemover()
    
    # Convert to RGBA if needed
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    # Apply rembg
    image = rembg_processor(image)
    return image

app = FastAPI()
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Utility to generate correlation ID per request
import contextvars
request_id_var = contextvars.ContextVar('request_id', default=None)

def get_request_id():
    rid = request_id_var.get()
    if rid is None:
        rid = str(uuid.uuid4())
        request_id_var.set(rid)
    return rid

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    import time
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path, http_status=response.status_code).inc()
    REQUEST_LATENCY.labels(endpoint=request.url.path).observe(process_time)
    
    return response

from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi import Depends, HTTPException, status
import secrets

# Auth
security = HTTPBasic()

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    api_user = os.environ.get("API_USERNAME", "admin")
    api_pass = os.environ.get("API_PASSWORD", "admin")
    
    is_correct_username = secrets.compare_digest(credentials.username.encode("utf8"), api_user.encode("utf8"))
    is_correct_password = secrets.compare_digest(credentials.password.encode("utf8"), api_pass.encode("utf8"))
    
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/health")
async def health():
    return {"status": "ok", "worker_id": worker_id}


class GenerateRequest(BaseModel):
    image: Optional[str] = Field(None, description="Base64 encoded image")
    text: Optional[str] = Field(None, description="Text prompt for T2I")
    negative_prompt: Optional[str] = Field(None, description="Negative prompt for T2I")
    mesh: Optional[str] = Field(None, description="Base64 encoded mesh (glb)")
    seed: int = Field(1234, description="Random seed")
    octree_resolution: int = Field(128, description="Octree resolution")
    num_inference_steps: int = Field(5, description="Inference steps")
    guidance_scale: float = Field(5.0, description="Guidance scale")
    texture: bool = Field(False, description="Generate texture")
    face_count: int = Field(40000, description="Target face count for reduction")
    model: str = Field("Normal", description="Model category: Normal, Multiview")
    type: str = Field("glb", description="Output file format (glb, obj)")


@app.post("/generate")
async def generate(request: GenerateRequest, username: str = Depends(authenticate)):
    logger.info(f"[req_id={get_request_id()}] Worker generating... User: {username}")
    params = request.model_dump()
    params["model_key"] = params.pop("model")
    
    if params.get("image"):
        # Load image from base64
        image = load_image_from_base64(params["image"])
        # Apply background removal
        image = apply_rembg(image)
        params["image"] = image
    
    if params.get("texture"):
        params["do_texture"] = True
    
    if params.get("mesh"):
         params["mesh_obj"] = trimesh.load(BytesIO(base64.b64decode(params["mesh"])), file_type='glb')
    
    try:
        GENERATION_COUNT.labels(status='started').inc()
        result = await request_manager.submit(params, priority=10)
        
        GENERATION_COUNT.labels(status='success').inc()

        uid = result['uid']
        type_ = params.get('type', 'glb')
        
        mesh_to_save = result.get('textured_mesh') if params.get('do_texture') else result.get('mesh')
        
        # Handle Latent2MeshOutput object - convert to trimesh
        if hasattr(mesh_to_save, 'mesh_v') and hasattr(mesh_to_save, 'mesh_f'):
            mesh_to_save = trimesh.Trimesh(vertices=mesh_to_save.mesh_v, faces=mesh_to_save.mesh_f)
        
        os.makedirs(SAVE_DIR, exist_ok=True)
        save_path = os.path.join(SAVE_DIR, f'{str(uid)}.{type_}')
        mesh_to_save.export(save_path)
            
        torch.cuda.empty_cache()
        return FileResponse(save_path)
        
    except Exception as e:
        GENERATION_COUNT.labels(status='error').inc()
        logger.error(f"Error: {e}")
        traceback.print_exc()
        ret = {
            "text": server_error_msg,
            "error_code": 1,
        }
        return JSONResponse(ret, status_code=500)


@app.post("/send")
async def generate_send(request: GenerateRequest, username: str = Depends(authenticate)):
    logger.info(f"[req_id={get_request_id()}] Worker send... User: {username}")
    params = request.model_dump()
    params["model_key"] = params.pop("model")
    uid = uuid.uuid4()
    asyncio.create_task(request_manager.submit(params, priority=10))
    
    ret = {"uid": str(uid)}
    return JSONResponse(ret, status_code=200)


@app.get("/status/{uid}")
async def status(uid: str):
    save_file_path = os.path.join(SAVE_DIR, f'{uid}.glb')
    if not os.path.exists(save_file_path):
        response = {'status': 'processing'}
        return JSONResponse(response, status_code=200)
    else:
        base64_str = base64.b64encode(open(save_file_path, 'rb').read()).decode()
        response = {'status': 'completed', 'model_base64': base64_str}
        return JSONResponse(response, status_code=200)


def main():
    global request_manager
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8081)
    parser.add_argument("--model_path", type=str, default='tencent/Hunyuan3D-2')
    parser.add_argument("--tex_model_path", type=str, default='tencent/Hunyuan3D-2')
    parser.add_argument("--device", type=str, default="cuda")
    parser.add_argument("--limit-model-concurrency", type=int, default=5)
    parser.add_argument('--enable_tex', action='store_true')
    parser.add_argument('--enable_t2i', action='store_true', help='Enable Text2Image pipeline (requires additional VRAM)')
    parser.add_argument('--low_vram_mode', action='store_true', default=True, help='Enable low VRAM mode with CPU offload')
    args = parser.parse_args()
    logger.info(f"[req_id={get_request_id()}] args: {args}")

    model_mgr = ModelManager(capacity=1, device=args.device)
    
    def get_loader(model_path, subfolder):
        return lambda: InferencePipeline(
            model_path=model_path,
            tex_model_path=args.tex_model_path,
            subfolder=subfolder,
            device=args.device,
            enable_t2i=args.enable_t2i,
            enable_tex=args.enable_tex,
            low_vram_mode=args.low_vram_mode
        )

    model_mgr.register_model("Normal", get_loader("tencent/Hunyuan3D-2", "hunyuan3d-dit-v2-0-turbo"))

    model_mgr.register_model("Multiview", get_loader("tencent/Hunyuan3D-2mv", "hunyuan3d-dit-v2-mv-turbo"))

    request_manager = PriorityRequestManager(model_mgr, max_concurrency=args.limit_model_concurrency)
    
    @app.on_event("startup")
    async def startup_event():
        await request_manager.start()

    @app.on_event("shutdown")
    async def shutdown_event():
        await request_manager.stop()

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")

if __name__ == "__main__":
    main()
