# Backend API Documentation

## Project Structure

The backend is organized as follows:

```text
backend/
├── app.py                 # Flask application factory and API setup
├── db/                    # Database models, JSON reference data, and initialization
│   ├── models.py         # SQLAlchemy ORM models (User, Character, Item, etc.)
│   ├── reference_data/   # Slug-keyed item and enemy templates plus cached accessors
│   └── README.md          # Backend database notes and initialization guidance
├── resources/            # Flask-RESTful resource classes for REST endpoints
│   ├── authentication.py        # Authentication resources (signup, signin, me)
│   ├── characters.py            # Character management resources
│   ├── users.py                 # User account resources
│   ├── items.py                 # Item management resources
│   ├── encounters.py            # Encounter creation resource
│   └── combats.py               # Combat action resource
├── utils/                # Utilities and helpers
│   ├── api_response_cache.py # Cached API payload helpers and invalidation hooks
│   ├── app_cache.py          # Flask cache configuration
│   ├── game_utils.py         # Game logic helpers (tokens, loadouts, combat)
│   ├── route_helpers.py      # Common route helpers and validation functions
│   └── url_converters.py     # Werkzeug converters that resolve owned ORM objects
└── __init__.py
```

## The Endpoints Table

| Resource name  | Resource URL                                                                                                                          | Resource description                                     | Implemented |
| :------------: | :------------------------------------------------------------------------------------------------------------------------------------ | :------------------------------------------------------- | :---------: |
| Authentication | `/login/signup` - `POST`<br>`/login/signin` - `POST`<br>`/login/signout` - `POST`<br>`/login/me` - `GET`                              | Token-based authentication endpoints                     |     Yes     |
|     User      | `/users/<user:user>` - `GET` `PUT` `DELETE`<br>`/users/<user:user>/inventory` - `GET` `DELETE`                                     | User account management and shared inventory            |     Yes     |
|   Character   | `/users/<user:user>/characters` - `GET` `POST`<br>`/characters/<character:character>` - `GET` `PUT` `DELETE`<br>`/characters/<character:character>/select` - `POST`<br>`/characters/<character:character>/full_heal` - `POST`<br>`/characters/<character:character>/equipment` - `GET` `POST`<br>`/characters/<character:character>/equipment/<item:item>` - `DELETE` | Character management, selection, leveling, experience, equipment, and healing |     Yes     |
|      Item     | `/items` - `POST`<br>`/items/<item:item>` - `GET` `DELETE`                                                                    | Item creation and inventory operations                   |     Yes     |
|   Encounter   | `/encounters` - `POST`                                                                                     | Dungeon encounter creation                                |     Yes     |
|     Combat     | `/combats/<combat:combat>/attack` - `POST`<br>`/combats/<combat:combat>/run` - `POST`<br>`/combats/<combat:combat>/home` - `POST` | Dungeon combat actions                                    |     Yes     |

## Endpoint Details

### Authentication

- `POST /api/login/signup` - create a user account.
- `POST /api/login/signin` - authenticate a user.
- `POST /api/login/signout` - clear the client token.
- `GET /api/login/me` - return the current authenticated user.

Authenticated requests must send `Authorization: Bearer <token>`. The `/login/me` response also includes the currently selected character when the token is scoped to one.

### Users

- `GET /api/users/<user:user>` - fetch one user.
- `PUT /api/users/<user:user>` - update a user.
- `DELETE /api/users/<user:user>` - delete a user.

#### Characters list

- `GET /api/users/<user:user>/characters` - list characters for the specified user.
- `POST /api/users/<user:user>/characters` - create a new character for the specified user.

### Characters

#### Character

- `GET /api/characters/<character:character>` - fetch one character.
- `PUT /api/characters/<character:character>` - update a character's stats.
- `DELETE /api/characters/<character:character>` - delete a character.
- `POST /api/characters/<character:character>/select` - issue a token scoped to the selected character.
- `POST /api/characters/<character:character>/full_heal` - heal a character to full health.

#### Equipment

- `GET /api/characters/<character:character>/equipment` - list equipped items for a character.
- `POST /api/characters/<character:character>/equipment` - equip an item from the user's shared inventory.
- `DELETE /api/characters/<character:character>/equipment/<item:item>` - unequip an item and return it to the user's shared inventory.

### Inventory

- `GET /api/users/<user:user>/inventory` - list the shared inventory items for a user.
- `DELETE /api/users/<user:user>/inventory` - clear the shared inventory while preserving equipped items.

### Items

- `POST /api/items` - create one or more new items for the active character.
- `GET /api/items/<item:item>` - fetch one item.
- `DELETE /api/items/<item:item>` - remove an item.

### Encounters

- `POST /api/encounters` - create a new dungeon encounter and matching combat state for the active character.

### Combat

- `POST /api/combats/<combat:combat>/attack` - attack the active combat.
- `POST /api/combats/<combat:combat>/run` - attempt to flee the active combat.
- `POST /api/combats/<combat:combat>/home` - leave the dungeon after defeating the current enemy.

## Deployment

The backend container starts with `project/backend/start-backend.sh`, which initializes the database and then runs the API with a WSGI server on port `5000`.

The SQLite database is stored in the container instance volume so the Adminer service can inspect it in both development and production.
In Adminer, choose the SQLite driver and open `/app/instance/game.db` from the shared volume. The container loads `login-password-less.php` from `adminer/plugins-enabled` and uses `ADMIN_PASSWORD` as the local unlock password.

The dashboard is available behind the shared admin gateway at `/admin/dashboard`, and its login password comes from the `ADMIN_PASSWORD` environment variable.
Adminer is available at `/admin/adminer` and unlocks through the bundled password-less login plugin.

## API Docs

Swagger UI is available at `/api/docs`, and the OpenAPI document is served from `/api/openapi.yaml`.

## Admin Tools

- `/admin/dashboard` - Flask Monitoring Dashboard.
- `/admin/adminer` - Adminer.
