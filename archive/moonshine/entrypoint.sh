#!/bin/bash
set -e

# Use environment variables with defaults
MOONSHINE_MODEL="${MOONSHINE_MODEL:-moonshine/tiny}"
MOONSHINE_DEBUG="${MOONSHINE_DEBUG:-false}"

# Build command arguments
args=(
    --uri "tcp://0.0.0.0:10302"
    --model "$MOONSHINE_MODEL"
)

if [ "$MOONSHINE_DEBUG" = "true" ]; then
    args+=(--debug)
fi

exec python3 /app/moonshine_wrapper.py "${args[@]}"
