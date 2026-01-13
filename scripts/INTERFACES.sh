#!/usr/bin/env bash
# GUIA DE INTERFACES HUNYUAN 3D — Estabilizadas e Funcionais
# ==============================================================

echo "=========================================="
echo "INTERFACES DISPONÍVEIS - HUNYUAN 3D"
echo "=========================================="

source .venv/bin/activate

echo ""
echo "1️⃣  GUI WEB (Gradio + FastAPI Backend)"
echo "   Comando: python my_hunyuan_3d.py"
echo "   Acessar: http://localhost:8081"
echo "   Descrição: Interface completa com upload, preview 3D, download"
echo ""

echo "2️⃣  REST API (FastAPI Swagger)"
echo "   Comando: python my_hunyuan_3d.py --api"
echo "   Acessar: http://localhost:8081/docs"
echo "   Descrição: API RESTful para integração em terceiros"
echo ""

echo "3️⃣  CLI Sênior (Orchestrator)"
echo "   Comando: python orchestrator.py --subject 'mega man' --material 'plastic' --finish 'glossy' --steps 50"
echo "   Descrição: CLI para controle fino de parâmetros, sem GUI"
echo ""

echo "4️⃣  CLI Produção (Pipeline Simples)"
echo "   Comando: python run_production.py imagem.png -o output.glb"
echo "   Descrição: Pipeline robusto com auto-limpeza, ideal para batch/scripting"
echo ""

echo "=========================================="
echo "RESUMO TÉCNICO"
echo "=========================================="
echo "✓ Pipeline estabilizado: enable_t2i=False, low_vram_mode=True"
echo "✓ Patch generator device aplicado em hy3dgen/inference.py"
echo "✓ RTX 3060 12GB: VRAM suficiente para Shape Generation"
echo "✓ Reprodutibilidade confirmada (T6)"
echo "✓ Limpeza automática de malha (FloaterRemover + fix_normals)"
echo ""
