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

import os
import random
import asyncio
import uuid
import webbrowser
import argparse
import json
from contextlib import asynccontextmanager
from pathlib import Path

import gradio as gr
import trimesh
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from hy3dgen.shapegen.utils import logger
from hy3dgen.manager import PriorityRequestManager, ModelManager
from hy3dgen.inference import InferencePipeline
from hy3dgen.apps.ui_templates import HTML_TEMPLATE_MODEL_VIEWER, HTML_PLACEHOLDER, CSS_STYLES

# Global Manager
request_manager = None

MAX_SEED = int(1e7)
SAVE_DIR = 'gradio_cache'
HAS_T2I = False
TURBO_MODE = True
HAS_TEXTUREGEN = True
SUPPORTED_FORMATS = ['glb', 'obj']

HTML_HEIGHT = 650
HTML_WIDTH = 500

def get_example_img_list(): return []
def get_example_txt_list(): return []
def get_example_mv_list(): return []

def gen_save_folder():
    os.makedirs(SAVE_DIR, exist_ok=True)
    new_folder = os.path.join(SAVE_DIR, str(uuid.uuid4()))
    os.makedirs(new_folder, exist_ok=True)
    return new_folder

def export_mesh(mesh, save_folder, textured=False, file_type='glb'):
    # Validate mesh input
    if mesh is None:
        raise ValueError("Cannot export None mesh")
    
    if textured:
        path = os.path.join(save_folder, f'textured_mesh.{file_type}')
    else:
        path = os.path.join(save_folder, f'white_mesh.{file_type}')
    
    # Handle Latent2MeshOutput object - convert to trimesh
    if hasattr(mesh, 'mesh_v') and hasattr(mesh, 'mesh_f'):
        mesh = trimesh.Trimesh(vertices=mesh.mesh_v, faces=mesh.mesh_f)
    
    # For non-textured meshes, apply white material
    # For textured meshes, preserve existing visual/texture data
    if not textured:
        import numpy as np
        # Create a copy to avoid modifying the original mesh
        mesh = mesh.copy()
        # Create white vertex colors with full opacity
        white_color = np.array([255, 255, 255, 255], dtype=np.uint8)
        mesh.visual = trimesh.visual.ColorVisuals(mesh=mesh)
        # Set face colors (more reliable than vertex colors)
        mesh.visual.face_colors = np.tile(white_color, (len(mesh.faces), 1))
    else:
        # For textured mesh, preserve existing visual/texture data
        # Log the visual type for debugging
        visual_type = mesh.visual.__class__.__name__ if hasattr(mesh, 'visual') else 'None'
        logger.info(f"Exporting textured mesh with visual type: {visual_type}")
        if hasattr(mesh, 'visual') and mesh.visual is not None:
            # Check for image in visual (TextureVisuals has material.image)
            if hasattr(mesh.visual, 'material') and mesh.visual.material is not None:
                has_image = hasattr(mesh.visual.material, 'image') and mesh.visual.material.image is not None
                logger.info(f"Visual material has texture image: {has_image}")
            elif hasattr(mesh.visual, 'image'):
                has_image = mesh.visual.image is not None
                logger.info(f"Visual has direct texture image: {has_image}")
    
    if file_type not in ['glb', 'obj']:
        mesh.export(path)
    else:
        # Use include_normals=True for better geometry quality in GLB
        mesh.export(path, include_normals=True)
    
    logger.info(f"Exported {'textured' if textured else 'white'} mesh to {path}")
    return path

def randomize_seed_fn(seed: int, randomize_seed: bool) -> int:
    if randomize_seed:
        seed = random.randint(0, MAX_SEED)
    return seed

def build_model_viewer_html(save_folder, height=660, width=790, textured=False):
    if textured:
        related_path = "./textured_mesh.glb"
        output_html_path = os.path.join(save_folder, 'textured_mesh.html')
    else:
        related_path = "./white_mesh.glb"
        output_html_path = os.path.join(save_folder, 'white_mesh.html')
    
    template_html = HTML_TEMPLATE_MODEL_VIEWER
    with open(output_html_path, 'w', encoding='utf-8') as f:
        template_html = template_html.replace('#src#', f'{related_path}')
        f.write(template_html)
    rel_path = os.path.relpath(output_html_path, SAVE_DIR)
    iframe_tag = f'<iframe src="/static/{rel_path}" style="width: 100%; height: 100%; min-height: 600px; border: none; border-radius: 8px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);"></iframe>'
    return iframe_tag

