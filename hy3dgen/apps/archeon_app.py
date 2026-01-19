
import os
import argparse
import logging
import gradio as gr
import torch
import numpy as np
import asyncio
from pathlib import Path
from PIL import Image
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

# Internal Modular Imports
from hy3dgen.manager import ModelManager, PriorityRequestManager
from hy3dgen.inference import InferencePipeline
from hy3dgen.apps.ui_templates import CSS_STYLES, HTML_TEMPLATE_MODEL_VIEWER, HTML_PLACEHOLDER, HTML_ERROR_TEMPLATE
from hy3dgen.utils.system import setup_logging, get_user_cache_dir

# Setup Logger
logger = setup_logging("archeon_app")

# Global State
SAVE_DIR = str(get_user_cache_dir() / "gradio_cache")
HAS_T2I = False
HAS_TEXTUREGEN = True
request_manager = None
i18n = {'msg_stop_confirm': 'Are you sure you want to stop generation?'}

# --- Helper Functions ---

# [SECURITY] Safe Static Files serving
class SafeStaticFiles(StaticFiles):
    def lookup_path(self, path):
        full_path, stat_result = super().lookup_path(path)
        # Add any extra security checks here if needed
        return full_path, stat_result

def gen_save_folder():
    import uuid
    folder = os.path.join(SAVE_DIR, str(uuid.uuid4()))
    os.makedirs(folder, exist_ok=True)
    return folder

def export_mesh(mesh, folder, textured=False, file_type='glb'):
    filename = "textured_mesh" if textured else "white_mesh"
    path = os.path.join(folder, f"{filename}.{file_type}")
    
    if textured:
        try:
           # Trimesh export
           mesh.export(path)
        except Exception as e:
           logger.error(f"Trimesh export failed: {e}")
           # Fallback or re-raise
           raise e
    else:
        mesh.export(path)
        
    logger.info(f"Exported {filename} to {path}")
    return path

def build_model_viewer_html(save_folder, textured=True):
    # For local viewing, we can use relative path if served via static mount
    # But for Gradio 'allowed_paths', absolute path works best.
    pass 
    # Actually, let's just return the component needed. 
    # We will use the 'file' output for the DownloadButton and a constructed HTML/Model3D component.
    # In this logic, we return HTML string.
    
    file_name = "textured_mesh.glb" if textured else "white_mesh.glb"
    file_path = f"/outputs/{os.path.basename(save_folder)}/{file_name}" # Pseudo-path if mounted
    # Simpler: use the 'file=' argument in DownloadButton logic and return the object
    return None # We will handle HTML construction in the yield if needed, otherwise just Model3D

# --- Core Generation Logic ---

