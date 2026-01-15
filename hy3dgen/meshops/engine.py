import logging
import asyncio
import os
import uuid
import tempfile
import trimesh
import copy
from typing import Dict, Any, List
from io import BytesIO
from PIL import Image

from hy3dgen.api.schemas import MeshOpsRequest, JobResponse, JobStatus, Artifact, ArtifactType, Operation, MapType
from hy3dgen.api.utils import download_file, download_image_as_pil
from . import ops

logger = logging.getLogger("meshops.engine")

PRESETS = {
    "game_ready_pbr_50k": [
        {"op_id": "p1", "type": "cleanup", "params": {"remove_loose_parts": True, "remove_degenerate_faces": True}},
        {"op_id": "p2", "type": "decimate", "params": {"target_tris": 50000}, "depends_on": ["p1"]},
        {"op_id": "p3", "type": "transform", "params": {"pivot": "bottom_center"}, "depends_on": ["p2"]} 
    ],
    "print_watertight": [
        {"op_id": "p1", "type": "cleanup", "params": {"weld_vertices": {"enabled": True}}},
        {"op_id": "p2", "type": "repair", "params": {"watertight": True}, "depends_on": ["p1"]},
        {"op_id": "p3", "type": "validate", "params": {"checks": ["watertight"]}, "depends_on": ["p2"]}
    ],
    "auto_texture_pbr_2k": [
        {"op_id": "p1", "type": "cleanup", "params": {}},
        {"op_id": "p2", "type": "auto_texture", "params": {"steps": 30}, "depends_on": ["p1"]}
    ]
}

