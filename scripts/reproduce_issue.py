
import os
import sys
import logging
import time
import torch
from hy3dgen.inference import InferencePipeline

# Configure logging to file
logging.basicConfig(
    filename='debug_log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger('').addHandler(console)

logger = logging.getLogger("reproduce")

def test_generation():
    logger.info("Starting reproduction script...")
    
    model_path = "tencent/Hunyuan3D-2"
    subfolder = "hunyuan3d-dit-v2-0"
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    logger.info(f"Device: {device}")
    logger.info(f"Loading model from {model_path} / {subfolder}")
    
    try:
        pipeline = InferencePipeline(
            model_path=model_path,
            tex_model_path=model_path,
            subfolder=subfolder,
            device=device,
            enable_t2i=True,
            enable_tex=False,
            low_vram_mode=True
        )
        logger.info("Pipeline loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load pipeline: {e}", exc_info=True)
        return

    logger.info("Starting dummy generation...")
    # Dummy params
    params = {
        "text": "a cute robot",
        "num_inference_steps": 10, # small number
        "num_chunks": 1000,
        "seed": 42
    }
    
    try:
        result = pipeline.generate("test_uid", params)
        logger.info("Generation successful!")
    except Exception as e:
        logger.error(f"Generation failed: {e}", exc_info=True)

if __name__ == "__main__":
    test_generation()
