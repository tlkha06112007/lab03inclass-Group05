from __future__ import annotations

import argparse
import logging
import sys
from time import perf_counter
from typing import TYPE_CHECKING

from pydantic import ValidationError

from assistant_core.errors import ConfigError, DataError, InvalidRequest
from assistant_core.models import Message
from assistant_core.responder import StubLLMResponder

if TYPE_CHECKING:
    from assistant_core.service import AssistantService


def build_service(*args, **kwargs) -> AssistantService:
    # Import here so --help works before the other modules are ready.
    from assistant_core.config import load_settings
    from assistant_core.knowledge import Handbook, OfficeDirectory
    from assistant_core.logging_setup import JsonFormatter
    from assistant_core.service import AssistantService

    settings = load_settings()
    if settings.llm_provider != "stub":
        raise ConfigError("Only the stub provider is supported in Lab 3.")

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger("assistant_core")
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(settings.log_level)
    logger.propagate = False

    offices = OfficeDirectory.from_csv(settings.data_dir / "offices.csv")
    handbook = Handbook.from_json(settings.data_dir / "handbook.json")
    return AssistantService(settings, offices, handbook, StubLLMResponder())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ask about offices, tuition and rules.")
    parser.add_argument("message", nargs="+", help="Question for the assistant")
    args = parser.parse_args(argv)
    text = " ".join(args.message)
    try:
        if not text.strip():
            raise InvalidRequest("Empty message")
        message = Message(text=text)
    except (ValidationError, InvalidRequest):
        print("Error: message must contain 1-2000 characters and not be blank.", file=sys.stderr)
        return 2

    try:
        service = build_service()
    except (ConfigError, DataError, ValueError):
        # Exception details can contain environment values, so do not print them.
        print("Error: check configuration and knowledge files.", file=sys.stderr)
        return 1

    start = perf_counter()
    try:
        response = service.handle(message)
    except InvalidRequest:
        print("Error: request cannot be processed.", file=sys.stderr)
        return 2
    logging.getLogger("assistant_core").info(
        "handled",
        extra={
            "intent": response.intent.value,
            "latency_ms": round((perf_counter() - start) * 1000, 2),
            "session": message.session_id,
            "degraded": response.degraded,
        },
    )
    print(response.answer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
