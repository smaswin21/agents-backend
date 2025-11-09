# agents-backend

A  backend for the project which provides the house agent, API routers, DB models and an LLM integration.

This repository contains the server-side code used by the agent suite. The main app lives in the `backend/` folder.

## High level

- Language: Python
- Entrypoint: `backend/main.py`
- Purpose: run API endpoints and house agent components; interacts with a MongoDB backing store and an LLM provider.

## Repo layout

```
backend/
	main.py                # application entrypoint
	pyproject.toml         # project metadata / dependencies
	splitwise.py           # splitwise integration (optional)
	db/                    # database models and mongo helper
		 __init__.py
		models.py
		mongo.py
	house_agent/            # agent code, tools, routers and state
		config.py
		graph.py
		llm.py
		run.py                 # driver for running the agent
		state.py
		tools.py
		routers/              # fastapi routers for endpoints
			agent_messages.py
			auth.py
			health.py
			house_agent.py
			household.py
			root.py
	schemas/               # pydantic schemas for requests/responses
		__init__.py
		household.py
		message.py
		pantry.py
		user.py
```

## Requirements / prerequisites

- Python 3.10+ (3.11 recommended)
- A running MongoDB instance for persistence
- Optionally: an LLM provider API key if you plan to use LLM-backed features (e.g., OpenAI API key)

The project contains a `pyproject.toml`. It's recommended to use Poetry to install dependencies.

## Quick start (recommended)

If the project is packaged via pyproject, you can also use:

```bash
cd backend
# If you use poetry
poetry install
# or install editable with pip (if configured)
python -m pip install -e .
```

## Environment variables

Create a `.env` or export variables in your shell before running. Typical variables the app may require:

- `MONGO_URI` (or similar) — connection string to your MongoDB instance
- `OPENAI_API_KEY` (optional) — if using an OpenAI integration or other LLM API keys
- Any other provider keys referenced in `house_agent/config.py`

Note: check `backend/house_agent/config.py` for exact variable names used by this project.

## Running the application

From the repo root (or `backend` folder):

```bash
cd backend
# Run the main application
poetry run python main.py
```

If `house_agent/run.py` provides a standalone agent runner, you can run it directly (see its docstring/comments):

```bash
python -m house_agent.run
```

## Development notes

- API routers live under `backend/house_agent/routers/`.
- DB models and mongo helpers are in `backend/db/`.
- Pydantic schemas are in `backend/schemas/`.
- LLM abstraction is in `backend/house_agent/llm.py` — check it to configure provider-specific behavior.

## Recommended next steps

- Verify exact environment variable names in `backend/house_agent/config.py`.
- Add a `requirements.txt` or ensure `pyproject.toml` contains pinned dependencies for reproducible installs.
- Add a small `docker-compose.yml` if you want an easy local MongoDB for development.
- Add basic unit tests and a fast CI job that runs them.

