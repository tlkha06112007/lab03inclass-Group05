import pytest
from assistant_core.service import AssistantService


class StubSettings:
    tuition_per_credit = 630_000  # Ví dụ 15 tín chỉ = 9,450,000 VND


class StubOffice:
    def __init__(self, name, room, hours):
        self.name = name
        self.room = room
        self.hours = hours


class StubOffices:
    names = ["Academic Affairs", "Student Affairs"]

    def find(self, text: str):
        if "academic" in text.lower():
            return StubOffice("Academic Affairs", "A101", "8:00 - 16:30")
        return None


class StubRule:
    def __init__(self, rule_id, title):
        self.id = rule_id
        self.title = title


class StubHandbook:
    def search(self, text: str):
        if "thesis" in text.lower() or "rule" in text.lower():
            return StubRule("R001", "Thesis Regulation")
        return None


class StubLLMResponder:
    def __init__(self, fail=False):
        self.fail = fail

    def explain(self, text, rule):
        if self.fail:
            from assistant_core.errors import ProviderError
            raise ProviderError("LLM Provider Timeout")
        return f"LLM explanation for {rule.title}"


@pytest.fixture
def service():
    """[Part B.3] Fixture khởi tạo AssistantService với các Stub dependencies"""
    return AssistantService(
        settings=StubSettings(),
        offices=StubOffices(),
        handbook=StubHandbook(),
        responder=StubLLMResponder(fail=False)
    )