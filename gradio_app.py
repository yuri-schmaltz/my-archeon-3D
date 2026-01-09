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
from glob import glob
from pathlib import Path

import gradio as gr
import torch
import trimesh
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uuid

from hy3dgen.shapegen.utils import logger
from hy3dgen.manager import PriorityRequestManager, ModelManager
from hy3dgen.inference import InferencePipeline

# Global Manager
request_manager = None

MAX_SEED = int(1e7)


def get_example_img_list():
    return []


def get_example_txt_list():
    return []


def get_example_mv_list():
    return []


def gen_save_folder(max_size=200):
    os.makedirs(SAVE_DIR, exist_ok=True)

    # Get all folder paths
    dirs = [f for f in Path(SAVE_DIR).iterdir() if f.is_dir()]

    # If folder count exceeds max_size, delete the oldest folder
    # [PATCH] Disabled to prevent data loss
    # if len(dirs) >= max_size:
    #     # Sort by creation time, oldest first
    #     oldest_dir = min(dirs, key=lambda x: x.stat().st_ctime)
    #     shutil.rmtree(oldest_dir)
    #     print(f"Removed the oldest folder: {oldest_dir}")

    # Generate a new uuid folder name
    new_folder = os.path.join(SAVE_DIR, str(uuid.uuid4()))
    os.makedirs(new_folder, exist_ok=True)
    print(f"Created new folder: {new_folder}")

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
    # Remove first folder from path to make relative path
    if textured:
        related_path = f"./textured_mesh.glb"
        template_name = './assets/modelviewer-textured-template.html'
        output_html_path = os.path.join(save_folder, f'textured_mesh.html')
    else:
        related_path = f"./white_mesh.glb"
        template_name = './assets/modelviewer-template.html'
        output_html_path = os.path.join(save_folder, f'white_mesh.html')
    offset = 50 if textured else 10
    with open(os.path.join(CURRENT_DIR, template_name), 'r', encoding='utf-8') as f:
        template_html = f.read()

    with open(output_html_path, 'w', encoding='utf-8') as f:
        template_html = template_html.replace('#height#', f'{height - offset}')
        template_html = template_html.replace('#width#', f'{width}')
        template_html = template_html.replace('#src#', f'{related_path}/')
        f.write(template_html)

    rel_path = os.path.relpath(output_html_path, SAVE_DIR)
    iframe_tag = f'<iframe src="/static/{rel_path}" height="{height}" width="100%" frameborder="0"></iframe>'
    print(
        f'Find html file {output_html_path}, {os.path.exists(output_html_path)}, relative HTML path is /static/{rel_path}')

    return f"""
        <div style='height: {height}; width: 100%;'>
        {iframe_tag}
        </div>
    """


async def shape_generation(
    model_key,
    caption=None,
    image=None,
    mv_image_front=None,
    mv_image_back=None,
    mv_image_left=None,
    mv_image_right=None,
    steps=50,
    guidance_scale=7.5,
    seed=1234,
    octree_resolution=256,
    check_box_rembg=False,
    num_chunks=200000,
    randomize_seed: bool = False,
):
    mv_mode = model_key == "Multiview"
    if not mv_mode and image is None and caption is None:
        raise gr.Error("Please provide either a caption or an image.")
    
    mv_images = {}
    if mv_mode:
        if mv_image_front is None and mv_image_back is None and mv_image_left is None and mv_image_right is None:
            raise gr.Error("Please provide at least one view image.")
        if mv_image_front: mv_images['front'] = mv_image_front
        if mv_image_back: mv_images['back'] = mv_image_back
        if mv_image_left: mv_images['left'] = mv_image_left
        if mv_image_right: mv_images['right'] = mv_image_right

    seed = int(randomize_seed_fn(seed, randomize_seed))
    octree_resolution = int(octree_resolution)
    
    params = {
        "model_key": model_key,
        "text": caption,
        "image": image,
        "mv_images": mv_images if mv_mode else None,
        "num_inference_steps": steps,
        "guidance_scale": guidance_scale,
        "seed": seed,
        "octree_resolution": octree_resolution,
        "do_rembg": check_box_rembg,
        "num_chunks": num_chunks,
        "do_texture": False
    }

    # Submit to manager
    try:
        result = await request_manager.submit(params)
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise gr.Error(f"Generation failed: {e}")

    # Process result
    mesh = result["mesh"]
    stats = result["stats"]
    out_image = result["image"]
    
    # Save (reusing local helpers)
    save_folder = gen_save_folder()
    
    # Stats update
    stats['number_of_faces'] = mesh.faces.shape[0]
    stats['number_of_vertices'] = mesh.vertices.shape[0]
    mesh.metadata['extras'] = stats

    path = export_mesh(mesh, save_folder, textured=False)
    html_height = 690 if mv_mode else 650
    model_viewer_html = build_model_viewer_html(save_folder, height=html_height, width=HTML_WIDTH)
    
    return (
        gr.update(value=path),
        model_viewer_html,
        stats,
        seed,
    )


