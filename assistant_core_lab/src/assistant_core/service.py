import logging
import time
from collections.abc import Callable

from assistant_core.errors import InvalidRequest, ProviderError
from assistant_core.models import Intent, Message, Response, Source
from assistant_core.responder import TemplateResponder
from assistant_core.router import route
from assistant_core.tools import parse_credits

log = logging.getLogger(__name__)


class AssistantService:
    def __init__(self, settings, offices, handbook, responder):
        self.settings = settings
        self.offices = offices
        self.handbook = handbook
        self.responder = responder
        self.fallback = TemplateResponder()

        # Dùng dict[...] và Callable từ collections.abc cho Ruff
        self._intent_handlers: dict[Intent, Callable[[Message], Response]] = {
            Intent.GREETING: self._handle_greeting,
            Intent.FEE: self._handle_fee,
            Intent.OFFICE: self._handle_office,
            Intent.RULE: self._handle_rule,
            Intent.UNKNOWN: self._handle_unknown,
        }

    def handle(self, msg: Message) -> Response:
        # Bẫy tin nhắn chỉ chứa khoảng trắng
        if not msg.text.strip():
            raise InvalidRequest("Message text cannot be empty or whitespace.")

        start = time.perf_counter()

        intent = route(msg.text, self.offices.names)
        handler = self._intent_handlers.get(intent, self._handle_unknown)

        response = handler(msg)

        # Ghi log kèm extra theo đúng thiết kế của logging_setup.py
        log.info(
            "handled",
            extra={
                "intent": response.intent.value,
                "latency_ms": round((time.perf_counter() - start) * 1000, 1),
                "session": msg.session_id,
                "degraded": response.degraded,
            },
        )

        return response

    def _handle_greeting(self, msg: Message) -> Response:
        return Response(
            answer="Hello! I can help with offices, fees and rules.",
            intent=Intent.GREETING,
        )

    def _fee(self, text: str) -> Response:
        credits = parse_credits(text)

        # Khi số tín chỉ = 0
        if credits == 0:
            return Response(answer="How many credits?", intent=Intent.FEE)

        # Khi số tín chỉ vượt max_credits (mặc định 30)
        max_credits = getattr(self.settings, "max_credits", 30)
        if credits > max_credits:
            return Response(answer="too many credits", intent=Intent.FEE)

        # Tính học phí theo credit_rate_vnd
        rate = getattr(self.settings, "credit_rate_vnd", 450_000)
        total = credits * rate

        return Response(
            answer=f"Your tuition is {total:,} VND.",
            intent=Intent.FEE,
        )

    def _handle_fee(self, msg: Message) -> Response:
        return self._fee(msg.text)

    def _handle_office(self, msg: Message) -> Response:
        o = self.offices.find(msg.text)
        if o:
            answer = f"{o.name}: room {o.room}, open {o.hours}."
        else:
            answer = "Office not found."
        return Response(answer=answer, intent=Intent.OFFICE)

    def _handle_rule(self, msg: Message) -> Response:
        return self._rule(msg.text)

    def _handle_unknown(self, msg: Message) -> Response:
        return Response(
            answer="Sorry, I don't know that yet.",
            intent=Intent.UNKNOWN,
        )

    def _rule(self, text: str) -> Response:
        rule = self.handbook.search(text)
        if rule is None:
            return Response(
                answer="Sorry, I don't know that yet.",
                intent=Intent.UNKNOWN,
            )

        sources = [Source(id=rule.id, title=rule.title)]

        try:
            return Response(
                answer=self.responder.explain(text, rule),
                intent=Intent.RULE,
                sources=sources,
            )
        except ProviderError:
            log.warning("provider failed; using template fallback")
            answer = self.fallback.explain(text, rule)
            return Response(
                answer=answer,
                intent=Intent.RULE,
                sources=sources,
                degraded=True,
            )