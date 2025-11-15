# Context Edge ML Training Container
#
# Multi-stage build for GPU training environment

FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04 AS base

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Install Python and system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    python3-dev \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Set Python 3.10 as default
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1
RUN update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1

# Upgrade pip
RUN pip install --upgrade pip setuptools wheel

# ============================================================================
# Stage 2: PyTorch Installation
# ============================================================================

FROM base AS pytorch

# Install PyTorch with CUDA support
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# ============================================================================
# Stage 3: Training Dependencies
# ============================================================================

FROM pytorch AS training

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install -r requirements.txt

# Copy training scripts
COPY train.py .
COPY convert.py .
COPY deploy.py .

# Create directories for data and models
RUN mkdir -p /data /models

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV CUDA_VISIBLE_DEVICES=0

# Default command
CMD ["python", "train.py", "--help"]
