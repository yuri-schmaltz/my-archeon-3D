import httpx
import os
from PIL import Image
from io import BytesIO
from urllib.parse import urlparse

async def download_image_as_pil(uri: str) -> Image.Image:
    """
    Downloads an image from a URI (http/https/file) and returns a PIL Image.
    """
    parsed = urlparse(uri)
    
    if parsed.scheme in ('http', 'https'):
        async with httpx.AsyncClient() as client:
            resp = await client.get(uri, timeout=30.0)
            resp.raise_for_status()
            data = resp.content
    elif parsed.scheme == 'file' or not parsed.scheme:
        # Handle file:// or raw paths
        path = parsed.path
        if not os.path.exists(path):
            raise FileNotFoundError(f"Image not found at path: {path}")
        with open(path, "rb") as f:
            data = f.read()
    else:
        raise ValueError(f"Unsupported URI scheme: {parsed.scheme}")
    
    return Image.open(BytesIO(data)).convert("RGB")
