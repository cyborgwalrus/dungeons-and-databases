# Backend API Documentation

The backend exposes its routes under the `/api` prefix.

## Endpoint Table

| Resource name  | Resource url                                                                                                                          | Resource description                                     | Implemented |
| :------------: | :------------------------------------------------------------------------------------------------------------------------------------ | :------------------------------------------------------- | :---------: |
| Authentication | `/login/signup` - `POST`<br>`/login/signin` - `POST`<br>`/login/signout` - `POST`<br>`/login/me` - `GET`                              | Authentication endpoints for Flask-Login                 |     Yes     |
|     Users      | `/users/` - `GET`<br>`/users/<int:user_id>` - `GET` `PUT` `DELETE`                                                                     | User account management                                  |     Yes     |
|   Characters   | `/characters/` - `GET` `POST`<br>`/characters/<int:character_id>` - `GET` `DELETE`                                                     | Character management                                     |     Yes     |
|     Player     | `/player` - `GET` `PUT`<br>`/player/full` - `GET`<br>`/player/level-up` - `POST`<br>`/player/health` - `POST`                         | Alias for managing the currently active player character |     Yes     |
|   Inventory    | `/characters/<int:character_id>/inventory/` - `POST` `PUT` `DELETE`                                                                 | Character inventory operations                           |     Yes     |
|      Item      | `/characters/<int:character_id>/inventory/<int:item_id>` - `GET` `POST` `PUT` `DELETE`                                                 | Individual inventory item operations                     |     Yes     |
|    Dungeon     | `/dungeon/encounters/` - `GET` `POST`<br>`/dungeon/encounters/<int:encounter_id>` - `GET` `DELETE`<br>`/dungeon/encounters/<int:character_id>/current` - `GET`<br>`/dungeon/attack` - `POST`<br>`/dungeon/run` - `POST` | Dungeon encounter and combat operations                  |     Yes     |

## Authentication

- `POST /api/login/signup` - create a user account.
- `POST /api/login/signin` - authenticate a user.
- `POST /api/login/signout` - clear the active session.
- `GET /api/login/me` - return the current authenticated user.

## Users

- `GET /api/users/` - list users.
- `GET /api/users/<int:user_id>` - fetch one user.
- `PUT /api/users/<int:user_id>` - update a user.
- `DELETE /api/users/<int:user_id>` - delete a user.

## Characters

- `GET /api/characters/` - list characters.
- `POST /api/characters/` - create a character.
- `GET /api/characters/<int:character_id>` - fetch one character.
- `DELETE /api/characters/<int:character_id>` - delete a character.
- `GET /api/player` - fetch the active player character.
- `PUT /api/player` - update the active player character.
- `POST /api/player/level-up` - level up the active player character.
- `POST /api/health` - heal the active player character.
- `GET /api/player/full` - fetch the full active player payload.

## Inventory

- `POST /api/characters/<int:character_id>/inventory/` - add one or more items to inventory.
- `DELETE /api/characters/<int:character_id>/inventory/` - clear inventory.
- `GET /api/characters/<int:character_id>/inventory/<int:item_id>` - fetch one inventory item.
- `POST /api/characters/<int:character_id>/inventory/<int:item_id>` - equip or unequip an item.

Character and player payloads returned by `/api/characters/<int:character_id>` and `/api/player/full` include separate `inventory` and `equipped` arrays.

## Setup

Run the backend by running the docker compose file in the root of the project