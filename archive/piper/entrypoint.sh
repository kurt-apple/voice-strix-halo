#!/bin/bash
set -e

# Use environment variables with defaults
PIPER_VOICE="${PIPER_VOICE:-en_US-lessac-medium}"
PIPER_LENGTH_SCALE="${PIPER_LENGTH_SCALE:-1.0}"
PIPER_NOISE_SCALE="${PIPER_NOISE_SCALE:-0.667}"
PIPER_NOISE_W="${PIPER_NOISE_W:-0.8}"
PIPER_DEBUG="${PIPER_DEBUG:-false}"

# Build command - use wrapper to configure ONNX Runtime threading
CMD="python3 /app/piper_wrapper.py \
    --voice $PIPER_VOICE \
    --length-scale $PIPER_LENGTH_SCALE \
    --noise-scale $PIPER_NOISE_SCALE \
    --noise-w $PIPER_NOISE_W \
    --uri tcp://0.0.0.0:10200 \
    --data-dir /data \
    --download-dir /data"

# Add debug flag if enabled
if [ "$PIPER_DEBUG" = "true" ]; then
    CMD="$CMD --debug"
fi

# Run the command
exec $CMD
