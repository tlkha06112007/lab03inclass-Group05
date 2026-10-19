import pytest
from pydantic import ValidationError

from assistant_core.errors import InvalidRequest
from assistant_core.models import Intent, Message
from assistant_core.responder import StubLLMResponder


def test_greeting(service):
    """Test chức năng chào hỏi"""
    res = service.handle(Message(text="hello"))
    assert res.intent == Intent.GREETING
    assert "Hello!" in res.answer


def test_fee_calculation(service):
    """Test học phí với câu hỏi chứa từ 'tuition' (21 tín chỉ * 450,000 = 9,450,000 VND)"""
    res = service.handle(Message(text="What is the tuition for 21 credits?"))
    assert res.intent == Intent.FEE
    assert res.answer == "Your tuition is 9,450,000 VND."


def test_fee_edge_cases(service):
    """Test các trường hợp 0 tín chỉ và vượt quá 30 tín chỉ"""
    res_zero = service.handle(Message(text="What is the tuition for 0 credits?"))
    assert res_zero.intent == Intent.FEE
    assert res_zero.answer == "How many credits?"

    res_max = service.handle(Message(text="What is the tuition for 35 credits?"))
    assert res_max.intent == Intent.FEE
    assert res_max.answer == "too many credits"


def test_office_lookup(service):
    """Test tìm kiếm thông tin văn phòng"""
    res = service.handle(Message(text="Where is academic office?"))
    assert res.intent == Intent.OFFICE
    assert "A101" in res.answer


def test_unknown_intent(service):
    """Test câu hỏi không thuộc intent nào"""
    res = service.handle(Message(text="random unknown query xyz"))
    assert res.intent == Intent.UNKNOWN
    assert res.answer == "Sorry, I don't know that yet."


def test_empty_message_validation_error():
    """Chuỗi rỗng '' bị Pydantic ValidationError chặn ngay từ khởi tạo Message"""
    with pytest.raises(ValidationError):
        Message(text="")


def test_whitespace_message_invalid_request(service):
    """Chuỗi chỉ có khoảng trắng '   ' đi qua Message nhưng bị handle() chặn bằng InvalidRequest"""
    msg = Message(text="   ")
    with pytest.raises(InvalidRequest):
        service.handle(msg)


def test_fallback_when_provider_fails(service):
    """Test fallback PDF khi LLM Provider gặp sự cố"""
    service.responder = StubLLMResponder(fail=True)
    r = service.handle(Message(text="thesis registration credits"))

    assert r.degraded is True
    assert r.sources is not None
    assert len(r.sources) > 0