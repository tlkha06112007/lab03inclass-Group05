"""Lab 8 Part E: turn YOUR Week-7 failures into regression tests.

Write at least three tests. Each one must:
  - have a name that says what went wrong, e.g. test_empty_sources_does_not_crash_ui
  - FAIL on the old code (check by temporarily undoing your fix), and PASS after the fix.
Use the fixtures `service`, `settings` from conftest.py, or build a TestClient like tests/test_security.py.
"""
import inspect
from pathlib import Path

from assistant_core.models import Message
from assistant_core.service import AssistantService
from ui.logic import format_sources


def test_example_greeting_still_works(service):
    """Example: a control case that must never break."""
    assert "Hello" in service.handle(Message(text="hi")).answer


def test_empty_sources_does_not_crash_ui():
    """UI must show nothing (not crash) when the answer has no sources."""
    assert format_sources([]) == ""


def test_sources_use_em_dash_not_hyphen():
    """Bug: a hyphen was typed instead of the em dash, so the sources line did not match the spec."""
    assert format_sources([{"id": "S26#1", "title": "1 Library borrowing"}]) == "Sources: S26#1 — 1 Library borrowing"


ROOT = Path(__file__).resolve().parents[1]


def test_service_keeps_responder_and_rag_arguments():
    """Bug: AssistantService lost its `responder` argument when `rag=None` was added."""
    params = list(inspect.signature(AssistantService.__init__).parameters)
    assert params[1:] == ["settings", "offices", "handbook", "responder", "rag"]


def test_requirements_keep_sqlmodel_and_streamlit():
    """Bug: a merge conflict nearly dropped sqlmodel (needed by db.py) when streamlit was added."""
    text = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert "sqlmodel==" in text and "streamlit==" in text
