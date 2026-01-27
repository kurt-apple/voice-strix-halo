FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install Python dependencies
# Using streaming PCM, no audio processing libraries needed
RUN pip install --no-cache-dir \
    wyoming \
    httpx

# Copy application files
COPY kokoro_handler.py .
COPY kokoro_wrapper.py .
COPY entrypoint.sh .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Expose Wyoming protocol port
EXPOSE 10203

# Run entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]
