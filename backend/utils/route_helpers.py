"""Shared request parsing and ownership helpers for resource handlers."""

from typing import Any

from pydantic import ValidationError
from sqlalchemy import select

from backend.db.models import Character, EquipmentSlot, Item, User
from backend.db.session import db
from backend.utils.game_utils import get_current_user, get_player


def json_error(message: Any, status: int = 400) -> tuple[dict[str, Any], int]:
    """Return a standardized JSON error response."""
    return {'error': message}, status


def validate_payload(schema, data: dict[str, Any]):
    """Validate request data against a Pydantic schema."""
    try:
        return schema.model_validate(data), None
    except ValidationError as error:
        return None, ({'error': error.errors()}, 400)


def require_current_user() -> tuple[User | None, tuple[Any, int] | None]:
    """Require an authenticated user or return a standardized error response."""
    user = get_current_user()
    if user is None:
        return None, ({'error': 'Unauthorized'}, 401)
    return user, None


def get_character(character_id: int | None = None) -> Character | None:
    """Return a specific character or the active player character."""
    if character_id is not None:
        return db.session.get(Character, character_id)

    return get_player()


def require_current_character() -> tuple[Character | None, tuple[Any, int] | None]:
    """Require an active character or return a standardized error response."""
    character = get_character()
    if not character:
        return None, ({'error': 'No active character selected'}, 400)
    return character, None


def require_character_owner(character_id: int) -> tuple[Character | None, tuple[Any, int] | None]:
    """Require that the current user owns the requested character.

    Args:
        character_id: The character ID to verify ownership for.

    Returns:
        The matching character when the current user owns it, otherwise a
        standard JSON error response.
    """
    user, error_response = require_current_user()
    if error_response:
        return None, error_response
    assert user is not None

    character = db.session.get(Character, character_id)
    if not character:
        return None, ({'error': 'Character not found'}, 404)
    if character.user_id != user.id:
        return None, ({'error': 'Unauthorized'}, 401)
    return character, None


def get_item(character: Character, item_id: int) -> Item | None:
    """Return an unequipped item from the character's shared inventory by ID."""
    item = next(
        (
            candidate
            for candidate in db.session.scalars(select(Item))
            if candidate.user_id == character.user_id
            and candidate.id == item_id
            and not candidate.is_equipped
        ),
        None,
    )
    return item


def require_item(
    character: Character,
    item_id: int,
    *,
    message: str = 'Item not found',
    status: int = 404,
) -> tuple[Item | None, tuple[Any, int] | None]:
    """Return an item or a standard JSON error response.

    Args:
        character: The active character whose shared inventory is being
            queried.
        item_id: The inventory item ID to locate.
        message: The error message to return when the item is missing.
        status: The HTTP status code to return when the item is missing.

    Returns:
        The matching inventory item or a standardized JSON error response.
    """
    item = get_item(character, item_id)
    if not item:
        return None, ({'error': message}, status)
    return item, None


def equip_item(character: Character, item: Item) -> tuple[Any, int] | None:
    """Move an inventory item into the character's equipment set.

    Args:
        character: The character receiving the equipped item.
        item: The inventory item to equip.

    Returns:
        ``None`` when the item can be equipped, otherwise a standardized JSON
        error response.
    """
    slot_type = item.slot_type
    if not slot_type:
        return {'error': 'Item cannot be equipped'}, 400

    assert character.id is not None
    assert item.id is not None

    existing_equipment = next(
        (
            candidate
            for candidate in db.session.scalars(select(EquipmentSlot))
            if candidate.character_id == character.id and candidate.slot_type == slot_type
        ),
        None,
    )
    if existing_equipment:
        existing_equipment.item = item
        existing_equipment.item_id = item.id
        existing_equipment.slot_type = slot_type
        db.session.add(existing_equipment)
        return None

    db.session.add(
        EquipmentSlot(
            character=character,
            item=item,
            character_id=character.id,
            item_id=item.id,
            slot_type=slot_type,
        )
    )
    return None


def unequip_item(character: Character, item_id: int) -> tuple[Any, int] | None:
    """Return an equipped item to the character's inventory.

    Args:
        character: The character that owns the equipped item.
        item_id: The equipped item ID to remove.

    Returns:
        ``None`` when the item is successfully unequipped, otherwise a
        standardized JSON error response.
    """
    equipment = next(
        (
            candidate
            for candidate in db.session.scalars(select(EquipmentSlot))
            if candidate.character_id == character.id and candidate.item_id == item_id
        ),
        None,
    )
    if not equipment:
        return {'error': 'Equipment not found'}, 404
    db.session.delete(equipment)
    if equipment.item is not None:
        equipment.item.equipment = None
    return None
