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


LOGDIR = '.'

from hy3dgen.shapegen.utils import get_logger
logger = get_logger("api_server")

server_error_msg = "**NETWORK ERROR DUE TO HIGH TRAFFIC. PLEASE REGENERATE OR REFRESH THIS PAGE.**"
moderation_msg = "YOUR INPUT VIOLATES OUR CONTENT MODERATION GUIDELINES. PLEASE TRY AGAIN."

def pretty_print_semaphore(semaphore):
    if semaphore is None:
        return "None"
    return f"Semaphore(value={semaphore._value}, locked={semaphore.locked()})"


SAVE_DIR = 'gradio_cache'
os.makedirs(SAVE_DIR, exist_ok=True)

worker_id = str(uuid.uuid4())[:6]



# Metrics
REQUEST_COUNT = Counter('app_request_count', 'Total application requests', ['method', 'endpoint', 'http_status'])
REQUEST_LATENCY = Histogram('app_request_latency_seconds', 'Request latency', ['endpoint'])
GENERATION_COUNT = Counter('app_generation_total', 'Total generations', ['status'])

# Global Manager
request_manager = None

def load_image_from_base64(image):
    return Image.open(BytesIO(base64.b64decode(image)))

# ModelWorker class removed, replaced by InferencePipeline


app = FastAPI()
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
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
    
    # If vars are empty string, disable auth? No, safer to default to something or enforce.
    # Logic: If defaults are kept, it's insecure but functional.
    
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


class GenerateRequest(BaseModel):
    image: Optional[str] = Field(None, description="Base64 encoded image")
    text: Optional[str] = Field(None, description="Text prompt for T2I")
    mesh: Optional[str] = Field(None, description="Base64 encoded mesh (glb)")
    seed: int = Field(1234, description="Random seed")
    octree_resolution: int = Field(128, description="Octree resolution")
    num_inference_steps: int = Field(5, description="Inference steps")
    guidance_scale: float = Field(5.0, description="Guidance scale")
    texture: bool = Field(False, description="Generate texture")
    face_count: int = Field(40000, description="Target face count for reduction")
    type: str = Field("glb", description="Output file format (glb, obj)")


@app.post("/generate")
async def generate(request: GenerateRequest, username: str = Depends(authenticate)):
    logger.info(f"[req_id={get_request_id()}] Worker generating... User: {username}")
    params = request.model_dump()
    
    # Adapt params for InferencePipeline
    if params.get("image"):
        params["image"] = load_image_from_base64(params["image"])
    
    if params.get("texture"):
        params["do_texture"] = True
    
    # ... logic for mesh upload handling if needed ...
    # InferencePipeline expects 'mesh' to be an object if passed? 
    # Or param 'mesh' is NOT used by pipeline directly unless it's texturing stage.
    # Logic in original ModelWorker loaded mesh from base64 if provided.
    
    if params.get("mesh"):
         params["mesh_obj"] = trimesh.load(BytesIO(base64.b64decode(params["mesh"])), file_type='glb')
    
    try:
        GENERATION_COUNT.labels(status='started').inc()
        # Submit to Priority Queue (high priority = lower number, using default 10)
        # We need to adapt the return to file_path
        
        # NOTE: request_manager submit returns the RESULT dict from InferencePipeline
        result = await request_manager.submit(params, priority=10)
        
        GENERATION_COUNT.labels(status='success').inc()

        # Result contains 'mesh', 'textured_mesh', 'uid'
        # We need to save it to return a FileResponse
        uid = result['uid']
        type_ = params.get('type', 'glb')
        
        mesh_to_save = result.get('textured_mesh') if params.get('do_texture') else result.get('mesh')
        
        with tempfile.NamedTemporaryFile(suffix=f'.{type_}', delete=False) as temp_file:
            mesh_to_save.export(temp_file.name)
            # Re-read?? Original code did re-read.
            save_path = os.path.join(SAVE_DIR, f'{str(uid)}.{type_}')
            mesh_to_save.export(save_path)
            
        torch.cuda.empty_cache()
        return FileResponse(save_path)
        
    except ValueError as e:
        GENERATION_COUNT.labels(status='error').inc()
        traceback.print_exc()
        print("Caught ValueError:", e)
        ret = {
            "text": server_error_msg,
            "error_code": 1,
        }
        return JSONResponse(ret, status_code=404)
    except torch.cuda.CudaError as e:
        GENERATION_COUNT.labels(status='error').inc()
        print("Caught torch.cuda.CudaError:", e)
        ret = {
            "text": server_error_msg,
            "error_code": 1,
        }
        return JSONResponse(ret, status_code=404)
    except Exception as e:
        GENERATION_COUNT.labels(status='error').inc()
        print("Caught Unknown Error", e)
        traceback.print_exc()
        ret = {
            "text": server_error_msg,
            "error_code": 1,
        }
        return JSONResponse(ret, status_code=404)


@app.post("/send")
async def generate_send(request: GenerateRequest, username: str = Depends(authenticate)):
    logger.info(f"[req_id={get_request_id()}] Worker send... User: {username}")
    params = request.model_dump()
    uid = uuid.uuid4()
    # Send is async background
    asyncio.create_task(request_manager.submit(params, priority=10))
    
    ret = {"uid": str(uid)}
    return JSONResponse(ret, status_code=200)


@app.get("/status/{uid}")
async def status(uid: str):
    save_file_path = os.path.join(SAVE_DIR, f'{uid}.glb')
    print(save_file_path, os.path.exists(save_file_path))
    if not os.path.exists(save_file_path):
        response = {'status': 'processing'}
        return JSONResponse(response, status_code=200)
    else:
        base64_str = base64.b64encode(open(save_file_path, 'rb').read()).decode()
        response = {'status': 'completed', 'model_base64': base64_str}
        return JSONResponse(response, status_code=200)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8081)
    parser.add_argument("--model_path", type=str, default='tencent/Hunyuan3D-2mini')
    parser.add_argument("--tex_model_path", type=str, default='tencent/Hunyuan3D-2')
    parser.add_argument("--device", type=str, default="cuda")
    parser.add_argument("--limit-model-concurrency", type=int, default=5)
    parser.add_argument('--enable_tex', action='store_true')
    args = parser.parse_args()
    logger.info(f"[req_id={get_request_id()}] args: {args}")

    # Initialize Manager
    model_mgr = ModelManager(capacity=1, device=args.device)
    
    def pipeline_loader():
        return InferencePipeline(
            model_path=args.model_path,
            tex_model_path=args.tex_model_path,
            subfolder='hunyuan3d-dit-v2-mini-turbo', # hardcoded default in orig ModelWorker? orig used kwargs
            device=args.device,
            enable_t2i=True, # Original ModelWorker seemed to instantiate T2I always? Actually check line 94 of original. It was there.
            enable_tex=args.enable_tex
        )
        
    model_mgr.register_model("primary", pipeline_loader)

    request_manager = PriorityRequestManager(model_mgr, max_concurrency=args.limit_model_concurrency)
    
    @app.on_event("startup")
    async def startup_event():
        await request_manager.start()

    @app.on_event("shutdown")
    async def shutdown_event():
        await request_manager.stop()

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
