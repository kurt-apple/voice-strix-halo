# Kokoro TTS - ROCm / Strix Halo (gfx1151)
#
# AMD's official rocm/pytorch image is the only reliable base for gfx1151.
# It ships Ubuntu 24.04 + ROCm 7.1.1 + PyTorch 2.9.1 pre-built for gfx1151,
# which avoids the kernel module / wheel compatibility nightmare documented
# in ROCm/ROCm issues #5824, #5853.
#
# Check for newer tags at: https://hub.docker.com/r/rocm/pytorch/tags
FROM rocm/pytorch:rocm7.1.1_ubuntu24.04_py3.12_pytorch_release_2.9.1

# ── System deps ───────────────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    espeak-ng \
    libsndfile1 \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# ── Python deps ───────────────────────────────────────────────────────────────
# Install into the system Python that already has the correct ROCm torch.
# DO NOT reinstall torch here - it would overwrite the ROCm build.
RUN pip install --no-cache-dir \
    kokoro>=0.9.4 \
    soundfile \
    fastapi \
    uvicorn[standard] \
    pydantic \
    python-multipart \
    numpy

# ── App ───────────────────────────────────────────────────────────────────────
WORKDIR /app
COPY server.py .

# ── Strix Halo / gfx1151 environment ─────────────────────────────────────────
# gfx1151 is natively supported in this image - NO HSA_OVERRIDE needed.
# HSA_ENABLE_SDMA=0 prevents checkerboard artifacts / memory faults on APUs
# with unified memory (documented in ROCm strix halo optimization guide).
# FLASH_ATTENTION_TRITON_AMD_ENABLE uses Triton as the FA backend since
# flash-attention doesn't ship a native gfx1151 frontend.
ENV HSA_ENABLE_SDMA=0 \
    FLASH_ATTENTION_TRITON_AMD_ENABLE=1 \
    PYTORCH_TUNABLEOP_ENABLED=0 \
    HIP_VISIBLE_DEVICES=0 \
    KOKORO_DEVICE=cuda

EXPOSE 8880

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8880"]
