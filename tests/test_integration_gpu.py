"""
Integration tests for shape and texture generation pipelines.

These tests require:
- CUDA-capable GPU
- Model weights downloaded
- Sufficient VRAM (6GB+ recommended)

Run with: pytest tests/test_integration_gpu.py

Skip if no GPU: pytest tests/ -k "not gpu"
"""

import pytest
import torch
import os
from pathlib import Path


# Skip all tests in this file if no CUDA
pytestmark = pytest.mark.skipif(
    not torch.cuda.is_available(),
    reason="Integration tests require CUDA GPU"
)


@pytest.fixture
def test_image_path():
    """Path to test image (should exist in assets/)"""
    path = Path("assets/demo.png")
    if not path.exists():
        pytest.skip(f"Test image not found: {path}")
    return str(path)


class TestShapeGeneration:
    """Integration tests for shape generation pipeline"""
    
    def test_shape_pipeline_loads(self):
        """Test that shape generation pipeline can be loaded"""
        from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline
        
        # This may download weights on first run
        pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
            'tencent/Hunyuan3D-2'
        )
        
        assert pipeline is not None
        assert hasattr(pipeline, '__call__')
    
    @pytest.mark.slow
    def test_shape_generation_runs(self, test_image_path):
        """Test that shape generation produces valid mesh"""
        from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline
        
        pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
            'tencent/Hunyuan3D-2'
        )
        
        # Run inference (this will take time)
        meshes = pipeline(image=test_image_path)
        
        assert len(meshes) > 0, "Pipeline should return at least one mesh"
        
        mesh = meshes[0]
        assert hasattr(mesh, 'vertices'), "Mesh should have vertices"
        assert hasattr(mesh, 'faces'), "Mesh should have faces"
        assert len(mesh.vertices) > 0, "Mesh should have non-zero vertices"
        assert len(mesh.faces) > 0, "Mesh should have non-zero faces"


class TestTextureGeneration:
    """Integration tests for texture generation pipeline"""
    
    def test_texture_pipeline_loads(self):
        """Test that texture generation pipeline can be loaded"""
        from hy3dgen.texgen import Hunyuan3DPaintPipeline
        
        pipeline = Hunyuan3DPaintPipeline.from_pretrained(
            'tencent/Hunyuan3D-2'
        )
        
        assert pipeline is not None
        assert hasattr(pipeline, '__call__')


class TestEndToEnd:
    """End-to-end tests for complete workflow"""
    
    @pytest.mark.slow
    @pytest.mark.e2e
    def test_image_to_textured_mesh(self, test_image_path):
        """Test complete workflow: image -> shape -> texture"""
        from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline
        from hy3dgen.texgen import Hunyuan3DPaintPipeline
        
        # Step 1: Generate shape
        shape_pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
            'tencent/Hunyuan3D-2'
        )
        mesh = shape_pipeline(image=test_image_path)[0]
        
        # Step 2: Generate texture
        texture_pipeline = Hunyuan3DPaintPipeline.from_pretrained(
            'tencent/Hunyuan3D-2'
        )
        textured_mesh = texture_pipeline(mesh, image=test_image_path)
        
        # Validate result
        assert textured_mesh is not None
        assert len(textured_mesh.vertices) > 0
        
        # Check if texture was applied
        assert hasattr(textured_mesh.visual, 'material'), \
            "Textured mesh should have material"
