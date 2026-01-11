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
import shutil
import uuid
import webbrowser
import argparse
from pathlib import Path

import gradio as gr
import torch
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

def export_mesh(mesh, save_folder, textured=False, type='glb'):
    if textured:
        path = os.path.join(save_folder, f'textured_mesh.{type}')
    else:
        path = os.path.join(save_folder, f'white_mesh.{type}')
    if type not in ['glb', 'obj']:
        mesh.export(path)
    else:
        mesh.export(path, include_normals=textured)
    return path

def randomize_seed_fn(seed: int, randomize_seed: bool) -> int:
    if randomize_seed:
        seed = random.randint(0, MAX_SEED)
    return seed

def build_model_viewer_html(save_folder, height=660, width=790, textured=False):
    if textured:
        related_path = f"./textured_mesh.glb"
        output_html_path = os.path.join(save_folder, f'textured_mesh.html')
    else:
        related_path = f"./white_mesh.glb"
        output_html_path = os.path.join(save_folder, f'white_mesh.html')
    
    template_html = HTML_TEMPLATE_MODEL_VIEWER
    with open(output_html_path, 'w', encoding='utf-8') as f:
        template_html = template_html.replace('#src#', f'{related_path}')
        f.write(template_html)
    rel_path = os.path.relpath(output_html_path, SAVE_DIR)
    iframe_tag = f'<iframe src="/static/{rel_path}" style="width: 100%; height: 600px; border: none; border-radius: 8px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);"></iframe>'
    return iframe_tag

