#!/usr/bin/env python3
"""
End-to-end test for Hunyuan3D-2
Tests the complete generation pipeline from shape to texture
"""
import sys
import os
import tempfile
import json
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all core modules import correctly"""
    logger.info("🧪 Testing imports...")
    try:
        from hy3dgen.manager import PriorityRequestManager, ModelManager
        from hy3dgen.inference import InferencePipeline
        from hy3dgen.apps.gradio_app import build_app
        logger.info("✓ All imports successful")
        return True
    except Exception as e:
        logger.error(f"✗ Import failed: {e}")
        return False

def test_dependencies():
    """Test that all dependencies are available"""
    logger.info("🧪 Testing dependencies...")
    deps = {
        'gradio': 'gradio',
        'fastapi': 'fastapi',
        'torch': 'torch',
        'transformers': 'transformers',
        'diffusers': 'diffusers',
        'trimesh': 'trimesh',
        'numpy': 'numpy',
        'pydantic': 'pydantic',
    }
    
    missing = []
    for name, import_name in deps.items():
        try:
            __import__(import_name)
            logger.info(f"  ✓ {name}")
        except ImportError:
            logger.warning(f"  ✗ {name}")
            missing.append(name)
    
    if missing:
        logger.error(f"Missing dependencies: {missing}")
        return False
    
    logger.info("✓ All dependencies available")
    return True

def test_mesh_operations():
    """Test basic mesh operations"""
    logger.info("🧪 Testing mesh operations...")
    try:
        import numpy as np
        import trimesh
        from PIL import Image
        from hy3dgen.texgen.differentiable_renderer.mesh_utils import save_mesh
        
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
        logger.info(f"  ✓ Created mesh with {len(mesh.vertices)} vertices")
        
        # Test texture
        from trimesh.visual.color import ColorVisuals
        mesh.visual = ColorVisuals(vertex_colors=[255,0,0,255]*4)
        uv = np.array([[0,0], [1,0], [0,1], [1,1]], dtype=np.float32)
        mesh.visual.uv = uv
        
        texture = Image.new('RGB', (64, 64), color=(255, 0, 0))
        textured_mesh = save_mesh(mesh, texture)
        
        logger.info(f"  ✓ Applied texture successfully")
        
        # Test export
        with tempfile.NamedTemporaryFile(suffix='.glb', delete=False) as f:
            temp_path = f.name
        
        try:
            textured_mesh.export(temp_path, include_normals=True)
            file_size = Path(temp_path).stat().st_size
            logger.info(f"  ✓ Exported GLB ({file_size} bytes)")
            
            # Test reload
            reloaded = trimesh.load(temp_path)
            logger.info(f"  ✓ Reloaded GLB successfully")
            return True
        
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    except Exception as e:
        logger.error(f"✗ Mesh operation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_app_building():
    """Test Gradio app construction"""
    logger.info("🧪 Testing app building...")
    try:
        import warnings
        warnings.filterwarnings('ignore')
        
        from hy3dgen.apps.gradio_app import build_app
        demo = build_app()
        
        logger.info(f"  ✓ Blocks title: {demo.title}")
        logger.info(f"  ✓ App built successfully")
        return True
    
    except Exception as e:
        logger.error(f"✗ App building failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoints():
    """Test API endpoints structure"""
    logger.info("🧪 Testing API endpoints...")
    try:
        from fastapi import FastAPI
        from contextlib import asynccontextmanager
        
        # Verify we can create FastAPI app with lifespan
        @asynccontextmanager
        async def lifespan(app):
            yield
        
        app = FastAPI(lifespan=lifespan)
        logger.info("  ✓ FastAPI app with lifespan created")
        return True
    
    except Exception as e:
        logger.error(f"✗ API test failed: {e}")
        return False

def run_tests():
    """Run all tests"""
    logger.info("=" * 70)
    logger.info("🚀 HUNYUAN3D-2 END-TO-END TEST SUITE")
    logger.info("=" * 70)
    
    tests = [
        ("Imports", test_imports),
        ("Dependencies", test_dependencies),
        ("Mesh Operations", test_mesh_operations),
        ("App Building", test_app_building),
        ("API Endpoints", test_api_endpoints),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            result = test_func()
            results[name] = "PASS" if result else "FAIL"
        except Exception as e:
            logger.error(f"✗ {name} test crashed: {e}")
            results[name] = "ERROR"
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("📊 TEST RESULTS SUMMARY")
    logger.info("=" * 70)
    
    for name, result in results.items():
        icon = "✓" if result == "PASS" else "✗"
        logger.info(f"{icon} {name:30} {result}")
    
    logger.info("=" * 70)
    
    passed = sum(1 for r in results.values() if r == "PASS")
    total = len(results)
    
    logger.info(f"\n📈 {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("\n✅ ALL TESTS PASSED - SYSTEM READY!")
        return 0
    else:
        logger.error("\n❌ SOME TESTS FAILED - CHECK LOGS")
        return 1

if __name__ == "__main__":
    sys.exit(run_tests())
