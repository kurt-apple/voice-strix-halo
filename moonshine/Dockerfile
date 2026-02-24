FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for audio processing
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    wyoming \
    numpy \
    useful-moonshine-onnx

# Create data directory for model cache
RUN mkdir -p /data/models

# Copy application files
COPY moonshine_wrapper.py /app/moonshine_wrapper.py
COPY moonshine_handler.py /app/moonshine_handler.py
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Expose Wyoming protocol port
EXPOSE 10302

ENTRYPOINT ["/app/entrypoint.sh"]