async def generation_all(
    model_key,
    caption=None,
    image=None,
    mv_image_front=None,
    mv_image_back=None,
    mv_image_left=None,
    mv_image_right=None,
    steps=50,
    guidance_scale=7.5,
    seed=1234,
    octree_resolution=256,
    check_box_rembg=False,
    num_chunks=200000,
    randomize_seed: bool = False,
):
    mv_mode = model_key == "Multiview"
    # Same setup
    if not mv_mode and image is None and caption is None:
        raise gr.Error("Please provide either a caption or an image.")
        
    mv_images = {}
    if mv_mode:
       if mv_image_front: mv_images['front'] = mv_image_front
       if mv_image_back: mv_images['back'] = mv_image_back
       if mv_image_left: mv_images['left'] = mv_image_left
       if mv_image_right: mv_images['right'] = mv_image_right
       if not mv_images: raise gr.Error("Please provide at least one view image.")

    seed = int(randomize_seed_fn(seed, randomize_seed))
    octree_resolution = int(octree_resolution)
    
    params = {
        "model_key": model_key,
        "text": caption,
        "image": image,
        "mv_images": mv_images if mv_mode else None,
        "num_inference_steps": steps,
        "guidance_scale": guidance_scale,
        "seed": seed,
        "octree_resolution": octree_resolution,
        "do_rembg": check_box_rembg,
        "num_chunks": num_chunks,
        "do_texture": True # Request Texture
    }

    try:
        result = await request_manager.submit(params)
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise gr.Error(f"Generation failed: {e}")

    mesh = result["mesh"]
    textured_mesh = result["textured_mesh"]
    stats = result["stats"]
    out_image = result["image"]
    
    save_folder = gen_save_folder()
    
    stats['number_of_faces'] = mesh.faces.shape[0]
    stats['number_of_vertices'] = mesh.vertices.shape[0]
    textured_mesh.metadata['extras'] = stats

    path = export_mesh(mesh, save_folder, textured=False)
    path_textured = export_mesh(textured_mesh, save_folder, textured=True)
    
    html_height = 690 if mv_mode else 650
    model_viewer_html_textured = build_model_viewer_html(save_folder, height=html_height, width=HTML_WIDTH, textured=True)

    return (
        gr.update(value=path),
        gr.update(value=path_textured),
        model_viewer_html_textured,
        stats,
        seed,
    )


