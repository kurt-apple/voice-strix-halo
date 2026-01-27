"""Wyoming protocol event handler for Kokoro TTS."""

import logging
import time

import httpx
from wyoming.audio import AudioChunk, AudioStart, AudioStop
from wyoming.event import Event
from wyoming.info import Describe, Info
from wyoming.tts import Synthesize
from wyoming.server import AsyncEventHandler

_LOGGER = logging.getLogger(__name__)


class KokoroEventHandler(AsyncEventHandler):
    """Event handler for Wyoming protocol events."""

    def __init__(
        self,
        reader,
        writer,
        wyoming_info: Info,
        api_url: str,
        voice: str,
        speed: float = 1.0,
        api_timeout: float = 30.0,
    ) -> None:
        """Initialize handler."""
        super().__init__(reader, writer)

        self.wyoming_info = wyoming_info
        self.api_url = api_url.rstrip("/")
        self.voice = voice
        self.speed = speed
        self.api_timeout = api_timeout

    async def handle_event(self, event: Event) -> bool:
        """Handle a Wyoming protocol event."""
        if Describe.is_type(event.type):
            await self.write_event(self.wyoming_info.event())
            _LOGGER.debug("Sent info")
            return True

        if Synthesize.is_type(event.type):
            synthesize = Synthesize.from_event(event)
            _LOGGER.info("Synthesizing: %s", synthesize.text)

            try:
                # Prepare API request with streaming enabled
                endpoint = f"{self.api_url}/audio/speech"
                payload = {
                    "model": "kokoro",
                    "voice": self.voice,
                    "input": synthesize.text,
                    "response_format": "pcm",  # Raw PCM for streaming
                    "speed": self.speed,
                    "stream": True,  # Enable streaming
                }

                _LOGGER.debug("Calling Kokoro API (streaming): %s", endpoint)
                start_time = time.time()
                first_chunk_time = None
                total_samples = 0

                # Kokoro outputs 24000 Hz 16-bit mono PCM
                sample_rate = 24000

                # Send audio start event immediately
                await self.write_event(
                    AudioStart(
                        rate=sample_rate,
                        width=2,  # 16-bit = 2 bytes
                        channels=1,  # mono
                    ).event()
                )

                # Stream response chunks as they arrive
                async with httpx.AsyncClient(timeout=self.api_timeout) as client:
                    async with client.stream("POST", endpoint, json=payload) as response:
                        response.raise_for_status()

                        # Buffer for incomplete samples
                        buffer = b""

                        async for chunk in response.aiter_bytes(chunk_size=512):
                            if first_chunk_time is None:
                                first_chunk_time = time.time()
                                ttfb = first_chunk_time - start_time
                                _LOGGER.info("Time to first byte: %.3f seconds", ttfb)

                            # Add chunk to buffer
                            buffer += chunk

                            # Process complete samples (2 bytes per sample for int16)
                            while len(buffer) >= 2:
                                # Calculate how many complete samples we have
                                samples_available = len(buffer) // 2

                                # Send in chunks of 1024 samples for low latency
                                chunk_samples = min(samples_available, 1024)
                                chunk_bytes = buffer[: chunk_samples * 2]
                                buffer = buffer[chunk_samples * 2 :]

                                # Send audio chunk
                                await self.write_event(
                                    AudioChunk(
                                        audio=chunk_bytes,
                                        rate=sample_rate,
                                        width=2,
                                        channels=1,
                                    ).event()
                                )

                                total_samples += chunk_samples

                        # Send any remaining buffered data
                        if len(buffer) >= 2:
                            remaining_samples = len(buffer) // 2
                            chunk_bytes = buffer[: remaining_samples * 2]
                            await self.write_event(
                                AudioChunk(
                                    audio=chunk_bytes,
                                    rate=sample_rate,
                                    width=2,
                                    channels=1,
                                ).event()
                            )
                            total_samples += remaining_samples

                # Calculate metrics
                total_time = time.time() - start_time
                audio_duration = total_samples / sample_rate
                rtf = total_time / audio_duration if audio_duration > 0 else 0
                _LOGGER.info(
                    "Streaming complete: %d samples, %d Hz, %.2f seconds, RTF: %.2fx, Total time: %.2fs",
                    total_samples,
                    sample_rate,
                    audio_duration,
                    rtf,
                    total_time,
                )

                # Send audio stop event
                await self.write_event(AudioStop().event())
                _LOGGER.debug("Audio synthesis complete")

            except httpx.HTTPError as e:
                _LOGGER.error("HTTP request failed: %s", e, exc_info=True)
                # Send empty audio to indicate failure
                await self.write_event(AudioStart(rate=24000, width=2, channels=1).event())
                await self.write_event(AudioStop().event())
            except Exception as e:
                _LOGGER.error("Synthesis failed: %s", e, exc_info=True)
                # Send empty audio to indicate failure
                await self.write_event(AudioStart(rate=24000, width=2, channels=1).event())
                await self.write_event(AudioStop().event())

            return True

        return True
