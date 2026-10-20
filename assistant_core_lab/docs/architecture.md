# assistant_core architecture

## 1. Modules

| Module | Responsibility |
|---|---|
| config.py | read settings from the environment; validate |
| errors.py | named exceptions |
| models.py | public contract: Message, Response, Intent, Source |
| router.py | choose an Intent with simple rules |
| knowledge.py | office directory (CSV) and handbook (JSON) with search |
| tools.py | deterministic tuition calculation |
| responder.py | response generation behind one interface (stub LLM, template) |
| service.py | AssistantService.handle(Message) -> Response, the only entry point |
| logging_setup.py | structured JSON logs |
| __main__.py | command-line interface |

## 2. Service interface

`AssistantService.handle(msg: Message) -> Response`

- `Message`: `text` (1-2000 chars), `session_id`
- `Response`: `answer`, `intent`, `sources[]`, `degraded` (True if a fallback was used)
- Errors: an empty `text` is rejected by `Message` (`ValidationError`); whitespace-only text raises `InvalidRequest`; startup raises `ConfigError` / `DataError`; provider failures never reach the caller (a fallback answers instead, with `degraded=True`). A fee question the tools cannot compute (for example, credits out of range) is answered with an explanatory message instead of raising.

The CLI, the future FastAPI backend and the UI all call this one method.

## 3. Decisions

### Decision 1: Fees are computed in tools.py, never by an LLM
- Context: tuition must be exact and testable.
- Decision: pure functions `parse_credits` and `tuition`, no I/O.
- Consequence: a characterisation test locks the old value (9,450,000 VND).

### Decision 2: The LLM sits behind a Responder interface
- Context: the AI provider arrives in Week 4 and can fail.
- Decision: a `Responder` Protocol with a template and a stub implementation; the service falls back to the template on `ProviderError` and sets `degraded=True`.
- Consequence: tests and CI run offline; providers can be swapped without editing the service.

### Decision 3: Configuration comes from the environment
- Context: fees and the API key must not live in code or Git.
- Decision: `config.py` reads environment variables; `.env.example` documents all of them; `.env` is gitignored.
- Consequence: changing the credit rate is one variable, and the key is never printed (`repr=False`).