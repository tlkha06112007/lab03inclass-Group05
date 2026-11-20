from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from time import perf_counter
from typing import TYPE_CHECKING

from pydantic import ValidationError

from assistant_core.errors import ConfigError, DataError, InvalidRequest
from assistant_core.models import Message
from assistant_core.responder import StubLLMResponder

if TYPE_CHECKING:
    from assistant_core.service import AssistantService


def _build_rag(settings):
    """Lab 6: retrieval + LLM answerer. Returns None when there is no knowledge base folder."""
    kb_dir = getattr(settings, "kb_dir", None)
    if kb_dir is None or not Path(kb_dir).exists():
        return None
    from assistant_core.llm import make_llm
    from assistant_core.rag.answerer import RagAnswerer
    from assistant_core.rag.chunker import load_folder
    from assistant_core.rag.index import make_index
    from assistant_core.tools import run_tool_call

    index = make_index(settings.retrieval_kind, load_folder(kb_dir))
    llm = None
    if settings.llm_provider != "template":
        llm = make_llm(
            settings.llm_provider,
            settings.llm_model,
            settings.llm_base_url,
            settings.llm_api_key,
            settings.llm_timeout_s,
        )

    def tool_runner(raw: str) -> str | None:
        return run_tool_call(raw, settings.credit_rate_vnd, settings.retake_multiplier, settings.max_credits)

    return RagAnswerer(
        index, llm, settings.retrieval_min_score, prompt_version=settings.prompt_version, tool_runner=tool_runner
    )


def build_service(*args, **kwargs) -> AssistantService:
    # Import here so --help works before the other modules are ready.
    from assistant_core.config import load_settings
    from assistant_core.knowledge import Handbook, OfficeDirectory
    from assistant_core.logging_setup import JsonFormatter
    from assistant_core.service import AssistantService

    settings = load_settings()
    if settings.llm_provider not in ("stub", "template", "ollama", "openai"):
        raise ConfigError("Unsupported LLM provider.")

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger("assistant_core")
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(settings.log_level)
    logger.propagate = False

    offices = OfficeDirectory.from_csv(settings.data_dir / "offices.csv")
    handbook = Handbook.from_json(settings.data_dir / "handbook.json")
    return AssistantService(settings, offices, handbook, StubLLMResponder(), _build_rag(settings))


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
    for src in response.sources:
        print(f"  source: {src.id} - {src.title}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
