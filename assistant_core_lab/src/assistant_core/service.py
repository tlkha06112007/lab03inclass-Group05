import logging
import time
from collections.abc import Callable

from assistant_core.errors import InvalidRequest, ProviderError
from assistant_core.models import Intent, Message, Response, Source
from assistant_core.responder import TemplateResponder
from assistant_core.router import route
from assistant_core.tools import parse_credits, tuition

log = logging.getLogger(__name__)


class AssistantService:
    def __init__(self, settings, offices, handbook, responder):
        self.settings = settings
        self.offices = offices
        self.handbook = handbook
        self.responder = responder
        self.fallback = TemplateResponder()

        self._intent_handlers: dict[Intent, Callable[[Message], Response]] = {
            Intent.GREETING: self._handle_greeting,
            Intent.FEE: self._handle_fee,
            Intent.OFFICE: self._handle_office,
            Intent.RULE: self._handle_rule,
            Intent.UNKNOWN: self._handle_unknown,
        }

    def handle(self, msg: Message) -> Response:
        # Chặn tin nhắn chỉ chứa khoảng trắng bằng InvalidRequest từ errors.py
        if not msg.text.strip():
            raise InvalidRequest("Message text cannot be empty or whitespace.")

        start = time.perf_counter()

        intent = route(msg.text, self.offices.names)
        handler = self._intent_handlers.get(intent, self._handle_unknown)

        response = handler(msg)

        # Ghi log kèm extra theo thiết kế logging
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
        """Sử dụng parse_credits và tuition từ tools.py cùng settings thật."""
        try:
            credits, retake = parse_credits(text)
            total = tuition(
                credits=credits,
                retake=retake,
                rate=self.settings.credit_rate_vnd,
                retake_multiplier=self.settings.retake_multiplier,
                max_credits=self.settings.max_credits,
            )
            return Response(
                answer=f"Your tuition is {total:,} VND.",
                intent=Intent.FEE,
            )
        except InvalidRequest as exc:
            return Response(
                answer=str(exc),
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
