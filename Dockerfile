# Stage 1: Builder
# Use NVIDIA CUDA devel image for building extensions
FROM nvidia/cuda:12.1.0-devel-ubuntu22.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/opt/venv/bin:$PATH"
# Fix to avoid "list index out of range" when building without GPU visibility
ENV TORCH_CUDA_ARCH_LIST="7.0 7.5 8.0 8.6+PTX"

# Install system dependencies for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3.10-venv \
    python3.10-dev \
    python3-pip \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python3.10 -m venv /opt/venv

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . /app
WORKDIR /app

# Install custom CUDA extensions
# These require nvcc available in devel image
RUN cd hy3dgen/texgen/custom_rasterizer && python3 setup.py install
RUN cd hy3dgen/texgen/differentiable_renderer && python3 setup.py install

# Install the package itself
RUN pip install .

# Stage 2: Runtime
# Use NVIDIA CUDA runtime image (much smaller)
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/opt/venv/bin:$PATH"

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3.10-venv \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code (needed for runtime assets/scripts)
COPY --from=builder /app /app
WORKDIR /app

# Expose ports for API and Gradio
EXPOSE 8080 8081

# Default command
# CMD ["python3", "api_server.py", "--host", "0.0.0.0", "--port", "8080"]
CMD ["bash", "scripts/start.sh"]
