#!/usr/bin/env python3
"""
Test mesh texture preservation through the pipeline
"""
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

import trimesh
import numpy as np
from PIL import Image
from hy3dgen.texgen.differentiable_renderer.mesh_render import MeshRender
from hy3dgen.texgen.differentiable_renderer.mesh_utils import save_mesh as save_mesh_util

print("Testing texture preservation fix...")
print("=" * 60)

# Create a simple test mesh
vertices = np.array([
    [0, 0, 0],
    [1, 0, 0],
    [0, 1, 0],
    [1, 1, 0]
], dtype=np.float32)

faces = np.array([
    [0, 1, 2],
    [1, 3, 2]
], dtype=np.uint32)

# Create mesh with UVs
mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
uv = np.array([
    [0, 0],
    [1, 0],
    [0, 1],
    [1, 1]
], dtype=np.float32)

# Set initial visual (needed for save_mesh to work)
from trimesh.visual.color import ColorVisuals
mesh.visual = ColorVisuals(vertex_colors=[255,0,0,255]*4)

print(f"1. Original mesh visual type: {type(mesh.visual).__name__}")
print(f"   Has UV: {hasattr(mesh.visual, 'uv')}")

# Create a test texture
texture_image = Image.new('RGB', (64, 64), color=(255, 0, 0))

# Test 1: mesh_utils.save_mesh() preserves texture
print(f"\n2. Testing save_mesh() from mesh_utils...")
print(f"   Input mesh visual: {type(mesh.visual).__name__}")

# First set UV
mesh.visual.uv = uv

textured_mesh = save_mesh_util(mesh, texture_image)
print(f"   Output mesh visual: {type(textured_mesh.visual).__name__}")

if hasattr(textured_mesh.visual, 'material'):
    print(f"   Has material: True")
    if hasattr(textured_mesh.visual.material, 'image'):
        print(f"   Material has image: {textured_mesh.visual.material.image is not None}")
else:
    print(f"   Has material: False")

# Test 2: Ensure mesh.copy() preserves TextureVisuals
print(f"\n3. Testing mesh.copy() preserves TextureVisuals...")
mesh_copy = textured_mesh.copy()
print(f"   Copied mesh visual: {type(mesh_copy.visual).__name__}")

if hasattr(mesh_copy.visual, 'material'):
    print(f"   Copied has material: True")
    if hasattr(mesh_copy.visual.material, 'image'):
        has_image = mesh_copy.visual.material.image is not None
        print(f"   Copied material has image: {has_image}")
        if has_image:
            print(f"   ✓ IMAGE PRESERVED IN COPY!")

# Test 3: Export to GLB
print(f"\n4. Testing GLB export...")
output_path = "/tmp/test_textured_mesh.glb"
try:
    mesh_copy.export(output_path, include_normals=True)
    print(f"   ✓ Exported to {output_path}")
    
    # Reload and check
    reloaded = trimesh.load(output_path)
    
    # Trimesh loads GLB as a Scene, extract the mesh
    if hasattr(reloaded, 'geometry'):
        # It's a Scene
        meshes = list(reloaded.geometry.values())
        if meshes:
            reloaded_mesh = meshes[0]
    else:
        reloaded_mesh = reloaded
    
    print(f"   Reloaded type: {type(reloaded_mesh).__name__}")
    print(f"   Reloaded mesh visual: {type(reloaded_mesh.visual).__name__}")
    
    if hasattr(reloaded_mesh.visual, 'material'):
        print(f"   Reloaded has material: True")
        if hasattr(reloaded_mesh.visual.material, 'image'):
            has_image = reloaded_mesh.visual.material.image is not None
            print(f"   Reloaded material has image: {has_image}")
            if has_image:
                print(f"   ✓ IMAGE PRESERVED IN GLB!")
except Exception as e:
    print(f"   Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Test completed!")
