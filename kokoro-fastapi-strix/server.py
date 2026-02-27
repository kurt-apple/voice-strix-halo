"""
Kokoro TTS - OpenAI-compatible REST API
Endpoints mirror the OpenAI /v1/audio/speech spec so it works as a drop-in
with any client that supports custom base_url (openai-python, LangChain, etc.)
"""

import io
import logging
import os
import time
from typing import Literal

import soundfile as sf
import torch
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("kokoro-api")

# ── Device setup ──────────────────────────────────────────────────────────────

def get_device() -> str:
    env = os.getenv("KOKORO_DEVICE", "auto")
    if env != "auto":
        return env
    if torch.cuda.is_available():
        log.info("ROCm/CUDA device found: %s", torch.cuda.get_device_name(0))
        return "cuda"
    log.warning("No GPU found, falling back to CPU")
    return "cpu"

DEVICE = get_device()

# ── Model init ────────────────────────────────────────────────────────────────

log.info("Loading Kokoro on device=%s ...", DEVICE)
from kokoro import KPipeline

# lang_code "a" = American English; change or expose as needed
_pipeline_cache: dict[str, KPipeline] = {}

def get_pipeline(lang_code: str = "a") -> KPipeline:
    if lang_code not in _pipeline_cache:
        log.info("Initialising KPipeline lang_code=%s", lang_code)
        _pipeline_cache[lang_code] = KPipeline(lang_code=lang_code, device=DEVICE)
    return _pipeline_cache[lang_code]

# Warm up on startup
try:
    pipe = get_pipeline("a")
    log.info("Kokoro warm-up complete")
except Exception as e:
    log.error("Kokoro init failed: %s", e)
    raise

# ── FastAPI ───────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Kokoro TTS",
    description="OpenAI-compatible TTS API backed by Kokoro-82M on ROCm",
    version="1.0.0",
)

# ── Request / response models ─────────────────────────────────────────────────

AudioFormat = Literal["mp3", "wav", "opus", "flac", "pcm"]

class SpeechRequest(BaseModel):
    model: str = Field(default="kokoro", description="Ignored, always uses Kokoro")
    input: str = Field(..., description="Text to synthesize", max_length=4096)
    voice: str = Field(default="af_heart", description="Voice name")
    response_format: AudioFormat = Field(default="wav")
    speed: float = Field(default=1.0, ge=0.25, le=4.0)

MIME = {
    "mp3":  "audio/mpeg",
    "wav":  "audio/wav",
    "opus": "audio/ogg; codecs=opus",
    "flac": "audio/flac",
    "pcm":  "audio/pcm",
}

SF_FORMAT = {
    "wav":  ("WAV",  "PCM_16"),
    "flac": ("FLAC", "PCM_16"),
    "mp3":  ("MP3",  None),      # handled separately
    "pcm":  (None,   None),      # raw float32 bytes
    "opus": ("OGG",  "VORBIS"),  # approximation; true opus needs ffmpeg
}

def audio_to_bytes(samples, sample_rate: int, fmt: AudioFormat) -> bytes:
    buf = io.BytesIO()
    if fmt == "pcm":
        return samples.astype("float32").tobytes()
    sf_fmt, sf_sub = SF_FORMAT[fmt]
    if sf_sub:
        sf.write(buf, samples, sample_rate, format=sf_fmt, subtype=sf_sub)
    else:
        sf.write(buf, samples, sample_rate, format=sf_fmt)
    return buf.getvalue()

# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {
        "status": "ok",
        "device": DEVICE,
        "gpu": torch.cuda.get_device_name(0) if DEVICE == "cuda" else None,
    }

@app.get("/v1/audio/voices")
def list_voices():
    """Return available voices. Kokoro ships ~20 presets."""
    voices = [
        # American English
        "af_heart", "af_bella", "af_nicole", "af_sarah", "af_sky",
        "am_adam", "am_michael",
        # British English
        "bf_emma", "bf_isabella", "bm_george", "bm_lewis",
        # Other (requires matching lang_code pipeline)
        "jf_alpha", "jm_kumo",  # Japanese
    ]
    return {"voices": voices}

@app.post("/v1/audio/speech")
async def create_speech(req: SpeechRequest):
    if not req.input.strip():
        raise HTTPException(status_code=400, detail="Input text is empty")

    t0 = time.perf_counter()
    pipe = get_pipeline("a")  # TODO: infer lang from voice prefix or add param

    try:
        # KPipeline returns a generator of (graphemes, phonemes, audio_tensor)
        chunks = []
        for _, _, audio in pipe(req.input, voice=req.voice, speed=req.speed):
            if audio is not None:
                chunks.append(audio.numpy())
    except Exception as e:
        log.exception("Synthesis failed")
        raise HTTPException(status_code=500, detail=str(e))

    if not chunks:
        raise HTTPException(status_code=500, detail="No audio generated")

    import numpy as np
    samples = np.concatenate(chunks)
    sample_rate = 24000  # Kokoro native sample rate

    audio_bytes = audio_to_bytes(samples, sample_rate, req.response_format)
    elapsed = time.perf_counter() - t0
    duration = len(samples) / sample_rate
    log.info(
        "Synthesized %.1fs audio in %.2fs (RTF=%.2f) voice=%s fmt=%s",
        duration, elapsed, elapsed / max(duration, 0.001),
        req.voice, req.response_format,
    )

    return Response(
        content=audio_bytes,
        media_type=MIME[req.response_format],
        headers={"X-Synthesis-Time": f"{elapsed:.3f}"},
    )

@app.post("/v1/audio/speech/stream")
async def stream_speech(req: SpeechRequest):
    """
    Streaming endpoint - yields WAV chunks as they're generated.
    Useful for sentence-by-sentence TTS in a pipeline.
    """
    import numpy as np

    if not req.input.strip():
        raise HTTPException(status_code=400, detail="Input text is empty")

    pipe = get_pipeline("a")

    def generate():
        try:
            for _, _, audio in pipe(req.input, voice=req.voice, speed=req.speed):
                if audio is not None:
                    samples = audio.numpy()
                    buf = io.BytesIO()
                    sf.write(buf, samples, 24000, format="WAV", subtype="PCM_16")
                    yield buf.getvalue()
        except Exception as e:
            log.exception("Streaming synthesis failed: %s", e)

    return StreamingResponse(generate(), media_type="audio/wav")
