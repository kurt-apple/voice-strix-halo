# Voice Strix Halo

A complete voice AI pipeline for AMD Ryzen AI Max 395+ (Radeon 8060S) with ROCm 7.1.1 GPU acceleration.

## Overview

This project provides a full voice conversation system with:
- **Speech-to-Text (STT)** - Whisper for audio transcription
- **LLM Inference** - Local language model processing via llama.cpp
- **Text-to-Speech (TTS)** - Kokoro for voice synthesis
- **Orchestrator** - Context management and API coordination
- **Web Interface** - Vue.js frontend with push-to-talk

## Architecture

**Current Implementation:**
```
Frontend (Vue, :3000)
    ↓ [audio recording]
Whisper STT (:10300, REST API)
    ↓ [text transcript]
Frontend
    ↓ [text message]
Orchestrator (:10501, orchestrator service)
    ├─→ llama-cpp (:8080) → [LLM response]
    └─→ Kokoro TTS (:8880) → [audio]
    ↓ [streaming audio]
Frontend → audio playback
```

**Architectural Issue:** Frontend currently coordinates the pipeline. Better architecture would have Whisper call Orchestrator directly, eliminating frontend as middleware.

**What the Orchestrator does:**
- Maintains conversation history/context per session
- Forwards user messages to LLM for response generation
- Converts LLM responses to speech via TTS
- Streams audio back to client

## Active Services

### Core Services

| Service | Port | Description |
|---------|------|-------------|
| **whisper** | 10300 | Faster Whisper with CTranslate2 + ROCm GPU, REST API |
| **wyoming-moonshine** | 10302 | Moonshine ONNX STT, CPU-only (uses Wyoming protocol) |
| **llama-cpp** | 8080 | Local LLM inference with ROCm GPU support |
| **kokoro** | 8880 | Local Kokoro TTS with GPU acceleration |
| **orchestrator** | 10501 | Orchestrator: manages context, calls LLM + TTS |
| **frontend** | 3000 | Vue.js voice interaction UI with push-to-talk |

### Archived Services

Additional STT/TTS engines are available in the `archive/` directory:
- voxtral (Mistral Voxtral STT, not working with current ROCm/vLLM setup)
- qwen3-tts, chatterbox-turbo, pocket-tts (alternative TTS engines)
- piper (legacy TTS)

## Quick Start

### 1. Prerequisites

- AMD GPU (Radeon 8060S from Ryzen AI Max 395+)
- ROCm 7.1.1 drivers installed
- Docker and Docker Compose

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings (GPU architecture, model choices, etc.)
```

Key settings in `.env`:
- `HSA_OVERRIDE_GFX_VERSION` - GPU architecture (default: 11.5.1 for RDNA 3.5)
- `WHISPER_MODEL` - Whisper model size (tiny/base/small/medium/large/large-v3-turbo)
- `MODEL_NAME` - LLM model name (default: qwen3-next)
- `KOKORO_VOICE` - Default TTS voice (af_bella, am_adam, etc.)

### 3. Build and Run

```bash
docker compose up -d
```

First run will download models. This may take 10-30 minutes depending on your connection.

### 4. Access the UI

Open http://localhost:3000 in your browser. Hold **SPACE** to record your voice.

## Usage

### Voice Interaction

1. Open http://localhost:3000
2. Press and hold **SPACE BAR** to record
3. Speak your message
4. Release **SPACE BAR**
5. Wait for transcription, LLM response, and audio playback

### API Endpoints

The orchestrator exposes OpenAI-compatible endpoints:

```bash
# Chat completion with TTS (returns text + base64 audio)
curl -X POST http://localhost:10501/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3-next",
    "messages": [{"role": "user", "content": "Hello!"}],
    "voice": "af_bella"
  }'

# Text-to-speech only
curl -X POST http://localhost:10501/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "kokoro",
    "input": "Hello world",
    "voice": "af_bella"
  }' --output speech.wav

# Streaming TTS
curl -X POST http://localhost:10501/v1/audio/speech/stream \
  -H "Content-Type: application/json" \
  -d '{
    "model": "kokoro",
    "input": "Hello world",
    "voice": "af_bella"
  }' --output speech.wav

# Health check
curl http://localhost:10501/health

# List available voices
curl http://localhost:10501/v1/audio/voices
```

## Configuration

All configuration is in `.env`. Key options:

| Variable | Description | Default |
|----------|-------------|---------|
| `HSA_OVERRIDE_GFX_VERSION` | GPU architecture | 11.5.1 |
| `WHISPER_MODEL` | Whisper model size | large-v3-turbo |
| `MODEL_NAME` | LLM model name | qwen3-next |
| `KOKORO_VOICE` | Default TTS voice | onyx |
| `MAX_CONTEXT_PCT` | Max context usage before trimming | 0.90 |
| `MESSAGE_TTL_MS` | Message time-to-live in milliseconds | 600000 (10 min) |

### Available Voices

Kokoro voices (format: `{accent}{gender}_{name}`):
- **American Female**: af_bella, af_sarah, af_sky
- **American Male**: am_adam, am_michael
- **British Female**: bf_emma, bf_isabella
- **British Male**: bm_george, bm_lewis

Voice mixing is supported:
- Simple: `af_bella+af_sky`
- Weighted: `af_bella(2)+af_sky(1)`

## Development

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

### Rebuild Services
```bash
docker compose build <service-name>
docker compose up -d <service-name>
```

### View Logs
```bash
docker compose logs -f <service-name>
```

### Common Issues

**Whisper not transcribing:**
- Check logs: `docker compose logs -f whisper`
- Verify GPU is accessible: `docker exec -it whisper-rocm rocminfo`
- Test endpoint: `curl http://localhost:10300/health`

**Out of GPU memory:**
- Reduce `WHISPER_MODEL` size (try `medium` or `small`)
- Ensure only needed services are running

**Audio not playing:**
- Check browser console for errors
- Verify Kokoro is running: `docker compose logs -f kokoro`
- Test TTS endpoint directly: `curl http://localhost:8880/v1/audio/voices`

## Hardware Requirements

- **GPU**: AMD Radeon 8060S (or compatible RDNA 3.5)
- **VRAM**: 16GB+ recommended for full pipeline
- **RAM**: 32GB+ recommended
- **Disk**: ~50GB for models and Docker images

## Known Issues

See [TODO.md](TODO.md) for current issues and planned improvements.

Major architectural issues:
1. Frontend does orchestration instead of Whisper calling orchestrator directly
2. Single global conversation context (no multi-user support)

See [VIBES.md](VIBES.md) for completed improvements.

## License

See individual service directories for component licenses.
