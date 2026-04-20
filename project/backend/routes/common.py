from typing import Any

from flask import jsonify

from ..db.cache_helpers import get_item_type_data
from ..utils.game_utils import get_current_user as get_authenticated_user, get_player
from ..db.models import Character, Encounter, Item, User


def get_current_user() -> User | None:
    return get_authenticated_user()


def require_current_user() -> tuple[User | None, tuple[Any, int] | None]:
    user = get_current_user()
    if user is None:
        return None, json_error('Unauthorized', 401)
    return user, None


def require_current_user_id(user_id: int) -> tuple[User | None, tuple[Any, int] | None]:
    user, error_response = require_current_user()
    if error_response:
        return None, error_response
    assert user is not None
    if user.id != user_id:
        return None, json_error('User not found', 404)
    return user, None


def get_character(character_id: int | None = None) -> Character:
    if character_id is not None:
        return Character.query.get(character_id)

    return get_player()


def require_current_character() -> tuple[Character | None, tuple[Any, int] | None]:
    character = get_character()
    if not character:
        return None, json_error('No active character selected', 400)
    return character, None


def require_character_owner(character_id: int) -> tuple[Character | None, tuple[Any, int] | None]:
    user, error_response = require_current_user()
    if error_response:
        return None, error_response
    assert user is not None

    character = Character.query.get(character_id)
    if not character or character.user_id != user.id:
        return None, json_error('Character not found', 404)
    return character, None


def require_encounter_owner(encounter_id: int) -> tuple[Encounter | None, tuple[Any, int] | None]:
    user, error_response = require_current_user()
    if error_response:
        return None, error_response
    assert user is not None

    encounter = Encounter.query.get(encounter_id)
    if not encounter or not encounter.character or encounter.character.user_id != user.id:
        return None, json_error('Encounter not found', 404)
    return encounter, None


def get_item(character: Character, item_id: int) -> Item | None:
    if not character.user or not character.user.inventory:
        return None
    return Item.query.filter_by(inventory_id=character.user.inventory.id, id=item_id).first()


def get_item_type(item_type_id: int) -> dict[str, Any] | None:
    return get_item_type_data(item_type_id)


def get_json_data(request: Any) -> dict[str, Any]:
    return request.get_json(silent=True) or {}


def json_error(message: str, status: int = 400) -> tuple[Any, int]:
    return jsonify({'error': message}), status