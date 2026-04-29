# Dungeons & Databases

> [!IMPORTANT]
> All the code parts of the readmes in this repository has been created using Github Copilot and GPT-5.4 mini agents, available for free to students with a monthly token allowance (generous enough to fit the whole project into). Prompt history available in [prompt_history/copilot_chat_prompts.csv](prompt_history/copilot_chat_prompts.csv).


Browser based dungeon crawler. Equip your character with your best items and delve into the depths of the dungeon. The deeper you go, the better the loot, but beware; The monsters get tougher and only winners get to keep their loot.

## Architecture

### Frontend

Vanilla JavaScript, HTML and CSS.

### Backend

RESTFul hypermedia API implemented in Python with Flask, SQLAlchemy and SQLite. OpenAPI documentation available at `/api/docs`, `/api/openapi.yaml` or the Api Docs button in the frontend login screen.

Backend dependencies can be found in [pyproject.toml](pyproject.toml) and are managed with [uv](https://docs.astral.sh/uv/).

## Group information

* Hla Kay Poe: [hpoe22@student.oulu.fi](mailto:hpoe22@student.oulu.fi)
* Matias Björklund: [matias.bjorklund@student.oulu.fi](mailto:matias.bjorklund@student.oulu.fi)

## Deployment

### Running tests locally

1. Install [uv](https://docs.astral.sh/uv/).
2. Run `uv sync --extra test` from the repository root to initialize the local `.venv` and install runtime and test dependencies.
3. Run `uv run pytest` from the repository root to execute the backend test suite.
4. Run `uv run pytest --cov` from the repository root to execute the backend test suite with coverage reporting.

### Development mode with hot reload using Docker

> [!CAUTION]
> This deployment configuration is preset with `WIPE_DB_ON_RESTART=true`, which wipes the database on every restart. To configure this, change the value of `WIPE_DB_ON_RESTART` in the `docker-compose.yml` file.

1. Install [Docker Compose](https://docs.docker.com/compose/install/).
2. Run `docker compose up --build` from the repository root to start the backend API and frontend app in development mode with hot reload.
3. Access the frontend app at `http://localhost:8080` and the backend API at `http://localhost:5000`.

### Production mode using Docker

Production mode disables hot reload and sets `WIPE_DB_ON_RESTART=false` to persist the database across restarts. File mounts from the host are replaced with Docker volumes.

1. Install [Docker Compose](https://docs.docker.com/compose/install/).
2. Run `docker compose -f docker-compose.prod.yml up --build` from the repository root to start the backend API and frontend app in production mode.
3. Access the frontend app at `http://localhost:8080` and the backend API at `http://localhost:5000`.

## Code Coverage

Latest code coverage report of the main branch backend API is available at <https://cyborgwalrus.github.io/dungeons-and-databases/index.html>

## Github Actions

The repository includes the following Github Actions workflows:

* [coverage.yaml](.github/workflows/coverage.yml) - Runs the backend test suite with coverage reporting and publishes the report to Github Pages.

## Quick Links

* API docs: `/api/docs`
* OpenAPI spec: `/api/openapi.yaml`
* Frontend app: the root of the deployed site
* Flask admin dashboard: `/admin/dashboard`
* Adminer dashboard for database management: `/admin/adminer` (default credentials: `admin`/`admin`, system: SQLite3, database file: `/app/instance/dnd.db`)