async def unified_generation(model_key, caption, negative_prompt, image, mv_image_front, mv_image_back, mv_image_left, mv_image_right, steps, guidance_scale, seed, octree_resolution, check_box_rembg, num_chunks, randomize_seed, do_texture, progress):
    mv_mode = model_key == "Multiview"
    mv_images = {}
    if mv_mode:
        if mv_image_front: mv_images['front'] = mv_image_front
        if mv_image_back: mv_images['back'] = mv_image_back
        if mv_image_left: mv_images['left'] = mv_image_left
        if mv_image_right: mv_images['right'] = mv_image_right
    seed = int(randomize_seed_fn(seed, randomize_seed))
    
    # Thread-safe progress tracking
    import queue
    import threading
    progress_queue = queue.Queue()
    progress_lock = threading.Lock()
    last_progress = {'percent': 0.0, 'message': 'Starting...'}
    stop_updater = {'value': False}  # Usar dict para permitir modificação em closure
    
    def gradio_progress_callback(percent, message):
        """Thread-safe callback que funciona mesmo quando chamado de executors"""
        logger.info(f"Progress update: {percent}% - {message}")
        with progress_lock:
            last_progress['percent'] = percent
            last_progress['message'] = message
        progress_queue.put((percent, message))

    # Background task para processar atualizações de progresso
    async def progress_updater():
        while not stop_updater['value']:
            try:
                percent, message = progress_queue.get(timeout=0.1)
                p = max(0.0, min(1.0, float(percent) / 100.0))
                try:
                    progress(p, desc=message)
                except Exception as e:
                    logger.debug(f"Gradio progress() call failed: {e}")
            except queue.Empty:
                await asyncio.sleep(0.05)
            except Exception as e:
                logger.debug(f"Progress update error: {e}")
                await asyncio.sleep(0.05)
    
    # Inicia o updater em background
    updater_task = asyncio.create_task(progress_updater())
    
    # Force init progress bar
    progress(0.0, desc="Initializing...")

    params = {
        'model_key': model_key,
        'text': caption,
        'negative_prompt': negative_prompt,
        'image': image,
        'mv_images': mv_images if mv_mode else None,
        'num_inference_steps': int(steps), # Renamed from 'steps' in the instruction to match existing pipeline
        'guidance_scale': guidance_scale,
        'seed': seed,
        'octree_resolution': int(octree_resolution), # Ensure it's an int
        'do_rembg': check_box_rembg,
        'num_chunks': int(num_chunks),
        'do_texture': do_texture, # Flag to indicate if texturing is needed
        'progress_callback': gradio_progress_callback
    }
    
    # [LOGGING] Print all parameters to console
    log_params = params.copy()
    # Sanitize large objects for logging
    if 'image' in log_params: log_params['image'] = f"<Image: {type(params['image'])}>"
    if 'mv_images' in log_params and log_params['mv_images']: 
        log_params['mv_images'] = {k: f"<Image: {type(v)}>" for k, v in log_params['mv_images'].items()}
    if 'progress_callback' in log_params: del log_params['progress_callback']
    
    logger.info("==================================================")
    logger.info("ACTION: Generation Request Submitted")
    logger.info(f"PARAMS: {json.dumps(log_params, indent=2, default=str)}")
    logger.info("==================================================")

    try:
        result = await request_manager.submit(params)
        mesh, stats = result["mesh"], result["stats"]
    finally:
        # Para o progress updater
        stop_updater['value'] = True
        updater_task.cancel()
        try:
            await updater_task
        except asyncio.CancelledError:
            pass
    
    save_folder = gen_save_folder()
    
    path_white = export_mesh(mesh, save_folder, textured=False)
    html_white = build_model_viewer_html(save_folder, textured=False)
    
    if do_texture:
        textured_mesh = result["textured_mesh"]
        # If texturing failed, use white mesh as fallback
        if textured_mesh is None:
            logger.warning("Texture generation failed, using untextured mesh")
            textured_mesh = mesh
        path_textured = export_mesh(textured_mesh, save_folder, textured=True)
        html_textured = build_model_viewer_html(save_folder, textured=True)
        return gr.update(value=path_white), gr.update(value=path_textured), html_textured, stats, seed
    else:
        return gr.update(value=path_white), html_white, stats, seed

async def shape_generation(*args, progress=gr.Progress()):
    return await unified_generation(*args, do_texture=False, progress=progress)

async def generation_all(*args, progress=gr.Progress()):
    return await unified_generation(*args, do_texture=True, progress=progress)