class MeshOpsEngine:
    def __init__(self):
        pass

    def _topological_sort(self, operations: List[dict]) -> List[dict]:
        """
        Sorts operations based on their 'depends_on' field.
        """
        from collections import defaultdict, deque
        
        adj = defaultdict(list)
        in_degree = defaultdict(int)
        op_map = {op["op_id"]: op for op in operations}
        
        for op in operations:
            if op["op_id"] not in in_degree:
                in_degree[op["op_id"]] = 0
                
            for dep in op.get("depends_on", []):
                if dep in op_map:
                    adj[dep].append(op["op_id"])
                    in_degree[op["op_id"]] += 1
        
        queue = deque([oid for oid, deg in in_degree.items() if deg == 0])
        sorted_ops = []
        
        while queue:
            u = queue.popleft()
            sorted_ops.append(op_map[u])
            for v in adj[u]:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)
                    
        if len(sorted_ops) != len(operations):
            logger.warning("Cycle or missing dependency in MeshOps. Using original order.")
            return operations
            
        return sorted_ops

    async def process_async(self, req: MeshOpsRequest) -> List[Artifact]:
        logger.info(f"Starting MeshOps request {req.request_id}")
        
        # 0. Caching (Simple Payload Hashing)
        import hashlib
        import json
        payload_hash = hashlib.sha256(req.model_dump_json().encode()).hexdigest()
        # In a real system, we'd check a redis/disk cache here
        # logger.info(f"Payload hash: {payload_hash}")

        meshes = {}
        extra_artifacts = []
        
        # 1. Load Sources (Parallel)
        async def fetch_source(src):
            try:
                data = await download_file(src.uri)
                suffix = f".{src.format}"
                with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                    tmp.write(data)
                    tmp_path = tmp.name
                
                if src.format == "blend":
                    from . import blender_utils
                    try:
                        glb_path = await blender_utils.convert_blend_to_glb(tmp_path)
                        loaded = trimesh.load(glb_path, file_type="glb")
                        os.unlink(glb_path)
                    except Exception as blend_err:
                        logger.error(f"Failed to convert .blend: {blend_err}")
                        raise blend_err
                else:
                    loaded = trimesh.load(tmp_path, file_type=src.format)
                
                os.unlink(tmp_path)
                
                if isinstance(loaded, trimesh.Scene):
                    loaded = loaded.dump(concatenate=True)
                
                return src.mesh_id, loaded
            except Exception as e:
                logger.error(f"Failed to load {src.mesh_id}: {e}")
                raise e

        # Parallelize mesh loading
        if req.input.source_meshes:
            results = await asyncio.gather(*[fetch_source(s) for s in req.input.source_meshes])
            for mid, mobj in results:
                meshes[mid] = mobj
                logger.debug(f"Loaded {mid}")

        # 2. Build Pipeline
        pipeline = []
        if req.preset:
            p_ops = PRESETS.get(req.preset.preset_id, [])
            pipeline.extend(copy.deepcopy(p_ops))
            
        for op in req.operations:
            pipeline.append(op.model_dump())
            
        # 3. Sort
        sorted_pipeline = self._topological_sort(pipeline)
        
        # 4. Execute
        report_ops = []
        for op_def in sorted_pipeline:
            # ... (rest of loop remains same, but optimize downloading inside auto_texture/packing if needed)
            op_type = op_def["type"]
            params = op_def["params"]
            target_ids = op_def["target"].get("mesh_id", "*")
            
            targets = list(meshes.keys()) if target_ids == "*" else ([target_ids] if target_ids in meshes else [])
            
            for mid in targets:
                mesh = meshes[mid]
                try:
                    res_metric = {}
                    if op_type == "validate":
                        res_metric = ops.validate_mesh(mesh, params)
                    elif op_type == "transform":
                        meshes[mid] = ops.transform_mesh(mesh, params)
                    elif op_type == "cleanup":
                        meshes[mid] = ops.cleanup_mesh(mesh, params)
                    elif op_type == "decimate":
                        target_faces = params.get("target_tris", 10000)
                        if len(mesh.faces) > target_faces:
                            meshes[mid] = mesh.simplify_quadratic_decimation(target_faces)
                    elif op_type == "auto_texture":
                        from . import tex_ops
                        images = []
                        if req.input.aux_inputs and req.input.aux_inputs.reference_images:
                            from hy3dgen.api.utils import download_image_as_pil
                            for img_item in req.input.aux_inputs.reference_images:
                                img = await download_image_as_pil(img_item.uri)
                                images.append(img)
                        
                        # Use the first one or the whole list if the pipeline supports it
                        image_input = images if len(images) > 1 else (images[0] if images else None)
                        
                        from hy3dgen.api.routes import get_manager
                        mgr = get_manager()
                        inf_pipe = await mgr.get_worker("Normal")
                        tex_pipe = getattr(inf_pipe, "pipeline_tex", None)
                        meshes[mid] = await tex_ops.apply_auto_texture(mesh, tex_pipe, image_input, params)
                        
                    elif op_type == "channel_packing":
                        from . import tex_ops
                        if req.input.aux_inputs and req.input.aux_inputs.texture_sources:
                            input_maps = {}
                            for ts in req.input.aux_inputs.texture_sources:
                                for mtype in ts.maps:
                                    img_data = await download_file(ts.uri)
                                    input_maps[mtype] = Image.open(BytesIO(img_data))
                            
                            if input_maps:
                                preset = params.get("preset", "orm")
                                packed_img = tex_ops.pack_channels(input_maps, preset)
                                fname = f"{req.output.artifact_prefix}_packed_{preset}.png"
                                fpath = f"/tmp/{fname}"
                                packed_img.save(fpath)
                                extra_artifacts.append(Artifact(
                                    type=ArtifactType.TEXTURES,
                                    format="png",
                                    uri=fpath,
                                    metadata={"preset": preset}
                                ))
                    elif op_type == "texture_bake":
                        from . import tex_ops
                        # target_ids is the lowpoly
                        # params might have high_mesh_id
                        high_id = params.get("high_mesh_id")
                        if not high_id or high_id not in meshes:
                            # Self-bake or fallback
                            high_mesh = mesh
                        else:
                            high_mesh = meshes[high_id]
                        
                        try:
                            bake_maps = params.get("maps", ["normal", "ao"])
                            resolution = params.get("resolution", 2048)
                            results = await tex_ops.bake_maps_native(high_mesh, mesh, bake_maps, resolution=resolution)
                            
                            for mname, mpath in results.items():
                                fname = f"{req.output.artifact_prefix}_{mid}_baked_{mname}.png"
                                final_path = f"/tmp/{fname}"
                                import shutil
                                shutil.copy(mpath, final_path)
                                extra_artifacts.append(Artifact(
                                    type=ArtifactType.TEXTURES,
                                    format="png",
                                    uri=final_path,
                                    metadata={"mesh_id": mid, "map_type": mname}
                                ))
                        except Exception as bake_err:
                            logger.error(f"Native baking failed: {bake_err}")
                            raise bake_err
                    else:
                        logger.info(f"Skipping unimplemented op: {op_type}")
                        continue
                        
                    report_ops.append({"op_id": op_def["op_id"], "status": "success", "metrics": res_metric})
                except Exception as e:
                    logger.error(f"Op {op_def['op_id']} failed on {mid}: {e}")
                    report_ops.append({"op_id": op_def["op_id"], "status": "failed", "error": str(e)})
                    if op_def.get("on_fail") == "stop":
                        raise e

        # 5. Export
        out_artifacts = []
        out_fmt = (req.constraints.target_formats[0].value if req.constraints.target_formats else "glb")
        
        for mid, mesh in meshes.items():
            fname = f"{req.output.artifact_prefix}_{mid}.{out_fmt}"
            fpath = f"/tmp/{fname}"
            ops.export_mesh(mesh, fpath, out_fmt)
            out_artifacts.append(Artifact(
                type=ArtifactType.MESH,
                format=out_fmt,
                uri=fpath,
                metadata={"mesh_id": mid}
            ))
            
        out_artifacts.extend(extra_artifacts)
        
        out_artifacts.append(Artifact(
            type=ArtifactType.REPORT,
            format="json",
            uri="",
            metadata={"ops_executed": report_ops}
        ))
        
        return out_artifacts
