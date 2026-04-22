# Backend API Documentation

## Project Structure

The backend is organized as follows:

```text
backend/
├── app.py                 # Flask application factory and API setup
├── db/                    # Database models, JSON reference data, and initialization
│   ├── models.py         # SQLAlchemy ORM models (User, Character, Item, etc.)
│   ├── init_db.py        # Reference-data warmup and database initialization
│   ├── reference_data/   # Slug-keyed item and enemy templates plus cached accessors
├── resources/            # Flask-RESTful resource classes for REST endpoints
│   ├── authentication.py        # Authentication resources (signup, signin, me)
│   ├── characters.py            # Character management resources
│   ├── users.py                 # User account resources
│   ├── items.py                 # Item management resources
│   ├── encounters.py            # Encounter creation resource
│   └── combats.py               # Combat action resource
├── utils/                # Utilities and helpers
│   ├── game_utils.py         # Game logic helpers (tokens, loadouts, combat)
│   ├── serializers.py        # Response serialization functions
│   ├── app_cache.py          # Flask cache configuration
│   └── route_helpers.py      # Common route helpers and validation functions
└── __init__.py
```

## The Endpoints Table

| Resource name  | Resource URL                                                                                                                          | Resource description                                     | Implemented |
| :------------: | :------------------------------------------------------------------------------------------------------------------------------------ | :------------------------------------------------------- | :---------: |
| Authentication | `/login/signup` - `POST`<br>`/login/signin` - `POST`<br>`/login/signout` - `POST`<br>`/login/me` - `GET`                              | Token-based authentication endpoints                     |     Yes     |
|     Users      | `/users/<int:user_id>` - `GET` `PUT` `DELETE`<br>`/users/<int:user_id>/inventory` - `GET` `DELETE`                                     | User account management and shared inventory            |     Yes     |
|   Characters   | `/users/<int:user_id>/characters` - `GET` `POST`<br>`/characters/<int:character_id>` - `GET` `PUT` `DELETE`<br>`/characters/<int:character_id>/select` - `POST`<br>`/characters/<int:character_id>/full_heal` - `POST`<br>`/characters/<int:character_id>/equipment` - `GET` `POST`<br>`/characters/<int:character_id>/equipment/<int:item_id>` - `DELETE` | Character management, selection, leveling, experience, equipment, and healing |     Yes     |
|      Items     | `/items` - `POST`<br>`/items/<int:item_id>` - `GET` `DELETE`                                                                    | Item creation and inventory operations                   |     Yes     |
|   Encounters   | `/encounters` - `POST`                                                                                     | Dungeon encounter creation                                |     Yes     |
|     Combat     | `/combats/<int:combat_id>/attack` - `POST`<br>`/combats/<int:combat_id>/run` - `POST`                      | Dungeon combat actions                                    |     Yes     |

## Endpoint Details

### Authentication

- `POST /api/login/signup` - create a user account.
- `POST /api/login/signin` - authenticate a user.
- `POST /api/login/signout` - clear the client token.
- `GET /api/login/me` - return the current authenticated user.

Authenticated requests must send `Authorization: Bearer <token>`. The `/login/me` response also includes the currently selected character when the token is scoped to one.

### Users

- `GET /api/users/<int:user_id>` - fetch one user.
- `PUT /api/users/<int:user_id>` - update a user.
- `DELETE /api/users/<int:user_id>` - delete a user.

### Characters

- `GET /api/users/<int:user_id>/characters` - list characters for the specified user.
- `POST /api/users/<int:user_id>/characters` - create a new character for the specified user.
- `GET /api/characters/<int:character_id>` - fetch one character.
- `PUT /api/characters/<int:character_id>` - update a character's stats.
- `DELETE /api/characters/<int:character_id>` - delete a character.
- `POST /api/characters/<int:character_id>/select` - issue a token scoped to the selected character.
- `POST /api/characters/<int:character_id>/full_heal` - heal a character to full health.
- `GET /api/characters/<int:character_id>/equipment` - list equipped items for a character.
- `POST /api/characters/<int:character_id>/equipment` - equip an item from the user's shared inventory.
- `DELETE /api/characters/<int:character_id>/equipment/<int:item_id>` - unequip an item and return it to the user's shared inventory.

### Inventory

- `GET /api/users/<int:user_id>/inventory` - list the shared inventory items for a user.
- `DELETE /api/users/<int:user_id>/inventory` - clear the shared inventory while preserving equipped items.

### Items

- `POST /api/items` - create one or more new items for the active character.
- `GET /api/items/<int:item_id>` - fetch one item.
- `DELETE /api/items/<int:item_id>` - remove an item.

### Encounters

- `POST /api/encounters` - create a new dungeon encounter and matching combat state for the active character.

### Combat

- `POST /api/combats/<int:combat_id>/attack` - attack the active combat.
- `POST /api/combats/<int:combat_id>/run` - attempt to flee the active combat.

### Setup

Run the backend by running the docker compose file in the root of the project.