def build_app(example_is=None, example_ts=None, example_mvs=None):
    # Gradio 6.3+: theme and css are handled in mount_gradio_app
    with gr.Blocks(
        title='Hunyuan-3D-2.0',
        analytics_enabled=False,
        fill_height=True
    ) as demo:
        # State to track current model mode based on tab
        model_key_state = gr.State("Normal")

        with gr.Row():
            with gr.Column(scale=4):
                
                with gr.Accordion("Input Prompt", open=True):
                    with gr.Tabs(selected='tab_img_prompt') as tabs_prompt:
                        with gr.Tab('Image Prompt', id='tab_img_prompt') as tab_ip:
                            image = gr.Image(label='Image', type='pil', image_mode='RGBA', height=250)
                        
                        with gr.Tab('MultiView Prompt', id='tab_mv_prompt') as tab_mv_p:
                            with gr.Row():
                                mv_image_front = gr.Image(label='Front', type='pil', image_mode='RGBA', height=120)
                                mv_image_back = gr.Image(label='Back', type='pil', image_mode='RGBA', height=120)
                            with gr.Row():
                                mv_image_left = gr.Image(label='Left', type='pil', image_mode='RGBA', height=120)
                                mv_image_right = gr.Image(label='Right', type='pil', image_mode='RGBA', height=120)

                        with gr.Tab('Text Prompt', id='tab_txt_prompt', visible=HAS_T2I) as tab_tp:
                            caption = gr.Textbox(label='Text Prompt', placeholder='HunyuanDiT will be used to generate image.', lines=3)
                            negative_prompt = gr.Textbox(label='Negative Prompt', placeholder='Low quality, distortion, etc.', lines=2)

                with gr.Accordion("Generation Settings", open=False):
                    with gr.Tabs(selected='tab_options' if TURBO_MODE else 'tab_export'):
                        with gr.Tab("Options", id='tab_options', visible=TURBO_MODE):
                            gen_mode = gr.Radio(label='Generation Mode', choices=['Turbo', 'Fast', 'Standard'], value='Turbo')
                            decode_mode = gr.Radio(label='Decoding Mode', choices=['Low', 'Standard', 'High'], value='Standard')
                        with gr.Tab('Advanced Options', id='tab_advanced_options'):
                            with gr.Row():
                                check_box_rembg = gr.Checkbox(value=True, label='Remove Background')
                                randomize_seed = gr.Checkbox(label="Randomize seed", value=True)
                            seed = gr.Slider(label="Seed", minimum=0, maximum=MAX_SEED, step=1, value=1234)
                            with gr.Row():
                                num_steps = gr.Slider(maximum=100, minimum=1, value=5, step=1, label='Inference Steps')
                                octree_resolution = gr.Slider(maximum=512, minimum=16, value=256, label='Octree Resolution')
                            with gr.Row():
                                cfg_scale = gr.Number(value=5.0, label='Guidance Scale')
                                num_chunks = gr.Slider(maximum=5000000, minimum=1000, value=8000, label='Number of Chunks')

                with gr.Row():
                    btn = gr.Button(value='Gen Shape', variant='primary')
                    btn_all = gr.Button(value='Gen Textured Shape', variant='primary', visible=HAS_TEXTUREGEN)
                    btn_stop = gr.Button(value='Stop Generation', variant='stop', visible=False)

            with gr.Column(scale=8):
                with gr.Tabs(selected='gen_mesh_panel') as tabs_output:
                    with gr.Tab('Generated Mesh', id='gen_mesh_panel'):
                        with gr.Column(elem_id="gen_output_container"):
                            html_gen_mesh = gr.HTML(HTML_PLACEHOLDER, label='Output', elem_id="model_3d_viewer")
                            with gr.Row(elem_classes="download-row"):
                                file_out = gr.DownloadButton(label="Download .glb", variant='primary', visible=True)
                                file_out2 = gr.DownloadButton(label="Download Textured .glb", variant='primary', visible=True)
                    with gr.Tab('Mesh Statistic', id='stats_panel'):
                        stats = gr.Json({}, label='Mesh Stats')
        
        # Helper to toggle buttons
        def on_gen_start():
            logger.info("UI EVENT: 'Gen Shape' or 'Gen Textured Shape' button clicked.")
            return gr.update(visible=False), gr.update(visible=False), gr.update(visible=True)
        
        def on_gen_finish():
            logger.info("UI EVENT: Generation finished (or stopped). Restoring UI.")
            return gr.update(visible=True), gr.update(visible=HAS_TEXTUREGEN), gr.update(visible=False)

        # Update model state based on tab selection
        def update_model_key(evt: gr.SelectData):
            # When Tabs have IDs, the selected value is the ID
            if evt.value == "tab_mv_prompt":
                return "Multiview"
            return "Normal"

        tabs_prompt.select(fn=update_model_key, outputs=model_key_state)

        # Wire events
        # Event Chain 1: Shape Generation
        succ1_1 = btn.click(on_gen_start, outputs=[btn, btn_all, btn_stop])
        succ1_2 = succ1_1.then(
            shape_generation, 
            inputs=[model_key_state, caption, negative_prompt, image, mv_image_front, mv_image_back, mv_image_left, mv_image_right, num_steps, cfg_scale, seed, octree_resolution, check_box_rembg, num_chunks, randomize_seed], 
            outputs=[file_out, html_gen_mesh, stats, seed]
        )
        succ1_3 = succ1_2.then(on_gen_finish, outputs=[btn, btn_all, btn_stop])
        
        # Event Chain 2: Textured Generation
        succ2_1 = btn_all.click(on_gen_start, outputs=[btn, btn_all, btn_stop])
        succ2_2 = succ2_1.then(
            generation_all, 
            inputs=[model_key_state, caption, negative_prompt, image, mv_image_front, mv_image_back, mv_image_left, mv_image_right, num_steps, cfg_scale, seed, octree_resolution, check_box_rembg, num_chunks, randomize_seed], 
            outputs=[file_out, file_out2, html_gen_mesh, stats, seed]
        )
        succ2_3 = succ2_2.then(on_gen_finish, outputs=[btn, btn_all, btn_stop])

        # Stop Button
        btn_stop.click(
            fn=on_gen_finish, 
            outputs=[btn, btn_all, btn_stop], 
            cancels=[succ1_2, succ2_2]
        )

    return demo

