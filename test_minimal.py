#!/usr/bin/env python
"""
PASSO 1: Teste Mínimo para Validar Ambiente (S0)
Objetivo: Desabilitar T2I, usar imagem direta, confirmar pipeline sem OOM/AttributeError
"""

import torch
import logging
from hy3dgen.inference import InferencePipeline
from PIL import Image

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_minimal")

def main():
    logger.info("=" * 60)
    logger.info("PASSO 1: TESTE MÍNIMO - VALIDAÇÃO DE AMBIENTE")
    logger.info("=" * 60)
    
    # Configuração mínima - SEM T2I
    logger.info("Inicializando pipeline (enable_t2i=False, enable_tex=False)...")
    
    try:
        pipeline = InferencePipeline(
            model_path="tencent/Hunyuan3D-2",
            tex_model_path="tencent/Hunyuan3D-2",
            subfolder="hunyuan3d-dit-v2-0",
            device="cuda",
            enable_t2i=False,  # <-- DESABILITADO para economizar VRAM
            enable_tex=False,
            low_vram_mode=True
        )
        logger.info("✓ Pipeline carregado com sucesso!")
    except Exception as e:
        logger.error(f"✗ FALHA no carregamento do pipeline: {e}", exc_info=True)
        return False
    
    # Carregar imagem de teste
    logger.info("Carregando imagem de teste...")
    try:
        image = Image.open('test_input.png').convert('RGBA')
        logger.info(f"✓ Imagem carregada: {image.size}, modo={image.mode}")
    except Exception as e:
        logger.error(f"✗ FALHA ao carregar imagem: {e}")
        return False
    
    # Parâmetros de geração mínimos
    params = {
        "image": image,
        "num_inference_steps": 10,
        "num_chunks": 1000,
        "seed": 42
    }
    
    logger.info(f"Parâmetros: {params}")
    logger.info("Iniciando geração...")
    
    try:
        result = pipeline.generate("minimal_test", params)
        logger.info("✓ Geração concluída!")
    except Exception as e:
        logger.error(f"✗ FALHA na geração: {e}", exc_info=True)
        return False
    
    # Validar mesh
    mesh_output = result["mesh"]
    
    # Converter Latent2MeshOutput para trimesh
    import trimesh
    if hasattr(mesh_output, 'mesh_v') and hasattr(mesh_output, 'mesh_f'):
        # É um Latent2MeshOutput
        mesh = trimesh.Trimesh(vertices=mesh_output.mesh_v, faces=mesh_output.mesh_f)
        logger.info("✓ Convertido Latent2MeshOutput → trimesh.Trimesh")
    else:
        # Já é um trimesh
        mesh = mesh_output
    
    logger.info(f"Mesh Stats:")
    logger.info(f"  - Vértices: {len(mesh.vertices)}")
    logger.info(f"  - Faces: {len(mesh.faces)}")
    logger.info(f"  - Bounds: {mesh.bounds.tolist()}")
    logger.info(f"  - Is Watertight: {mesh.is_watertight}")
    logger.info(f"  - Volume: {mesh.volume:.4f}")
    logger.info(f"  - Surface Area: {mesh.area:.4f}")
    
    # Exportar
    output_path = "output_minimal.glb"
    logger.info(f"Exportando para {output_path}...")
    try:
        mesh.export(output_path)
        import os
        file_size = os.path.getsize(output_path)
        logger.info(f"✓ Arquivo exportado: {file_size} bytes ({file_size/1024:.2f} KB)")
    except Exception as e:
        logger.error(f"✗ FALHA no export: {e}")
        return False
    
    # Critérios de PASS
    logger.info("=" * 60)
    logger.info("CRITÉRIOS DE VALIDAÇÃO:")
    logger.info("=" * 60)
    
    checks = {
        "Pipeline carregou sem OOM": True,
        "Pipeline carregou sem AttributeError": True,
        "Geração completou sem crash": True,
        f"Mesh tem >1000 faces ({len(mesh.faces)})": len(mesh.faces) > 1000,
        f"Arquivo exportado >10KB ({file_size/1024:.2f}KB)": file_size > 10240,
    }
    
    all_pass = True
    for check, status in checks.items():
        symbol = "✓" if status else "✗"
        logger.info(f"{symbol} {check}")
        if not status:
            all_pass = False
    
    logger.info("=" * 60)
    if all_pass:
        logger.info("RESULTADO: ✓✓✓ PASSO 1 PASSOU ✓✓✓")
        logger.info("Próximo: Passo 2 (corrigir generator device)")
    else:
        logger.info("RESULTADO: ✗✗✗ PASSO 1 FALHOU ✗✗✗")
        logger.info("Próximo: Passo 1.1 (fix CPU offload ou desabilitar)")
    logger.info("=" * 60)
    
    return all_pass

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
