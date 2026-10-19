
"""Settings read from the environment (Twelve-Factor III) and validated."""
 
from __future__ import annotations
 
import os
from collections.abc import Mapping
from pathlib import Path
 
from dotenv import dotenv_values
from pydantic import BaseModel, Field, ValidationError, field_validator
 
from assistant_core.errors import ConfigError
 
LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
 
# Settings field -> environment variable. Keep in sync with .env.example.
ENV_VARS = {
    "data_dir": "ASSISTANT_DATA_DIR",
    "llm_provider": "LLM_PROVIDER",
    "llm_api_key": "LLM_API_KEY",
    "credit_rate_vnd": "CREDIT_RATE_VND",
    "retake_multiplier": "RETAKE_MULTIPLIER",
    "max_credits": "MAX_CREDITS",
    "log_level": "LOG_LEVEL",
}
 
 
class Settings(BaseModel):
    """All defaults live here, and only here."""
 
    data_dir: Path = Path("data")
    llm_provider: str = "stub"
    llm_api_key: str | None = Field(default=None, repr=False)  # never printed
    credit_rate_vnd: int = Field(default=450_000, gt=0)
    retake_multiplier: float = Field(default=1.5, ge=0)
    max_credits: int = Field(default=30, gt=0)
    log_level: str = "INFO"
 
    @field_validator("llm_provider")
    @classmethod
    def _normalise_provider(cls, value: str) -> str:
        return value.strip().lower()
 
    @field_validator("log_level")
    @classmethod
    def _check_log_level(cls, value: str) -> str:
        level = value.strip().upper()
        if level not in LOG_LEVELS:
            raise ValueError(f"must be one of {', '.join(LOG_LEVELS)}")
        return level
 
 
def _describe(errors: list) -> str:
    """Turn pydantic errors into 'ENV_VAR: problem' text, without echoing any input value."""
    parts = []
    for err in errors:
        field = err["loc"][0] if err["loc"] else None
        parts.append(f"{ENV_VARS.get(field, field or 'settings')}: {err['msg']}")
    return "; ".join(parts)
 
 
def load_settings(
    env_file: str | os.PathLike[str] | None = ".env",
    environ: Mapping[str, str] | None = None,
) -> Settings:
    """Build Settings from the environment.
 
    environ=None (normal run): values come from the real environment, with the
    .env file as a fallback (real environment variables win, and os.environ is
    not modified). environ=<dict> (tests): only that dict is used, so a test never
    depends on the machine it runs on. Bad or missing values raise ConfigError.
    """
    if environ is None:
        env: dict[str, str | None] = {}
        if env_file:
            env.update(dotenv_values(env_file))
        env.update(os.environ)
    else:
        env = dict(environ)
 
    values = {}
    for field, name in ENV_VARS.items():
        raw = (env.get(name) or "").strip()
        if raw:  # unset or empty -> use the default from Settings
            values[field] = raw
 
    try:
        settings = Settings(**values)
    except ValidationError as exc:
        raise ConfigError(_describe(exc.errors())) from None
 
    if settings.llm_provider != "stub" and not settings.llm_api_key:
        raise ConfigError(f"LLM_API_KEY is required when LLM_PROVIDER={settings.llm_provider!r}")
    return settings

