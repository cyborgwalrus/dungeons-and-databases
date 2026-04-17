from typing import Any

from flask import jsonify
from flask_login import current_user

from ..game_utils import get_player
from ..db.models import Character, Item, ItemType, User


def get_current_user() -> User | None:
    if current_user.is_authenticated:
        user_id = current_user.get_id()
        user = User.query.get(int(user_id)) if user_id else None
        if user:
            return user
    return None


def get_character(character_id: int | None = None) -> Character:
    if character_id is not None:
        character = Character.query.get(character_id)
        if character:
            return character
    character = get_player()
    if character is not None:
        return character

    character = Character.query.first()
    if character is not None:
        return character

    raise LookupError('No character available')


def get_item(character: Character, item_id: int) -> Item | None:
    return Item.query.filter_by(owner_id=character.id, id=item_id).first()


def get_item_type(item_type_id: int) -> ItemType | None:
    return ItemType.query.get(item_type_id)


def get_json_data(request: Any) -> dict[str, Any]:
    return request.get_json(silent=True) or {}


def json_error(message: str, status: int = 400) -> tuple[Any, int]:
    return jsonify({'error': message}), status