# Jest Fest

## Setup

Setup a `.env` file based on `.env.template`. You will need to obtain API keys for Open AI and Eleven Labs.

```
poetry install --no-root
poetry run python ./jest_fest/lib/palette.py
```

## Running

After following setup:

```
poetry run uvicorn jest_fest.main:app --reload --host=0.0.0.0 --port 80 --env-file .env
```
