# Backend API Documentation

The backend exposes its routes under the `/api` prefix.

## Endpoint Table

| Resource name  | Resource URL                                                                                                                          | Resource description                                     | Implemented |
| :------------: | :------------------------------------------------------------------------------------------------------------------------------------ | :------------------------------------------------------- | :---------: |
| Authentication | `/login/signup` - `POST`<br>`/login/signin` - `POST`<br>`/login/signout` - `POST`<br>`/login/me` - `GET`                              | Token-based authentication endpoints                     |     Yes     |
|     Users      | `/users/` - `GET`<br>`/users/<int:user_id>` - `GET` `PUT` `DELETE`                                                                     | User account management                                  |     Yes     |
|   Characters   | `/characters/` - `GET` `POST`<br>`/characters/<int:character_id>` - `GET` `PUT` `DELETE`<br>`/characters/<int:character_id>/select` - `POST`<br>`/characters/<int:character_id>/level_up` - `POST`<br>`/characters/<int:character_id>/full_heal` - `POST` | Character management, selection, leveling, and healing |     Yes     |
|      Item      | `/items/` - `POST`<br>`/items/<int:item_id>` - `GET` `PUT` `DELETE`                                                                    | Item creation and item-level operations                  |     Yes     |
|   Inventory    | `/characters/<int:character_id>/inventory/` - `POST` `DELETE`                                                                          | Bulk inventory operations for a character               |     Yes     |
|    Dungeon     | `/dungeon/enter` - `POST`<br>`/dungeon/attack` - `POST`<br>`/dungeon/run` - `POST`                                                     | Dungeon entry and combat operations                      |     Yes     |

## Authentication

- `POST /api/login/signup` - create a user account.
- `POST /api/login/signin` - authenticate a user.
- `POST /api/login/signout` - clear the client token.
- `GET /api/login/me` - return the current authenticated user.

Authenticated requests must send `Authorization: Bearer <token>`. The `/login/me` response also includes the currently selected character when the token is scoped to one.

## Users

- `GET /api/users/` - list users.
- `GET /api/users/<int:user_id>` - fetch one user.
- `PUT /api/users/<int:user_id>` - update a user.
- `DELETE /api/users/<int:user_id>` - delete a user.

## Characters

- `GET /api/characters/` - list characters.
- `POST /api/characters/` - create a character.
- `GET /api/characters/<int:character_id>` - fetch one character.
- `PUT /api/characters/<int:character_id>` - update a character's stats.
- `DELETE /api/characters/<int:character_id>` - delete a character.
- `POST /api/characters/<int:character_id>/select` - issue a token scoped to the selected character.
- `POST /api/characters/<int:character_id>/level_up` - level up a character.
- `POST /api/characters/<int:character_id>/full_heal` - heal a character to full health.

Character payloads returned by `GET /api/characters/<int:character_id>` include separate `inventory` and `equipped` arrays.
Selecting a character via `POST /api/characters/<int:character_id>/select` returns a new token scoped to that character.

## Items

- `POST /api/items/` - create one or more new items for the active character.
- `GET /api/items/<int:item_id>` - fetch one item.
- `PUT /api/items/<int:item_id>` - update or equip an item.
- `DELETE /api/items/<int:item_id>` - remove an item.

## Character Inventory

- `POST /api/characters/<int:character_id>/inventory/` - add one or more items to a character's inventory.
- `DELETE /api/characters/<int:character_id>/inventory/` - clear a character's unequipped inventory.

## Dungeon

- `POST /api/dungeon/enter` - enter or resume the active dungeon encounter.
- `POST /api/dungeon/attack` - attack the active encounter.
- `POST /api/dungeon/run` - attempt to flee the active encounter.

## Setup

Run the backend by running the docker compose file in the root of the project.
