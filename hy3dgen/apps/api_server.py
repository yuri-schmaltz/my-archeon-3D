import argparse
import uvicorn
import sys
import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio

from hy3dgen.manager import ModelManager, PriorityRequestManager

from hy3dgen.api.routes import router
import hy3dgen.api.routes as routes_module

# Logging
import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio

from hy3dgen.manager import ModelManager, PriorityRequestManager

from hy3dgen.api.routes import router
import hy3dgen.api.routes as routes_module
from hy3dgen.utils.system import setup_logging

# Logging
logger = setup_logging("api_server")

def create_app(args=None):
    if args is None:
         parser = argparse.ArgumentParser()
         # Defaults matching main()
         parser.add_argument("--model_path", type=str, default='tencent/Hunyuan3D-2')
         parser.add_argument("--subfolder", type=str, default='hunyuan3d-dit-v2-0-turbo')
         parser.add_argument("--texgen_model_path", type=str, default='tencent/Hunyuan3D-2')
         parser.add_argument('--port', type=int, default=8081)
         parser.add_argument('--host', type=str, default='127.0.0.1')
         parser.add_argument('--device', type=str, default='cuda')
         parser.add_argument('--low_vram_mode', action='store_true', default=True)
         args, _ = parser.parse_known_args()

    logger.info(f"Initializing Archeon 3D API Server on {args.host}:{args.port}")
    
    # 1. Setup Backend Managers
    model_mgr = ModelManager(capacity=1 if args.low_vram_mode else 3, device=args.device)
    
    def get_loader(model_path, subfolder):
        from hy3dgen.inference import InferencePipeline
        return lambda: InferencePipeline(
            model_path=model_path, 
            tex_model_path=args.texgen_model_path, 
            subfolder=subfolder,
            device=args.device, 
            enable_t2i=True, 
            enable_tex=True, 
            low_vram_mode=args.low_vram_mode
        )
    
    model_mgr.register_model("Normal", get_loader(args.model_path, args.subfolder))
    
    request_manager = PriorityRequestManager(model_mgr, max_concurrency=1)
    
    # 2. Inject Manager into Routes
    routes_module.request_manager = request_manager
    
    # 3. Define App Lifespan
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info("Starting Worker Manager...")
        asyncio.create_task(request_manager.start())
        yield
        logger.info("Stopping Worker Manager...")
        await request_manager.stop()
    
    # 4. Create App
    app = FastAPI(title="Archeon 3D API", version="1.0.0", lifespan=lifespan)
    app.include_router(router)
    return app, args

def main():
    app, args = create_app()
    # 5. Run
    uvicorn.run(app, host=args.host, port=args.port) 

if __name__ == "__main__":
    main()
