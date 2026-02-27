# Voice Strix Halo

A complete voice AI pipeline for AMD Ryzen AI Max 395+ (Radeon 8060S) with ROCm 7.1.1 GPU acceleration.

## Overview

This project provides a full voice conversation system with:
- **Speech-to-Text (STT)** - Multiple engines for transcription
- **LLM Inference** - Local language model processing
- **Text-to-Speech (TTS)** - Multiple engines for voice synthesis
- **Web Interface** - Vue.js frontend for voice interaction

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌─────────────┐
│  Frontend   │────▶│   Whisper    │────▶│  llama-cpp  │────▶│   Kokoro    │
│  (Vue App)  │     │    (STT)     │     │    (LLM)    │     │    (TTS)    │
│  :3000      │     │   :10300     │     │   :8080     │     │   :8880     │
└─────────────┘     └──────────────┘     └─────────────┘     └─────────────┘
                                                 │
                              ┌──────────────────┤
                              ▼                  ▼
                     ┌──────────────┐    ┌──────────────┐
                     │ voice-pipeline│    │ Wyoming Proto│
                     │   :10501     │    │  Services    │
                     └──────────────┘    └──────────────┘
```

## Services

### STT (Speech-to-Text)

| Service | Port | Description |
|---------|------|-------------|
| wyoming-whisper | 10300 | Faster Whisper with CTranslate2 + ROCm GPU |
| wyoming-moonshine | 10302 | Moonshine ONNX, CPU-only, ultra-low latency |
| wyoming-voxtral | 10301 | Mistral Voxtral with vLLM (NOT WORKING) |

### TTS (Text-to-Speech)

| Service | Port | Description |
|---------|------|-------------|
| wyoming-qwen-tts | 10200 | Qwen3-TTS with GPU acceleration |
| wyoming-chatterbox-turbo | 10201 | Chatterbox Turbo, sub-200ms latency |
| wyoming-pocket-tts | 10202 | Pocket TTS, CPU-only, ultra-low latency |
| wyoming-kokoro-tts | 10203 | Proxies to external Kokoro-FastAPI |

### Pipeline Services

| Service | Port | Description |
|---------|------|-------------|
| llama-cpp | 8080 | Local LLM inference with ROCm |
| kokoro | 8880 | Local Kokoro TTS with GPU |
| voice-pipeline | 10501 | Orchestration: STT → LLM → TTS |

### Frontend

| Service | Port | Description |
|---------|------|-------------|
| frontend | 3000 | Vue.js voice interaction UI |

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
- `WHISPER_MODEL` - Whisper model size (tiny/base/small/medium/large)
- `QWEN_MODEL` - Qwen TTS model
- `HF_TOKEN` - HuggingFace token for gated models

### 3. Build and Run

```bash
docker compose up -d
```

### 4. Access the UI

Open http://localhost:3000 in your browser. Hold **SPACE** to record your voice.

## Usage

### Voice Pipeline (Recommended)

The full pipeline processes voice input through:
1. **Whisper** - Transcribes speech to text
2. **llama-cpp** - Generates AI response
3. **Kokoro** - Converts response to speech

The frontend sends audio to the voice-pipeline service which orchestrates all three.

### Wyoming Protocol Services

Each STT/TTS service implements the Wyoming protocol for Home Assistant integration:
- STT services on ports 10300-10302
- TTS services on ports 10200-10203

### Direct API Calls

```bash
# Chat with voice pipeline (returns text + audio)
curl -X POST http://localhost:10501/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3-next",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'

# Text-to-speech only
curl -X POST http://localhost:10501/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "kokoro",
    "input": "Hello world",
    "voice": "af_bella"
  }' --output speech.wav
```

## Configuration

All configuration is in `.env`. Key options:

| Variable | Description | Default |
|----------|-------------|---------|
| `HSA_OVERRIDE_GFX_VERSION` | GPU architecture | 11.5.1 |
| `WHISPER_MODEL` | Whisper model size | large-v3-turbo |
| `QWEN_MODEL` | Qwen TTS model | Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice |
| `KOKORO_VOICE` | Kokoro voice | af_bella |
| `MODEL_NAME` | LLM model name | qwen3-next |

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

## Hardware Requirements

- **GPU**: AMD Radeon 8060S (or compatible RDNA 3.5)
- **VRAM**: 16GB+ recommended for full pipeline
- **RAM**: 32GB+ recommended
- **Disk**: ~50GB for models and Docker images

## License

See individual service directories for component licenses.
