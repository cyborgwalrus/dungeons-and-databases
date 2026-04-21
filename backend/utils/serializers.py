from typing import Any

from backend.db.models import Character, Encounter, Item, ItemType, User


def serialize_item_type(item_type: ItemType | None) -> dict[str, Any] | None:
    """Convert an item type model into the API shape used by the client."""
    return item_type.to_dict() if item_type else None


def serialize_item(item: Item | None) -> dict[str, Any] | None:
    """Convert an item model into a JSON-safe payload for the API."""
    return item.to_dict() if item else None


def serialize_character(character: Character | None, include_inventory: bool = False) -> dict[str, Any] | None:
    """Serialize a character and optionally include inventory and equipment."""
    if not character:
        return None
    return character.to_dict(include_inventory=include_inventory)


def serialize_user(user: User | None) -> dict[str, Any] | None:
    """Serialize a user together with their characters and inventory."""
    return user.to_dict() if user else None


def serialize_encounter(encounter: Encounter | None) -> dict[str, Any] | None:
    """Serialize the active dungeon encounter for the combat UI."""
    return encounter.to_dict() if encounter else None
