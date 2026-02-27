#!/bin/bash
set -e

# Use environment variables with defaults
VOXTRAL_MODEL="${VOXTRAL_MODEL:-mistralai/Voxtral-Mini-4B-Realtime-2602}"
VOXTRAL_LANGUAGE="${VOXTRAL_LANGUAGE:-en}"
VOXTRAL_GPU_MEMORY="${VOXTRAL_GPU_MEMORY:-0.9}"
VOXTRAL_DEBUG="${VOXTRAL_DEBUG:-false}"

# Build command arguments
CMD_ARGS=(
    --uri "tcp://0.0.0.0:10301"
    --model "$VOXTRAL_MODEL"
    --language "$VOXTRAL_LANGUAGE"
    --gpu-memory-utilization "$VOXTRAL_GPU_MEMORY"
)

# Add debug flag if enabled
if [ "$VOXTRAL_DEBUG" = "true" ]; then
    CMD_ARGS+=(--debug)
fi

# Log configuration
echo "Starting Voxtral STT service"
echo "Model: $VOXTRAL_MODEL"
echo "Language: $VOXTRAL_LANGUAGE"
echo "GPU Memory Utilization: $VOXTRAL_GPU_MEMORY"

# Run the Wyoming server
exec python3 /app/voxtral_wrapper.py "${CMD_ARGS[@]}"
