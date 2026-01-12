#!/usr/bin/env python3
"""Test if mesh.copy() fix in mesh_render.py preserves texture"""

import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add workspace to path
sys.path.insert(0, str(Path(__file__).parent))

import trimesh
import numpy as np
from PIL import Image

def test_mesh_copy_preserves_texture():
    """Test that mesh.copy() preserves TextureVisuals"""
    
    # Create a simple test mesh
    vertices = np.array([
        [0, 0, 0],
        [1, 0, 0],
        [0, 1, 0],
        [1, 1, 0]
    ])
    
    faces = np.array([
        [0, 1, 2],
        [1, 3, 2]
    ])
    
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
    
    # Add UV coordinates and texture
    uv = np.array([
        [0, 0],
        [1, 0],
        [0, 1],
        [1, 1]
    ])
    
    texture_image = Image.new('RGB', (64, 64), color='red')
    material = trimesh.visual.texture.SimpleMaterial(image=texture_image)
    mesh.visual = trimesh.visual.TextureVisuals(uv=uv, image=texture_image, material=material)
    
    logger.info(f"Original mesh visual type: {type(mesh.visual)}")
    logger.info(f"Original mesh has image: {mesh.visual.image is not None}")
    
    # Test mesh.copy()
    mesh_copy = mesh.copy()
    
    logger.info(f"Copied mesh visual type: {type(mesh_copy.visual)}")
    logger.info(f"Copied mesh has image: {mesh_copy.visual.image is not None}")
    
    # Verify they are different objects
    assert mesh is not mesh_copy, "Mesh copy should be a different object"
    
    # Verify texture is preserved
    assert isinstance(mesh_copy.visual, trimesh.visual.TextureVisuals), \
        f"Expected TextureVisuals, got {type(mesh_copy.visual)}"
    assert mesh_copy.visual.image is not None, "Copied mesh should have texture image"
    
    logger.info("✓ mesh.copy() preserves TextureVisuals correctly!")
    return True

if __name__ == "__main__":
    try:
        test_mesh_copy_preserves_texture()
        logger.info("All tests passed!")
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        sys.exit(1)
