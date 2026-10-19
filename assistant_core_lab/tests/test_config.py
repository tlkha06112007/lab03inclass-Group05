from pathlib import Path
 
import pytest
from dotenv import dotenv_values
 
from assistant_core.config import ENV_VARS, Settings, load_settings
from assistant_core.errors import ConfigError
 
ROOT = Path(__file__).resolve().parents[1]
 
 
def test_defaults_when_environment_is_empty():
    s = load_settings(environ={})
    assert s == Settings()
    assert s.data_dir == Path("data")
    assert s.llm_provider == "stub"
    assert s.llm_api_key is None
    assert s.credit_rate_vnd == 450_000
    assert s.retake_multiplier == 1.5
    assert s.max_credits == 30
    assert s.log_level == "INFO"
 
 
def test_reads_values_from_environ():
    s = load_settings(
        environ={
            "ASSISTANT_DATA_DIR": "/srv/data",
            "CREDIT_RATE_VND": "500000",
            "RETAKE_MULTIPLIER": "2",
            "MAX_CREDITS": "24",
            "LOG_LEVEL": "debug",
        }
    )
    assert s.data_dir == Path("/srv/data")
    assert s.credit_rate_vnd == 500_000
    assert s.retake_multiplier == 2.0
    assert s.max_credits == 24
    assert s.log_level == "DEBUG"  # normalised
 
 
def test_empty_value_falls_back_to_default():
    s = load_settings(environ={"LLM_API_KEY": "", "MAX_CREDITS": "  "})
    assert s.llm_api_key is None
    assert s.max_credits == 30
 
 
def test_real_provider_requires_api_key():
    with pytest.raises(ConfigError, match="LLM_API_KEY"):
        load_settings(environ={"LLM_PROVIDER": "openai"})
 
 
def test_real_provider_with_api_key_is_ok():
    s = load_settings(environ={"LLM_PROVIDER": "openai", "LLM_API_KEY": "sk-abc"})
    assert s.llm_provider == "openai"
    assert s.llm_api_key == "sk-abc"
 
 
def test_provider_is_case_insensitive():
    assert load_settings(environ={"LLM_PROVIDER": "STUB"}).llm_provider == "stub"
 
 
@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("CREDIT_RATE_VND", "abc"),
        ("CREDIT_RATE_VND", "0"),
        ("CREDIT_RATE_VND", "-1"),
        ("MAX_CREDITS", "1.5"),
        ("MAX_CREDITS", "0"),
        ("RETAKE_MULTIPLIER", "x"),
        ("RETAKE_MULTIPLIER", "-0.5"),
        ("LOG_LEVEL", "LOUD"),
    ],
)
def test_invalid_values_raise_config_error(name, value):
    with pytest.raises(ConfigError, match=name):
        load_settings(environ={name: value})
 
 
def test_api_key_never_appears_in_repr_or_errors():
    secret = "sk-very-secret-123"
    s = load_settings(environ={"LLM_PROVIDER": "openai", "LLM_API_KEY": secret})
    assert secret not in repr(s)
    assert secret not in str(s)
 
    with pytest.raises(ConfigError) as info:
        load_settings(environ={"LLM_API_KEY": secret, "CREDIT_RATE_VND": "abc"})
    assert secret not in str(info.value)
 
 
def test_env_file_is_read_and_real_environment_wins(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("MAX_CREDITS=12\nCREDIT_RATE_VND=600000\n", encoding="utf-8")
    monkeypatch.delenv("MAX_CREDITS", raising=False)
    monkeypatch.setenv("CREDIT_RATE_VND", "700000")
 
    s = load_settings(env_file=str(env_file))
    assert s.max_credits == 12  # from the file
    assert s.credit_rate_vnd == 700_000  # os.environ wins over the file
 
 
def test_loading_env_file_does_not_modify_os_environ(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("MAX_CREDITS=12\n", encoding="utf-8")
    monkeypatch.delenv("MAX_CREDITS", raising=False)
    load_settings(env_file=str(env_file))
    import os
 
    assert "MAX_CREDITS" not in os.environ
 
 
def test_missing_env_file_is_fine(tmp_path, monkeypatch):
    for name in ENV_VARS.values():
        monkeypatch.delenv(name, raising=False)
    assert load_settings(env_file=str(tmp_path / "nope.env")) == Settings()
 
 
def test_env_example_lists_all_seven_variables():
    example = dotenv_values(ROOT / ".env.example")
    assert set(example) == set(ENV_VARS.values())
    assert len(example) == 7
 
 
def test_env_example_matches_the_defaults():
    example = dotenv_values(ROOT / ".env.example")
    assert load_settings(environ={k: v or "" for k, v in example.items()}) == Settings()
 
 
def test_dotenv_is_git_ignored():
    lines = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert ".env" in lines