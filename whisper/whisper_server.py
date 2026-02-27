#!/usr/bin/env python3
"""
Simple HTTP REST API server for Faster Whisper
Replaces Wyoming protocol with OpenAI-compatible REST endpoints
"""

import os
import io
import logging
from typing import Optional
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from faster_whisper import WhisperModel
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO if os.getenv("WHISPER_DEBUG", "false").lower() != "true" else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Environment configuration
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "medium")
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "float16")
WHISPER_BEAM_SIZE = int(os.getenv("WHISPER_BEAM_SIZE", "5"))
WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "en")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cuda")  # cuda for ROCm via HIP
HTTP_PORT = int(os.getenv("HTTP_PORT", "10300"))
HTTP_HOST = os.getenv("HTTP_HOST", "0.0.0.0")

# Initialize FastAPI app
app = FastAPI(
    title="Faster Whisper REST API",
    description="REST API for Faster Whisper speech-to-text",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model instance
model: Optional[WhisperModel] = None


def load_model():
    """Load Whisper model on startup"""
    global model
    logger.info(f"Loading Whisper model: {WHISPER_MODEL}")
    logger.info(f"Device: {WHISPER_DEVICE}, Compute type: {WHISPER_COMPUTE_TYPE}")

    model = WhisperModel(
        WHISPER_MODEL,
        device=WHISPER_DEVICE,
        compute_type=WHISPER_COMPUTE_TYPE,
        download_root="/data/models"
    )
    logger.info("Model loaded successfully")


@app.on_event("startup")
async def startup_event():
    """Load model on server startup"""
    load_model()


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "model": WHISPER_MODEL,
        "device": WHISPER_DEVICE,
        "compute_type": WHISPER_COMPUTE_TYPE
    }


@app.post("/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    """
    Transcribe audio file to text

    Compatible with frontend WhisperService expectation:
    - Accepts multipart/form-data with 'audio' field
    - Returns JSON: {"text": "transcription"}
    """
    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")

    try:
        # Read audio file into memory
        audio_bytes = await audio.read()
        logger.debug(f"Received audio file: {audio.filename}, size: {len(audio_bytes)} bytes")

        # Transcribe
        segments, info = model.transcribe(
            io.BytesIO(audio_bytes),
            language=WHISPER_LANGUAGE if WHISPER_LANGUAGE != "auto" else None,
            beam_size=WHISPER_BEAM_SIZE,
            vad_filter=True,  # Voice activity detection to filter silence
        )

        # Collect all segments into single transcript
        transcript = " ".join(segment.text for segment in segments).strip()

        logger.info(f"Transcription: {transcript}")

        return JSONResponse({
            "text": transcript,
            "language": info.language,
            "language_probability": info.language_probability,
        })

    except Exception as e:
        logger.error(f"Transcription error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/audio/transcriptions")
async def transcriptions_openai(
    file: UploadFile = File(..., description="Audio file to transcribe"),
):
    """
    OpenAI-compatible transcription endpoint

    This endpoint matches the OpenAI Whisper API format for easier integration
    """
    result = await transcribe(file)
    # OpenAI format returns just the text in a different structure
    return {
        "text": result["text"]
    }


if __name__ == "__main__":
    logger.info(f"Starting Faster Whisper REST server on {HTTP_HOST}:{HTTP_PORT}")
    logger.info(f"Model: {WHISPER_MODEL}, Device: {WHISPER_DEVICE}, Compute: {WHISPER_COMPUTE_TYPE}")

    uvicorn.run(
        app,
        host=HTTP_HOST,
        port=HTTP_PORT,
        log_level="debug" if os.getenv("WHISPER_DEBUG", "false").lower() == "true" else "info"
    )
