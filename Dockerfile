# Use NVIDIA CUDA base image for GPU support
FROM nvidia/cuda:12.1.0-devel-ubuntu22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/opt/venv/bin:$PATH"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3.10-venv \
    python3.10-dev \
    python3-pip \
    git \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python3.10 -m venv /opt/venv

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir pytest httpx pydantic prometheus-client

# Install the package in editable mode (or standard mode)
COPY . /app
WORKDIR /app
RUN pip install -e .

# Install custom CUDA extensions (as noted in README)
# Note: This might require specific GPU architecture flags depending on deployment
# Skipping rigorous compilation for now to keep build fast, unless required
RUN cd hy3dgen/texgen/custom_rasterizer && python3 setup.py install
RUN cd hy3dgen/texgen/differentiable_renderer && python3 setup.py install

# Expose ports for API and Gradio
EXPOSE 8080 8081

# Default command (can be overridden)
CMD ["python3", "api_server.py", "--host", "0.0.0.0", "--port", "8080"]
