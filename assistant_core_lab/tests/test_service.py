import pytest
from assistant_core.errors import ValidationError
from assistant_core.models import Intent, Message
from tests.conftest import StubLLMResponder


def test_greeting(service):
    """Test chức năng chào hỏi"""
    res = service.handle(Message(text="hello"))
    assert res.intent == Intent.GREETING
    assert "Hello!" in res.answer


def test_fee_calculation(service):
    """Test tính học phí (15 credits * 630,000 = 9,450,000 VND)"""
    res = service.handle(Message(text="I register 15 credits"))
    assert res.intent == Intent.FEE
    assert res.answer == "Your tuition is 9,450,000 VND."


def test_office_lookup(service):
    """Test tìm kiếm thông tin văn phòng"""
    res = service.handle(Message(text="Where is academic office?"))
    assert res.intent == Intent.OFFICE
    assert "A101" in res.answer


def test_unknown_intent(service):
    """Test xử lý câu hỏi không xác định / không tìm thấy rule"""
    res = service.handle(Message(text="random unknown query xyz"))
    assert res.intent == Intent.UNKNOWN
    assert res.answer == "Sorry, I don't know that yet."


def test_empty_message_raises_validation_error(service):
    """Test tin nhắn rỗng hoặc toàn khoảng trắng phải raise ValidationError"""
    with pytest.raises(ValidationError):
        service.handle(Message(text=""))

    with pytest.raises(ValidationError):
        service.handle(Message(text="   "))


def test_fallback_when_provider_fails(service):
    """[Step 9] Test fallback PDF cho sẵn khi LLM Provider bị lỗi"""
    service.responder = StubLLMResponder(fail=True)
    r = service.handle(Message(text="thesis registration credits"))
    
    assert r.degraded is True
    assert r.sources is not None
    assert len(r.sources) > 0