# Wyoming `faster-whisper` (ROCm 7.1.1)

Docker setup for Wyoming + `faster-whisper` with [ctranslate2-rocm](https://github.com/paralin/ctranslate2-rocm/blob/rocm/ROCM.md) designed for the AMD Ryzen AI Max 395+ (Radeon 8060S)

## Features

- **Whisper Medium Model** for high-quality speech recognition
- **ROCm 7.1.1** GPU acceleration for AMD GPUs
- **Wyoming Protocol** for easy Home Assistant integration
- **CTranslate2-rocm** (paralin fork) for native AMD GPU support with HIP

## Prerequisites

- AMD GPU (i.e. Radeon 8060S from Ryzen AI Max 395+)
- ROCm drivers installed on host (version 7.1.1)
- Docker and Docker Compose
- ~5GB VRAM for medium model
- ~15GB disk space for Docker image (larger due to multi-arch build)

## Installation

### 1. Find Your GPU Architecture

```bash
rocminfo | grep "gfx"
```

You'll see output like `gfx1100`, `gfx1030`, `gfx906`, etc.

### 2. Configure GPU Architecture

Create the `.env` file and set your GPU architecture override:

```bash
# For RDNA 3 (RX 7000 series): gfx1100, gfx1101, gfx1102
HSA_OVERRIDE_GFX_VERSION=11.0.0

# For RDNA 2 (RX 6000 series): gfx1030, gfx1031, gfx1032
HSA_OVERRIDE_GFX_VERSION=10.3.0

# For RDNA (RX 5000 series): gfx1010, gfx1012
HSA_OVERRIDE_GFX_VERSION=10.1.0

# For Vega: gfx900, gfx906
HSA_OVERRIDE_GFX_VERSION=9.0.0
```

See `.env.example` for more GPU architecture mappings.

### 3. Build and Run

```bash
docker compose up -d --build
```

## Home Assistant Integration

### Add Wyoming Integration

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for **"Wyoming Protocol"**
3. Enter connection details:
   - **Host**: `<docker-host-ip>` (e.g., `192.168.1.100`)
   - **Port**: `10300`
4. Click **Submit**

## Configuration

### Change Whisper Model

Edit `Dockerfile` entrypoint to use different model sizes:

```dockerfile
ENTRYPOINT ["python3", "-m", "wyoming_faster_whisper", \
    "--model", "tiny",  # Options: tiny, base, small, medium, large
    ...
```

Model sizes and VRAM requirements:
- **tiny**: ~1GB VRAM, fastest, good for simple commands
- **base**: ~1.5GB VRAM, balanced
- **small**: ~2GB VRAM, better accuracy
- **medium**: ~5GB VRAM, high accuracy (default)
- **large**: ~10GB VRAM, best accuracy, slower

### Adjust Performance

Edit `Dockerfile` entrypoint:

```dockerfile
# Faster, lower quality
--compute-type int8
--beam-size 1

# Slower, higher quality
--compute-type float16
--beam-size 5
```

## Resources

- [Wyoming Protocol](https://github.com/rhasspy/wyoming)
- [Faster Whisper](https://github.com/SYSTRAN/faster-whisper)
- [paralin/ctranslate2-rocm](https://github.com/paralin/ctranslate2-rocm) - ROCm fork used
- [paralin/whisperX-rocm](https://github.com/paralin/whisperX-rocm) - Reference for ROCm setup
- [ROCm Documentation](https://rocm.docs.amd.com/)
- [CTranslate2 ROCm Blog](https://rocm.blogs.amd.com/artificial-intelligence/ctranslate2/README.html)

## License

- Whisper: MIT License
- CTranslate2: MIT License
- Wyoming: MIT License
- faster-whisper: MIT License
