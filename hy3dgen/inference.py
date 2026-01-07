import os
import time
import torch
import logging
import trimesh
import base64
from io import BytesIO
from typing import Dict, Any, Optional

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
                 mc_algo: str = 'mc'):
        
        self.device = device
        self.rembg = BackgroundRemover()
        
        logger.info(f"Loading ShapeGen model from {model_path}...")
        self.pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
            model_path,
            subfolder=subfolder,
            use_safetensors=True,
            device=device,
        )
        
        if use_flashvdm:
            self.pipeline.enable_flashvdm(mc_algo=mc_algo)

        self.pipeline_t2i = None
        if enable_t2i:
            logger.info("Loading Text2Image model...")
            self.pipeline_t2i = HunyuanDiTPipeline(
                'Tencent-Hunyuan/HunyuanDiT-v1.1-Diffusers-Distilled',
                device=device
            )

        self.pipeline_tex = None
        if enable_tex:
            logger.info(f"Loading TexGen model from {tex_model_path}...")
            self.pipeline_tex = Hunyuan3DPaintPipeline.from_pretrained(tex_model_path)

        # Helper workers
        self.floater_remover = FloaterRemover()
        self.degenerate_remover = DegenerateFaceRemover()
        self.face_reducer = FaceReducer()

    def generate(self, uid: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for generation.
        params: dict containing 'image', 'text', 'seed', 'do_texture', etc.
        """
        logger.info(f"[{uid}] Generation started.")
        stats = {'time': {}}
        t0 = time.time()

        # 1. Input Processing (Text -> Image if needed)
        image = params.get("image")
        if image is None:
            if params.get("text") and self.pipeline_t2i:
                logger.info(f"[{uid}] Generating image from text...")
                t1 = time.time()
                image = self.pipeline_t2i(params["text"])
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
             t1 = time.time()
             image = self.rembg(image)
             stats['time']['rembg'] = time.time() - t1
        elif isinstance(image, dict):
             # MV Mode: rembg is handled or images are already processed?
             # Gradio app does rmbg loop.
             if params.get("do_rembg", True):
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
        generator = torch.Generator(self.device).manual_seed(seed)
        
        shape_params = {
            "image": image,
            "num_inference_steps": params.get("num_inference_steps", 30),
            "guidance_scale": params.get("guidance_scale", 7.5),
            "octree_resolution": params.get("octree_resolution", 256),
            "num_chunks": params.get("num_chunks", 200000),
            "generator": generator,
            "output_type": "mesh"
        }
        
        # Determine if MV mode (passed via params or inferred)
        # For now assume standard flow
        
        logger.info(f"[{uid}] Generating shape...")
        t1 = time.time()
        # The pipeline output is a list, we take [0]
        mesh = self.pipeline(**shape_params)[0]
        stats['time']['shape_gen'] = time.time() - t1

        # Post-processing (always do basic cleanup?) 
        # API did it only if texturing? Grado does it optionally?
        # Let's clean up a bit if requested
        if params.get("reduce_face", False):
             mesh = self.floater_remover(mesh)
             mesh = self.degenerate_remover(mesh)
             
        
        # 3. Texturing (Optional)
        textured_mesh = None
        if params.get("do_texture", False) and self.pipeline_tex:
            logger.info(f"[{uid}] Generating texture...")
            # Usually require cleanup before texturing
            mesh = self.floater_remover(mesh)
            mesh = self.degenerate_remover(mesh)
            mesh = self.face_reducer(mesh, max_facenum=params.get("target_face_num", 40000))
            
            t1 = time.time()
            textured_mesh = self.pipeline_tex(mesh, image)
            stats['time']['tex_gen'] = time.time() - t1
        
        stats['time']['total'] = time.time() - t0
        
        return {
            "mesh": mesh,
            "textured_mesh": textured_mesh,
            "image": image,
            "stats": stats,
            "uid": uid
        }

