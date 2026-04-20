from typing import Any

from flask import current_app, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from ..db.cache_helpers import get_all_item_type_data, get_item_type_data
from ..db.models import Character, Item, User, db


AUTH_TOKEN_SALT = 'dungeons-and-databases-auth-token'
DEFAULT_AUTH_TOKEN_MAX_AGE_SECONDS = 60 * 60 * 24 * 30
DEFAULT_LOADOUT_ITEM_NAMES = [
    'Steel Sword',
    'Leather Armor',
    'Iron Shield',
    'Iron Helmet',
    'Silver Necklace',
    'Enchanted Ring',
]


def _get_auth_serializer() -> URLSafeTimedSerializer:
    secret_key = current_app.config.get('SECRET_KEY')
    if not secret_key:
        raise RuntimeError('SECRET_KEY is required for token auth')
    return URLSafeTimedSerializer(secret_key=secret_key, salt=AUTH_TOKEN_SALT)


def issue_auth_token(user_id: int, character_id: int | None = None) -> str:
    serializer = _get_auth_serializer()
    payload = {'user_id': int(user_id), 'character_id': int(character_id) if character_id is not None else None}
    return serializer.dumps(payload)


def get_request_auth_payload() -> dict[str, Any] | None:
    authorization = request.headers.get('Authorization', '').strip()
    if not authorization:
        return None

    token_prefix = 'bearer '
    if authorization.lower().startswith(token_prefix):
        token = authorization[len(token_prefix):].strip()
    else:
        token = authorization
    if not token:
        return None

    try:
        serializer = _get_auth_serializer()
        max_age = int(current_app.config.get('AUTH_TOKEN_MAX_AGE_SECONDS', DEFAULT_AUTH_TOKEN_MAX_AGE_SECONDS))
        payload = serializer.loads(token, max_age=max_age)
    except (BadSignature, SignatureExpired, TypeError, ValueError):
        return None

    if not isinstance(payload, dict):
        return None

    user_id = payload.get('user_id')
    if user_id is None:
        return None
    try:
        payload['user_id'] = int(user_id)
    except (TypeError, ValueError):
        return None

    character_id = payload.get('character_id')
    if character_id is not None:
        try:
            payload['character_id'] = int(character_id)
        except (TypeError, ValueError):
            return None

    return payload


def get_current_user() -> User | None:
    payload = get_request_auth_payload()
    if not payload:
        return None

    user = User.query.get(payload['user_id'])
    return user


def get_player() -> Character | None:
    payload = get_request_auth_payload()
    if not payload:
        return None

    character_id = payload.get('character_id')
    if character_id is None:
        return None

    character = Character.query.get(character_id)
    if not character:
        return None

    if character.user_id != payload['user_id']:
        return None

    return character


def seed_character_loadout(character: Character) -> None:
    item_types_by_name = {item_type['name']: item_type for item_type in get_all_item_type_data()}
    for item_name in DEFAULT_LOADOUT_ITEM_NAMES:
        item_type = item_types_by_name.get(item_name)
        if item_type:
            add_inventory_item(character, item_type['id'], copy_from_item=False)


def add_inventory_item(player: Character, item_id: int, *, copy_from_item: bool = False, is_loot: bool | None = None) -> Item | None:
    source_item = Item.query.get(item_id) if copy_from_item else None
    if source_item:
        item_type = get_item_type_data(source_item.item_type_id)
        level = source_item.level
        loot_flag = source_item.is_loot if is_loot is None else is_loot
    else:
        item_type = get_item_type_data(item_id)
        if not item_type:
            return None
        level = 1
        loot_flag = False if is_loot is None else is_loot

    if not item_type:
        return None

    inventory_item = Item(
        name=item_type['name'],
        item_type_id=item_type['id'],
        owner_id=player.id,
        level=level,
        health_bonus=item_type['base_health_bonus'] or 0,
        damage_bonus=item_type['base_damage_bonus'] or 0,
        is_equipped=False,
        is_loot=loot_flag,
    )
    db.session.add(inventory_item)
    return inventory_item


def remove_inventory_item(player: Character, item_id: int) -> Item | None:
    inventory_item = Item.query.filter_by(owner_id=player.id, is_equipped=False, id=item_id).first()
    if not inventory_item:
        inventory_item = Item.query.filter_by(owner_id=player.id, is_equipped=False, item_type_id=item_id).first()
    if not inventory_item:
        return None

    if inventory_item in player.inventory:
        player.inventory.remove(inventory_item)
    db.session.delete(inventory_item)
    return inventory_item


def clear_loot_flags(player: Character) -> None:
    for item in player.inventory:
        if item.is_loot:
            item.is_loot = False


def destroy_loot_items(player: Character) -> None:
    loot_items = [item for item in player.inventory if item.is_loot]
    for item in loot_items:
        if item in player.inventory:
            player.inventory.remove(item)
        db.session.delete(item)
