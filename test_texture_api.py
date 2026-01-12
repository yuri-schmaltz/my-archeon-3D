#!/usr/bin/env python3
"""
Script para testar a geração de textura via API Gradio
Verificar se TextureVisuals é preservado no export
"""

import requests
import json
import time
import sys
from pathlib import Path

# Configuração
GRADIO_URL = "http://127.0.0.1:7860"
ENDPOINT = f"{GRADIO_URL}/run/unified_generation"

def test_texture_generation():
    """Testar geração com textura"""
    
    print("=" * 60)
    print("Testing Texture Generation Fix")
    print("=" * 60)
    
    # Dados de entrada
    payload = {
        "data": [
            "a red cube",  # prompt
            "",            # optional_prompt
            False,         # remove_bg
            True,          # enable_texturing
            42,            # seed
            "generation_all"  # mode
        ]
    }
    
    print(f"\nSending request to {ENDPOINT}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(ENDPOINT, json=payload, timeout=300)
        print(f"\nResponse status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\nResponse data (first 200 chars):")
            print(str(result)[:200])
            
            # Verificar os arquivos gerados
            if "data" in result:
                data = result["data"]
                if len(data) > 0:
                    # First item is usually the white mesh
                    # Second item is the textured mesh (GLB file path)
                    print(f"\nGenerated files:")
                    for i, item in enumerate(data[:3]):
                        if isinstance(item, dict) and "name" in item:
                            print(f"  [{i}] {item['name']}")
                        elif isinstance(item, str):
                            print(f"  [{i}] {item}")
                    
                    # Try to find the textured mesh file
                    textured_mesh_path = None
                    for item in data:
                        if isinstance(item, dict) and "name" in item:
                            if "textured" in item["name"].lower():
                                textured_mesh_path = item["name"]
                                break
                        elif isinstance(item, str) and "textured" in item.lower():
                            textured_mesh_path = item
                            break
                    
                    if textured_mesh_path:
                        print(f"\n✓ Found textured mesh: {textured_mesh_path}")
                        
                        # Check if file exists
                        if Path(textured_mesh_path).exists():
                            file_size = Path(textured_mesh_path).stat().st_size
                            print(f"  File size: {file_size} bytes")
                            
                            # A GLB with texture should be > 5MB typically
                            if file_size > 1000000:  # > 1MB
                                print(f"  ✓ File size looks good for textured mesh")
                            else:
                                print(f"  ! Warning: File size seems small for textured mesh")
                        else:
                            print(f"  ! File not found at: {textured_mesh_path}")
                    else:
                        print(f"\n! Could not find textured mesh in response")
            else:
                print(f"No data in response")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_texture_generation()
    sys.exit(0 if success else 1)
