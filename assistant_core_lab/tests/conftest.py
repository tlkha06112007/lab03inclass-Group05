import pytest
from assistant_core.models import Rule
from assistant_core.responder import StubLLMResponder


class Settings:
    def __init__(
        self,
        credit_rate_vnd: int = 450_000,
        retake_multiplier: float = 1.5,
        max_credits: int = 30,
    ):
        self.credit_rate_vnd = credit_rate_vnd
        self.retake_multiplier = retake_multiplier
        self.max_credits = max_credits


class StubOffice:
    def __init__(self, name, room, hours):
        self.name = name
        self.room = room
        self.hours = hours


class StubOffices:
    # Tên văn phòng dạng chữ viết thường
    names = ["academic office", "student office"]

    def find(self, text: str):
        if "academic" in text.lower():
            return StubOffice("Academic Affairs", "A101", "8:00 - 16:30")
        return None


class StubHandbook:
    def search(self, text: str):
        if "thesis" in text.lower() or "rule" in text.lower():
            # Sử dụng Rule thật có đầy đủ id, title, text để phục vụ TemplateResponder
            return Rule(
                id="R001",
                title="Thesis Regulation",
                text="Thesis registration rules and details.",
            )
        return None


@pytest.fixture
def service():
    from assistant_core.service import AssistantService

    return AssistantService(
        settings=Settings(credit_rate_vnd=450_000),
        offices=StubOffices(),
        handbook=StubHandbook(),
        responder=StubLLMResponder(fail=False),
    )