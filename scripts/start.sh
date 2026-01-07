#!/bin/bash
set -e

# Start API Server in background
echo "Starting API Server on port 8080..."
python3 api_server.py --host 0.0.0.0 --port 8080 &
API_PID=$!

# Start Gradio App in foreground
echo "Starting Gradio App on port 8081..."
# Note: gradio_app.py uses --port for server_port if implemented, or we need to check arguments.
# Looking at gradio_app.py: parser.add_argument("--port", type=int, default=8081)
python3 gradio_app.py --server_name 0.0.0.0 --port 8081 --model_path tencent/Hunyuan3D-2 --subfolder hunyuan3d-dit-v2-0 --texgen_model_path tencent/Hunyuan3D-2 --low_vram_mode

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?