async def unified_generation(model_key, caption, image, mv_image_front, mv_image_back, mv_image_left, mv_image_right, steps, guidance_scale, seed, octree_resolution, check_box_rembg, num_chunks, randomize_seed, do_texture, progress):
    mv_mode = model_key == "Multiview"
    mv_images = {}
    if mv_mode:
        if mv_image_front: mv_images['front'] = mv_image_front
        if mv_image_back: mv_images['back'] = mv_image_back
        if mv_image_left: mv_images['left'] = mv_image_left
        if mv_image_right: mv_images['right'] = mv_image_right
    seed = int(randomize_seed_fn(seed, randomize_seed))
    # Progress callback bridge
    loop = asyncio.get_running_loop()
    def gradio_progress_callback(percent, message):
        # Schedule the update on the main event loop to be thread-safe
        def _update():
            progress(percent / 100.0, desc=message)
        loop.call_soon_threadsafe(_update)

    params = {
        'model_key': model_key,
        'text': caption,
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
    result = await request_manager.submit(params)
    mesh, stats = result["mesh"], result["stats"]
    save_folder = gen_save_folder()
    
    path_white = export_mesh(mesh, save_folder, textured=False)
    html_white = build_model_viewer_html(save_folder, textured=False)
    
    if do_texture:
        textured_mesh = result["textured_mesh"]
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
    with gr.Blocks(theme=gr.themes.Base(), title='Hunyuan-3D-2.0', analytics_enabled=False, css=CSS_STYLES) as demo:
        with gr.Row():
            with gr.Column(scale=3):
                model_key = gr.Dropdown(label="Model Category", choices=["Normal", "Small", "Multiview"], value="Normal")
                with gr.Tabs(selected='tab_img_prompt') as tabs_prompt:
                    with gr.Tab('Image Prompt', id='tab_img_prompt') as tab_ip:
                        image = gr.Image(label='Image', type='pil', image_mode='RGBA', height=250)
                    with gr.Tab('Text Prompt', id='tab_txt_prompt', visible=HAS_T2I) as tab_tp:
                        caption = gr.Textbox(label='Text Prompt', placeholder='HunyuanDiT will be used to generate image.')
                    with gr.Tab('MultiView Prompt', id='tab_mv_prompt', visible=False) as tab_mv_p:
                        with gr.Row():
                            mv_image_front = gr.Image(label='Front', type='pil', image_mode='RGBA', height=120)
                            mv_image_back = gr.Image(label='Back', type='pil', image_mode='RGBA', height=120)
                        with gr.Row():
                            mv_image_left = gr.Image(label='Left', type='pil', image_mode='RGBA', height=120)
                            mv_image_right = gr.Image(label='Right', type='pil', image_mode='RGBA', height=120)
                with gr.Row():
                    btn = gr.Button(value='Gen Shape', variant='primary')
                    btn_all = gr.Button(value='Gen Textured Shape', variant='primary', visible=HAS_TEXTUREGEN)

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
            with gr.Column(scale=8):
                with gr.Tabs(selected='gen_mesh_panel') as tabs_output:
                    with gr.Tab('Generated Mesh', id='gen_mesh_panel'):
                        html_gen_mesh = gr.HTML(HTML_PLACEHOLDER, label='Output')
                        with gr.Row():
                            file_out = gr.DownloadButton(label="Download .glb", variant='primary', visible=True)
                            file_out2 = gr.DownloadButton(label="Download Textured .glb", variant='primary', visible=True)
                    with gr.Tab('Mesh Statistic', id='stats_panel'):
                        stats = gr.Json({}, label='Mesh Stats')
            # User Gallery removed for Wave 1 fixes (Non-functional)
        
        btn.click(shape_generation, inputs=[model_key, caption, image, mv_image_front, mv_image_back, mv_image_left, mv_image_right, num_steps, cfg_scale, seed, octree_resolution, check_box_rembg, num_chunks, randomize_seed], outputs=[file_out, html_gen_mesh, stats, seed])
        btn_all.click(generation_all, inputs=[model_key, caption, image, mv_image_front, mv_image_back, mv_image_left, mv_image_right, num_steps, cfg_scale, seed, octree_resolution, check_box_rembg, num_chunks, randomize_seed], outputs=[file_out, file_out2, html_gen_mesh, stats, seed])
        # Logic to switch interfaces
        def update_input_interface(model_key):
            if model_key == "Multiview":
                return gr.update(visible=False), gr.update(visible=False), gr.update(visible=True)
            else:
                return gr.update(visible=True), gr.update(visible=HAS_T2I), gr.update(visible=False)

        model_key.change(fn=update_input_interface, inputs=model_key, outputs=[tab_ip, tab_tp, tab_mv_p])

    return demo

def main():
    global request_manager, SAVE_DIR, HAS_T2I, HAS_TEXTUREGEN
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_path", type=str, default='tencent/Hunyuan3D-2mini')
    parser.add_argument("--subfolder", type=str, default='hunyuan3d-dit-v2-mini-turbo')
    parser.add_argument("--texgen_model_path", type=str, default='tencent/Hunyuan3D-2')
    parser.add_argument('--port', type=int, default=7860)
    parser.add_argument('--host', type=str, default='127.0.0.1')
    parser.add_argument('--device', type=str, default='cuda')
    parser.add_argument('--cache-path', type=str, default='gradio_cache')
    parser.add_argument('--enable_t23d', action='store_true')
    parser.add_argument('--disable_tex', action='store_true')
    parser.add_argument('--low_vram_mode', action='store_true')
    parser.add_argument('--no-browser', action='store_true', help='Do not open the browser automatically')
    args = parser.parse_args()
    SAVE_DIR = args.cache_path
    os.makedirs(SAVE_DIR, exist_ok=True)
    HAS_T2I = args.enable_t23d
    HAS_TEXTUREGEN = not args.disable_tex

    model_mgr = ModelManager(capacity=1 if args.low_vram_mode else 3, device=args.device)
    def get_loader(model_path, subfolder):
        return lambda: InferencePipeline(
            model_path=model_path, tex_model_path=args.texgen_model_path, subfolder=subfolder,
            device=args.device, enable_t2i=args.enable_t23d, enable_tex=not args.disable_tex
        )
    model_mgr.register_model("Normal", get_loader("tencent/Hunyuan3D-2", "hunyuan3d-dit-v2-0-turbo"))
    model_mgr.register_model("Small", get_loader("tencent/Hunyuan3D-2mini", "hunyuan3d-dit-v2-mini-turbo"))
    model_mgr.register_model("Multiview", get_loader("tencent/Hunyuan3D-2mv", "hunyuan3d-dit-v2-mv-turbo"))
    request_manager = PriorityRequestManager(model_mgr, max_concurrency=1)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(request_manager.start())
    app = FastAPI()
    static_dir = Path(SAVE_DIR).absolute()
    app.mount("/static", StaticFiles(directory=static_dir, html=True), name="static")
    demo = build_app()
    app = gr.mount_gradio_app(app, demo, path="/")
    url = f"http://{args.host}:{args.port}"
    print(f"\nHunyuan3D-2 Pro Unified is running at: {url}\n")
    if not args.no_browser:
        webbrowser.open(url)
    uvicorn.run(app, host=args.host, port=args.port, workers=1)

if __name__ == '__main__':
    main()