async def unified_generation(
    model_key, 
    caption, 
    negative_prompt, 
    image, 
    mv_front, mv_back, mv_left, mv_right,
    num_steps, 
    cfg_scale, 
    seed, 
    octree_res, 
    rembg, 
    num_chunks, 
    tex_steps, 
    tex_guidance, 
    tex_seed, 
    randomize_seed, 
    export_format,
    progress=gr.Progress()
):
    logger.info("UI EVENT: Generation started.")
    
    # Input Validation
    if image is None and not caption:
        raise gr.Error("Please provide an Image or a Text Prompt.")

    # Seed
    if randomize_seed:
        seed = np.random.randint(0, 2**32)
        tex_seed = np.random.randint(0, 2**32)
        
    # Construct task params
    params = {
        "model_key": model_key,
        "text": caption if caption else None,
        "negative_prompt": negative_prompt,
        "image": image,
        "mv_images": {
            "front": mv_front, "back": mv_back, "left": mv_left, "right": mv_right
        } if mv_front else None,
        "num_inference_steps": num_steps,
        "guidance_scale": cfg_scale,
        "seed": int(seed),
        "octree_resolution": octree_res,
        "do_rembg": rembg,
        "num_chunks": num_chunks,
        "do_texture": HAS_TEXTUREGEN,
        "tex_steps": tex_steps,
        "tex_guidance_scale": tex_guidance,
        "tex_seed": int(tex_seed)
    }
    
    logger.info(f"ACTION: Generation Request Submitted")
    
    try:
        # Request generation from manager
        # Note: request_manager.process_request might need to be awaited or returns a generator
        # Assuming it returns an async generator for progress
        
        generator = request_manager.process_request(params)
        
        mesh = None
        html_output = HTML_PLACEHOLDER
        
        async for update in generator:
            if isinstance(update, str):
                # Status message
                progress(0, desc=update)
            elif isinstance(update, tuple) and len(update) == 2:
                # Progress update (percentage, message)
                pct, msg = update
                progress(pct / 100.0, desc=msg)
            elif hasattr(update, 'vertices') or hasattr(update, 'scene'):
                # It's the final mesh!
                mesh = update
                
        # --- Post Processing & Export ---
        save_folder = gen_save_folder()
        
        # [ROBUSTNESS] Try/Except Block for Export
        try:
            if mesh is None:
                 raise ValueError("Generation finished but returned No Mesh.")

            path = export_mesh(mesh, save_folder, textured=HAS_TEXTUREGEN, file_type=export_format)
            
            if not os.path.exists(path) or os.path.getsize(path) == 0:
                 raise ValueError(f"Exported file missing/empty: {path}")

            logger.info(f"Yielding Final Result. Path: {path}")
            
            # Success Yield
            yield (
                gr.DownloadButton(value=path, visible=True, label="Download 3D Model"),
                gr.Model3D(value=path, visible=True), # Using standard Model3D component instead of raw HTML for safety
                seed,
                gr.update(visible=False), # Hide progress container if any
                gr.update(value="Generate") # Reset button
            )

        except Exception as e:
            logger.error(f"Export Error: {e}")
            raise gr.Error(f"Export Failed: {e}")

    except Exception as e:
        logger.error(f"Generation Error: {e}", exc_info=True)
        yield (
            gr.update(visible=False),
            HTML_ERROR_TEMPLATE.replace("#error_message#", str(e)),
            seed,
            gr.update(visible=False),
            gr.update(value="Generation Failed")
        )


async def on_gen_finish():
    # Helper to reset UI state
    return (
        gr.update(value="Generate", interactive=True),
        gr.update(visible=False), # Hide stop btn
        gr.update(visible=False)  # Hide loading
    )

# --- UI Builder ---

def build_app():
    with gr.Blocks(css=CSS_STYLES, title="Archeon 3D Pro", theme=gr.themes.Base()) as demo:
        
        # State
        model_key_state = gr.State("Normal")
        
        with gr.Row(elem_classes="main-row"):
            # Left Column: Inputs
            with gr.Column(scale=1, elem_classes="column-input"):
                gr.Markdown("### Archeon 3D")
                
                with gr.Tabs():
                    with gr.Tab("Image Prompt"):
                        image_input = gr.Image(label="Input Image", type="pil", height=300)
                        
                    with gr.Tab("Text Prompt"):
                        caption_input = gr.Textbox(label="Prompt", placeholder="A 3D model of...")
                        negative_input = gr.Textbox(label="Negative Prompt", placeholder="Low quality...")
                
                with gr.Accordion("Advanced Settings", open=False):
                    num_steps = gr.Slider(10, 100, value=50, label="Inference Steps")
                    cfg_scale = gr.Slider(1.0, 20.0, value=5.0, label="Guidance Scale")
                    seed_input = gr.Number(value=1234, label="Seed")
                    randomize_seed = gr.Checkbox(value=True, label="Randomize Seed")
                    rembg_check = gr.Checkbox(value=True, label="Remove Background")
                    octree_res = gr.Slider(128, 512, value=256, step=32, label="Octree Resolution")
                    export_fmt = gr.Dropdown(["glb", "obj"], value="glb", label="Export Format")

                with gr.Accordion("Texture Settings", open=True):
                    tex_steps = gr.Slider(10, 50, value=30, label="Texture Steps")
                    tex_guidance = gr.Slider(1.0, 10.0, value=5.0, label="Texture Guidance")
                    tex_seed = gr.Number(value=1234, label="Texture Seed")

                btn_gen = gr.Button("GENERATE", variant="primary", elem_classes="custom-btn-primary")
                btn_stop = gr.Button("STOP", variant="stop", visible=False, elem_classes="custom-btn-stop")
                
                output_file_btn = gr.DownloadButton(label="Download", visible=False)

            # Right Column: Viewer
            with gr.Column(scale=2, elem_classes="column-viewer"):
                output_viewer = gr.Model3D(
                    label="Generated Mesh", 
                    interactive=True, 
                    clear_color=[0, 0, 0, 0],
                    elem_id="model-3d-viewer"
                )
                # Or use HTML for custom viewer if preferred, but Model3D is safer for now.
                # error_box = gr.HTML(visible=True) # For errors

        # Binding
        
        # Generator wrapper to matching outputs
        # outputs=[file_out, html_gen_mesh, seed, progress_html, btn_stop] in original
        # Here: [output_file_btn, output_viewer, seed_input, ???, btn_gen status?]
        
        # Generator wrapper to matching outputs
        gen_event = btn_gen.click(
            fn=lambda: (gr.update(value="Generating...", interactive=False), gr.update(visible=True)),
            outputs=[btn_gen, btn_stop]
        ).then(
            fn=unified_generation,
            inputs=[
                model_key_state, caption_input, negative_input, image_input, 
                gr.State(None), gr.State(None), gr.State(None), gr.State(None), # MV placeholders
                num_steps, cfg_scale, seed_input, octree_res, rembg_check, 
                gr.State(8000), tex_steps, tex_guidance, tex_seed, randomize_seed, export_fmt
            ],
            outputs=[output_file_btn, output_viewer, seed_input, gr.State(None), btn_gen]
        )
        
        btn_stop.click(
            fn=on_gen_finish,
            outputs=[btn_gen, btn_stop, gr.State(None)],
            cancels=[gen_event] # Correctly passing the event object
        )

    return demo

