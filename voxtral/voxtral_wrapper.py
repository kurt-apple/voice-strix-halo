"""Wyoming protocol server for Voxtral STT."""

import argparse
import asyncio
import logging
from functools import partial

from wyoming.info import Attribution, Info, AsrProgram, AsrModel
from wyoming.server import AsyncServer

from voxtral_handler import VoxtralEventHandler

_LOGGER = logging.getLogger(__name__)


async def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Voxtral STT Wyoming Protocol Server")
    parser.add_argument("--uri", required=True, help="URI to bind to (e.g., tcp://0.0.0.0:10301)")
    parser.add_argument("--model", default="mistralai/Voxtral-Mini-4B-Realtime-2602", help="Model name/path")
    parser.add_argument("--language", default="en", help="Default language code")
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.9, help="GPU memory utilization (0.0-1.0)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    _LOGGER.info("Starting Voxtral STT server")
    _LOGGER.info("Model: %s", args.model)
    _LOGGER.info("Language: %s", args.language)
    _LOGGER.info("URI: %s", args.uri)

    # Define supported languages (13 languages per Voxtral docs)
    # Note: Voxtral auto-detects language, but we advertise these capabilities
    supported_languages = [
        "en",  # English
        "es",  # Spanish
        "fr",  # French
        "de",  # German
        "it",  # Italian
        "pt",  # Portuguese
        "ru",  # Russian
        "zh",  # Chinese
        "ja",  # Japanese
        "ko",  # Korean
        "ar",  # Arabic
        "hi",  # Hindi
        "nl",  # Dutch
    ]

    # Create Wyoming info
    wyoming_info = Info(
        asr=[
            AsrProgram(
                name="voxtral",
                description="Mistral Voxtral Mini 4B Realtime STT",
                attribution=Attribution(
                    name="Mistral AI",
                    url="https://huggingface.co/mistralai/Voxtral-Mini-4B-Realtime-2602",
                ),
                installed=True,
                models=[
                    AsrModel(
                        name=args.model,
                        description="Voxtral Mini 4B - Real-time streaming ASR with <500ms latency",
                        attribution=Attribution(
                            name="Mistral AI",
                            url="https://huggingface.co/mistralai/Voxtral-Mini-4B-Realtime-2602",
                        ),
                        installed=True,
                        languages=supported_languages,
                    )
                ],
            )
        ],
    )

    # Create event handler factory
    handler_factory = partial(
        VoxtralEventHandler,
        wyoming_info=wyoming_info,
        model_name=args.model,
        language=args.language,
        gpu_memory_utilization=args.gpu_memory_utilization,
    )

    # Start server
    _LOGGER.info("Server starting on %s", args.uri)
    server = AsyncServer.from_uri(args.uri)

    try:
        await server.run(handler_factory)
    except KeyboardInterrupt:
        _LOGGER.info("Server stopped by user")
    except Exception as e:
        _LOGGER.error("Server error: %s", e, exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
