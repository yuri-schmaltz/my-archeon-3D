import subprocess
import os
import logging
import tempfile
import asyncio
from typing import List, Optional, Dict

logger = logging.getLogger("meshops.blender")

BLENDER_EXE = os.environ.get("BLENDER_PATH", "blender")

BLEND_TO_GLB_SCRIPT = """
import bpy
import sys
import os

# Clear existing
bpy.ops.wm.read_factory_settings(use_empty=True)

input_path = sys.argv[-2]
output_path = sys.argv[-1]

# Load .blend
try:
    if input_path.endswith(".blend"):
        bpy.ops.wm.open_mainfile(filepath=input_path)
    else:
        # Try importing if it's not a blend (e.g. obj/stl)
        # But for this script we focus on blend
        pass
        
    # Export to GLB
    bpy.ops.export_scene.gltf(filepath=output_path, export_format='GLB')
    print(f"Successfully converted {input_path} to {output_path}")
except Exception as e:
    print(f"Error during conversion: {e}")
    sys.exit(1)
"""

BAKE_SCRIPT = """
import bpy
import sys
import os

# Args: [high_poly, low_poly, output_dir, bake_types...]
high_path = sys.argv[-4]
low_path = sys.argv[-3]
out_dir = sys.argv[-2]
maps_to_bake = sys.argv[-1].split(",") # e.g. "NORMAL,AO"

bpy.ops.wm.read_factory_settings(use_empty=True)

try:
    # 1. Load High Poly
    bpy.ops.import_scene.gltf(filepath=high_path)
    high_obj = bpy.context.selected_objects[0]
    high_obj.name = "HighPoly"
    
    # 2. Load Low Poly
    bpy.ops.import_scene.gltf(filepath=low_path)
    low_obj = [obj for obj in bpy.context.selected_objects if obj.name != "HighPoly"][0]
    low_obj.name = "LowPoly"

    # 3. Setup Baking
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.device = 'CPU' # Or GPU if available
    
    # Ensure UVs on Low Poly
    bpy.context.view_layer.objects.active = low_obj
    if not low_obj.data.uv_layers:
        bpy.ops.object.editmode_toggle()
        bpy.ops.uv.smart_project()
        bpy.ops.object.editmode_toggle()

    # Create image for each map
    for map_type in maps_to_bake:
        img_name = f"baked_{map_type.lower()}"
        img = bpy.data.images.new(img_name, width=2048, height=2048)
        
        # Setup material/nodes for baking
        mat = bpy.data.materials.new(name=f"Bake_{map_type}")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        node = nodes.new('ShaderNodeTexImage')
        node.image = img
        nodes.active = node
        
        if not low_obj.data.materials:
            low_obj.data.materials.append(mat)
        else:
            low_obj.data.materials[0] = mat

        # BAKE
        bpy.ops.object.select_all(action='DESELECT')
        high_obj.select_set(True)
        low_obj.select_set(True)
        bpy.context.view_layer.objects.active = low_obj
        
        bpy.ops.object.bake(type=map_type, use_selected_to_active=True, margin=16)
        
        # Save
        out_path = os.path.join(out_dir, f"{img_name}.png")
        img.save_render(filepath=out_path)
        print(f"Baked {map_type} to {out_path}")

except Exception as e:
    print(f"Bake error: {e}")
    sys.exit(1)
"""

def is_blender_available():
    try:
        subprocess.run([BLENDER_EXE, "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except FileNotFoundError:
        return False

async def convert_blend_to_glb(blend_path: str) -> str:
    """
    Converts a .blend file to .glb using headless Blender.
    Returns the path to the temporary .glb file.
    """
    if not is_blender_available():
        raise RuntimeError(f"Blender not found at '{BLENDER_EXE}'. Cannot process .blend files.")

    glb_out = blend_path + ".glb"
    
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode='w') as script_file:
        script_file.write(BLEND_TO_GLB_SCRIPT)
        script_path = script_file.name

    try:
        cmd = [
            BLENDER_EXE,
            "--background",
            "--python", script_path,
            "--", # Separator for script args
            blend_path,
            glb_out
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=600.0)
        except asyncio.TimeoutError:
            process.kill()
            logger.error("Blender conversion timed out after 600s")
            raise RuntimeError("Blender conversion timed out")
        
        if process.returncode != 0:
            logger.error(f"Blender conversion failed: {stderr.decode()}")
            raise RuntimeError(f"Blender error: {stderr.decode()}")
            
        return glb_out
    finally:
        if os.path.exists(script_path):
            os.unlink(script_path)

async def bake_mesh_maps(high_poly_path: str, low_poly_path: str, maps: List[str]) -> Dict[str, str]:
    """
    Bakes maps from high poly to low poly using Blender.
    Returns a dict of map_type -> path.
    """
    if not is_blender_available():
        raise RuntimeError("Blender required for high-fidelity baking.")

    tmp_dir = tempfile.mkdtemp()
    
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode='w') as script_file:
        script_file.write(BAKE_SCRIPT)
        script_path = script_file.name

    try:
        # Map internal types to Blender types
        b_types = []
        for m in maps:
            if m.lower() == "normal": b_types.append("NORMAL")
            elif m.lower() == "ao": b_types.append("AO")
            
        cmd = [
            BLENDER_EXE, "--background", "--python", script_path, "--",
            high_poly_path, low_poly_path, tmp_dir, ",".join(b_types)
        ]
        
        process = await asyncio.create_subprocess_exec(*cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=1200.0) # Baking takes longer
        except asyncio.TimeoutError:
            process.kill()
            logger.error("Blender baking timed out after 1200s")
            raise RuntimeError("Blender baking timed out")
            
        if process.returncode != 0:
            logger.error(f"Baking failed: {stderr.decode()}")
            raise RuntimeError(f"Baking error: {stderr.decode()}")
            
        # Collect results
        results = {}
        for f in os.listdir(tmp_dir):
            for m in maps:
                if m.lower() in f.lower():
                    results[m.lower()] = os.path.join(tmp_dir, f)
        return results
    finally:
        if os.path.exists(script_path): os.unlink(script_path)