def build_app():
    title = 'Hunyuan3D-2 Pro: High Resolution Textured 3D Assets Generation'
    if TURBO_MODE:
        title = title.replace(':', '-Turbo: Fast ')

    title_html = f"""
    <div style="font-size: 2em; font-weight: bold; text-align: center; margin-bottom: 5px">

    {title}
    </div>
    <div align="center">
    Tencent Hunyuan3D Team
    </div>
    <div align="center">
      <a href="https://github.com/tencent/Hunyuan3D-2">Github</a> &ensp; 
      <a href="http://3d-models.hunyuan.tencent.com">Homepage</a> &ensp;
      <a href="https://3d.hunyuan.tencent.com">Hunyuan3D Studio</a> &ensp;
      <a href="#">Technical Report</a> &ensp;
      <a href="https://huggingface.co/Tencent/Hunyuan3D-2"> Pretrained Models</a> &ensp;
    </div>
    """
    custom_css = """
    .app.svelte-wpkpf6.svelte-wpkpf6:not(.fill_width) {
        max-width: 1480px;
    }
    .mv-image button .wrap {
        font-size: 10px;
    }

    .mv-image .icon-wrap {
        width: 20px;
    }

    """

    with gr.Blocks(theme=gr.themes.Base(), title='Hunyuan-3D-2.0', analytics_enabled=False, css=custom_css) as demo:
        gr.HTML(title_html)

        with gr.Row():
            with gr.Column(scale=3):
                model_key = gr.Dropdown(
                    label="Model Category",
                    choices=["Normal", "Small", "Multiview"],
                    value="Normal"
                )
                
                with gr.Tabs(selected='tab_img_prompt') as tabs_prompt:
                    with gr.Tab('Image Prompt', id='tab_img_prompt') as tab_ip:
                        image = gr.Image(label='Image', type='pil', image_mode='RGBA', height=290)

                    with gr.Tab('Text Prompt', id='tab_txt_prompt', visible=HAS_T2I) as tab_tp:
                        caption = gr.Textbox(label='Text Prompt',
                                             placeholder='HunyuanDiT will be used to generate image.',
                                             info='Example: A 3D model of a cute cat, white background')
                    with gr.Tab('MultiView Prompt', id='tab_mv_prompt', visible=False) as tab_mv_p:
                        # gr.Label('Please upload at least one front image.')
                        with gr.Row():
                            mv_image_front = gr.Image(label='Front', type='pil', image_mode='RGBA', height=140,
                                                      min_width=100, elem_classes='mv-image')
                            mv_image_back = gr.Image(label='Back', type='pil', image_mode='RGBA', height=140,
                                                     min_width=100, elem_classes='mv-image')
                        with gr.Row():
                            mv_image_left = gr.Image(label='Left', type='pil', image_mode='RGBA', height=140,
                                                     min_width=100, elem_classes='mv-image')
                            mv_image_right = gr.Image(label='Right', type='pil', image_mode='RGBA', height=140,
                                                      min_width=100, elem_classes='mv-image')

                with gr.Row():
                    btn = gr.Button(value='Gen Shape', variant='primary', min_width=100)
                    btn_all = gr.Button(value='Gen Textured Shape',
                                        variant='primary',
                                        visible=HAS_TEXTUREGEN,
                                        min_width=100)

                with gr.Group():
                    file_out = gr.File(label="File", visible=False)
                    file_out2 = gr.File(label="File", visible=False)

                with gr.Tabs(selected='tab_options' if TURBO_MODE else 'tab_export'):
                    with gr.Tab("Options", id='tab_options', visible=TURBO_MODE):
                        gen_mode = gr.Radio(label='Generation Mode',
                                            info='Recommendation: Turbo for most cases, Fast for very complex cases, Standard seldom use.',
                                            choices=['Turbo', 'Fast', 'Standard'], value='Turbo')
                        decode_mode = gr.Radio(label='Decoding Mode',
                                               info='The resolution for exporting mesh from generated vectset',
                                               choices=['Low', 'Standard', 'High'],
                                               value='Standard')
                    with gr.Tab('Advanced Options', id='tab_advanced_options'):
                        with gr.Row():
                            check_box_rembg = gr.Checkbox(value=True, label='Remove Background', min_width=100)
                            randomize_seed = gr.Checkbox(label="Randomize seed", value=True, min_width=100)
                        seed = gr.Slider(
                            label="Seed",
                            minimum=0,
                            maximum=MAX_SEED,
                            step=1,
                            value=1234,
                            min_width=100,
                        )
                        with gr.Row():
                            num_steps = gr.Slider(maximum=100,
                                                  minimum=1,
                                                  value=5 if 'turbo' in args.subfolder else 30,
                                                  step=1, label='Inference Steps')
                            octree_resolution = gr.Slider(maximum=512, minimum=16, value=256, label='Octree Resolution')
                        with gr.Row():
                            cfg_scale = gr.Number(value=5.0, label='Guidance Scale', min_width=100)
                            num_chunks = gr.Slider(maximum=5000000, minimum=1000, value=8000,
                                                   label='Number of Chunks', min_width=100)
                    with gr.Tab("Export", id='tab_export'):
                        with gr.Row():
                            file_type = gr.Dropdown(label='File Type', choices=SUPPORTED_FORMATS,
                                                    value='glb', min_width=100)
                            reduce_face = gr.Checkbox(label='Simplify Mesh', value=False, min_width=100)
                            export_texture = gr.Checkbox(label='Include Texture', value=False,
                                                         visible=False, min_width=100)
                        target_face_num = gr.Slider(maximum=1000000, minimum=100, value=10000,
                                                    label='Target Face Number')
                        with gr.Row():
                            confirm_export = gr.Button(value="Transform", min_width=100)
                            file_export = gr.DownloadButton(label="Download", variant='primary',
                                                            interactive=False, min_width=100)

            with gr.Column(scale=6):
                with gr.Tabs(selected='gen_mesh_panel') as tabs_output:
                    with gr.Tab('Generated Mesh', id='gen_mesh_panel'):
                        html_gen_mesh = gr.HTML(HTML_OUTPUT_PLACEHOLDER, label='Output')
                    with gr.Tab('Exporting Mesh', id='export_mesh_panel'):
                        html_export_mesh = gr.HTML(HTML_OUTPUT_PLACEHOLDER, label='Output')
                    with gr.Tab('Mesh Statistic', id='stats_panel'):
                        stats = gr.Json({}, label='Mesh Stats')

            with gr.Column(scale=3):
                with gr.Tabs(selected='tab_img_gallery') as gallery:
                    with gr.Tab('Image to 3D Gallery', id='tab_img_gallery') as tab_gi:
                        with gr.Row():
                            gr.Examples(examples=example_is, inputs=[image],
                                        label=None, examples_per_page=18)

                    with gr.Tab('Text to 3D Gallery', id='tab_txt_gallery', visible=HAS_T2I) as tab_gt:
                        with gr.Row():
                            gr.Examples(examples=example_ts, inputs=[caption],
                                        label=None, examples_per_page=18)
                    with gr.Tab('MultiView to 3D Gallery', id='tab_mv_gallery', visible=False) as tab_gmv:
                        with gr.Row():
                            gr.Examples(examples=example_mvs,
                                        inputs=[mv_image_front, mv_image_back, mv_image_left, mv_image_right],
                                        label=None, examples_per_page=6)

        gr.HTML(f"""
        if not HAS_TEXTUREGEN:
            gr.HTML("""
            <div style="margin-top: 5px;"  align="center">
                <b>Warning: </b>
                Texture synthesis is disable due to missing requirements,
                 please install requirements following <a href="https://github.com/Tencent/Hunyuan3D-2?tab=readme-ov-file#install-requirements">README.md</a>to activate it.
            </div>
            """)

        def on_model_key_change(key):
            is_mv = key == "Multiview"
            return (
                gr.update(visible=not is_mv), # tab_ip
                gr.update(visible=HAS_T2I and not is_mv), # tab_tp
                gr.update(visible=is_mv), # tab_mv_p
                gr.update(selected='tab_mv_prompt' if is_mv else 'tab_img_prompt'), # tabs_prompt
                gr.update(visible=not is_mv), # tab_gi
                gr.update(visible=HAS_T2I and not is_mv), # tab_gt
                gr.update(visible=is_mv), # tab_gmv
                gr.update(selected='tab_mv_gallery' if is_mv else 'tab_img_gallery'), # gallery
            )

        model_key.change(
            on_model_key_change, 
            inputs=[model_key], 
            outputs=[tab_ip, tab_tp, tab_mv_p, tabs_prompt, tab_gi, tab_gt, tab_gmv, gallery]
        )

        tab_ip.select(fn=lambda: gr.update(selected='tab_img_gallery'), outputs=gallery)
        if HAS_T2I:
            tab_tp.select(fn=lambda: gr.update(selected='tab_txt_gallery'), outputs=gallery)
        tab_mv_p.select(fn=lambda: gr.update(selected='tab_mv_gallery'), outputs=gallery)

        btn.click(
            shape_generation,
            inputs=[
                caption,
                image,
                mv_image_front,
                mv_image_back,
                mv_image_left,
                mv_image_right,
                num_steps,
                cfg_scale,
                seed,
                octree_resolution,
                check_box_rembg,
                num_chunks,
                randomize_seed,
            ],
            outputs=[file_out, html_gen_mesh, stats, seed]
        ).then(
            lambda: (gr.update(visible=False, value=False), gr.update(interactive=True), gr.update(interactive=True),
                     gr.update(interactive=False)),
            outputs=[export_texture, reduce_face, confirm_export, file_export],
        ).then(
            lambda: gr.update(selected='gen_mesh_panel'),
            outputs=[tabs_output],
        )

        btn_all.click(
            generation_all,
            inputs=[
                caption,
                image,
                mv_image_front,
                mv_image_back,
                mv_image_left,
                mv_image_right,
                num_steps,
                cfg_scale,
                seed,
                octree_resolution,
                check_box_rembg,
                num_chunks,
                randomize_seed,
            ],
            outputs=[file_out, file_out2, html_gen_mesh, stats, seed]
        ).then(
            lambda: (gr.update(visible=True, value=True), gr.update(interactive=False), gr.update(interactive=True),
                     gr.update(interactive=False)),
            outputs=[export_texture, reduce_face, confirm_export, file_export],
        ).then(
            lambda: gr.update(selected='gen_mesh_panel'),
            outputs=[tabs_output],
        )

        def on_gen_mode_change(value):
            if value == 'Turbo':
                return gr.update(value=5)
            elif value == 'Fast':
                return gr.update(value=10)
            else:
                return gr.update(value=30)

        gen_mode.change(on_gen_mode_change, inputs=[gen_mode], outputs=[num_steps])

        def on_decode_mode_change(value):
            if value == 'Low':
                return gr.update(value=196)
            elif value == 'Standard':
                return gr.update(value=256)
            else:
                return gr.update(value=384)

        decode_mode.change(on_decode_mode_change, inputs=[decode_mode], outputs=[octree_resolution])

        def on_export_click(file_out, file_out2, file_type, reduce_face, export_texture, target_face_num):
            if file_out is None:
                raise gr.Error('Please generate a mesh first.')

            print(f'exporting {file_out}')
            print(f'reduce face to {target_face_num}')
            if export_texture:
                mesh = trimesh.load(file_out2)
                save_folder = gen_save_folder()
                path = export_mesh(mesh, save_folder, textured=True, type=file_type)

                # for preview
                save_folder = gen_save_folder()
                _ = export_mesh(mesh, save_folder, textured=True)
                model_viewer_html = build_model_viewer_html(save_folder, height=HTML_HEIGHT, width=HTML_WIDTH,
                                                            textured=True)
            else:
                mesh = trimesh.load(file_out)
                mesh = floater_remove_worker(mesh)
                mesh = degenerate_face_remove_worker(mesh)
                if reduce_face:
                    mesh = face_reduce_worker(mesh, target_face_num)
                save_folder = gen_save_folder()
                path = export_mesh(mesh, save_folder, textured=False, type=file_type)

                # for preview
                save_folder = gen_save_folder()
                _ = export_mesh(mesh, save_folder, textured=False)
                model_viewer_html = build_model_viewer_html(save_folder, height=HTML_HEIGHT, width=HTML_WIDTH,
                                                            textured=False)
            print(f'export to {path}')
            return model_viewer_html, gr.update(value=path, interactive=True)

        confirm_export.click(
            lambda: gr.update(selected='export_mesh_panel'),
            outputs=[tabs_output],
        ).then(
            on_export_click,
            inputs=[file_out, file_out2, file_type, reduce_face, export_texture, target_face_num],
            outputs=[html_export_mesh, file_export]
        )

    return demo


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--model_path", type=str, default='tencent/Hunyuan3D-2mini')
    parser.add_argument("--subfolder", type=str, default='hunyuan3d-dit-v2-mini-turbo')
    parser.add_argument("--texgen_model_path", type=str, default='tencent/Hunyuan3D-2')
    parser.add_argument('--port', type=int, default=8081)
    parser.add_argument('--host', type=str, default='0.0.0.0')
    parser.add_argument('--device', type=str, default='cuda')
    parser.add_argument('--mc_algo', type=str, default='mc')
    parser.add_argument('--cache-path', type=str, default='gradio_cache')
    parser.add_argument('--enable_t23d', action='store_true')
    parser.add_argument('--disable_tex', action='store_true')
    parser.add_argument('--enable_flashvdm', action='store_true')
    parser.add_argument('--compile', action='store_true')
    parser.add_argument('--low_vram_mode', action='store_true')
    args = parser.parse_args()

    SAVE_DIR = args.cache_path
    os.makedirs(SAVE_DIR, exist_ok=True)

    HAS_T2I = args.enable_t23d
    TURBO_MODE = True # Default for unified app
    HTML_WIDTH = 500
    HTML_OUTPUT_PLACEHOLDER = f"""
    <div style='height: {650}px; width: 100%; border-radius: 8px; border-color: #e5e7eb; border-style: solid; border-width: 1px; display: flex; justify-content: center; align-items: center;'>
      <div style='text-align: center; font-size: 16px; color: #6b7280;'>
        <p style="color: #8d8d8d;">Welcome to Hunyuan3D!</p>
        <p style="color: #8d8d8d;">No mesh here.</p>
      </div>
    </div>
    """

    INPUT_MESH_HTML = """
    <div style='height: 490px; width: 100%; border-radius: 8px; 
    border-color: #e5e7eb; border-style: solid; border-width: 1px;'>
    </div>
    """
    example_is = get_example_img_list()
    example_ts = get_example_txt_list()
    example_mvs = get_example_mv_list()

    # Remove global initialization
    # HAS_T2I handled via params logic
    HAS_TEXTUREGEN = not args.disable_tex

    # Create Manager and Start
    model_mgr = ModelManager(capacity=1 if args.low_vram_mode else 3, device=args.device)
    
    # Register Model Loaders
    def get_loader(model_path, subfolder):
        return lambda: InferencePipeline(
            model_path=model_path,
            tex_model_path=args.texgen_model_path,
            subfolder=subfolder,
            device=args.device,
            enable_t2i=args.enable_t23d,
            enable_tex=not args.disable_tex,
            use_flashvdm=args.enable_flashvdm,
            mc_algo=args.mc_algo
        )

    model_mgr.register_model("Normal", get_loader("tencent/Hunyuan3D-2", "hunyuan3d-dit-v2-0-turbo"))
    model_mgr.register_model("Small", get_loader("tencent/Hunyuan3D-2mini", "hunyuan3d-dit-v2-mini-turbo"))
    model_mgr.register_model("Multiview", get_loader("tencent/Hunyuan3D-2mv", "hunyuan3d-dit-v2-mv-turbo"))
    
    request_manager = PriorityRequestManager(model_mgr, max_concurrency=1)
    
    # Start Manager Loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(request_manager.start())
    
    # https://discuss.huggingface.co/t/how-to-serve-an-html-file/33921/2
    # create a FastAPI app
    app = FastAPI()
    # create a static directory to store the static files
    static_dir = Path(SAVE_DIR).absolute()
    static_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=static_dir, html=True), name="static")
    shutil.copytree('./assets/env_maps', os.path.join(static_dir, 'env_maps'), dirs_exist_ok=True)

    if args.low_vram_mode:
        torch.cuda.empty_cache()
    demo = build_app()
    app = gr.mount_gradio_app(app, demo, path="/")
    uvicorn.run(app, host=args.host, port=args.port, workers=1)
