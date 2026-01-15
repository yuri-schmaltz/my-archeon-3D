import torch
import numpy as np
import logging
from PIL import Image
import trimesh
from typing import Dict, Any, List, Optional
from hy3dgen.api.schemas import ChannelPacking, MapType

logger = logging.getLogger("meshops.tex_ops")

def pack_channels(maps: Dict[MapType, Image.Image], preset: str = "orm") -> Image.Image:
    """
    Packs separate maps into a single RGB texture.
    ORM: R=AO, G=Roughness, B=Metallic
    RMA: R=Roughness, G=Metallic, B=AO
    """
    # Initialize with default values (AO=1, Roughness=1, Metallic=0)
    width, height = next(iter(maps.values())).size if maps else (1024, 1024)
    
    # Create empty arrays
    r = np.ones((height, width), dtype=np.uint8) * 255
    g = np.ones((height, width), dtype=np.uint8) * 255
    b = np.zeros((height, width), dtype=np.uint8)

    def get_map_array(mtype, default_val=255):
        if mtype in maps:
            img = maps[mtype].convert("L")
            if img.size != (width, height):
                img = img.resize((width, height), Image.LANCZOS)
            return np.array(img)
        return np.ones((height, width), dtype=np.uint8) * default_val

    if preset == "orm":
        # R: AO, G: Roughness, B: Metallic
        r = get_map_array(MapType.AO, 255)
        g = get_map_array(MapType.ROUGHNESS, 255)
        b = get_map_array(MapType.METALLIC, 0)
    elif preset == "rma":
        # R: Roughness, G: Metallic, B: AO
        r = get_map_array(MapType.ROUGHNESS, 255)
        g = get_map_array(MapType.METALLIC, 0)
        b = get_map_array(MapType.AO, 255)
    
    packed = np.stack([r, g, b], axis=-1)
    return Image.fromarray(packed)

async def apply_auto_texture(mesh: trimesh.Trimesh, 
                            pipeline: Any, 
                            image: Image.Image, 
                            params: Dict[str, Any]) -> trimesh.Trimesh:
    """
    Calls the Hunyuan3DPaintPipeline.
    """
    if pipeline is None:
        logger.warning("Texture pipeline not available. Skipping auto_texture.")
        return mesh
        
    # Prepare params
    tex_kwargs = {
        'steps': params.get("steps", 30),
        'guidance_scale': params.get("guidance_scale", 5.0),
        'seed': params.get("seed", 0)
    }
    
    logger.info(f"Running auto_texture with {tex_kwargs}")
    # PaintPipeline expects a trimesh mesh and a PIL image
    try:
        # Run in a thread if it's synchronous (it is)
        # But for now, we assume we are in the background worker which is already in an executor
        # if using Manager.generate_safe. 
        # However, MeshOpsEngine is called from background_job_wrapper directly.
        # We should use asyncio.to_thread or similar if needed.
        
        textured_mesh = pipeline(mesh, image, **tex_kwargs)
        return textured_mesh
    except Exception as e:
        logger.error(f"Auto-texture failed: {e}")
        return mesh

def apply_material_maps(mesh: trimesh.Trimesh, maps: Dict[MapType, Image.Image]):
    """
    Attaches textures to the trimesh material.
    Trimesh PBR material supports:
    baseColorTexture, metallicRoughnessTexture, emittanceTexture, normalTexture, occlusionTexture
    """
    if not hasattr(mesh, 'visual') or not isinstance(mesh.visual, trimesh.visual.TextureVisuals):
        # We need UVs to use textures.
        # If no UVs, this will likely fail or do nothing useful.
        logger.warning("Applying textures to mesh without TextureVisuals/UVs.")
        
    # Check if we should pack ORM
    # In GLTF/GLB, Metallic and Roughness are packed into one texture (B=Metallic, G=Roughness).
    
    # Base Color
    if MapType.BASECOLOR in maps:
        if not hasattr(mesh.visual, 'material'):
            mesh.visual.material = trimesh.visual.material.PBRMaterial()
            
        mesh.visual.material.baseColorTexture = maps[MapType.BASECOLOR]
        
    # Pack MetallicRoughness if both exist or one exists
    if MapType.METALLIC in maps or MapType.ROUGHNESS in maps:
        # GLTF Standard: Green=Roughness, Blue=Metallic
        width, height = next(iter(maps.values())).size
        mr_map = np.zeros((height, width, 3), dtype=np.uint8)
        
        if MapType.ROUGHNESS in maps:
            mr_map[:,:,1] = np.array(maps[MapType.ROUGHNESS].convert("L"))
        else:
            mr_map[:,:,1] = 255 # Default roughness 1.0
            
        if MapType.METALLIC in maps:
            mr_map[:,:,2] = np.array(maps[MapType.METALLIC].convert("L"))
            
        mesh.visual.material.metallicRoughnessTexture = Image.fromarray(mr_map)

    if MapType.NORMAL in maps:
        mesh.visual.material.normalTexture = maps[MapType.NORMAL]
        
    if MapType.AO in maps:
        mesh.visual.material.occlusionTexture = maps[MapType.AO]
        
    return mesh
