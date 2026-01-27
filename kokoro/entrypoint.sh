#!/usr/bin/env bash
set -e

# Set default values
KOKORO_API_URL="${KOKORO_API_URL:-http://10.0.3.23:8880/v1}"
KOKORO_VOICE="${KOKORO_VOICE:-af_bella}"
KOKORO_SPEED="${KOKORO_SPEED:-1.0}"
KOKORO_TIMEOUT="${KOKORO_TIMEOUT:-30}"
KOKORO_DEBUG="${KOKORO_DEBUG:-false}"

echo "Starting Wyoming Kokoro TTS server..."
echo "API URL: ${KOKORO_API_URL}"
echo "Voice: ${KOKORO_VOICE}"
echo "Speed: ${KOKORO_SPEED}"
echo "Timeout: ${KOKORO_TIMEOUT}s"
echo "Debug: ${KOKORO_DEBUG}"

# Build command arguments
CMD_ARGS=(
    --uri "tcp://0.0.0.0:10203"
    --api-url "${KOKORO_API_URL}"
    --voice "${KOKORO_VOICE}"
    --speed "${KOKORO_SPEED}"
    --api-timeout "${KOKORO_TIMEOUT}"
)

# Add debug flag if enabled
if [ "${KOKORO_DEBUG}" = "true" ]; then
    CMD_ARGS+=(--debug)
fi

# Execute wrapper
exec python3 kokoro_wrapper.py "${CMD_ARGS[@]}"
