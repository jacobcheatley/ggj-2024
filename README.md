# Comedy Court

## Setup

Set 

```
poetry install --no-root
poetry run uvicorn comedy_court.main:app --reload --host=0.0.0.0 --port 80 --env-file .env
```