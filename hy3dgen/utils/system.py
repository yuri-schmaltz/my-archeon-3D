import os
import sys
import shutil
import time
import logging
import socket
import platformdirs
from pathlib import Path
from logging.handlers import RotatingFileHandler

APP_NAME = "Archeon3D"
APP_AUTHOR = "Tencent"

def get_user_data_dir() -> Path:
    """Returns the user data directory (e.g., for models, persistent data)."""
    return Path(platformdirs.user_data_dir(APP_NAME, APP_AUTHOR))

def get_user_cache_dir() -> Path:
    """Returns the user cache directory (e.g., for temporary generation outputs)."""
    return Path(platformdirs.user_cache_dir(APP_NAME, APP_AUTHOR))

def get_user_log_dir() -> Path:
    """Returns the user log directory."""
    return Path(platformdirs.user_log_dir(APP_NAME, APP_AUTHOR))

def setup_logging(name: str = None) -> logging.Logger:
    """
    Configures logging to write to both console and a rotating file in the user log directory.
    """
    log_dir = get_user_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "archeon_3d.log"

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Avoid adding duplicate handlers if setup is called multiple times
    if logger.handlers:
        return logger

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formater = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formater)
    logger.addHandler(console_handler)

    # File Handler (Rotating)
    # Max size 5MB, keep 3 backup files
    file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG) # Log more details to file
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    logger.info(f"Logging initialized. Logs written to matching OS standard path: {log_file}")
    
    # [SECURITY] Enforce 700 permissions on log dir
    try:
        os.chmod(log_dir, 0o700)
    except Exception:
        pass # Best effort
    
    # Hook into system exceptions to log crashes
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_exception
    
    return logger

def find_free_port(start_port: int = 8081, max_tries: int = 100) -> int:
    """
    Finds a free port starting from `start_port`.
    """
    for port in range(start_port, start_port + max_tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"Could not find a free port in range {start_port}-{start_port + max_tries}")

    
def cleanup_old_cache(max_age_days: int = 7):

    """
    Removes subdirectories in the user cache directory deeper than max_age_days.
    This prevents the disk from filling up with old generated assets.
    """
    logger = logging.getLogger("archeon_system")
    cache_dir = get_user_cache_dir() / "archeon_cache"
    
    if not cache_dir.exists():
        return

    now = time.time()
    cutoff = now - (max_age_days * 86400)
    
    deleted_count = 0
    reclaimed_bytes = 0
    
    try:
        for item in cache_dir.iterdir():
            if item.is_dir():
                # Check modification time
                mtime = item.stat().st_mtime
                if mtime < cutoff:
                    try:
                        # Calculate size for logging
                        size = sum(f.stat().st_size for f in item.glob('**/*') if f.is_file())
                        reclaimed_bytes += size
                        shutil.rmtree(item)
                        deleted_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to cleanup cache item {item}: {e}")
    except Exception as e:
        logger.error(f"Error during cache cleanup: {e}")

    if deleted_count > 0:
        logger.info(f"Cache Cleanup: Removed {deleted_count} old folders, reclaimed {reclaimed_bytes / 1024 / 1024:.2f} MB")

