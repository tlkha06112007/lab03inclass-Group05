"""Lab 8 Part E: turn YOUR Week-7 failures into regression tests.

Write at least three tests. Each one must:
  - have a name that says what went wrong, e.g. test_empty_sources_does_not_crash_ui
  - FAIL on the old code (check by temporarily undoing your fix), and PASS after the fix.
Use the fixtures `service`, `settings` from conftest.py, or build a TestClient like tests/test_security.py.
"""
from assistant_core.models import Message
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
