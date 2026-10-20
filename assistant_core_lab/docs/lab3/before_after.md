# Before / After maintainability

| Question | Monolith | assistant_core |
|---|---|---|
| Places to change the credit rate | 1 constant in code (`RATE = 450000`) | 1 variable (`CREDIT_RATE_VND`); `.env.example` documents it and `config.py` only holds the default (450_000) |
| Tests run offline and deterministically? | no (`random.random() < 0.1` in `llm()` makes the call fail at random) | yes (`pytest -q` run twice: 83 passed both times; the stub provider only fails when told to) |
| Missing handbook.json | prints "could not load handbook" and continues silently | stops at startup with a clear message (`Error: check configuration and knowledge files.`) |
| Secret printed or logged? | yes (`llm()` prints `API_KEY` when `DEBUG = True`, the default) | no (a log line only has `intent`, `latency_ms`, `session` and `degraded`; no key and no message text) |
| Module-level globals | 9 (3 mutable: history, offices, handbook) | 6 (1 mutable: `ENV_VARS` dict in `config.py`) |
| Bare `except:` | 3 | 0 |
| Longest function (lines) | 56 (`handle`) | 37 (`main` in `__main__.py`); in `service.py` the longest is `_rule` (25) |
| Swap the LLM without touching the service? | no (`llm()` is called directly inside `handle()`) | yes (`Responder` Protocol in `responder.py`, injected into `AssistantService.__init__`) |

How I measured: a small AST script for module-level globals, bare `except:` and function length (run on the monolith and on `src/assistant_core`); `pytest -q` run twice for determinism; `ruff check .` and `ruff check --select BLE .` both pass; `python -m assistant_core "hi"` to inspect the log; `Select-String "450"` to find where the credit rate lives; temporarily renaming `handbook.json` to test a missing data file.

## What got more complex?

There are more files and a few more concepts (Pydantic models, Protocol, dependency injection). The trade-off is worth it when more than one person maintains the code or it must be tested and extended, as in this project.