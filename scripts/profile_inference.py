import time
import torch
import argparse
import sys
import os

# Ensure we can import hy3dgen
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hy3dgen.inference import InferencePipeline

def profile_inference(model_path, tex_model_path, device='cuda'):
    print(f"Loading pipeline from {model_path} on {device}...")
    start_load = time.time()
    
    pipeline = InferencePipeline(
        model_path=model_path,
        tex_model_path=tex_model_path,
        subfolder='hunyuan3d-dit-v2-mini', # Defaulting for profile
        device=device,
        enable_t2i=True,
        enable_tex=True
    )
    print(f"Load time: {time.time() - start_load:.2f}s")
    
    # Text to 3D
    prompt = "A simple red apple"
    print(f"Profiling T2I+Gen3D for prompt: '{prompt}'")
    params = {
        'text': prompt,
        'octree_resolution': 128,
        'num_inference_steps': 5, # Low for profiling speed
        'do_texture': True
    }
    
    if device == 'cuda':
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.synchronize()
        
    start_infer = time.time()
    result = pipeline.generate("test_uid", params)
    
    if device == 'cuda':
        torch.cuda.synchronize()
        peak_mem = torch.cuda.max_memory_allocated() / 1024**2
        print(f"Peak VRAM: {peak_mem:.2f} MB")
        
    print(f"Total Inference Time: {time.time() - start_infer:.2f}s")
    print("Done.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_path", type=str, default='tencent/Hunyuan3D-2mini')
    parser.add_argument("--tex_model_path", type=str, default='tencent/Hunyuan3D-2')
    args = parser.parse_args()
    
    try:
        profile_inference(args.model_path, args.tex_model_path)
    except Exception as e:
        print(f"Profiling failed (possibly due to missing models locally): {e}")
        sys.exit(1)
