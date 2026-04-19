from typing import Any

from flask import jsonify
from flask_login import current_user

from ..utils.cache_helpers import get_item_type_data
from ..utils.game_utils import get_player
from ..db.models import Character, Item, User


def get_current_user() -> User | None:
    if current_user.is_authenticated:
        user_id = current_user.get_id()
        user = User.query.get(int(user_id)) if user_id else None
        if user:
            return user
    return None


def get_character(character_id: int | None = None) -> Character:
    if character_id is not None:
        return Character.query.get(character_id)

    return get_player()


def get_item(character: Character, item_id: int) -> Item | None:
    return Item.query.filter_by(owner_id=character.id, id=item_id).first()


def get_item_type(item_type_id: int) -> dict[str, Any] | None:
    return get_item_type_data(item_type_id)


def get_json_data(request: Any) -> dict[str, Any]:
    return request.get_json(silent=True) or {}


def json_error(message: str, status: int = 400) -> tuple[Any, int]:
    return jsonify({'error': message}), status