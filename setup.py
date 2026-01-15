import os
from pathlib import Path
from setuptools import setup, find_packages

def read_requirements(path):
    with open(path, "r", encoding="utf-8") as f:
        return [
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#")
        ]

here = Path(__file__).parent.resolve()
long_description = (here / "README.md").read_text(encoding="utf-8")

# Categorize requirements
all_reqs = read_requirements(here / "requirements.txt")

# Core inference requirements (subset for basic usage)
core_reqs = [
    "numpy>=2.2.0,<2.3.0",
    "torch>=2.9.0",
    "torchvision>=0.24.0",
    "diffusers>=0.36.0",
    "transformers>=4.57.0",
    "einops>=0.8.0",
    "opencv-python>=4.12.0",
    "tqdm>=4.67.0",
    "omegaconf>=2.3.0",
    "ninja>=1.13.0",
    "pybind11>=3.0.0",
    "trimesh>=4.11.0",
    "pillow>=12.0.0",
]

# Map categories from requirements.txt to extras
dev_reqs = ["pytest", "httpx", "ruff", "coverage"]
docs_reqs = ["sphinx", "sphinx-rtd-theme", "furo", "myst-parser"]

setup(
    packages=find_packages(),
    include_package_data=True,
)

