import pytest
from pydantic import ValidationError

from assistant_core.errors import InvalidRequest
from assistant_core.models import Intent, Message
from assistant_core.responder import StubLLMResponder


def test_greeting(service):
    """Test chức năng chào hỏi."""
    res = service.handle(Message(text="hello"))
    assert res.intent == Intent.GREETING
    assert "Hello!" in res.answer


def test_fee_calculation(service):
    """Test học phí cho 18 tín chỉ + 2 học lại (18*450k + 2*450k*1.5 = 9,450,000 VND)."""
    res = service.handle(Message(text="tuition for 18 credits and 2 retake"))
    assert res.intent == Intent.FEE
    assert res.answer == "Your tuition is 9,450,000 VND."


def test_fee_edge_cases(service):
    """Test trường hợp không nhập số tín chỉ và vượt quá số tín chỉ tối đa (30)."""
    # Không nhập số tín chỉ
    res_no_credits = service.handle(Message(text="what is the tuition fee?"))
    assert res_no_credits.intent == Intent.FEE
    assert res_no_credits.answer == "How many credits?"

    # Vượt quá 30 tín chỉ
    res_too_many = service.handle(Message(text="tuition for 35 credits"))
    assert res_too_many.intent == Intent.FEE
    assert "between 1 and 30" in res_too_many.answer


def test_office_lookup(service):
    """Test tìm kiếm thông tin văn phòng."""
    res = service.handle(Message(text="Where is academic office?"))
    assert res.intent == Intent.OFFICE
    assert "A101" in res.answer


def test_unknown_intent(service):
    """Test câu hỏi không khớp quy định nào."""
    res = service.handle(Message(text="random unknown query xyz"))
    assert res.answer == "Sorry, I don't know that yet."


def test_empty_message_validation_error():
    """Chuỗi rỗng '' bị Pydantic ValidationError chặn ngay khi khởi tạo Message."""
    with pytest.raises(ValidationError):
        Message(text="")


def test_whitespace_message_invalid_request(service):
    """Chuỗi chỉ chứa khoảng trắng '   ' bị handle() chặn bằng InvalidRequest."""
    msg = Message(text="   ")
    with pytest.raises(InvalidRequest):
        service.handle(msg)


def test_fallback_when_provider_fails(service):
    """Test fallback PDF khi LLM Provider gặp sự cố."""
    service.responder = StubLLMResponder(fail=True)
    r = service.handle(Message(text="thesis registration credits"))

    assert r.degraded is True
    assert r.sources is not None
    assert len(r.sources) > 0
    assert r.sources[0].id == "R001"