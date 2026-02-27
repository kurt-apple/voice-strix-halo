FROM docker.io/kyuz0/vllm-therock-gfx1151:latest

# ffmpeg is required for audio decoding
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Install speaches (formerly faster-whisper-server) without its bundled CTranslate2
RUN pip install "speaches[uvicorn]" --no-deps && \
    pip install huggingface-hub tokenizers faster-whisper --no-deps && \
    pip install av numpy

# Install the ROCm-compatible CTranslate2 — built against the ROCm in this image
# Option A: pigeek prebuilt wheel (check releases for correct version)
# RUN pip install https://github.com/pigeek/CTranslate2-rocm/releases/download/<tag>/<wheel>.whl

# Option B (safer): build from source against the existing ROCm stack
RUN pip install cmake && \
    git clone --recursive https://github.com/OpenNMT/CTranslate2.git /tmp/ct2 && \
    cd /tmp/ct2 && \
    mkdir build && cd build && \
    cmake .. \
      -DCMAKE_BUILD_TYPE=Release \
      -DWITH_CUDA=ON \
      -DGPU_RUNTIME=HIP \
      -DCMAKE_HIP_ARCHITECTURES=gfx1151 \
      -DGPU_TARGETS=gfx1151 \
      -DOPENMP_RUNTIME=COMP \
      -DWITH_MKL=OFF \
      -DWITH_DNNL=OFF && \
    make -j$(nproc) && \
    make install && \
    cd /tmp/ct2/python && pip install . && \
    rm -rf /tmp/ct2

ENV UVICORN_HOST=0.0.0.0
ENV UVICORN_PORT=8000
ENV WHISPER__INFERENCE_DEVICE=cuda
ENV WHISPER__COMPUTE_TYPE=float16
# Tell ROCm this is gfx1151
ENV HSA_OVERRIDE_GFX_VERSION=11.5.1

EXPOSE 8000
CMD ["uvicorn", "speaches.main:app"]