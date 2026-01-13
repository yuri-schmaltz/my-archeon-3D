# Multi-stage Dockerfile for Hunyuan3D-2

# Stage 1: Builder
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04 as builder

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3-pip \
    python3-dev \
    build-essential \
    git \
    cmake \
    ninja-build \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python3 -m pip install --upgrade pip setuptools wheel && \
    python3 -m pip install virtualenv

WORKDIR /tmp/build
RUN python3 -m virtualenv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    CUDA_HOME=/usr/local/cuda

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    curl \
    wget \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Create application directory
WORKDIR /app

# Copy application code
COPY . /app

# Create cache directory
RUN mkdir -p /app/gradio_cache /app/logs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:7860/ || exit 1

# Expose ports
EXPOSE 7860 8000

# Default command - run Gradio app
ENV PYTHONPATH=/app:$PYTHONPATH

# Support both Gradio and API server
ENTRYPOINT ["python3", "-m"]
CMD ["hy3dgen.apps.gradio_app"]

# Alternative: API server
# CMD ["hy3dgen.apps.api_server"]
