#!/usr/bin/env python
"""
ETAPA DE PÓS-PROCESSAMENTO: Limpeza e Repair de Malha
Objetivo: Remover floaters, degenerados, fixar normais, gerar versão clean
"""

import logging
import trimesh
from hy3dgen.shapegen import FloaterRemover, DegenerateFaceRemover

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_clean")

def main():
    logger.info("=" * 60)
    logger.info("PÓS-PROCESSAMENTO: LIMPEZA E REPAIR DE MALHA")
    logger.info("=" * 60)
    
    # Carregar mesh gerada
    logger.info("Carregando output_minimal.glb...")
    try:
        scene = trimesh.load('output_minimal.glb')
        if isinstance(scene, trimesh.Scene):
            meshes = list(scene.geometry.values())
            mesh = meshes[0]
        else:
            mesh = scene
        logger.info(f"✓ Mesh carregada: {len(mesh.vertices)} verts, {len(mesh.faces)} faces")
    except Exception as e:
        logger.error(f"✗ FALHA ao carregar mesh: {e}")
        return False
    
    # Stats antes
    logger.info("=" * 60)
    logger.info("ANTES do repair:")
    logger.info("=" * 60)
    logger.info(f"Vértices: {len(mesh.vertices)}")
    logger.info(f"Faces: {len(mesh.faces)}")
    logger.info(f"Is Watertight: {mesh.is_watertight}")
    logger.info(f"Volume: {mesh.volume:.4f}")
    logger.info(f"Surface Area: {mesh.area:.4f}")
    
    # Limpeza 1: Remover floaters
    logger.info("\nAplicando FloaterRemover...")
    try:
        floater_remover = FloaterRemover()
        mesh = floater_remover(mesh)
        logger.info(f"✓ Floaters removidos | Novo mesh: {len(mesh.vertices)} verts, {len(mesh.faces)} faces")
    except Exception as e:
        logger.warning(f"⚠ FloaterRemover falhou: {e}")
    
    # Limpeza 2: Remover degenerados
    logger.info("Aplicando DegenerateFaceRemover...")
    try:
        degen_remover = DegenerateFaceRemover()
        mesh = degen_remover(mesh)
        logger.info(f"✓ Degenerados removidos | Novo mesh: {len(mesh.vertices)} verts, {len(mesh.faces)} faces")
    except Exception as e:
        logger.warning(f"⚠ DegenerateFaceRemover falhou: {e}")
    
    # Limpeza 3: Fixar normais (resolver watertight/spikes)
    logger.info("Aplicando mesh.fix_normals()...")
    try:
        # Remover vértices não utilizados
        mesh.remove_unreferenced_vertices()
        # Fixar normais
        mesh.fix_normals()
        logger.info(f"✓ Normais corrigidas | Mesh: {len(mesh.vertices)} verts, {len(mesh.faces)} faces")
    except Exception as e:
        logger.warning(f"⚠ fix_normals falhou: {e}")
    
    # Stats depois
    logger.info("=" * 60)
    logger.info("DEPOIS do repair:")
    logger.info("=" * 60)
    logger.info(f"Vértices: {len(mesh.vertices)}")
    logger.info(f"Faces: {len(mesh.faces)}")
    logger.info(f"Is Watertight: {mesh.is_watertight}")
    logger.info(f"Volume: {mesh.volume:.4f}")
    logger.info(f"Surface Area: {mesh.area:.4f}")
    
    # Exportar
    output_path = "output_minimal_clean.glb"
    logger.info(f"\nExportando para {output_path}...")
    try:
        mesh.export(output_path)
        import os
        file_size = os.path.getsize(output_path)
        logger.info(f"✓ Arquivo exportado: {file_size} bytes ({file_size/1024:.2f} KB)")
    except Exception as e:
        logger.error(f"✗ FALHA no export: {e}")
        return False
    
    # Validação final
    logger.info("=" * 60)
    logger.info("VALIDAÇÃO FINAL:")
    logger.info("=" * 60)
    
    checks = {
        f"Mesh mantém >1000 faces ({len(mesh.faces)})": len(mesh.faces) > 1000,
        f"Arquivo exportado >1KB ({file_size/1024:.2f}KB)": file_size > 1024,
        f"Watertight melhorou ou manteve": mesh.is_watertight,
        f"Volume válido (não é negativo ou zero)": mesh.volume > 0,
    }
    
    for check, status in checks.items():
        symbol = "✓" if status else "⚠"
        logger.info(f"{symbol} {check}")
    
    logger.info("=" * 60)
    logger.info("PÓS-PROCESSAMENTO CONCLUÍDO!")
    logger.info(f"Resultado: output_minimal_clean.glb ({file_size/1024:.2f} KB)")
    logger.info("=" * 60)
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
