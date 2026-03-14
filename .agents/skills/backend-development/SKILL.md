# Backend Development & Testing

## Local Setup

```bash
cd hybrid-rag-backend
poetry install
```

## Running the Backend

```bash
cd hybrid-rag-backend
poetry run fastapi dev app/main.py --port 8000
```

- Health check: `GET http://localhost:8000/health` returns `{"status": "healthy"}`
- API docs: `http://localhost:8000/docs`
- Root: `GET http://localhost:8000/` returns app info JSON

## Configuration

- All settings are in `hybrid-rag-backend/.env` and loaded via pydantic-settings in `app/core/config.py`
- The `Settings` class uses `env_file = ".env"` with `extra = "ignore"`

## Langfuse Observability

- Langfuse is the observability provider (replaced LangSmith)
- Uses `langfuse` v3.x SDK (`from langfuse.langchain import CallbackHandler`)
- Env vars: `LANGFUSE_SECRET_KEY`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_BASE_URL`
- Graceful degradation: when keys are empty/missing, `langfuse_client = None` and `get_langfuse_handler()` returns `None`
- All service layer `chain.invoke()` calls pass callbacks via `config={"callbacks": [h for h in [get_langfuse_handler()] if h is not None]}`

## Key Compatibility Notes

- `langfuse` v2.x is NOT compatible with `langchain` 1.x (broken import: `langchain.callbacks.base` removed in langchain 1.0)
- Must use `langfuse` v3.x+ which uses `langfuse.langchain` module path
- The v3+ SDK uses `LANGFUSE_BASE_URL` (not `LANGFUSE_HOST`) as the environment variable

## No Lint/CI Tooling

- No ruff, flake8, mypy, or pre-commit hooks configured
- No GitHub Actions CI configured
- No test suite exists yet (`tests/__init__.py` is empty)
