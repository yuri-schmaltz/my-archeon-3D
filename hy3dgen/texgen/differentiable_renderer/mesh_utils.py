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

import trimesh
import numpy as np


def load_mesh(mesh):
    vtx_pos = mesh.vertices if hasattr(mesh, 'vertices') else None
    pos_idx = mesh.faces if hasattr(mesh, 'faces') else None

    # Check if mesh has UV coordinates
    if hasattr(mesh.visual, 'uv') and mesh.visual.uv is not None:
        vtx_uv = mesh.visual.uv
    else:
        # Generate simple planar UV mapping if none exists
        if vtx_pos is not None:
            # Normalize vertex positions to [0, 1] range for UV
            min_coords = vtx_pos.min(axis=0)
            max_coords = vtx_pos.max(axis=0)
            range_coords = max_coords - min_coords
            # Avoid division by zero
            range_coords[range_coords == 0] = 1.0
            # Use XY projection for UV
            vtx_uv = (vtx_pos[:, :2] - min_coords[:2]) / range_coords[:2]
            # Ensure UV is within [0, 1]
            vtx_uv = np.clip(vtx_uv, 0, 1)
        else:
            vtx_uv = None
    
    uv_idx = mesh.faces if hasattr(mesh, 'faces') else None

    texture_data = None

    return vtx_pos, pos_idx, vtx_uv, uv_idx, texture_data


def save_mesh(mesh, texture_data):
    """Save mesh with texture data, creating UV coordinates if needed"""
    # Check if mesh has UV coordinates
    if not hasattr(mesh.visual, 'uv') or mesh.visual.uv is None:
        # Generate simple planar UV mapping if none exists
        vertices = mesh.vertices
        # Normalize vertex positions to [0, 1] range for UV
        min_coords = vertices.min(axis=0)
        max_coords = vertices.max(axis=0)
        range_coords = max_coords - min_coords
        # Avoid division by zero
        range_coords[range_coords == 0] = 1.0
        # Use XY projection for UV (can be enhanced with proper unwrapping)
        uv = (vertices[:, :2] - min_coords[:2]) / range_coords[:2]
        # Ensure UV is within [0, 1]
        uv = np.clip(uv, 0, 1)
    else:
        uv = mesh.visual.uv
    
    material = trimesh.visual.texture.SimpleMaterial(image=texture_data, diffuse=(255, 255, 255))
    texture_visuals = trimesh.visual.TextureVisuals(uv=uv, material=material)
    mesh.visual = texture_visuals
    return mesh
