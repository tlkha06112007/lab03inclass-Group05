from assistant_core.models import Intent
from assistant_core.router import route

OFFICES = {"training office", "library"}


def test_route_greeting():
    assert route("hello", OFFICES) == Intent.GREETING


def test_route_fee():
    assert route("what is the tuition fee?", OFFICES) == Intent.FEE


def test_route_office():
    assert route("where is the training office?", OFFICES) == Intent.OFFICE


def test_route_rule():
    assert route("random unknown question", OFFICES) == Intent.RULE