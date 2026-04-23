"""Shared request parsing and ownership helpers for resource handlers."""

from typing import Any

from sqlalchemy import select
from pydantic import ValidationError

from backend.db.models import Character, EquipmentSlot, Item, User
from backend.db.session import db
from backend.utils.game_utils import get_current_user, get_player


def require_current_user() -> tuple[User | None, tuple[Any, int] | None]:
    """Require an authenticated user or return a standardized error response."""
    user = get_current_user()
    if user is None:
        return None, json_error('Unauthorized', 401)
    return user, None


def require_current_user_id(user_id: int) -> tuple[User | None, tuple[Any, int] | None]:
    """Require that the authenticated user matches the requested user ID."""
    user, error_response = require_current_user()
    if error_response:
        return None, error_response
    assert user is not None
    if user.id != user_id:
        return None, json_error('Unauthorized', 401)
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
        return None, json_error('No active character selected', 400)
    return character, None


def require_character_owner(character_id: int) -> tuple[Character | None, tuple[Any, int] | None]:
    """Require that the current user owns the requested character."""
    user, error_response = require_current_user()
    if error_response:
        return None, error_response
    assert user is not None

    character = db.session.get(Character, character_id)
    if not character:
        return None, json_error('Character not found', 404)
    if character.user_id != user.id:
        return None, json_error('Unauthorized', 401)
    return character, None


def get_item(character: Character, item_id: int) -> Item | None:
    """Return an item from the character's shared inventory by ID."""
    item = db.session.execute(
        select(Item).where(Item.user_id == character.user_id, Item.id == item_id),
    ).scalar_one_or_none()
    if not item or item.is_equipped:
        return None
    return item


def require_item(
    character: Character,
    item_id: int,
    *,
    message: str = 'Item not found',
    status: int = 404,
) -> tuple[Item | None, tuple[Any, int] | None]:
    """Return an item or a standard JSON error response."""
    item = get_item(character, item_id)
    if not item:
        return None, json_error(message, status)
    return item, None

def equip_item(character: Character, item: Item) -> tuple[Any, int] | None:
    """Move an inventory item into the character's equipment set."""
    slot_type = item.slot_type
    if not slot_type:
        return json_error('Item cannot be equipped', 400)

    assert character.id is not None
    assert item.id is not None

    existing_equipment = db.session.execute(
        select(EquipmentSlot).where(
            EquipmentSlot.character_id == character.id,
            EquipmentSlot.slot_type == slot_type,
        ),
    ).scalar_one_or_none()
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
    """Return an equipped item to the character's inventory."""
    equipment = db.session.execute(
        select(EquipmentSlot).where(
            EquipmentSlot.character_id == character.id,
            EquipmentSlot.item_id == item_id,
        ),
    ).scalar_one_or_none()
    if not equipment:
        return json_error('Equipment not found', 404)
    db.session.delete(equipment)
    if equipment.item is not None:
        equipment.item.equipment = None
    return None


def get_json_data(request: Any) -> dict[str, Any]:
    """Return JSON request data or an empty mapping when the body is missing."""
    return request.get_json(silent=True) or {}


def parse_required_string(
    data: dict[str, Any],
    field_name: str,
    *,
    default: Any = None,
) -> tuple[str | None, tuple[Any, int] | None]:
    """Return a trimmed required string field or a validation error."""
    value = data.get(field_name, default)
    if value is None:
        return None, json_error(f'{field_name} is required')

    text = str(value).strip()
    if not text:
        return None, json_error(f'{field_name} is required')
    return text, None


def parse_int_field(
    data: dict[str, Any],
    field_name: str,
    *,
    minimum: int | None = None,
    required: bool = True,
    default: Any = None,
) -> tuple[int | None, tuple[Any, int] | None]:
    """Return a validated integer field or a validation error."""
    value = data.get(field_name, default)
    parsed_value: int | None = None
    error_response: tuple[Any, int] | None = None

    if value is None:
        if required:
            error_response = json_error(f'{field_name} is required')
    else:
        try:
            parsed_value = int(value)
        except (TypeError, ValueError):
            error_response = json_error(f'{field_name} must be a valid integer')

        if error_response is None and minimum is not None and parsed_value is not None:
            if parsed_value < minimum:
                if minimum == 0:
                    error_response = json_error(
                        f'{field_name} must be non-negative'
                    )
                elif minimum == 1:
                    error_response = json_error(
                        f'{field_name} must be a positive integer'
                    )
                else:
                    error_response = json_error(
                        f'{field_name} must be at least {minimum}'
                    )

                parsed_value = None

    return parsed_value, error_response


def parse_string_list(
    values: Any,
    field_name: str,
) -> tuple[list[str] | None, tuple[Any, int] | None]:
    """Return a list of trimmed non-empty strings or a validation error."""
    if not isinstance(values, list):
        values = [values]

    parsed_values: list[str] = []
    for value in values:
        text = str(value).strip()
        if not text:
            return None, json_error(
                f'{field_name} must be non-empty strings'
            )
        parsed_values.append(text)

    return parsed_values, None


def json_error(message: str, status: int = 400) -> tuple[Any, int]:
    """Return a standard JSON error payload and HTTP status code."""
    return {'error': message}, status


def validate_payload(
    model_class,
    data: dict[str, Any],
) -> tuple[Any | None, tuple[dict[str, Any], int] | None]:
    """Validate request data with a SQLModel/Pydantic schema."""
    try:
        return model_class.model_validate(data), None
    except ValidationError as error:
        return None, ({'error': error.errors()}, 400)
