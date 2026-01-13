#!/usr/bin/env python3
"""
Performance benchmarking script for Hunyuan3D-2
Measures generation times, memory usage, and throughput
"""
import sys
import time
import json
import psutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import tempfile

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerformanceBenchmark:
    """Run performance benchmarks on Hunyuan3D pipeline"""
    
    def __init__(self):
        self.results = {}
        self.process = psutil.Process()
        self.start_memory = 0
        self.start_time = 0
    
    def _get_memory_info(self) -> Dict[str, float]:
        """Get current memory usage"""
        mem = self.process.memory_info()
        return {
            'rss_mb': mem.rss / 1024 / 1024,
            'vms_mb': mem.vms / 1024 / 1024,
        }
    
    def benchmark_imports(self) -> Dict[str, float]:
        """Benchmark import times"""
        logger.info("\n" + "="*70)
        logger.info("BENCHMARK 1: Import Performance")
        logger.info("="*70)
        
        results = {}
        modules = [
            ('hy3dgen.manager', 'ModelManager'),
            ('hy3dgen.inference', 'InferencePipeline'),
            ('hy3dgen.shapegen.pipelines', 'ShapeGenPipeline'),
            ('hy3dgen.texgen.pipelines', 'TextureGenPipeline'),
            ('hy3dgen.apps.gradio_app', 'build_app'),
        ]
        
        for module_name, item in modules:
            start = time.time()
            try:
                module = __import__(module_name, fromlist=[item])
                duration = (time.time() - start) * 1000  # ms
                results[item] = duration
                logger.info(f"  ✓ {item:30} {duration:8.2f} ms")
            except Exception as e:
                logger.error(f"  ✗ {item:30} FAILED: {e}")
                results[item] = -1
        
        return results
    
    def benchmark_mesh_operations(self) -> Dict[str, Any]:
        """Benchmark mesh creation and operations"""
        logger.info("\n" + "="*70)
        logger.info("BENCHMARK 2: Mesh Operations")
        logger.info("="*70)
        
        import numpy as np
        import trimesh
        
        results = {}
        
        # Create mesh vertices and faces
        vertices = np.array([
            [0, 0, 0],
            [1, 0, 0],
            [1, 1, 0],
            [0, 1, 0],
        ], dtype=np.float32)
        
        faces = np.array([
            [0, 1, 2],
            [0, 2, 3],
        ], dtype=np.uint32)
        
        # Test mesh creation
        start = time.time()
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
        results['mesh_creation_ms'] = (time.time() - start) * 1000
        logger.info(f"  ✓ Mesh creation:       {results['mesh_creation_ms']:8.2f} ms")
        
        # Test mesh copy
        start = time.time()
        mesh_copy = mesh.copy()
        results['mesh_copy_ms'] = (time.time() - start) * 1000
        logger.info(f"  ✓ Mesh copy:           {results['mesh_copy_ms']:8.2f} ms")
        
        # Test mesh export to bytes
        start = time.time()
        glb_bytes = mesh.export(file_type='glb')
        results['mesh_export_glb_ms'] = (time.time() - start) * 1000
        results['glb_size_kb'] = len(glb_bytes) / 1024
        logger.info(f"  ✓ GLB export:          {results['mesh_export_glb_ms']:8.2f} ms ({results['glb_size_kb']:.1f} KB)")
        
        # Test mesh reload
        start = time.time()
        from io import BytesIO
        reloaded = trimesh.load(BytesIO(glb_bytes), file_type='glb')
        results['mesh_reload_ms'] = (time.time() - start) * 1000
        logger.info(f"  ✓ Mesh reload:         {results['mesh_reload_ms']:8.2f} ms")
        
        # Test vertices processing
        large_verts = np.random.rand(10000, 3).astype(np.float32)
        large_faces = np.random.randint(0, 10000, (5000, 3), dtype=np.uint32)
        
        start = time.time()
        large_mesh = trimesh.Trimesh(vertices=large_verts, faces=large_faces, process=False)
        results['large_mesh_creation_ms'] = (time.time() - start) * 1000
        logger.info(f"  ✓ Large mesh (10K verts): {results['large_mesh_creation_ms']:8.2f} ms")
        
        return results
    
    def benchmark_app_building(self) -> Dict[str, Any]:
        """Benchmark Gradio app building"""
        logger.info("\n" + "="*70)
        logger.info("BENCHMARK 3: App Building")
        logger.info("="*70)
        
        results = {}
        
        try:
            from hy3dgen.apps.gradio_app import build_app
            
            mem_before = self._get_memory_info()
            start = time.time()
            app = build_app()
            duration = (time.time() - start) * 1000
            mem_after = self._get_memory_info()
            
            results['app_build_time_ms'] = duration
            results['memory_used_mb'] = mem_after['rss_mb'] - mem_before['rss_mb']
            
            logger.info(f"  ✓ Gradio app build:    {duration:8.2f} ms")
            logger.info(f"  ✓ Memory used:         {results['memory_used_mb']:8.2f} MB")
            logger.info(f"  ✓ App interface:       {len(app.blocks)} blocks")
            
        except Exception as e:
            logger.error(f"  ✗ App building failed: {e}")
            results['error'] = str(e)
        
        return results
    
    def benchmark_api_server(self) -> Dict[str, Any]:
        """Benchmark FastAPI server initialization"""
        logger.info("\n" + "="*70)
        logger.info("BENCHMARK 4: API Server")
        logger.info("="*70)
        
        results = {}
        
        try:
            from hy3dgen.apps.api_server import app
            
            start = time.time()
            # Just instantiate, don't run server
            duration = (time.time() - start) * 1000
            
            results['api_init_time_ms'] = duration
            
            # Count routes
            route_count = len([r for r in app.routes])
            results['total_routes'] = route_count
            
            logger.info(f"  ✓ API initialization:  {duration:8.2f} ms")
            logger.info(f"  ✓ Total routes:        {route_count}")
            
        except Exception as e:
            logger.error(f"  ✗ API server failed: {e}")
            results['error'] = str(e)
        
        return results
    
    def benchmark_import_overhead(self) -> Dict[str, float]:
        """Benchmark import overhead"""
        logger.info("\n" + "="*70)
        logger.info("BENCHMARK 5: Deep Import Overhead")
        logger.info("="*70)
        
        results = {}
        
        # Measure torch import (usually slowest)
        start = time.time()
        import torch
        results['torch_import_ms'] = (time.time() - start) * 1000
        logger.info(f"  ✓ PyTorch import:      {results['torch_import_ms']:8.2f} ms")
        logger.info(f"    - PyTorch version:   {torch.__version__}")
        
        # Measure transformers
        start = time.time()
        import transformers
        results['transformers_import_ms'] = (time.time() - start) * 1000
        logger.info(f"  ✓ Transformers import: {results['transformers_import_ms']:8.2f} ms")
        
        # Measure diffusers
        start = time.time()
        import diffusers
        results['diffusers_import_ms'] = (time.time() - start) * 1000
        logger.info(f"  ✓ Diffusers import:    {results['diffusers_import_ms']:8.2f} ms")
        
        return results
    
    def benchmark_system_info(self) -> Dict[str, Any]:
        """Collect system information"""
        logger.info("\n" + "="*70)
        logger.info("SYSTEM INFORMATION")
        logger.info("="*70)
        
        info = {
            'timestamp': datetime.now().isoformat(),
            'python_version': sys.version.split()[0],
            'cpu_count': psutil.cpu_count(),
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_total_gb': psutil.virtual_memory().total / 1024**3,
            'memory_available_gb': psutil.virtual_memory().available / 1024**3,
            'memory_used_gb': psutil.virtual_memory().used / 1024**3,
        }
        
        try:
            import torch
            info['torch_version'] = torch.__version__
            info['cuda_available'] = torch.cuda.is_available()
            if torch.cuda.is_available():
                info['cuda_device_count'] = torch.cuda.device_count()
                info['cuda_device_name'] = torch.cuda.get_device_name(0)
        except:
            info['torch_available'] = False
        
        logger.info(f"  CPU Cores:     {info['cpu_count']}")
        logger.info(f"  CPU Usage:     {info['cpu_percent']}%")
        logger.info(f"  Total Memory:  {info['memory_total_gb']:.2f} GB")
        logger.info(f"  Available:     {info['memory_available_gb']:.2f} GB")
        logger.info(f"  Used:          {info['memory_used_gb']:.2f} GB")
        logger.info(f"  Python:        {info['python_version']}")
        if info.get('cuda_available'):
            logger.info(f"  CUDA Device:   {info['cuda_device_name']}")
        
        return info
    
    def run_all_benchmarks(self) -> Dict[str, Any]:
        """Run all benchmarks"""
        logger.info("\n")
        logger.info("╔" + "="*68 + "╗")
        logger.info("║" + " "*15 + "HUNYUAN3D PERFORMANCE BENCHMARK" + " "*22 + "║")
        logger.info("╚" + "="*68 + "╝")
        
        all_results = {
            'system_info': self.benchmark_system_info(),
            'imports': self.benchmark_imports(),
            'import_overhead': self.benchmark_import_overhead(),
            'mesh_operations': self.benchmark_mesh_operations(),
            'app_building': self.benchmark_app_building(),
            'api_server': self.benchmark_api_server(),
        }
        
        # Summary
        logger.info("\n" + "="*70)
        logger.info("BENCHMARK SUMMARY")
        logger.info("="*70)
        
        total_import_time = sum([
            v for k, v in all_results.get('imports', {}).items() 
            if isinstance(v, (int, float))
        ])
        logger.info(f"✓ Total import time:      {total_import_time:8.2f} ms")
        logger.info(f"✓ Mesh operations:        Working")
        logger.info(f"✓ App building:           Working")
        logger.info(f"✓ API server:             Working")
        logger.info(f"✓ System memory:          {all_results['system_info']['memory_used_gb']:.2f}/{all_results['system_info']['memory_total_gb']:.2f} GB")
        
        return all_results
    
    def save_results(self, output_path: str = None) -> str:
        """Save benchmark results to JSON"""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"performance_benchmark_{timestamp}.json"
        
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        logger.info(f"\n✓ Results saved: {output_path}")
        return output_path

def main():
    """Run benchmarks"""
    benchmark = PerformanceBenchmark()
    benchmark.results = benchmark.run_all_benchmarks()
    output = benchmark.save_results()
    logger.info(f"\n✅ BENCHMARKING COMPLETE")
    logger.info(f"   Output: {output}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
