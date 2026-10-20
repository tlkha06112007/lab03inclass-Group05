# Lab 3 — Before / after maintainability comparison

Fill in for the monolith (before) and your refactored package (after).

| Question | Before | After |
|---|---|---|
| Where would you change the credit rate? How many places? | 1 place: the constant `RATE = 450000` in the code | 1 place for users: `CREDIT_RATE_VND` in `.env` (documented in `.env.example`); `config.py` only keeps the default 450_000 |
| Can you run the tests without internet or an API key? | Yes, but unreliably: `llm()` only pretends to call a model, `test()` just prints (no asserts), and `random.random() < 0.1` makes results vary | Yes: `pytest -q` run twice gave 83 passed both times; the stub provider needs no key and only fails when told to |
| What happens if `handbook.json` is missing? | Prints "could not load handbook" and continues silently | Stops at startup with `Error: check configuration and knowledge files.` |
| Is any secret printed or logged? | Yes: `llm()` prints `API_KEY` when `DEBUG = True` (the default) | No: a log line only has `intent`, `latency_ms`, `session` and `degraded` |
| How long does it take a new teammate to find the fee logic? | Estimate, not timed: it is inside the 56-line `handle()`, mixed with routing, search and the LLM call | Estimate, not timed: it is in its own file `tools.py` (`parse_credits`, `tuition`) |
| Number of global variables | 9 (3 mutable: `history`, `offices`, `handbook`) | 6 (1 mutable: `ENV_VARS` in `config.py`) |
| Number of bare `except:` blocks | 3 | 0 |
| Lines in the longest function | 56 (`handle`) | 37 (`main` in `__main__.py`); in `service.py` the longest is `_rule` (25) |
| `ruff check` issues | 6 (3 E722, 1 BLE001, 1 E501, 1 E711; ruff 0.6.9, lab config) | 0 (`ruff check .` run inside `assistant_core_lab`, as CI does) |
| Can you swap the LLM without touching the service? | No: `llm()` is called directly inside `handle()` | Yes: `Responder` Protocol, injected into `AssistantService.__init__` |

**Three sentences:** The biggest improvement is that settings and secrets now come from the environment instead of the code, so the API key is never printed and the credit rate changes in one place. The package is more complex, because one script of about 160 lines became ten modules plus Pydantic models, a Protocol and dependency injection to learn. I would still fix the duplicated "handled" log line, which suggests the logger or handler is set up twice.