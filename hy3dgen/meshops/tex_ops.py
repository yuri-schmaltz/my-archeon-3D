import torch
import numpy as np
import logging
from PIL import Image
import trimesh
import os
import tempfile
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

    if MapType.AO in maps:
        mesh.visual.material.occlusionTexture = maps[MapType.AO]
        
    return mesh

def generate_uvs(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    """
    Generates UV coordinates for a mesh using xatlas.
    """
    try:
        import xatlas
    except ImportError:
        logger.error("xatlas not found. Cannot generate UVs.")
        return mesh

    logger.info("Generating UVs using xatlas...")
    atlas = xatlas.Atlas()
    atlas.add_mesh(mesh.vertices, mesh.faces)
    atlas.generate()
    
    # get_mesh(0) returns (vmapping, indices, uvs)
    vmapping, indices, uvs = atlas.get_mesh(0)
    
    # xatlas might duplicate vertices to handle seams
    new_vertices = mesh.vertices[vmapping]
    new_faces = indices.reshape(-1, 3)
    
    # Create new mesh with UVs
    new_mesh = trimesh.Trimesh(vertices=new_vertices, faces=new_faces, process=False)
    new_mesh.visual = trimesh.visual.TextureVisuals(uv=uvs)
    
    # Transfer other properties if possible (trimesh copies normals usually)
    if hasattr(mesh.visual, 'material'):
        new_mesh.visual.material = mesh.visual.material
        
    return new_mesh

async def bake_maps_native(high_poly: trimesh.Trimesh, 
                           low_poly: trimesh.Trimesh, 
                           maps: List[str], 
                           resolution: int = 2048) -> Dict[str, str]:
    """
    Natively bakes maps from high-poly to low-poly using raycasting.
    Returns a dict of map_type -> path.
    """
    logger.info(f"Starting native baking for {maps} at {resolution}x{resolution}")
    
    # Ensure low_poly has UVs
    if not hasattr(low_poly.visual, 'uv') or low_poly.visual.uv is None:
        low_poly = generate_uvs(low_poly)
        
    uvs = low_poly.visual.uv
    results = {}
    tmp_dir = tempfile.mkdtemp()

    # Create Ray Intersector for High Poly
    if trimesh.ray.has_embree:
        intersector = trimesh.ray.ray_pyembree.RayMeshIntersector(high_poly)
    else:
        intersector = trimesh.ray.ray_triangle.RayMeshIntersector(high_poly)
    
    # Setup output maps
    baked_data = {m.lower(): np.zeros((resolution, resolution, 3), dtype=np.uint8) for m in maps}
    
    # Accumulators for bulk raycasting
    all_ray_origins = []
    all_ray_dirs = []
    all_pixel_coords = [] # (x, y)
    
    # 1. Rasterize UVs to find all ray starting points
    for i, face in enumerate(low_poly.faces):
        tri_uvs = uvs[face] * (resolution - 1)
        min_u, min_v = np.floor(np.min(tri_uvs, axis=0)).astype(int)
        max_u, max_v = np.ceil(np.max(tri_uvs, axis=0)).astype(int)
        min_u, max_u = np.clip([min_u, max_u], 0, resolution - 1)
        min_v, max_v = np.clip([min_v, max_v], 0, resolution - 1)
        
        u_coords = np.arange(min_u, max_u + 1)
        v_coords = np.arange(min_v, max_v + 1)
        uu, vv = np.meshgrid(u_coords, v_coords)
        pts = np.stack([uu.ravel(), vv.ravel()], axis=-1)
        
        # Barycentric coordinates
        v0 = tri_uvs[1] - tri_uvs[0]
        v1 = tri_uvs[2] - tri_uvs[0]
        v2 = pts - tri_uvs[0]
        d00, d01, d11 = np.dot(v0, v0), np.dot(v0, v1), np.dot(v1, v1)
        d20, d21 = np.einsum('ni,i->n', v2, v0), np.einsum('ni,i->n', v2, v1)
        denom = d00 * d11 - d01 * d01
        if abs(denom) < 1e-8: continue
        v_bary = (d11 * d20 - d01 * d21) / denom
        w_bary = (d00 * d21 - d01 * d20) / denom
        u_bary = 1.0 - v_bary - w_bary
        
        mask = (u_bary >= -0.01) & (v_bary >= -0.01) & (w_bary >= -0.01)
        if not np.any(mask): continue
        
        b = np.stack([u_bary[mask], v_bary[mask], w_bary[mask]], axis=-1)
        world_pos = np.einsum('ni,ij->nj', b, low_poly.vertices[face])
        world_norm = np.einsum('ni,ij->nj', b, low_poly.vertex_normals[face])
        norm_len = np.linalg.norm(world_norm, axis=1, keepdims=True)
        world_norm = np.divide(world_norm, norm_len, out=np.zeros_like(world_norm), where=norm_len > 1e-8)
        
        all_ray_origins.append(world_pos + world_norm * 0.001)
        all_ray_dirs.append(-world_norm)
        all_pixel_coords.append(pts[mask])

    if not all_ray_origins:
        logger.warning("No UV coverage found for baking.")
        return results

    all_ray_origins = np.concatenate(all_ray_origins, axis=0)
    all_ray_dirs = np.concatenate(all_ray_dirs, axis=0)
    all_pixel_coords = np.concatenate(all_pixel_coords, axis=0)

    # 2. Bulk Raycasting
    logger.info(f"Dispatching {len(all_ray_origins)} rays...")
    hit_idx, hit_ray_idx, hit_pos = intersector.intersects_id(
        all_ray_origins, all_ray_dirs, multiple_hits=False, return_locations=True
    )
    
    if len(hit_idx) > 0:
        pixel_x = all_pixel_coords[hit_ray_idx, 0].astype(int)
        pixel_y = all_pixel_coords[hit_ray_idx, 1].astype(int)
        
        if 'normal' in baked_data:
            hit_normals = high_poly.face_normals[hit_idx]
            norm_rgb = ((hit_normals + 1.0) * 127.5).astype(np.uint8)
            baked_data['normal'][pixel_y, pixel_x] = norm_rgb
            
        if 'ao' in baked_data:
            baked_data['ao'][pixel_y, pixel_x] = 255 # Simplified AO

    # Save results
    for mtype, data in baked_data.items():
        out_path = os.path.join(tmp_dir, f"baked_{mtype}.png")
        Image.fromarray(data).save(out_path)
        results[mtype] = out_path
        
    return results
