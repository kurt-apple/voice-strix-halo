FROM rocm/pytorch:rocm7.2_ubuntu24.04_py3.12_pytorch_release_2.9.1

ARG HSA_OVERRIDE_GFX_VERSION=11.5.1

ENV DEBIAN_FRONTEND=noninteractive \
    HSA_OVERRIDE_GFX_VERSION=${HSA_OVERRIDE_GFX_VERSION} \
    PYTHONUNBUFFERED=1

# Install system dependencies and build tools
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    ffmpeg \
    sox \
    git \
    ninja-build \
    cmake \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# Pin transformers version to match model requirements (from preprocessor_config.json)
RUN pip3 install --no-cache-dir \
    "transformers>=4.57.6" \
    accelerate \
    numpy \
    scipy \
    packaging \
    ninja \
    bitsandbytes

# Install qwen-tts from GitHub to get latest fixes (PyPI may be outdated)
# The model was just released Jan 22, 2026 and fixes are being actively pushed
RUN pip3 install --no-cache-dir git+https://github.com/QwenLM/Qwen3-TTS.git

# Install additional dependencies
RUN pip3 install --no-cache-dir \
    wyoming \
    onnxruntime-rocm

# Attempt to install Flash Attention 2 with Composable Kernel (CK) backend for AMD GPUs
# CK is AMD's optimized kernel library and may work on RDNA where Triton doesn't
# Reference: https://rocm.docs.amd.com/en/latest/how-to/rocm-for-ai/inference-optimization/model-acceleration-libraries.html
RUN pip3 install --no-cache-dir flash-attn --no-build-isolation || \
    echo "Flash Attention 2 installation failed - will fall back to SDPA"

# Create app directory
WORKDIR /app

# Copy application files
COPY qwen_wrapper.py /app/
COPY qwen_handler.py /app/
COPY entrypoint.sh /app/

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Expose Wyoming protocol port
EXPOSE 10200

ENTRYPOINT ["/app/entrypoint.sh"]
