# Kokoro TTS — ROCm / Strix Halo (gfx1151)

OpenAI-compatible TTS REST API backed by Kokoro-82M, running on AMD Ryzen AI Max+ 395 via ROCm.

## Prerequisites

### Host setup (one-time)

```bash
# Add your user to GPU groups
sudo usermod -aG video,render $USER
# Reboot or log out/in for group changes to take effect

# Verify ROCm can see the GPU
rocminfo | grep "gfx"
# Should show: gfx1151
```

ROCm drivers must be installed on the host. The container does NOT include kernel modules.
If you don't have ROCm installed: https://rocm.docs.amd.com/en/latest/deploy/linux/

## Quick start

```bash
# Build and start
docker compose up --build

# First run downloads Kokoro model weights (~500MB) from HuggingFace.
# Subsequent starts use the hf-cache volume.

# Check it's working
curl http://localhost:8880/health
```

## Usage

### Synthesize speech (OpenAI-compatible)

```bash
curl -X POST http://localhost:8880/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "kokoro",
    "input": "Hello, this is Kokoro running on Strix Halo.",
    "voice": "af_heart",
    "response_format": "wav"
  }' \
  --output output.wav
```

### List voices

```bash
curl http://localhost:8880/v1/audio/voices
```

### With OpenAI Python client

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8880/v1",
    api_key="not-needed",
)

with client.audio.speech.with_streaming_response.create(
    model="kokoro",
    voice="af_heart",
    input="Hello from Kokoro on Strix Halo!",
    response_format="wav",
) as response:
    response.stream_to_file("output.wav")
```

## Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Status, device, GPU name |
| `/v1/audio/voices` | GET | Available voice list |
| `/v1/audio/speech` | POST | Synthesize (full response) |
| `/v1/audio/speech/stream` | POST | Synthesize (chunked stream) |
| `/docs` | GET | Swagger UI |

## Voices

| Voice | Type | Accent |
|---|---|---|
| `af_heart` | Female | American |
| `af_bella` | Female | American |
| `af_nicole` | Female | American |
| `am_adam` | Male | American |
| `am_michael` | Male | American |
| `bf_emma` | Female | British |
| `bm_george` | Male | British |

## Troubleshooting

**"ROCk module is NOT loaded"**
ROCm kernel drivers aren't installed on the host. Install amdgpu/ROCm first.

**"HIP error: invalid device function"**
The image doesn't have native gfx1151 kernels compiled in.
Uncomment `HSA_OVERRIDE_GFX_VERSION: "11.0.0"` in docker-compose.yml as a fallback
(runs in gfx1100 compatibility mode, slight perf hit).

**Memory access fault / segfault**
Ensure `HSA_ENABLE_SDMA=0` is set (already in compose file).
This is a known issue with Strix Halo APU unified memory.

**Slow first inference**
MIOpen kernel compilation cache is being built. Subsequent runs are faster.
You can persist this cache by adding a volume for `/root/.cache/miopen`.

**GTT memory limit**
Strix Halo defaults to ~50% RAM as GPU-accessible. For 96GB systems, that's ~48GB.
To increase:
```bash
# Check current GTT size
cat /sys/class/drm/card0/device/mem_info_gtt_total
# Kokoro only needs ~2GB so the default is more than enough
```

## Notes on base image

This uses `rocm/pytorch:rocm7.1.1_ubuntu24.04_py3.12_pytorch_release_2.9.1` which is
AMD's official image with gfx1151 (Strix Halo) support compiled in. It's large (~20GB)
but it's the most reliable path — community attempts to build lighter ROCm images for
gfx1151 have historically run into kernel compilation issues.

Check for newer tags: https://hub.docker.com/r/rocm/pytorch/tags
