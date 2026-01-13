#!/usr/bin/env python
"""
PIPELINE INTEGRADO PARA PRODUÇÃO — Hunyuan3D Image→3D
Objetivo: Processar imagem → gerar mesh 3D watertight limpo → exportar GLB
"""

import argparse
import logging
import time
import sys
import os
from pathlib import Path

import torch
from PIL import Image

from hy3dgen.inference import InferencePipeline
from hy3dgen.shapegen import FloaterRemover, DegenerateFaceRemover

# ============================================================================
# Configuração de Logging
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("production")

# ============================================================================
# PIPELINE PRODUÇÃO
# ============================================================================

class HunyuanProductionPipeline:
    """Pipeline robusto de Image→3D com limpeza automática."""
    
    def __init__(self, 
                 model_path: str = "tencent/Hunyuan3D-2",
                 subfolder: str = "hunyuan3d-dit-v2-0",
                 device: str = "cuda",
                 low_vram_mode: bool = True):
        """
        Inicializa pipeline.
        
        Args:
            model_path: Caminho do modelo no HF
            subfolder: Subfolder do modelo
            device: 'cuda' ou 'cpu'
            low_vram_mode: Ativa offload para GPU com <16GB VRAM
        """
        self.device = device
        self.model_path = model_path
        self.subfolder = subfolder
        self.low_vram_mode = low_vram_mode
        
        logger.info("Inicializando InferencePipeline...")
        logger.info(f"  Device: {device}")
        logger.info(f"  Low VRAM Mode: {low_vram_mode}")
        
        try:
            self.pipeline = InferencePipeline(
                model_path=model_path,
                tex_model_path=model_path,
                subfolder=subfolder,
                device=device,
                enable_t2i=False,  # CRÍTICO: desabilitado para caber em 12GB VRAM
                enable_tex=False,  # Textura aumenta significativamente VRAM
                use_flashvdm=True,
                mc_algo='mc',
                low_vram_mode=low_vram_mode
            )
            logger.info("✓ Pipeline carregado com sucesso")
        except Exception as e:
            logger.error(f"✗ FALHA ao inicializar pipeline: {e}", exc_info=True)
            raise
        
        self.floater_remover = FloaterRemover()
        self.degen_remover = DegenerateFaceRemover()
    
    def process_image(self, image_path: str, output_path: str, 
                     num_steps: int = 30, 
                     num_chunks: int = 8000,
                     seed: int = 42,
                     apply_cleanup: bool = True) -> bool:
        """
        Processa imagem → gera mesh → limpa → exporta.
        
        Args:
            image_path: Caminho da imagem de entrada (PNG/JPG)
            output_path: Caminho do GLB de saída
            num_steps: Passos de difusão (30 padrão, >10 para melhor qualidade)
            num_chunks: Chunks volumétricos (8000 padrão)
            seed: Seed para reprodutibilidade
            apply_cleanup: Se True, aplica FloaterRemover + DegenerateFaceRemover + fix_normals
        
        Returns:
            True se sucesso, False se falha
        """
        logger.info("=" * 70)
        logger.info("PROCESSAMENTO INICIADO")
        logger.info("=" * 70)
        
        # 1. Carregar imagem
        logger.info(f"Carregando imagem: {image_path}")
        try:
            image = Image.open(image_path).convert('RGBA')
            logger.info(f"✓ Imagem carregada: {image.size}, modo={image.mode}")
        except Exception as e:
            logger.error(f"✗ FALHA ao carregar imagem: {e}")
            return False
        
        # 2. Gerar 3D
        logger.info("Iniciando geração 3D...")
        t0 = time.time()
        
        params = {
            "image": image,
            "num_inference_steps": num_steps,
            "num_chunks": num_chunks,
            "seed": seed,
            "reduce_face": False,  # Cleanup externo evita conflito de tipos (MeshSet vs trimesh)
        }
        
        try:
            result = self.pipeline.generate(f"prod_{int(t0)}", params)
            t_generation = time.time() - t0
            logger.info(f"✓ Geração concluída em {t_generation:.2f}s")
        except Exception as e:
            logger.error(f"✗ FALHA na geração: {e}", exc_info=True)
            return False
        
        # 3. Extrair mesh
        mesh_output = result["mesh"]
        
        # Converter Latent2MeshOutput → trimesh se necessário
        import trimesh
        if hasattr(mesh_output, 'mesh_v') and hasattr(mesh_output, 'mesh_f'):
            mesh = trimesh.Trimesh(vertices=mesh_output.mesh_v, faces=mesh_output.mesh_f)
            logger.info("✓ Convertido Latent2MeshOutput → trimesh")
        else:
            mesh = mesh_output
        
        logger.info(f"Mesh bruto: {len(mesh.vertices)} verts, {len(mesh.faces)} faces")
        
        # 4. Limpeza (opcional)
        if apply_cleanup:
            logger.info("\nAplicando limpeza de mesh...")
            
            try:
                logger.info("  - FloaterRemover...")
                mesh = self.floater_remover(mesh)
                logger.info(f"    ✓ {len(mesh.vertices)} verts, {len(mesh.faces)} faces")
            except Exception as e:
                logger.warning(f"    ⚠ FloaterRemover falhou: {e}")
            
            try:
                logger.info("  - DegenerateFaceRemover...")
                mesh = self.degen_remover(mesh)
                logger.info(f"    ✓ {len(mesh.vertices)} verts, {len(mesh.faces)} faces")
            except Exception as e:
                logger.warning(f"    ⚠ DegenerateFaceRemover falhou: {e}")
            
            try:
                logger.info("  - fix_normals & remove_unreferenced_vertices...")
                mesh.remove_unreferenced_vertices()
                mesh.fix_normals()
                logger.info(f"    ✓ {len(mesh.vertices)} verts, {len(mesh.faces)} faces")
            except Exception as e:
                logger.warning(f"    ⚠ fix_normals falhou: {e}")
        
        # 5. Validação
        logger.info("\nValidação da mesh:")
        logger.info(f"  - Vértices: {len(mesh.vertices)}")
        logger.info(f"  - Faces: {len(mesh.faces)}")
        logger.info(f"  - Is Watertight: {mesh.is_watertight}")
        logger.info(f"  - Volume: {mesh.volume:.6f}")
        logger.info(f"  - Surface Area: {mesh.area:.6f}")
        logger.info(f"  - Bounds: {mesh.bounds.tolist()}")
        
        # 6. Exportar
        logger.info(f"\nExportando para {output_path}...")
        try:
            mesh.export(output_path)
            file_size = os.path.getsize(output_path)
            logger.info(f"✓ Arquivo exportado: {file_size/1024/1024:.2f} MB ({file_size} bytes)")
        except Exception as e:
            logger.error(f"✗ FALHA ao exportar: {e}")
            return False
        
        # 7. Resumo final
        logger.info("=" * 70)
        logger.info("RESUMO FINAL")
        logger.info("=" * 70)
        logger.info(f"Input: {image_path}")
        logger.info(f"Output: {output_path}")
        logger.info(f"Mesh: {len(mesh.vertices)} verts, {len(mesh.faces)} faces")
        logger.info(f"Watertight: {'✓ SIM' if mesh.is_watertight else '✗ NÃO'}")
        logger.info(f"Tamanho: {file_size/1024/1024:.2f} MB")
        logger.info(f"Tempo total: {time.time() - t0:.2f}s")
        logger.info("=" * 70)
        
        return True


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Hunyuan 3D Production Pipeline: Image → 3D Mesh (GLB)"
    )
    parser.add_argument(
        "image",
        help="Caminho da imagem de entrada (PNG, JPG, etc.)"
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Caminho do arquivo GLB de saída (padrão: <image_base>_output.glb)"
    )
    parser.add_argument(
        "-s", "--steps",
        type=int,
        default=30,
        help="Passos de difusão (padrão: 30, range: 10-50)"
    )
    parser.add_argument(
        "-c", "--chunks",
        type=int,
        default=8000,
        help="Chunks volumétricos (padrão: 8000)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Seed para reprodutibilidade (padrão: 42)"
    )
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Desabilita limpeza automática (FloaterRemover, etc.)"
    )
    parser.add_argument(
        "--device",
        default="cuda",
        choices=["cuda", "cpu"],
        help="Device (padrão: cuda)"
    )
    parser.add_argument(
        "--no-low-vram",
        action="store_true",
        help="Desabilita low_vram_mode (não recomendado para RTX 3060)"
    )
    
    args = parser.parse_args()
    
    # Validar input
    if not os.path.exists(args.image):
        logger.error(f"✗ Arquivo não encontrado: {args.image}")
        return 1
    
    # Output default
    if args.output is None:
        base = Path(args.image).stem
        args.output = f"{base}_output.glb"
    
    # Validar steps
    if args.steps < 10 or args.steps > 50:
        logger.warning(f"⚠ Steps={args.steps} fora do range recomendado [10-50]")
    
    # Criar pipeline
    try:
        pipeline = HunyuanProductionPipeline(
            device=args.device,
            low_vram_mode=not args.no_low_vram
        )
    except Exception as e:
        logger.error(f"✗ Falha ao inicializar pipeline: {e}")
        return 1
    
    # Processar
    success = pipeline.process_image(
        image_path=args.image,
        output_path=args.output,
        num_steps=args.steps,
        num_chunks=args.chunks,
        seed=args.seed,
        apply_cleanup=not args.no_cleanup
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
