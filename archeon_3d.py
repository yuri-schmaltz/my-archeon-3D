import sys
import argparse

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
    # Quick check for API mode before importing heavy libraries
    is_api = "--api" in sys.argv
    
    # Setup global logging
    from hy3dgen.utils.system import setup_logging, find_free_port
    setup_logging("archeon_launcher")

    # Find free port if default 8081 (API) or 7860 (Gradio) is taken
    # We will let the sub-apps handle the port argument if passed, 
    # but we can try to facilitate dynamic allocation here if we want to inject it.
    # However, archeon_3d.py calls the 'main' of submodules which parse args again.
    # The best way is to inject the --port arg if not present or if collision.

    if is_api:
        sys.argv.remove("--api")
        # Defaults for API Server
        defaults = [
            "--host", "127.0.0.1",
            "--port", "8081",
            "--model_path", "tencent/Hunyuan3D-2",
            "--tex_model_path", "tencent/Hunyuan3D-2",
            # API server usually needs explicit enable_tex
        ]
        # Inject defaults only if not present? 
        # For simplicity, we stick to the pattern of appending defaults at the start
        # but users can override them because argparse uses the last value.
        # Wait, argparse uses the *last* value if repeated? Yes usually.
        # But we want to prepend defaults so user args (appended later) take precedence?
        # Actually sys.argv[1:1] inserts at working position.
        
        sys.argv[1:1] = defaults
        
        from hy3dgen.apps.api_server import main as api_main
        print("Starting Archeon 3D API Server...")
        api_main()
    else:
        # Defaults for Gradio App
        # Try to find a free port starting from 7860
        port = 7860
        try:
            port = find_free_port(7860)
        except Exception as e:
            logging.warning(f"Could not find free port: {e}, falling back to 7860")
            
        defaults = [
            "--host", "127.0.0.1",
            "--port", str(port),
            "--model_path", "tencent/Hunyuan3D-2",
            "--subfolder", "hunyuan3d-dit-v2-0-turbo",
            "--texgen_model_path", "tencent/Hunyuan3D-2",
            "--low_vram_mode",
            "--enable_t23d"
        ]
        sys.argv[1:1] = defaults
        
        from hy3dgen.apps.gradio_app import main as gradio_main
        print("Starting Archeon 3D Gradio App...")
        gradio_main()

if __name__ == "__main__":
    main()
