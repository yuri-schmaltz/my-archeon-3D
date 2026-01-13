#!/usr/bin/env python3
"""
Script para diagnóstico da interface Gradio
"""
import sys
import asyncio
import aiohttp

async def check_api_status():
    """Verifica o status da API"""
    url = "http://0.0.0.0:8081"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                print(f"Status da interface: {response.status}")
                if response.status == 200:
                    print("✓ Interface está respondendo")
                else:
                    print("✗ Interface retornou status não-OK")
    except asyncio.TimeoutError:
        print("✗ Timeout ao conectar na interface")
    except Exception as e:
        print(f"✗ Erro ao verificar interface: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("DIAGNÓSTICO DA INTERFACE GRADIO")
    print("=" * 60)
    asyncio.run(check_api_status())
