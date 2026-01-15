import time
import torch
import logging
import trimesh
from typing import Dict, Any

from hy3dgen.rembg import BackgroundRemover
from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline, FloaterRemover, DegenerateFaceRemover, FaceReducer
from hy3dgen.texgen import Hunyuan3DPaintPipeline
from hy3dgen.text2image import HunyuanDiTPipeline
from hy3dgen.shapegen.utils import get_logger

logger = get_logger("inference")

class InferencePipeline:
    """
    Unified pipeline for Hunyuan3D generation.
    Handles Text-to-Image, Image-to-3D, and Texturing.
    """
    def __init__(self, 
                 model_path: str, 
                 tex_model_path: str, 
                 subfolder: str, 
                 device: str = 'cuda', 
                 enable_t2i: bool = False,
                 enable_tex: bool = False,
                 use_flashvdm: bool = True,
                 mc_algo: str = 'mc',
                 low_vram_mode: bool = False):
        
        self.device = device
        self.low_vram_mode = low_vram_mode
        self.rembg = BackgroundRemover()
        
        logger.info(f"Loading ShapeGen model from {model_path}...")
        self.pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
            model_path,
            subfolder=subfolder,
            use_safetensors=True,
            device=device,
            low_vram_mode=low_vram_mode,
        )
        
        if use_flashvdm:
            self.pipeline.enable_flashvdm(mc_algo=mc_algo)

        if low_vram_mode:
            logger.info("Enabling CPU offload for ShapeGen model...")
            self.pipeline.enable_model_cpu_offload()
            torch.cuda.empty_cache()

        self.pipeline_t2i = None
        if enable_t2i:
            logger.info("Loading Text2Image model...")
            self.pipeline_t2i = HunyuanDiTPipeline(
                'Tencent-Hunyuan/HunyuanDiT-v1.1-Diffusers-Distilled',
                device=device,
                low_vram_mode=low_vram_mode
            )
            torch.cuda.empty_cache()

        self.pipeline_tex = None
        if enable_tex:
            logger.info(f"Loading TexGen model from {tex_model_path}...")
            self.pipeline_tex = Hunyuan3DPaintPipeline.from_pretrained(
                tex_model_path, 
                subfolder='hunyuan3d-paint-v2-0-turbo',
                low_vram_mode=low_vram_mode
            )
            if low_vram_mode:
                self.pipeline_tex.enable_model_cpu_offload()
                torch.cuda.empty_cache()

        # Helper workers
        self.floater_remover = FloaterRemover()
        self.degenerate_remover = DegenerateFaceRemover()
        self.face_reducer = FaceReducer()

    def generate(self, uid: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for generation.
        params: dict containing 'image', 'text', 'seed', 'do_texture', etc.
        """
        # Helper for progress reporting
        progress_callback = params.get("progress_callback", None)
        cancel_event = params.get("cancel_event", None)

        def report_progress(percent, msg):
            if cancel_event and cancel_event.is_set():
                logger.info(f"[{uid}] Generation cancelled by user.")
                raise InterruptedError("Generation cancelled locally")
                
            if progress_callback:
                progress_callback(percent, msg)
            logger.info(f"[{uid}] Progress {percent}%: {msg}")

        logger.info(f"[{uid}] Generation started.")
        stats = {'time': {}}
        t0 = time.time()

        report_progress(0, "Starting generation...")

        # 1. Input Processing (Text -> Image if needed)
        image = params.get("image")
        if image is None:
            if params.get("text") and self.pipeline_t2i:
                report_progress(5, "Generating Image from Text...")
                logger.info(f"[{uid}] Generating image from text...")
                t1 = time.time()
                # Use passed seed or default
                seed = int(params.get("seed", 0))
                steps = int(params.get("t2i_steps", 25))
                neg = params.get("negative_prompt", None)
                
                image = self.pipeline_t2i(
                    prompt=params["text"],
                    negative_prompt=neg,
                    seed=seed,
                    num_inference_steps=steps
                )
                stats['time']['t2i'] = time.time() - t1
            elif params.get("text") and not self.pipeline_t2i:
                raise ValueError("Text provided but T2I model is disabled.")
            elif "mv_images" in params:
                # MV Mode: we expect a dict of images or we construct it
                logging.info(f"[{uid}] Using Multi-View images...")
                image = params["mv_images"]
            else:
                pass 

        if image and not isinstance(image, dict):
             # Remove background for Single Image
             report_progress(10, "Removing Background...")
             t1 = time.time()
             image = self.rembg(image)
             stats['time']['rembg'] = time.time() - t1
        elif isinstance(image, dict):
             # MV Mode: rembg is handled or images are already processed?
             # Gradio app does rmbg loop.
             if params.get("do_rembg", True):
                 report_progress(10, "Removing Background (Multi-View)...")
                 t1 = time.time()
                 new_image = {}
                 for k, v in image.items():
                     if v.mode == "RGB": # or check_box_rembg
                        new_image[k] = self.rembg(v)
                     else:
                        new_image[k] = v
                 image = new_image
                 stats['time']['rembg'] = time.time() - t1
        
        # 2. Shape Generation
        # Prepare shape gen params
        seed = int(params.get("seed", 1234))
        # Create generator respecting offload: CPU generator avoids device mismatch when the model is offloaded
        if getattr(self, "low_vram_mode", False):
            generator = torch.Generator('cpu').manual_seed(seed)
        else:
            exec_device = self.pipeline._execution_device if hasattr(self.pipeline, '_execution_device') else self.device
            generator = torch.Generator(exec_device).manual_seed(seed)
        
        # Callback wrapper for pipeline
        # Map pipeline steps (0-100%) to specific global range (approx 20% to 80%)
        def pipeline_callback(step: int, timestep: int, latents: torch.Tensor):
            # Assuming ~30 to 50 steps usually
            # We want to map this progress to global 20% -> 80% range if texture is enabled
            # Or 20% -> 95% if texture is disabled
            
            total_steps = params.get("num_inference_steps", 30)
            has_texture = params.get("do_texture", False) and self.pipeline_tex
            
            start_range = 20
            end_range = 80 if has_texture else 95
            
            # steps go 0 -> total_steps
            ratio = (step + 1) / total_steps
            current_percent = start_range + int(ratio * (end_range - start_range))
            report_progress(current_percent, f"Generating Shape (Step {step+1}/{total_steps})")

        shape_params = {
            "image": image,
            "num_inference_steps": params.get("num_inference_steps", 30),
            "guidance_scale": params.get("guidance_scale", 7.5),
            "octree_resolution": params.get("octree_resolution", 256),
            "num_chunks": params.get("num_chunks", 8000), # Reduced default from 200k to 8k
            "generator": generator,
            "output_type": "mesh",
            "callback": pipeline_callback,
            "callback_steps": 1
        }
        
        # Determine if MV mode (passed via params or inferred)
        # For now assume standard flow
        
        report_progress(20, "Initializing Shape Generation...")
        print(f"[{uid}] Generating shape with params: steps={shape_params['num_inference_steps']}, chunks={shape_params['num_chunks']}", flush=True)
        t1 = time.time()
        # The pipeline output is a list, we take [0]
        try:
            mesh = self.pipeline(**shape_params)[0]
        except Exception as e:
            print(f"[{uid}] Shape generation FAILED: {e}", flush=True)
            raise e
        stats['time']['shape_gen'] = time.time() - t1
        print(f"[{uid}] Shape generation done in {stats['time']['shape_gen']:.2f}s", flush=True)

        # Convert Latent2MeshOutput to trimesh if needed
        if hasattr(mesh, 'mesh_v') and hasattr(mesh, 'mesh_f'):
            mesh = trimesh.Trimesh(vertices=mesh.mesh_v, faces=mesh.mesh_f)
            logger.info(f"[{uid}] Converted Latent2MeshOutput to trimesh")

        # Post-processing: Always apply basic cleanup for better quality
        report_progress(75, "Cleaning Mesh...")
        try:
            mesh = self.floater_remover(mesh)
            mesh = self.degenerate_remover(mesh)
        except Exception as e:
            logger.warning(f"[{uid}] Mesh cleanup warning: {e}")
        
        # 3. Texturing (Optional)
        textured_mesh = None
        if params.get("do_texture", False) and self.pipeline_tex:
            report_progress(85, "Generating Texture...")
            logger.info(f"[{uid}] Generating texture...")
            logger.info(f"[{uid}] Mesh before texturing: {len(mesh.vertices)} verts, {len(mesh.faces)} faces")
            
            # Further optimization for texture generation
            try:
                mesh = self.face_reducer(mesh, max_facenum=params.get("target_face_num", 40000))
                logger.info(f"[{uid}] Mesh after face reduction: {len(mesh.vertices)} verts, {len(mesh.faces)} faces")
            except Exception as e:
                logger.warning(f"[{uid}] Face reduction warning: {e}")
            
            try:
                t1 = time.time()
                
                # Extract texture-specific parameters
                tex_kwargs = {
                    'steps': params.get("tex_steps", 30),
                    'guidance_scale': params.get("tex_guidance_scale", 5.0),
                    'seed': int(params.get("tex_seed", 0))
                }
                logger.info(f"[{uid}] TexGen Params: {tex_kwargs}")
                
                textured_mesh = self.pipeline_tex(mesh, image, **tex_kwargs)
                stats['time']['tex_gen'] = time.time() - t1
                logger.info(f"[{uid}] Texture generation completed in {stats['time']['tex_gen']:.2f}s")
                logger.info(f"[{uid}] Textured mesh type: {type(textured_mesh)}")
                if hasattr(textured_mesh, 'visual'):
                    logger.info(f"[{uid}] Textured mesh visual type: {type(textured_mesh.visual)}")
                    if hasattr(textured_mesh.visual, 'image'):
                        logger.info(f"[{uid}] Textured mesh has image: {textured_mesh.visual.image is not None}")
                    if hasattr(textured_mesh.visual, 'uv'):
                        logger.info(f"[{uid}] Textured mesh has UV: {textured_mesh.visual.uv is not None}")
            except Exception as e:
                logger.error(f"[{uid}] Texture generation FAILED: {e}", exc_info=True)
                # Return untextured mesh with white color if texturing fails
                textured_mesh = mesh.copy()
                # Ensure it has white color for visual feedback
                import numpy as np
                white_color = np.array([255, 255, 255, 255], dtype=np.uint8)
                textured_mesh.visual = trimesh.visual.ColorVisuals(mesh=textured_mesh)
                textured_mesh.visual.face_colors = np.tile(white_color, (len(textured_mesh.faces), 1))
        
        stats['time']['total'] = time.time() - t0
        report_progress(100, "Generation Complete!")
        
        return {
            "mesh": mesh,
            "textured_mesh": textured_mesh,
            "image": image,
            "stats": stats,
            "uid": uid
        }

