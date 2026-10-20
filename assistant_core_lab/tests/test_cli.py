import json
import logging
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock

import pytest

from assistant_core import __main__ as cli
from assistant_core.errors import ConfigError, DataError, InvalidRequest
from assistant_core.models import Intent, Response
from assistant_core.responder import StubLLMResponder


@pytest.fixture
def dependencies(monkeypatch):
    """Mock teammate modules only inside each test, using the PDF interfaces."""

    class JsonFormatter(logging.Formatter):
        def format(self, record):
            data = {"level": record.levelname, "msg": record.getMessage()}
            for key in ("intent", "latency_ms", "session", "degraded"):
                if hasattr(record, key):
                    data[key] = getattr(record, key)
            return json.dumps(data)

    settings = SimpleNamespace(data_dir=Path("data"), llm_provider="stub", log_level="INFO")
    service = Mock()
    service.handle.return_value = Response(answer="Hello!", intent=Intent.GREETING)
    exports = {
        "config": {"load_settings": Mock(return_value=settings)},
        "knowledge": {"OfficeDirectory": Mock(), "Handbook": Mock()},
        "logging_setup": {"JsonFormatter": JsonFormatter},
        "service": {"AssistantService": Mock(return_value=service)},
    }
    for name, attributes in exports.items():
        module = ModuleType(f"assistant_core.{name}")
        module.__dict__.update(attributes)
        monkeypatch.setitem(sys.modules, module.__name__, module)
    logger = logging.getLogger("assistant_core")
    old_handlers, old_level, old_propagate = logger.handlers[:], logger.level, logger.propagate
    yield settings, service, exports
    for handler in logger.handlers:
        if handler not in old_handlers:
            handler.close()
    logger.handlers[:] = old_handlers
    logger.setLevel(old_level)
    logger.propagate = old_propagate


def test_build_service_wires_dependencies(dependencies):
    settings, service, modules = dependencies
    assert cli.build_service() is service
    modules["knowledge"]["OfficeDirectory"].from_csv.assert_called_once_with(settings.data_dir / "offices.csv")
    modules["knowledge"]["Handbook"].from_json.assert_called_once_with(settings.data_dir / "handbook.json")
    args = modules["service"]["AssistantService"].call_args.args
    assert args[:3] == (
        settings,
        modules["knowledge"]["OfficeDirectory"].from_csv.return_value,
        modules["knowledge"]["Handbook"].from_json.return_value,
    )
    assert isinstance(args[3], StubLLMResponder)


def test_answer_stdout_and_safe_log_stderr(dependencies, capsys, monkeypatch):
    _, service, _ = dependencies
    monkeypatch.setenv("LLM_API_KEY", "private-test-key")
    assert cli.main(["hello", "private-message"]) == 0
    message = service.handle.call_args.args[0]
    assert message.text == "hello private-message"
    captured = capsys.readouterr()
    assert captured.out == "Hello!\n"
    event = json.loads(captured.err)
    assert event["intent"] == "greeting"
    assert event["msg"] == "handled"
    assert event["degraded"] is False
    assert event["latency_ms"] >= 0
    assert "private-message" not in captured.err
    assert "private-test-key" not in captured.err


def test_degraded_response_is_logged(dependencies, capsys):
    _, service, _ = dependencies
    service.handle.return_value = Response(answer="Rule text", intent=Intent.RULE, degraded=True)
    assert cli.main(["exam absence"]) == 0
    captured = capsys.readouterr()
    assert captured.out == "Rule text\n"
    assert json.loads(captured.err)["degraded"] is True


@pytest.mark.parametrize("text", ["", "   ", "x" * 2001])
def test_invalid_message_is_rejected_before_startup(text, monkeypatch, capsys):
    build = Mock()
    monkeypatch.setattr(cli, "build_service", build)
    assert cli.main([text]) == 2
    build.assert_not_called()
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Error:" in captured.err
    assert "x" * 2001 not in captured.err


@pytest.mark.parametrize("error", [ConfigError, DataError, ValueError])
def test_startup_error_does_not_leak_details(error, monkeypatch, capsys):
    monkeypatch.setattr(cli, "build_service", Mock(side_effect=error("private-test-key")))
    assert cli.main(["hello"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "check configuration" in captured.err
    assert "private-test-key" not in captured.err


def test_unsupported_provider_fails(dependencies, capsys):
    settings, service, _ = dependencies
    settings.llm_provider = "not-implemented"
    assert cli.main(["hello"]) == 1
    service.handle.assert_not_called()
    assert capsys.readouterr().out == ""


def test_invalid_request_has_nonzero_exit(dependencies, capsys):
    _, service, _ = dependencies
    service.handle.side_effect = InvalidRequest("private question")
    assert cli.main(["fee"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "private question" not in captured.err


@pytest.mark.parametrize(("argv", "code"), [(["--help"], 0), ([], 2)])
def test_argument_parser_does_not_build_service(argv, code, monkeypatch):
    build = Mock()
    monkeypatch.setattr(cli, "build_service", build)
    with pytest.raises(SystemExit) as exc:
        cli.main(argv)
    assert exc.value.code == code
    build.assert_not_called()
