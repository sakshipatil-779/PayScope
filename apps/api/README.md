# MandateLens API

FastAPI backend service for MandateLens.

## Development Setup

```powershell
# From apps/api directory:
uv sync --extra dev
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Running Tests

```powershell
uv run pytest
```
