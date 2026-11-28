from fastapi.testclient import TestClient

from assistant_api.main import create_app


def test_whitespace_only_message_is_rejected_with_422(settings, service):
    """Failure: a message made only of spaces crashed the API with a 500."""
    client = TestClient(create_app(settings, service), raise_server_exceptions=False)
    assert client.post("/v1/chat", json={"message": "   "}).status_code == 422