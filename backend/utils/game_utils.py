"""Authentication, inventory, and loadout helpers for the backend."""

from typing import Any

from flask import current_app, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from backend.db.reference_data import get_all_item_type_data, get_item_type_data
from backend.db.models import Character, Item, User as UserModel, db


AUTH_TOKEN_SALT = 'dungeons-and-databases-auth-token'
DEFAULT_AUTH_TOKEN_MAX_AGE_SECONDS = 60 * 60 * 24 * 30
DEFAULT_LOADOUT_ITEM_IDS = [
    'steel_sword',
    'linen_armor',
    'iron_shield',
    'iron_helmet',
    'ruby_necklace',
    'silver_ring',
]


def get_auth_serializer() -> URLSafeTimedSerializer:
    """Build the serializer used to sign and validate auth tokens."""
    secret_key = current_app.config.get('SECRET_KEY')
    if not secret_key:
        raise RuntimeError('SECRET_KEY is required for token auth')
    return URLSafeTimedSerializer(secret_key=secret_key, salt=AUTH_TOKEN_SALT)


def issue_auth_token(user_id: int, character_id: int | None = None) -> str:
    """Create a signed auth token for the current user and optional character."""
    serializer = get_auth_serializer()
    payload = {
        'user_id': int(user_id),
        'character_id': int(character_id) if character_id is not None else None,
    }
    return serializer.dumps(payload)


def get_request_auth_payload() -> dict[str, Any] | None:
    """Parse and validate the bearer token from the incoming request."""
    payload: dict[str, Any] | None = None
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
        serializer = get_auth_serializer()
        max_age = int(
            current_app.config.get(
                'AUTH_TOKEN_MAX_AGE_SECONDS', DEFAULT_AUTH_TOKEN_MAX_AGE_SECONDS
            )
        )
        payload = serializer.loads(token, max_age=max_age)
    except (BadSignature, SignatureExpired, TypeError, ValueError):
        payload = None

    if isinstance(payload, dict):
        user_id = payload.get('user_id')
        if user_id is not None:
            try:
                payload['user_id'] = int(user_id)
            except (TypeError, ValueError):
                payload = None

        if payload is not None:
            character_id = payload.get('character_id')
            if character_id is not None:
                try:
                    payload['character_id'] = int(character_id)
                except (TypeError, ValueError):
                    payload = None
    else:
        payload = None

    return payload


def get_current_user() -> UserModel | None:
    """Return the authenticated user associated with the request token."""
    payload = get_request_auth_payload()
    if not payload:
        return None

    user = UserModel.query.get(payload['user_id'])
    return user


def get_player() -> Character | None:
    """Return the active character referenced by the request token, if any."""
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
    """Populate a new character with the default starter equipment."""
    item_types_by_id = {item_type['id']: item_type for item_type in get_all_item_type_data()}
    for item_type_id in DEFAULT_LOADOUT_ITEM_IDS:
        item_type = item_types_by_id.get(item_type_id)
        if item_type:
            add_inventory_item(character, item_type['id'])


def _scaled_bonus(base_bonus: int, level: int) -> int:
    """Scale item bonuses by level while preserving zero-value stats."""
    if base_bonus <= 0:
        return 0
    bonus_multiplier = 1.10 ** max(0, level - 1)
    return max(0, int(round(base_bonus * bonus_multiplier)))


def add_inventory_item(
    player: Character,
    item_id: str,
    *,
    level: int = 1,
    is_loot: bool | None = None,
) -> Item | None:
    """Create an inventory item from item type data and attach it to a player."""
    item_type = get_item_type_data(item_id)
    if not item_type:
        return None

    loot_flag = False if is_loot is None else is_loot

    inventory_item = Item(
        name=item_type['name'],
        item_type_id=item_type['id'],
        slot=item_type['slot'],
        user_id=player.user_id,
        level=max(1, int(level)),
        health=_scaled_bonus(item_type['health'] or 0, level),
        damage=_scaled_bonus(item_type['damage'] or 0, level),
        is_loot=loot_flag,
    )
    db.session.add(inventory_item)
    return inventory_item


def remove_inventory_item(player: Character, item_id: int | str) -> Item | None:
    """Remove an item from the player's inventory by item or type ID."""
    if not player.user:
        return None

    inventory_item = Item.query.filter_by(user_id=player.user_id, id=item_id).first()
    if inventory_item and inventory_item.is_equipped:
        return None
    if not inventory_item:
        inventory_item = Item.query.filter_by(
            user_id=player.user_id,
            item_type_id=str(item_id),
        ).first()
        if not inventory_item or inventory_item.is_equipped:
            return None

    db.session.delete(inventory_item)
    return inventory_item


def clear_loot_flags(player: Character) -> None:
    """Clear the loot marker from any items currently held by the player."""
    if not player.user:
        return
    for item in Item.query.filter_by(user_id=player.user_id, is_loot=True).all():
        item.is_loot = False


def destroy_loot_items(player: Character) -> None:
    """Delete all loot items from the player's inventory."""
    if not player.user:
        return
    loot_items = Item.query.filter_by(user_id=player.user_id, is_loot=True).all()
    for item in loot_items:
        if item.is_equipped:
            continue
        db.session.delete(item)