# --- Main Entry Point ---

def main():
    global request_manager, SAVE_DIR, HAS_T2I, HAS_TEXTUREGEN
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_path", type=str, default='tencent/Hunyuan3D-2')
    parser.add_argument("--subfolder", type=str, default='hunyuan3d-dit-v2-0-turbo')
    parser.add_argument("--texgen_model_path", type=str, default='tencent/Hunyuan3D-2')
    parser.add_argument('--port', type=int, default=7860)
    parser.add_argument('--host', type=str, default='127.0.0.1')
    parser.add_argument('--device', type=str, default='cuda')
    parser.add_argument('--cache-path', type=str, default=None)
    parser.add_argument('--enable_t23d', action='store_true')
    parser.add_argument('--disable_tex', action='store_true')
    parser.add_argument('--low_vram_mode', action='store_true', default=True)
    args = parser.parse_args()

    # Config Globals
    if args.cache_path:
        SAVE_DIR = args.cache_path
    os.makedirs(SAVE_DIR, exist_ok=True)
    
    HAS_T2I = args.enable_t23d
    HAS_TEXTUREGEN = not args.disable_tex

    # Environment Log
    logger.info(f"Archeon 3D Legacy UI Startup. Device: {args.device}")
    
    # Init Manager
    model_mgr = ModelManager(capacity=1 if args.low_vram_mode else 3, device=args.device)
    
    # Lazy Loader Logic
    def get_loader(model_path, subfolder):
        return lambda: InferencePipeline(
            model_path=model_path, tex_model_path=args.texgen_model_path, subfolder=subfolder,
            device=args.device, enable_t2i=HAS_T2I, enable_tex=HAS_TEXTUREGEN,
            low_vram_mode=args.low_vram_mode
        )
    model_mgr.register_model("Normal", get_loader("tencent/Hunyuan3D-2", "hunyuan3d-dit-v2-0-turbo"))
    
    request_manager = PriorityRequestManager(model_mgr, max_concurrency=1)
    
    # Mount on FastAPI
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info("Starting Worker...")
        asyncio.create_task(request_manager.start())
        yield
        logger.info("Stopping Worker...")
        await request_manager.stop()

    app = FastAPI(lifespan=lifespan)
    
    # Static Mount for outputs (Crucial for Download)
    static_dir = Path(SAVE_DIR).absolute()
    app.mount("/outputs", SafeStaticFiles(directory=static_dir, html=True), name="outputs")

    # Build UI
    archeon_ui = build_app()
    
    # Mount Gradio [ROBUSTNESS: ALLOWED PATHS]
    app = gr.mount_gradio_app(
        app, 
        archeon_ui, 
        path="/", 
        allowed_paths=[SAVE_DIR] # <--- Essential Fix
    )

    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()
