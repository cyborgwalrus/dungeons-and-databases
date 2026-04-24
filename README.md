# Dungeons & Databases

Browser dungeon crawler with a Flask API backend and a static frontend client.

## Group information
* Student 1. Hla Kay Poe and hpoe22@student.oulu.fi
* Student 2. Matias Björklund and matias.bjorklund@student.oulu.fi

## Documentation

- Backend API guide: [backend/README.md](backend/README.md)
- OpenAPI document: [backend/openapi.yaml](backend/openapi.yaml)
- Frontend client guide: [frontend/README.md](frontend/README.md)
- Database schema diagram: [docs/database-schema.puml](docs/database-schema.puml)

## Setup And Tests

Install [uv](https://docs.astral.sh/uv/) and run `uv sync --extra test` from the repository root to create the local `.venv` and install both runtime and test dependencies.

Run the backend test suite with `uv run pytest`.

## Quick Links

- API docs: `/api/docs`
- OpenAPI spec: `/api/openapi.yaml`
- Frontend app: the root of the deployed site

__Remember to include all required documentation and HOWTOs, including how to create and populate the database, how to run and test the API, the url to the entrypoint, instructions on how to setup and run the client, instructions on how to setup and run the axiliary service and instructions on how to deploy the api in a production environment__