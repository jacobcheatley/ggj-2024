# Jest Fest

## Setup

Setup `.env` based on `.env.template`

```
poetry install --no-root
poetry run uvicorn jest_fest.main:app --reload --host=0.0.0.0 --port 80 --env-file .env
```