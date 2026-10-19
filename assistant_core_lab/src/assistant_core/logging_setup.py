"""Structured JSON logging. Logs go to stderr; answers go to stdout.
 
Never log the API key or the full user message: log intent, latency, session
and whether a fallback was used.
"""
 
from __future__ import annotations
 
import json
import logging
import sys
 
from assistant_core.config import Settings
 
LOGGER_NAME = "assistant_core"
EXTRA_FIELDS = ("intent", "latency_ms", "session", "degraded")
 
 
class JsonFormatter(logging.Formatter):
    """One JSON object per log line."""
 
    def format(self, record: logging.LogRecord) -> str:
        data = {"level": record.levelname, "logger": record.name, "msg": record.getMessage()}
        for key in EXTRA_FIELDS:
            if hasattr(record, key):
                data[key] = getattr(record, key)
        return json.dumps(data, ensure_ascii=False)
 
 
def setup_logging(settings: Settings) -> logging.Logger:
    """Send JSON logs to stderr at settings.log_level. Safe to call more than once."""
    logger = logging.getLogger(LOGGER_NAME)
    for handler in list(logger.handlers):
        if getattr(handler, "_assistant_core", False):
            logger.removeHandler(handler)  # replace ours, leave handlers added by others
 
    handler = logging.StreamHandler(sys.stderr)
    handler._assistant_core = True  # type: ignore[attr-defined]
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    logger.setLevel(settings.log_level)  # already validated by Settings
    return logger