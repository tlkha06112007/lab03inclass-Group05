import pytest
from pydantic import ValidationError

from assistant_core.models import Intent, Message, Response


def test_message_rejects_empty_text():
    with pytest.raises(ValidationError):
        Message(text="")


def test_message_is_frozen():
    msg = Message(text="xin chào")
    with pytest.raises(ValidationError):
        msg.text = "khác"


def test_response_sources_not_shared():
    a = Response(answer="a", intent=Intent.UNKNOWN)
    b = Response(answer="b", intent=Intent.UNKNOWN)
    assert a.sources is not b.sources
