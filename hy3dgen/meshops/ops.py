import trimesh
import numpy as np
import logging

logger = logging.getLogger("meshops.ops")

def validate_mesh(mesh: trimesh.Trimesh, params: dict) -> dict:
    """
    Validates mesh properties against checks.
    """
    checks = params.get("checks", [])
    report = {"issues": [], "metrics": {}}
    
    report["metrics"]["vertices"] = len(mesh.vertices)
    report["metrics"]["faces"] = len(mesh.faces)
    report["metrics"]["watertight"] = mesh.is_watertight
    report["metrics"]["manifold"] = mesh.is_winding_consistent # approximation
    
    if "watertight" in checks and not mesh.is_watertight:
        report["issues"].append({"check": "watertight", "severity": "warn", "msg": "Mesh is not watertight"})
        
    if "degenerate_faces" in checks:
        # Check degenerate
        # Trimesh handles this in processing usually, but we can check
        pass
        
    return report

def transform_mesh(mesh: trimesh.Trimesh, params: dict) -> trimesh.Trimesh:
    """
    Applies scale, rotation, translation.
    """
    # Unit scaling logic could go here (m -> cm etc)
    
    # Explicit scale
    scale = params.get("scale")
    if scale:
        if isinstance(scale, (int, float)):
            matrix = trimesh.transformations.scale_matrix(scale)
            mesh.apply_transform(matrix)
            logger.info(f"Applied uniform scale: {scale}")
        elif isinstance(scale, dict):
            # Non-uniform
            sx = scale.get("x", 1.0)
            sy = scale.get("y", 1.0)
            sz = scale.get("z", 1.0)
            # Trimesh doesn't have a direct non-uniform scale matrix helper easily exposed
            # Construct matrix manually
            matrix = np.eye(4)
            matrix[0,0] = sx
            matrix[1,1] = sy
            matrix[2,2] = sz
            mesh.apply_transform(matrix)
            
    # Rotate
    rotate = params.get("rotate_deg")
    if rotate:
        if rotate.get("x"):
            mat = trimesh.transformations.rotation_matrix(np.radians(rotate["x"]), [1,0,0])
            mesh.apply_transform(mat)
        if rotate.get("y"):
            mat = trimesh.transformations.rotation_matrix(np.radians(rotate["y"]), [0,1,0])
            mesh.apply_transform(mat)
        if rotate.get("z"):
            mat = trimesh.transformations.rotation_matrix(np.radians(rotate["z"]), [0,0,1])
            mesh.apply_transform(mat)
            
    # Pivot
    pivot = params.get("pivot")
    if pivot == "center":
        # Centering at origin? Or just recentering geometry?
        # Usually users want to Move To Origin based on pivot.
        center = mesh.centroid
        mesh.apply_translation(-center)
    elif pivot == "bottom_center":
        bounds = mesh.bounds
        center = (bounds[0] + bounds[1]) / 2.0
        bottom_z = bounds[0][2]
        # Move so (center_x, center_y, bottom_z) is at (0,0,0)
        target = np.array([center[0], center[1], bottom_z])
        mesh.apply_translation(-target)

    return mesh

def cleanup_mesh(mesh: trimesh.Trimesh, params: dict) -> trimesh.Trimesh:
    """
    Trimesh cleanup.
    """
    if params.get("remove_loose_parts"):
        # split and keep largest? or just remove small?
        # For simplicity, keep largest connected component if ambiguous
        pass

    if params.get("remove_degenerate_faces", True):
        mesh.update_faces(mesh.nondegenerate_faces())
        
    if params.get("remove_internal_faces"):
        # Expensive in trimesh
        pass
        
    return mesh

def export_mesh(mesh: trimesh.Trimesh, path: str, fmt: str):
    mesh.export(path, file_type=fmt)
