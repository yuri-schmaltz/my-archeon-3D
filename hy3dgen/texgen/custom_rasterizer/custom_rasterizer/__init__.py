# Package init: load compiled extension and helpers
import os
import sys
import importlib

_pkg_dir = os.path.dirname(__file__)
_parent_dir = os.path.dirname(_pkg_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

# Load compiled extension module (custom_rasterizer_kernel*.so)
custom_rasterizer_kernel = importlib.import_module("custom_rasterizer_kernel")

from .io_glb import *
from .io_obj import *
from .render import *
