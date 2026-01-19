import httpx
import os
import logging
from PIL import Image
from io import BytesIO
from urllib.parse import urlparse

logger = logging.getLogger("hy3dgen.api.utils")

async def download_file(uri: str) -> bytes:
    """
    Downloads file bytes from URI.
    """
    parsed = urlparse(uri)
    if parsed.scheme in ('http', 'https'):
        async with httpx.AsyncClient() as client:
            resp = await client.get(uri, timeout=60.0)
            resp.raise_for_status()
            return resp.content
    elif parsed.scheme == 'file' or not parsed.scheme:
        path = os.path.realpath(parsed.path)
        # Security Note: In a web-server context, we would restrict paths.
        # However, for this Desktop App (Sidecar), we need to allow the user to load
        # images from anywhere in their filesystem.
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")
        with open(path, "rb") as f:
            return f.read()
    else:
        raise ValueError(f"Unsupported URI: {uri}")

async def download_image_as_pil(uri: str) -> Image.Image:
    data = await download_file(uri)
    return Image.open(BytesIO(data)).convert("RGB")
