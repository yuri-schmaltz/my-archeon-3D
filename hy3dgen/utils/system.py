import os
import sys
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
