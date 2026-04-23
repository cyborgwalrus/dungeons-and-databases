"""Authentication, inventory, loadout, and reference-data helpers for the backend."""

from functools import lru_cache
import json
from pathlib import Path
from typing import Any

from flask import current_app, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from backend.db.models import Character, Item, User as UserModel, db


_REFERENCE_DATA_DIR = Path(__file__).resolve().parents[1] / 'db'
_ITEM_TYPES_FILE = _REFERENCE_DATA_DIR / 'item_types.json'
_ENEMY_TYPES_FILE = _REFERENCE_DATA_DIR / 'enemy_types.json'


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


@lru_cache(maxsize=1)
def load_item_type_seed_data() -> tuple[dict[str, Any], ...]:
    """Load the item type seed records from the JSON source file."""
    return tuple(json.loads(_ITEM_TYPES_FILE.read_text(encoding='utf-8')))


@lru_cache(maxsize=1)
def load_enemy_type_seed_data() -> tuple[dict[str, Any], ...]:
    """Load the enemy type seed records from the JSON source file."""
    return tuple(json.loads(_ENEMY_TYPES_FILE.read_text(encoding='utf-8')))


def get_item_type(item_type_id: str | None) -> dict[str, Any] | None:
    """Return one item template by id or ``None`` when missing."""
    if item_type_id is None:
        return None
    normalized_id = str(item_type_id).strip()
    if not normalized_id:
        return None
    for template in load_item_type_seed_data():
        if template['id'] == normalized_id:
            return dict(template)
    return None


def get_item_types() -> list[dict[str, Any]]:
    """Return all item templates as a new list."""
    return [dict(template) for template in load_item_type_seed_data()]


def get_enemy_type(enemy_type_id: str | None) -> dict[str, Any] | None:
    """Return one enemy template by id or ``None`` when missing."""
    if enemy_type_id is None:
        return None
    normalized_id = str(enemy_type_id).strip()
    if not normalized_id:
        return None
    for template in load_enemy_type_seed_data():
        if template['id'] == normalized_id:
            return dict(template)
    return None


def get_enemy_types() -> list[dict[str, Any]]:
    """Return all enemy templates as a new list."""
    return [dict(template) for template in load_enemy_type_seed_data()]


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
    for item_type_id in DEFAULT_LOADOUT_ITEM_IDS:
        item_type = get_item_type(item_type_id)
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
) -> Item | None:
    """Create an inventory item from item type data and attach it to a player."""
    item_type = get_item_type(item_id)
    if not item_type:
        return None

    inventory_item = Item(
        name=item_type['name'],
        item_type_id=item_type['id'],
        slot_type=item_type['slot_type'],
        user_id=player.user_id,
        level=max(1, int(level)),
        health=_scaled_bonus(item_type['health'] or 0, level),
        damage=_scaled_bonus(item_type['damage'] or 0, level),
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


