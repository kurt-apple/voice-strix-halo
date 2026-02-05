FROM rocm/vllm-dev:latest

ARG HSA_OVERRIDE_GFX_VERSION

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    HSA_OVERRIDE_GFX_VERSION=${HSA_OVERRIDE_GFX_VERSION} \
    PYTORCH_ROCM_ARCH="gfx90a;gfx942;gfx1100;gfx1151" \
    VLLM_USE_TRITON_FLASH_ATTN=0

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install audio processing and Wyoming dependencies
# vLLM is already installed in the base image
RUN pip3 install --no-cache-dir \
    mistral_common>=1.9.0 \
    soxr \
    librosa \
    soundfile \
    wyoming

# Remove torchvision to avoid ROCm operator registration issues
# vLLM/transformers pull it in but Voxtral doesn't need vision capabilities
RUN pip3 uninstall -y torchvision || true

# Create app directory
WORKDIR /app

# Copy application files
COPY voxtral_wrapper.py /app/
COPY voxtral_handler.py /app/
COPY entrypoint.sh /app/

RUN chmod +x /app/entrypoint.sh

# Expose Wyoming protocol port
EXPOSE 10301

ENTRYPOINT ["/app/entrypoint.sh"]
