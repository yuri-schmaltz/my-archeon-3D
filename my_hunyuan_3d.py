import sys
from hy3dgen.apps.gradio_app import main

if __name__ == "__main__":
    defaults = [
        "--host", "0.0.0.0",
        "--port", "8081",
        "--model_path", "tencent/Hunyuan3D-2",
        "--subfolder", "hunyuan3d-dit-v2-0",
        "--texgen_model_path", "tencent/Hunyuan3D-2",
        "--low_vram_mode",
        "--enable_t23d"
    ]
    # Insert defaults at start of arguments (after script name), allowing user override
    sys.argv[1:1] = defaults
    main()
