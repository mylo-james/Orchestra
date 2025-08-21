# Tasks for Mylo the Human

## Secrets and environment setup (required)
- [ ] Create a `.env` file at the repo root with these variables:

```env
# OpenAI
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o
OPENAI_MAX_TOKENS=4096
OPENAI_TEMPERATURE=0.1

# GitHub (for tool framework)
GITHUB_TOKEN=
GITHUB_ORG=
GITHUB_REPO=

# Pinecone (optional; knowledge features)
PINECONE_API_KEY=
PINECONE_ENVIRONMENT=
PINECONE_INDEX_NAME=orchestra-knowledge

# Temporal (defaults OK for local)
TEMPORAL_HOST=localhost
TEMPORAL_PORT=7233
TEMPORAL_NAMESPACE=default
TEMPORAL_TASK_QUEUE=orchestra-tasks

# Logging (optional)
LOG_LEVEL=INFO
LOG_JSON=false
```

- [ ] Use a fine-grained GitHub PAT with repo scope; do not commit `.env`.
- [ ] Add the same secrets to CI as repository or environment secrets.

## Local validation
- [ ] Create and activate a venv, then install deps and run tests:
```bash
python3 -m venv .venv && . .venv/bin/activate
pip install poetry==1.7.1
poetry install
poetry run pytest -q
```
- [ ] (Optional) Quick OpenAI connectivity check (requires `OPENAI_API_KEY`):
```bash
poetry run python -c "from openai import AsyncOpenAI; import asyncio; async def m():\n    c=AsyncOpenAI();\n    r=await c.models.list();\n    print(len(r.data));\nasyncio.run(m())"
```
