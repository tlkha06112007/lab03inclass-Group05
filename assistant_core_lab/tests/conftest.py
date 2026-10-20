import pytest
from assistant_core.config import Settings
from assistant_core.knowledge import Rule
from assistant_core.responder import StubLLMResponder


class StubOffice:
    def __init__(self, name: str, room: str, hours: str):
        self.name = name
        self.room = room
        self.hours = hours


class StubOffices:
    # names là set chứa tên văn phòng dạng chữ viết thường
    names = {"academic office", "student office"}

    def find(self, text: str):
        if "academic" in text.lower():
            return StubOffice("Academic Affairs", "A101", "8:00 - 16:30")
        return None


class StubHandbook:
    def search(self, text: str):
        if "thesis" in text.lower() or "rule" in text.lower():
            # Rule thật có đầy đủ id, title, text phục vụ cho TemplateResponder
            return Rule(
                id="R001",
                title="Thesis Regulation",
                text="Students must register their thesis topic by week 4.",
            )
        return None


@pytest.fixture
def service():
    from assistant_core.service import AssistantService

    return AssistantService(
        settings=Settings(
            credit_rate_vnd=450_000,
            retake_multiplier=1.5,
            max_credits=30,
        ),
        offices=StubOffices(),
        handbook=StubHandbook(),
        responder=StubLLMResponder(fail=False),
    )