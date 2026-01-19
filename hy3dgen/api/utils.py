import httpx
import os
import logging
from PIL import Image
from io import BytesIO
from urllib.parse import urlparse

logger = logging.getLogger("hy3dgen.api.utils")

# [SECURITY] Allowed zones for local file access
# Users can load files from their home directory and temp
_ALLOWED_FILE_PREFIXES = None

def _get_allowed_prefixes():
    """Lazily compute allowed prefixes (cwd, home, temp)."""
    global _ALLOWED_FILE_PREFIXES
    if _ALLOWED_FILE_PREFIXES is None:
        _ALLOWED_FILE_PREFIXES = [
            os.path.realpath(os.getcwd()),
            os.path.realpath(os.path.expanduser("~")),
            os.path.realpath("/tmp"),
        ]
        # Windows temp directory
        if os.name == 'nt':
            temp_dir = os.environ.get('TEMP', os.environ.get('TMP', ''))
            if temp_dir:
                _ALLOWED_FILE_PREFIXES.append(os.path.realpath(temp_dir))
    return _ALLOWED_FILE_PREFIXES

def _validate_path_security(path: str) -> None:
    """
    Validate that resolved path is within allowed zones.
    Raises PermissionError if path is outside allowed zones.
    """
    resolved = os.path.realpath(path)
    for prefix in _get_allowed_prefixes():
        # Check if resolved path starts with prefix (with trailing separator to avoid partial matches)
        if resolved == prefix or resolved.startswith(prefix + os.sep):
            return
    raise PermissionError(f"Access denied: path is outside allowed zones")

async def download_file(uri: str) -> bytes:
    """
    Downloads file bytes from URI.
    Supports http/https and local file:// URIs.
    """
    parsed = urlparse(uri)
    if parsed.scheme in ('http', 'https'):
        async with httpx.AsyncClient() as client:
            resp = await client.get(uri, timeout=60.0)
            resp.raise_for_status()
            return resp.content
    elif parsed.scheme == 'file' or not parsed.scheme:
        path = os.path.realpath(parsed.path if parsed.scheme == 'file' else uri)
        # [SECURITY] Validate path is within allowed zones
        _validate_path_security(path)
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")
        with open(path, "rb") as f:
            return f.read()
    else:
        raise ValueError(f"Unsupported URI scheme: {parsed.scheme}")

async def download_image_as_pil(uri: str) -> Image.Image:
    data = await download_file(uri)
    return Image.open(BytesIO(data)).convert("RGB")

