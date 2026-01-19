import sys
import os
import warnings
import logging

# Suppress Warnings
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
warnings.filterwarnings("ignore")
logging.getLogger("uvicorn.access").setLevel(logging.ERROR)
logging.getLogger("uvicorn.error").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("diffusers").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("torch").setLevel(logging.ERROR)
logging.getLogger("numba").setLevel(logging.ERROR)

def main():
    # Setup global logging
    from hy3dgen.utils.system import setup_logging, cleanup_old_cache
    logger = setup_logging("archeon_launcher")
    
    # [DATA GOVERNANCE] Cleanup old files
    cleanup_old_cache(max_age_days=7)

    logger.info("Starting Archeon 3D in API-Only Mode (Gradio UI removed)")
    
    # Inject defaults if not present
    # This allows users to override them with command line args
    defaults = [
        "--host", "127.0.0.1",
        "--port", "8081",
        "--model_path", "tencent/Hunyuan3D-2",
        "--tex_model_path", "tencent/Hunyuan3D-2",
    ]
    
    # Only insert defaults if they aren't provided
    # A simple check: if the key isn't in argv, add the key and value
    # But argparse handles defaults well. api_server.py has defaults.
    # However, to be safe and explicit about the "Launcher" behavior:
    
    # We will just delegate to api_main. 
    # It parses sys.argv.
    
    from hy3dgen.apps.api_server import main as api_main
    try:
        api_main()
    except KeyboardInterrupt:
        logger.info("Archeon 3D stopped by user.")
    except Exception as e:
        logger.critical(f"Archeon 3D crashed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