def main():
    global request_manager, SAVE_DIR, HAS_T2I, HAS_TEXTUREGEN
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_path", type=str, default='tencent/Hunyuan3D-2')
    parser.add_argument("--subfolder", type=str, default='hunyuan3d-dit-v2-0-turbo')
    parser.add_argument("--texgen_model_path", type=str, default='tencent/Hunyuan3D-2')
    parser.add_argument('--port', type=int, default=7860)
    parser.add_argument('--host', type=str, default='127.0.0.1')
    parser.add_argument('--device', type=str, default='cuda')
    parser.add_argument('--cache-path', type=str, default='gradio_cache')
    parser.add_argument('--enable_t23d', action='store_true')
    parser.add_argument('--disable_tex', action='store_true', help='Disable texture generation (avoids custom_rasterizer requirement)')
    parser.add_argument('--low_vram_mode', action='store_true')
    parser.add_argument('--no-browser', action='store_true', help='Do not open the browser automatically')
    args = parser.parse_args()
    SAVE_DIR = args.cache_path
    os.makedirs(SAVE_DIR, exist_ok=True)
    HAS_T2I = args.enable_t23d
    HAS_TEXTUREGEN = not args.disable_tex
    
    if args.disable_tex:
        logger.info("Texturization disabled (custom_rasterizer not required)")

    model_mgr = ModelManager(capacity=1 if args.low_vram_mode else 3, device=args.device)
    def get_loader(model_path, subfolder):
        return lambda: InferencePipeline(
            model_path=model_path, tex_model_path=args.texgen_model_path, subfolder=subfolder,
            device=args.device, enable_t2i=args.enable_t23d, enable_tex=not args.disable_tex,
            low_vram_mode=args.low_vram_mode
        )
    model_mgr.register_model("Normal", get_loader("tencent/Hunyuan3D-2", "hunyuan3d-dit-v2-0-turbo"))

    model_mgr.register_model("Multiview", get_loader("tencent/Hunyuan3D-2mv", "hunyuan3d-dit-v2-mv-turbo"))
    request_manager = PriorityRequestManager(model_mgr, max_concurrency=1)
    
    # Define lifespan for FastAPI app (Gradio 6.3+ / FastAPI 0.93+)
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Startup
        logger.info("Starting PriorityRequestManager...")
        asyncio.create_task(request_manager.start())
        logger.info("PriorityRequestManager started successfully")
        yield
        # Shutdown (if needed)
    
    # Cria a aplicação FastAPI com lifespan
    app = FastAPI(lifespan=lifespan)
    
    static_dir = Path(SAVE_DIR).absolute()
    app.mount("/static", StaticFiles(directory=static_dir, html=True), name="static")
    demo = build_app()
    
    # Injeta CSS via head customizada (Gradio 6.3+)
    custom_head = f"<style>{CSS_STYLES}</style>"
    app = gr.mount_gradio_app(
        app, 
        demo, 
        path="/",
        head=custom_head,
        theme=gr.themes.Base()
    )
    url = f"http://{args.host}:{args.port}"
    print(f"\nHunyuan3D-2 Pro Unified is running at: {url}\n")
    if not args.no_browser:
        webbrowser.open(url)
    uvicorn.run(app, host=args.host, port=args.port, workers=1)

if __name__ == '__main__':
    main()
