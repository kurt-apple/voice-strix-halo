#!/usr/bin/env python3
"""Wyoming protocol server wrapper for Kokoro TTS."""

import argparse
import asyncio
import logging
from functools import partial

from wyoming.info import Attribution, Info, TtsProgram, TtsVoice
from wyoming.server import AsyncServer

from kokoro_handler import KokoroEventHandler

_LOGGER = logging.getLogger(__name__)


async def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Wyoming Kokoro TTS Server")
    parser.add_argument(
        "--api-url",
        default="http://10.0.3.23:8880/v1",
        help="Kokoro-FastAPI base URL",
    )
    parser.add_argument(
        "--voice",
        default="af_bella",
        help="Voice name (e.g., af_bella, af_sarah, bf_emma) or voice mix (e.g., af_bella+af_sky)",
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=1.0,
        help="Speech speed (0.5-2.0)",
    )
    parser.add_argument(
        "--api-timeout",
        type=float,
        default=30.0,
        help="API request timeout in seconds",
    )
    parser.add_argument(
        "--uri",
        required=True,
        help="URI to bind server (e.g., tcp://0.0.0.0:10203)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    _LOGGER.info("Starting Wyoming Kokoro TTS server")
    _LOGGER.info("API URL: %s", args.api_url)
    _LOGGER.info("Voice: %s", args.voice)
    _LOGGER.info("Speed: %.2f", args.speed)

    # Construct Wyoming protocol info
    # Kokoro supports multiple languages
    wyoming_info = Info(
        tts=[
            TtsProgram(
                name="kokoro-tts",
                description="Kokoro-82M TTS via FastAPI proxy",
                attribution=Attribution(
                    name="hexgrad",
                    url="https://huggingface.co/hexgrad/Kokoro-82M",
                ),
                installed=True,
                version="1.0.0",
                voices=[
                    TtsVoice(
                        name=args.voice,
                        description=f"Kokoro TTS - {args.voice}",
                        attribution=Attribution(
                            name="hexgrad",
                            url="https://huggingface.co/hexgrad/Kokoro-82M",
                        ),
                        installed=True,
                        version="1.0.0",
                        languages=["en", "ja", "zh", "ko", "fr", "es"],
                    )
                ],
            )
        ],
    )

    # Create event handler factory
    handler_factory = partial(
        KokoroEventHandler,
        wyoming_info=wyoming_info,
        api_url=args.api_url,
        voice=args.voice,
        speed=args.speed,
        api_timeout=args.api_timeout,
    )

    # Start server
    server = AsyncServer.from_uri(args.uri)
    _LOGGER.info("Server listening on %s", args.uri)

    try:
        await server.run(handler_factory)
    except KeyboardInterrupt:
        _LOGGER.info("Server stopped")


if __name__ == "__main__":
    asyncio.run(main())
