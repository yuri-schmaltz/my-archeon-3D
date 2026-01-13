import sys
import argparse

def main():
    # Quick check for API mode before importing heavy libraries
    is_api = "--api" in sys.argv
    
    if is_api:
        sys.argv.remove("--api")
        # Defaults for API Server
        defaults = [
            "--host", "0.0.0.0",
            "--port", "8081", # Default to 8081 for API to avoid conflict if both run
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
        defaults = [
            "--host", "0.0.0.0",
            "--port", "8081",
            "--model_path", "tencent/Hunyuan3D-2",
            "--subfolder", "hunyuan3d-dit-v2-0",
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
