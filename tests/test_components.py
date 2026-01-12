"""
Unit tests for Hunyuan3D-2 core components
"""
import sys
from pathlib import Path
import tempfile
import numpy as np
import trimesh
from PIL import Image

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from hy3dgen.texgen.differentiable_renderer.mesh_utils import save_mesh
from hy3dgen.texgen.differentiable_renderer.mesh_render import MeshRender


class TestMeshUtils:
    """Test mesh utility functions"""
    
    def test_save_mesh_with_texture(self):
        """Test that save_mesh preserves TextureVisuals"""
        # Create simple mesh
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
        
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
        
        # Set UVs
        from trimesh.visual.color import ColorVisuals
        mesh.visual = ColorVisuals(vertex_colors=[255,0,0,255]*4)
        uv = np.array([[0,0], [1,0], [0,1], [1,1]], dtype=np.float32)
        mesh.visual.uv = uv
        
        # Create texture
        texture_image = Image.new('RGB', (64, 64), color=(255, 0, 0))
        
        # Apply save_mesh
        textured_mesh = save_mesh(mesh, texture_image)
        
        # Verify texture is preserved
        assert hasattr(textured_mesh.visual, 'material'), "Should have material"
        assert hasattr(textured_mesh.visual.material, 'image'), "Material should have image"
        assert textured_mesh.visual.material.image is not None, "Image should not be None"
    
    def test_mesh_copy_preserves_texture(self):
        """Test that mesh.copy() preserves TextureVisuals"""
        # Create mesh with texture
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
        
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
        
        # Add texture
        from trimesh.visual.color import ColorVisuals
        mesh.visual = ColorVisuals(vertex_colors=[255,0,0,255]*4)
        uv = np.array([[0,0], [1,0], [0,1], [1,1]], dtype=np.float32)
        
        texture_image = Image.new('RGB', (64, 64), color=(255, 0, 0))
        material = trimesh.visual.texture.SimpleMaterial(image=texture_image)
        texture_visuals = trimesh.visual.TextureVisuals(uv=uv, material=material)
        mesh.visual = texture_visuals
        
        # Copy mesh
        mesh_copy = mesh.copy()
        
        # Verify copy has texture
        assert type(mesh_copy.visual).__name__ == 'TextureVisuals', \
            f"Expected TextureVisuals, got {type(mesh_copy.visual).__name__}"
        assert hasattr(mesh_copy.visual, 'material'), "Copy should have material"
        assert mesh_copy.visual.material.image is not None, "Copy should have texture image"
    
    def test_mesh_glb_export_with_texture(self):
        """Test that GLB export preserves texture"""
        # Create test mesh
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
        
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
        
        # Add texture
        from trimesh.visual.color import ColorVisuals
        mesh.visual = ColorVisuals(vertex_colors=[255,0,0,255]*4)
        uv = np.array([[0,0], [1,0], [0,1], [1,1]], dtype=np.float32)
        
        texture_image = Image.new('RGB', (64, 64), color=(255, 0, 0))
        material = trimesh.visual.texture.SimpleMaterial(image=texture_image)
        texture_visuals = trimesh.visual.TextureVisuals(uv=uv, material=material)
        mesh.visual = texture_visuals
        
        # Export to GLB
        with tempfile.NamedTemporaryFile(suffix='.glb', delete=False) as f:
            temp_path = f.name
        
        try:
            mesh.export(temp_path, include_normals=True)
            
            # Reload and verify
            reloaded = trimesh.load(temp_path)
            
            # Handle Scene object
            if hasattr(reloaded, 'geometry'):
                meshes = list(reloaded.geometry.values())
                reloaded = meshes[0] if meshes else reloaded
            
            # Check for texture
            assert type(reloaded.visual).__name__ == 'TextureVisuals', \
                "GLB should preserve TextureVisuals"
            
            if hasattr(reloaded.visual.material, 'baseColorTexture'):
                # Trimesh GLB uses baseColorTexture after reload
                assert reloaded.visual.material.baseColorTexture is not None, \
                    "GLB should have baseColorTexture"
        
        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestMeshRender:
    """Test MeshRender class"""
    
    def test_mesh_render_copy_preserves_data(self):
        """Test that MeshRender.load_mesh creates a proper copy"""
        # Create test mesh
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
        
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
        uv = np.array([[0,0], [1,0], [0,1], [1,1]], dtype=np.float32)
        
        from trimesh.visual.color import ColorVisuals
        mesh.visual = ColorVisuals(vertex_colors=[255,0,0,255]*4)
        mesh.visual.uv = uv
        
        # Create MeshRender and load mesh
        renderer = MeshRender()
        renderer.load_mesh(mesh)
        
        # Verify that mesh_copy is a separate object
        assert renderer.mesh_copy is not mesh, "mesh_copy should be a different object"
        assert len(renderer.mesh_copy.vertices) == len(mesh.vertices), \
            "mesh_copy should have same vertices"


class TestImports:
    """Test that all critical imports work"""
    
    def test_gradio_import(self):
        """Test Gradio import"""
        import gradio as gr
        assert hasattr(gr, 'Blocks'), "Gradio should have Blocks"
        assert hasattr(gr, 'mount_gradio_app'), "Gradio should have mount_gradio_app"
    
    def test_fastapi_import(self):
        """Test FastAPI import"""
        from fastapi import FastAPI
        from contextlib import asynccontextmanager
        
        # Just verify it can be created with lifespan
        try:
            @asynccontextmanager
            async def lifespan(app):
                yield
            
            app = FastAPI(lifespan=lifespan)
            assert app is not None, "FastAPI should be creatable"
        except TypeError:
            # Older FastAPI versions don't support lifespan parameter
            app = FastAPI()
            assert app is not None, "FastAPI should be creatable"
    
    def test_torch_import(self):
        """Test PyTorch import"""
        import torch
        assert hasattr(torch, 'cuda'), "PyTorch should have CUDA support"
    
    def test_trimesh_import(self):
        """Test Trimesh import"""
        import trimesh
        assert hasattr(trimesh, 'Trimesh'), "Trimesh should have Trimesh class"


class TestAPIServer:
    """Test API server components"""
    
    def test_api_server_imports(self):
        """Test that API server module can be imported"""
        from hy3dgen.apps import api_server
        # Just verify it can be imported without errors
        assert api_server is not None, "API server module should be importable"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
