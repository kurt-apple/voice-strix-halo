"""Wyoming protocol event handler for Voxtral STT (via vLLM)."""

import io
import logging
import time
import wave
from typing import Optional
import asyncio

import numpy as np
from wyoming.audio import AudioChunk, AudioStop
from wyoming.event import Event
from wyoming.info import Describe, Info
from wyoming.stt import Transcribe, Transcript
from wyoming.server import AsyncEventHandler

_LOGGER = logging.getLogger(__name__)

# Global model cache (thread-safe singleton)
_llm_cache = None
_model_lock = None


def get_vllm_model(model_name: str, gpu_memory_utilization: float = 0.9):
    """Get or create the vLLM LLM instance (cached singleton)."""
    global _llm_cache, _model_lock

    # Initialize lock on first call
    if _model_lock is None:
        import threading
        _model_lock = threading.Lock()

    with _model_lock:
        if _llm_cache is None:
            _LOGGER.info("Loading Voxtral model via vLLM: %s", model_name)
            try:
                from vllm import LLM

                # Initialize vLLM with Voxtral model
                # Temperature should always be 0.0 for Voxtral as per documentation
                _llm_cache = LLM(
                    model=model_name,
                    gpu_memory_utilization=gpu_memory_utilization,
                    trust_remote_code=True,
                    max_model_len=131072,  # Default ~3 hours of audio
                    dtype="bfloat16",
                )
                _LOGGER.info("vLLM model loaded successfully")
            except Exception as e:
                _LOGGER.error("Failed to load vLLM model: %s", e)
                raise

        return _llm_cache


class VoxtralEventHandler(AsyncEventHandler):
    """Event handler for Wyoming protocol STT events using Voxtral."""

    def __init__(
        self,
        reader,
        writer,
        wyoming_info: Info,
        model_name: str,
        language: str,
        gpu_memory_utilization: float,
    ) -> None:
        """Initialize handler."""
        super().__init__(reader, writer)

        self.wyoming_info = wyoming_info
        self.model_name = model_name
        self.language = language
        self.gpu_memory_utilization = gpu_memory_utilization
        self.llm = None

        # Audio buffer for accumulating chunks
        self.audio_buffer = bytearray()
        self.sample_rate = 16000  # Expected sample rate
        self.audio_width = 2  # 16-bit audio
        self.audio_channels = 1  # Mono

    async def handle_event(self, event: Event) -> bool:
        """Handle a Wyoming protocol event."""
        if Describe.is_type(event.type):
            await self.write_event(self.wyoming_info.event())
            _LOGGER.debug("Sent info")
            return True

        if Transcribe.is_type(event.type):
            transcribe = Transcribe.from_event(event)
            _LOGGER.info("Starting transcription (language: %s)", transcribe.language or "auto")

            # Reset audio buffer for new transcription
            self.audio_buffer = bytearray()
            self.sample_rate = 16000  # Default
            return True

        if AudioChunk.is_type(event.type):
            chunk = AudioChunk.from_event(event)

            # Update audio parameters from first chunk
            if not self.audio_buffer:
                self.sample_rate = chunk.rate
                self.audio_width = chunk.width
                self.audio_channels = chunk.channels
                _LOGGER.debug(
                    "Audio format: %d Hz, %d-bit, %d channel(s)",
                    self.sample_rate,
                    self.audio_width * 8,
                    self.audio_channels,
                )

            # Accumulate audio data
            self.audio_buffer.extend(chunk.audio)
            return True

        if AudioStop.is_type(event.type):
            _LOGGER.info("Audio complete, processing transcription (%d bytes)", len(self.audio_buffer))

            try:
                # Load model lazily on first transcription
                if self.llm is None:
                    self.llm = get_vllm_model(
                        self.model_name,
                        self.gpu_memory_utilization,
                    )

                # Convert accumulated audio buffer to numpy array
                audio_data = np.frombuffer(self.audio_buffer, dtype=np.int16)

                # Convert to float32 in range [-1, 1]
                audio_float = audio_data.astype(np.float32) / 32768.0

                _LOGGER.debug("Processing audio: %d samples at %d Hz", len(audio_float), self.sample_rate)

                # Run transcription in thread pool (vLLM is synchronous)
                start_time = time.time()
                loop = asyncio.get_event_loop()
                text = await loop.run_in_executor(
                    None,
                    self._transcribe_sync,
                    audio_float,
                    self.sample_rate,
                )
                transcription_time = time.time() - start_time

                _LOGGER.info("Transcription complete in %.2f seconds: %s", transcription_time, text)

                # Send transcript event
                await self.write_event(
                    Transcript(text=text).event()
                )

            except Exception as e:
                _LOGGER.error("Transcription failed: %s", e, exc_info=True)
                # Send empty transcript to indicate failure
                await self.write_event(Transcript(text="").event())

            return True

        return True

    def _transcribe_sync(self, audio_data: np.ndarray, sample_rate: int) -> str:
        """Synchronous transcription using vLLM (runs in thread pool)."""
        try:
            from vllm import SamplingParams
            import librosa

            # Resample to 16kHz if needed (Voxtral expects 16kHz)
            if sample_rate != 16000:
                _LOGGER.debug("Resampling audio from %d Hz to 16000 Hz", sample_rate)
                audio_data = librosa.resample(
                    audio_data,
                    orig_sr=sample_rate,
                    target_sr=16000,
                )

            # Prepare audio input for Voxtral
            # vLLM expects audio as a dict with "audio" key containing the numpy array
            audio_input = {"audio": audio_data}

            # Sampling parameters (temperature must be 0.0 for Voxtral)
            sampling_params = SamplingParams(
                temperature=0.0,
                max_tokens=8192,  # Adjust based on expected transcript length
            )

            # Run inference
            outputs = self.llm.generate(
                prompts=[None],  # Voxtral doesn't need a text prompt
                multi_modal_data=[audio_input],
                sampling_params=sampling_params,
            )

            # Extract transcription text
            if outputs and len(outputs) > 0:
                output = outputs[0]
                if output.outputs and len(output.outputs) > 0:
                    text = output.outputs[0].text.strip()
                    return text

            _LOGGER.warning("No transcription output from vLLM")
            return ""

        except Exception as e:
            _LOGGER.error("vLLM transcription error: %s", e, exc_info=True)
            return ""
