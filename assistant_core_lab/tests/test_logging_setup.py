import json
import logging

import pytest

from assistant_core.config import Settings
from assistant_core.logging_setup import LOGGER_NAME, JsonFormatter, setup_logging


@pytest.fixture(autouse=True)
def clean_logger():
    logger = logging.getLogger(LOGGER_NAME)
    saved_handlers, saved_level = list(logger.handlers), logger.level
    logger.handlers.clear()
    yield logger
    logger.handlers[:] = saved_handlers
    logger.setLevel(saved_level)


def make_record(**extra):
    record = logging.LogRecord("assistant_core", logging.INFO, __file__, 1, "handled", None, None)
    for key, value in extra.items():
        setattr(record, key, value)
    return record


def test_formatter_outputs_valid_json_with_extras():
    line = JsonFormatter().format(make_record(intent="fee", latency_ms=0.1, session="local", degraded=False))
    assert json.loads(line) == {
        "level": "INFO",
        "logger": "assistant_core",
        "msg": "handled",
        "intent": "fee",
        "latency_ms": 0.1,
        "session": "local",
        "degraded": False,
    }


def test_formatter_skips_missing_extras():
    data = json.loads(JsonFormatter().format(make_record(intent="rule")))
    assert data["intent"] == "rule"
    assert "latency_ms" not in data


def test_formatter_keeps_vietnamese_text_readable():
    record = make_record()
    record.msg = "xin chào"
    assert "xin chào" in JsonFormatter().format(record)


def test_logs_go_to_stderr_not_stdout(capsys):
    setup_logging(Settings())
    logging.getLogger(LOGGER_NAME).info("handled", extra={"intent": "fee", "degraded": False})
    out, err = capsys.readouterr()
    assert out == ""
    assert json.loads(err)["intent"] == "fee"


def test_level_comes_from_settings(capsys):
    setup_logging(Settings(log_level="WARNING"))
    log = logging.getLogger(LOGGER_NAME)
    log.info("hidden")
    log.warning("shown")
    lines = capsys.readouterr().err.strip().splitlines()
    assert [json.loads(line)["msg"] for line in lines] == ["shown"]


def test_calling_twice_does_not_duplicate_handlers(capsys):
    setup_logging(Settings())
    logger = setup_logging(Settings())
    assert len(logger.handlers) == 1
    logger.info("once")
    assert len(capsys.readouterr().err.strip().splitlines()) == 1


def test_second_call_applies_new_level():
    setup_logging(Settings(log_level="INFO"))
    logger = setup_logging(Settings(log_level="DEBUG"))
    assert logger.level == logging.DEBUG
