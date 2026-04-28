# Backend API Documentation

<!-- cspell:ignore Adminer puml enum -->

## Project Structure

The backend is organized as follows:

```text
backend/
├── __init__.py
├── app.py                  # Flask application factory, extension setup, and route registration
├── config.cfg              # Default Flask configuration used by the container and local runs
├── Dockerfile              # Backend container image definition
├── openapi.yaml            # OpenAPI document served at /api/openapi.yaml and used by Swagger UI
├── README.md               # Backend API notes and endpoint guide
├── start-backend.sh        # Container entrypoint that initializes the database and starts the API
├── adminer/
│   └── plugins-enabled/
│       └── login-password-less.php
├── db/                     # Database models, enums, session management, and reference data
│   ├── __init__.py
│   ├── enemy_types.json
│   ├── enums.py
│   ├── item_types.json
│   ├── models.py
│   ├── README.md
│   ├── schemas.py
│   └── session.py
├── resources/              # Flask-RESTful resource classes for API endpoints
│   ├── __init__.py
│   ├── authentication.py
│   ├── characters.py
│   ├── combat_builders.py
│   ├── combat_engine.py
│   ├── combats.py
│   ├── items.py
│   └── users.py
└── utils/                  # Shared helpers for app setup, caching, hypermedia, and route validation
    ├── __init__.py
    ├── api_response_cache.py
    ├── app_init.py
    ├── game_utils.py
    ├── hypermedia.py
    ├── route_helpers.py
    └── url_converters.py
```

## Setup And Testing

Use `uv sync --extra test` from the repository root to create the local virtual environment and install the backend runtime plus test dependencies.

Run the backend tests with `uv run pytest`.

## Deployment

The backend container starts with `project/backend/start-backend.sh`, which initializes the database and then runs the API with a WSGI server on port `5000`.

The SQLite database is stored in the container instance volume so the Adminer service can inspect it in both development and production.
In Adminer, choose the SQLite driver and open `/app/instance/game.db` from the shared volume. The container loads `login-password-less.php` from `adminer/plugins-enabled` and uses `ADMIN_PASSWORD` as the local unlock password.

The dashboard is available behind the shared admin gateway at `/admin/dashboard`, and its login password comes from the `ADMIN_PASSWORD` environment variable.
Adminer is available at `/admin/adminer` and unlocks through the bundled password-less login plugin.

## API Docs

Swagger UI is available at `/api/docs`, and the OpenAPI document is served from `/api/openapi.yaml`.

The API hypermedia state diagram lives at [../docs/hypermedia-state.puml](../docs/hypermedia-state.puml).

## Hypermedia

The API is hypermedia-driven: responses expose `_links` objects that advertise the valid actions for the current resource state.

![Hypermedia State](../docs/hypermedia-state.png)
*Rendered from [docs/hypermedia-state.puml](../docs/hypermedia-state.puml)*


## Endpoint Details

### Authentication

* `POST /api/login/signup` - create a user account.
* `POST /api/login/signin` - authenticate a user.
* `POST /api/login/signout` - clear the client token.
* `GET /api/login/me` - return the current authenticated user.

Authenticated requests must send `Authorization: Bearer <token>`. The `/login/me` response also includes the currently selected character when the token is scoped to one.

### Users

* `GET /api/users/<user:user>` - fetch one user.
* `PUT /api/users/<user:user>` - update a user.
* `DELETE /api/users/<user:user>` - delete a user.

#### Characters list

* `GET /api/users/<user:user>/characters` - list characters for the specified user.
* `POST /api/users/<user:user>/characters` - create a new character for the specified user.

### Characters

#### Character

* `GET /api/characters/<character:character>` - fetch one character.
* `PUT /api/characters/<character:character>` - update a character's stats.
* `DELETE /api/characters/<character:character>` - delete a character.
* `POST /api/characters/<character:character>/select` - issue a token scoped to the selected character.

#### Equipment Slots

* `GET /api/characters/<character:character>/equipment` - list equipped items for a character.
* `POST /api/characters/<character:character>/equipment/<item:item>` - equip an item into a character equipment slot from the user's shared inventory.
* `DELETE /api/characters/<character:character>/equipment/<item:item>` - unequip an item from a character equipment slot and return it to the user's shared inventory.
* Equipment slot types use the shared enum system on `slot_type`: `weapon`, `shield`, `armor`, `helmet`, `ring`, and `necklace`.

### Inventory

* `GET /api/users/<user:user>/inventory` - list the shared inventory items for a user.
* `DELETE /api/users/<user:user>/inventory` - clear the shared inventory while preserving equipped items.

### Items

* `POST /api/items` - create one or more new items for the active character.
* `GET /api/items/<item:item>` - fetch one item.
* `DELETE /api/items/<item:item>` - remove an item.

### Combat

* `POST /api/combats` - start a new dungeon combat for the active character.
* `GET /api/combats/<combat:combat>` - fetch the current combat state.
* `GET /api/combats/<combat:combat>/attack` - attack the active combat.
* `GET /api/combats/<combat:combat>/next_combat` - move deeper after defeating the current enemy.
* `GET /api/combats/<combat:combat>/run` - attempt to flee the active combat.
* `GET /api/combats/<combat:combat>/go_home` - leave the dungeon after defeating the current enemy.



## Admin Tools

* `/admin/dashboard` - Flask Monitoring Dashboard.
* `/admin/adminer` - Adminer.
