import logging
import time
from typing import Dict, Callable

from assistant_core.errors import ProviderError, ValidationError
from assistant_core.models import Intent, Message, Response, Source
from assistant_core.router import route
from assistant_core.tools import parse_credits
from assistant_core.responder import TemplateResponder

# [Step 9] Thêm logger
log = logging.getLogger(__name__)


class AssistantService:
    def __init__(self, settings, offices, handbook, responder):
        self.settings = settings
        self.offices = offices
        self.handbook = handbook
        self.responder = responder
        self.fallback = TemplateResponder()

        # Ánh xạ Intent tới hàm xử lý tương ứng
        self._intent_handlers: Dict[Intent, Callable[[Message], Response]] = {
            Intent.GREETING: self._handle_greeting,
            Intent.FEE: self._handle_fee,
            Intent.OFFICE: self._handle_office,
            Intent.RULE: self._handle_rule,
            Intent.UNKNOWN: self._handle_unknown,
        }

    def handle(self, msg: Message) -> Response:
        # [Step 9] Kiểm tra tin nhắn rỗng -> raise ValidationError
        if not msg.text or not msg.text.strip():
            raise ValidationError("Message text cannot be empty.")

        # Đo latency bằng time.perf_counter()
        start_time = time.perf_counter()

        intent = route(msg.text, self.offices.names)
        handler = self._intent_handlers.get(intent, self._handle_unknown)

        response = handler(msg)
        
        # Gán latency_ms vào response
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        response.latency_ms = elapsed_ms

        return response

    def _handle_greeting(self, msg: Message) -> Response:
        return Response(
            answer="Hello! I can help with offices, fees and rules.",
            intent=Intent.GREETING
        )

    def _fee(self, text: str) -> Response:
        """[Step 9] Tự viết _fee(): dùng parse_credits và tuition từ settings"""
        credits = parse_credits(text)
        # Tính toán học phí dựa trên số tín chỉ và giá tiền mỗi tín chỉ từ settings
        total_tuition = credits * self.settings.tuition_per_credit
        # Trả về chuỗi theo đúng format yêu cầu: "Your tuition is 9,450,000 VND."
        formatted_tuition = f"{total_tuition:,}"
        return Response(
            answer=f"Your tuition is {formatted_tuition} VND.",
            intent=Intent.FEE
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
            intent=Intent.UNKNOWN
        )

    def _rule(self, text: str) -> Response:
        rule = self.handbook.search(text)
        if rule is None:
            return Response(
                answer="Sorry, I don't know that yet.",
                intent=Intent.UNKNOWN
            )

        sources = [Source(id=rule.id, title=rule.title)]

        try:
            return Response(
                answer=self.responder.explain(text, rule),
                intent=Intent.RULE,
                sources=sources
            )
        except ProviderError:
            log.warning("provider failed; using template fallback")
            answer = self.fallback.explain(text, rule)
            return Response(
                answer=answer,
                intent=Intent.RULE,
                sources=sources,
                degraded=True
            )