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
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
from typing import Optional, Union

from hy3dgen.rembg import BackgroundRemover
from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline, FloaterRemover, DegenerateFaceRemover, FaceReducer, \
    MeshSimplifier
from hy3dgen.texgen import Hunyuan3DPaintPipeline
from hy3dgen.texgen import Hunyuan3DPaintPipeline
from hy3dgen.text2image import HunyuanDiTPipeline
from hy3dgen.manager import PriorityRequestManager, PrioritizedItem


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



def load_image_from_base64(image):
    return Image.open(BytesIO(base64.b64decode(image)))


class ModelWorker:
    def __init__(self,
                 model_path='tencent/Hunyuan3D-2mini',
                 tex_model_path='tencent/Hunyuan3D-2',
                 subfolder='hunyuan3d-dit-v2-mini-turbo',
                 device='cuda',
                 enable_tex=False):
        self.model_path = model_path
        self.worker_id = worker_id
        self.device = device
        logger.info(f"[req_id={get_request_id()}] Loading the model {model_path} on worker {worker_id} ...")

        self.rembg = BackgroundRemover()
        self.pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
            model_path,
            subfolder=subfolder,
            use_safetensors=True,
            device=device,
        )
        self.pipeline.enable_flashvdm(mc_algo='mc')
        # self.pipeline_t2i = HunyuanDiTPipeline(
        #     'Tencent-Hunyuan/HunyuanDiT-v1.1-Diffusers-Distilled',
        #     device=device
        # )
        if enable_tex:
            self.pipeline_tex = Hunyuan3DPaintPipeline.from_pretrained(tex_model_path)

    def get_queue_length(self):
        if model_semaphore is None:
            return 0
        else:
            return args.limit_model_concurrency - model_semaphore._value + (len(
                model_semaphore._waiters) if model_semaphore._waiters is not None else 0)

    def get_status(self):
        return {
            "speed": 1,
            "queue_length": self.get_queue_length(),
        }

    @torch.inference_mode()
    def generate(self, uid, params):
        if 'image' in params:
            image = params["image"]
            image = load_image_from_base64(image)
        else:
            if 'text' in params:
                text = params["text"]
                image = self.pipeline_t2i(text)
            else:
                raise ValueError("No input image or text provided")

        image = self.rembg(image)
        params['image'] = image

        if 'mesh' in params:
            mesh = trimesh.load(BytesIO(base64.b64decode(params["mesh"])), file_type='glb')
        else:
            seed = params.get("seed", 1234)
            params['generator'] = torch.Generator(self.device).manual_seed(seed)
            params['octree_resolution'] = params.get("octree_resolution", 128)
            params['num_inference_steps'] = params.get("num_inference_steps", 5)
            params['guidance_scale'] = params.get('guidance_scale', 5.0)
            params['mc_algo'] = 'mc'
            import time
            start_time = time.time()
            mesh = self.pipeline(**params)[0]
            logger.info(f"[req_id={get_request_id()}] --- %s seconds ---" % (time.time() - start_time))

        if params.get('texture', False):
            mesh = FloaterRemover()(mesh)
            mesh = DegenerateFaceRemover()(mesh)
            mesh = FaceReducer()(mesh, max_facenum=params.get('face_count', 40000))
            mesh = self.pipeline_tex(mesh, image)

        type = params.get('type', 'glb')
        with tempfile.NamedTemporaryFile(suffix=f'.{type}', delete=False) as temp_file:
            mesh.export(temp_file.name)
            mesh = trimesh.load(temp_file.name)
            save_path = os.path.join(SAVE_DIR, f'{str(uid)}.{type}')
            mesh.export(save_path)

        torch.cuda.empty_cache()
        return save_path, uid


app = FastAPI()
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 你可以指定允许的来源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头部
)


# Utilitário para gerar ID de correlação por requisição
import contextvars
request_id_var = contextvars.ContextVar('request_id', default=None)

def get_request_id():
    rid = request_id_var.get()
    if rid is None:
        rid = str(uuid.uuid4())
        request_id_var.set(rid)
    return rid


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
async def generate(request: GenerateRequest):
    logger.info(f"[req_id={get_request_id()}] Worker generating...")
    params = request.model_dump()
    uid = uuid.uuid4()
    uid = uuid.uuid4()
    try:
        # Submit to Priority Queue (high priority = lower number, using default 10)
        file_path, uid = await request_manager.submit(params, priority=10)
        return FileResponse(file_path)
    except ValueError as e:
        traceback.print_exc()
        print("Caught ValueError:", e)
        ret = {
            "text": server_error_msg,
            "error_code": 1,
        }
        return JSONResponse(ret, status_code=404)
    except torch.cuda.CudaError as e:
        print("Caught torch.cuda.CudaError:", e)
        ret = {
            "text": server_error_msg,
            "error_code": 1,
        }
        return JSONResponse(ret, status_code=404)
    except Exception as e:
        print("Caught Unknown Error", e)
        traceback.print_exc()
        ret = {
            "text": server_error_msg,
            "error_code": 1,
        }
        return JSONResponse(ret, status_code=404)


@app.post("/send")
async def generate_send(request: GenerateRequest):
    logger.info(f"[req_id={get_request_id()}] Worker send...")
    params = request.model_dump()
    uid = uuid.uuid4()
    # Send is async background, so we just acknowledge receipt. 
    # To properly track it, we should probably submit it to the queue in a fire-and-forget manner
    # But for now, let's keep the existing behavior but routed through manager or just separate thread?
    # The original was threading.Thread. Let's redirect to manager but without awaiting.
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

    worker = ModelWorker(model_path=args.model_path, device=args.device, enable_tex=args.enable_tex,
                         tex_model_path=args.tex_model_path)
                         
    # Initialize Manager
    request_manager = PriorityRequestManager(worker, max_concurrency=args.limit_model_concurrency)
    
    @app.on_event("startup")
    async def startup_event():
        await request_manager.start()

    @app.on_event("shutdown")
    async def shutdown_event():
        await request_manager.stop()

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
