from dataclasses import dataclass

import pytest

from assistant_core.errors import ProviderError
from assistant_core.responder import Responder, StubLLMResponder, TemplateResponder


@dataclass(frozen=True)
class RuleFixture:
    """The Rule contract from the PDF; knowledge.py belongs to member 3."""

    id: str
    title: str
    text: str


@pytest.fixture
def rule():
    return RuleFixture("H26-7.2", "Exam absence", "Submit evidence within 3 working days.")


def test_template_keeps_rule_text(rule):
    responder: Responder = TemplateResponder()
    assert responder.explain("When?", rule) == "Exam absence: Submit evidence within 3 working days."


def test_stub_is_deterministic(rule):
    responder: Responder = StubLLMResponder()
    expected = "Based on 'Exam absence': Submit evidence within 3 working days."
    for _ in range(10):
        assert responder.explain("When?", rule) == expected


def test_stub_failure_can_be_used_by_service_fallback(rule):
    responder = StubLLMResponder(fail=True)
    for _ in range(2):
        with pytest.raises(ProviderError, match="stub provider unavailable"):
            responder.explain("private question", rule)


def test_responder_does_not_print_or_log_user_data(rule, capsys, caplog, monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "private-test-key")
    with caplog.at_level("DEBUG"):
        for responder in (TemplateResponder(), StubLLMResponder()):
            answer = responder.explain("private question", rule)
            assert "private question" not in answer
    captured = capsys.readouterr()
    assert captured.out == captured.err == caplog.text == ""
