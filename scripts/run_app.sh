#!/bin/bash
export PYTHONPATH="/home/yurix/Documentos/my-hunyuan-3D/hy3dgen/texgen/custom_rasterizer:$PYTHONPATH"
cd /home/yurix/Documentos/my-hunyuan-3D
source .venv/bin/activate
python my_hunyuan_3d.py "$@"
