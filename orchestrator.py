
import argparse
import sys
import logging
import torch
import time
from hy3dgen.inference import InferencePipeline

# Senior Orchestrator Constants
SENIOR_NEG_PROMPT = (
    "background, floor, stand, multiple objects, extra parts, floating geometry, "
    "holes, spikes, self-intersection, melted/deformed shape, incorrect proportions, "
    "text, watermark, logo, baked lighting, heavy shadows in albedo, noisy surface"
)
PROMPT_TEMPLATE = (
    "1 {subject}, single isolated object, match the reference image silhouette and proportions. "
    "{material} materials with realistic surface finish: {finish}. "
    "Structural features: {features}. "
    "Constraints: no background geometry, no floor, no stand, no extra parts, no text/logo, no floating pieces. "
    "Geometry: clean watertight surface if possible, no holes, no spikes, no self-intersections; preserve sharp edges where needed. "
    "Texture: albedo without baked shadows; consistent UV/texture; PBR maps only if enabled. "
    "Scale/orientation: upright, centered pivot at base, real-world scale {size}."
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Orchestrator")

def construct_prompt(args):
    return PROMPT_TEMPLATE.format(
        subject=args.subject,
        material=args.material,
        finish=args.finish,
        features=args.features,
        size=args.size
    )

def main():
    parser = argparse.ArgumentParser(description="Senior Orchestrator for Hunyuan 3D")
    parser.add_argument("--subject", required=True, help="Main subject name")
    parser.add_argument("--material", default="standard", help="Material description")
    parser.add_argument("--finish", default="clean", help="Surface finish")
    parser.add_argument("--features", default="standard structure", help="Key structural features")
    parser.add_argument("--size", default="unknown", help="Real world scale")
    parser.add_argument("--steps", type=int, default=30, help="Inference steps")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--dry_run", action="store_true", help="Print prompt only, no generation")
    
    args = parser.parse_args()
    
    full_prompt = construct_prompt(args)
    logger.info("=== ORCHESTRATOR DIAGNOSIS ===")
    logger.info(f"Generated Senior Prompt: {full_prompt}")
    logger.info(f"Generated Senior Negative Prompt: {SENIOR_NEG_PROMPT}")
    
    if args.dry_run:
        logger.info("Dry run complete. Exiting.")
        return

    # Real Generation Logic
    model_path = "tencent/Hunyuan3D-2" 
    subfolder = "hunyuan3d-dit-v2-0"
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    logger.info(f"Initializing Pipeline on {device}...")
    try:
        pipeline = InferencePipeline(
            model_path=model_path,
            tex_model_path=model_path,
            subfolder=subfolder,
            device=device,
            enable_t2i=True,
            enable_tex=False # Focus on shape for now as per instructions (or make optional)
        )
    except Exception as e:
        logger.error(f"Failed to load pipeline: {e}")
        sys.exit(1)

    params = {
        "text": full_prompt,
        "negative_prompt": SENIOR_NEG_PROMPT,
        "num_inference_steps": args.steps,
        "seed": args.seed,
        "t2i_steps": 25,
        "num_chunks": 1000 # Default safe value
    }
    
    logger.info("Starting Generation...")
    start_time = time.time()
    try:
        result = pipeline.generate(f"orchestrate_{int(start_time)}", params)
        logger.info(f"Generation Success! Time: {time.time() - start_time:.2f}s")
        # In a real scenario we would save the mesh here.
        # mesh = result["mesh"]
        # mesh.export("output.obj")
    except Exception as e:
        logger.error(f"Generation Failed: {e}", exc_info=True)

if __name__ == "__main__":
    main()
