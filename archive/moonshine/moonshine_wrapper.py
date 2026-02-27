"""Wyoming protocol server for Moonshine STT."""

import argparse
import asyncio
import logging
from functools import partial

from wyoming.info import Attribution, Info, AsrProgram, AsrModel
from wyoming.server import AsyncServer

from moonshine_handler import MoonshineEventHandler

_LOGGER = logging.getLogger(__name__)

__version__ = "1.0.0"


async def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Moonshine STT Wyoming Protocol Server")
    parser.add_argument("--uri", required=True, help="URI to bind to (e.g., tcp://0.0.0.0:10302)")
    parser.add_argument("--model", default="moonshine/tiny", help="Model name (moonshine/tiny or moonshine/base)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    _LOGGER.info("Starting Moonshine STT server")
    _LOGGER.info("Model: %s", args.model)
    _LOGGER.info("URI: %s", args.uri)

    # Moonshine supports English plus several other languages depending on model variant
    supported_languages = [
        "en",
        "ar",
        "zh",
        "ja",
        "ko",
        "es",
        "uk",
        "vi",
    ]

    wyoming_info = Info(
        asr=[
            AsrProgram(
                name="moonshine",
                description="Moonshine - fast live speech recognition",
                attribution=Attribution(
                    name="Useful Sensors / Moonshine AI",
                    url="https://github.com/moonshine-ai/moonshine",
                ),
                installed=True,
                version=__version__,
                models=[
                    AsrModel(
                        name=args.model,
                        description=f"Moonshine ONNX ({args.model})",
                        attribution=Attribution(
                            name="Useful Sensors",
                            url="https://github.com/moonshine-ai/moonshine",
                        ),
                        installed=True,
                        languages=supported_languages,
                        version=__version__,
                    )
                ],
            )
        ],
    )

    handler_factory = partial(
        MoonshineEventHandler,
        wyoming_info=wyoming_info,
        model_name=args.model,
    )

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
