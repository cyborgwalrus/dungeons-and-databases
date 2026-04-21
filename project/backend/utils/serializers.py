from typing import Any

from ..db.models import Character, Encounter, Item, ItemType, User


def _slot_value(item: Any) -> str | None:
    """Return the string slot for a nested item type, if present."""
    if not item or not item.item_type or not item.item_type.slot:
        return None
    return item.item_type.slot.value


def serialize_item_type(item_type: ItemType | None) -> dict[str, Any] | None:
    """Convert an item type model into the API shape used by the client."""
    if not item_type:
        return None
    return {
        'id': item_type.id,
        'name': item_type.name,
        'slot': item_type.slot.value if item_type.slot else None,
        'health': item_type.health,
        'damage': item_type.damage,
    }


def serialize_item(item: Item | None) -> dict[str, Any] | None:
    """Convert an item model into a JSON-safe payload for the API."""
    if not item:
        return None
    return {
        'id': item.id,
        'item_type_id': item.item_type_id,
        'owner_id': item.owner_id,
        'name': item.name,
        'level': item.level,
        'is_equipped': item.is_equipped,
        'slot': _slot_value(item),
        'is_loot': item.is_loot,
        'health': item.health or 0,
        'damage': item.damage or 0,
        'item_type': serialize_item_type(item.item_type),
    }


def serialize_character(character: Character | None, include_inventory: bool = False) -> dict[str, Any] | None:
    """Serialize a character and optionally include inventory and equipment."""
    if not character:
        return None

    equipped_items = character.equipment_to_dict() if hasattr(character, 'equipment_to_dict') else []
    data = {
        'id': character.id,
        'user_id': character.user_id,
        'name': character.name,
        'level': character.level,
        'experience': character.experience,
        'experience_to_next_level': character.experience_to_next_level,
        'max_health': character.max_health,
        'health': character.health,
        'damage': character.damage,
        'bonus_health': character.bonus_health,
        'bonus_damage': character.bonus_damage,
    }

    if include_inventory:
        data['inventory'] = [serialize_item(item) for item in character.inventory_items]
        data['equipped'] = equipped_items

    return data


def serialize_user(user: User | None) -> dict[str, Any] | None:
    """Serialize a user together with their characters and inventory."""
    if not user:
        return None
    return {
        'id': user.id,
        'username': user.username,
        'characters': [serialize_character(character) for character in user.characters],
        'inventory': None if not user.inventory else {'id': user.inventory.id, 'user_id': user.inventory.user_id, 'items': [serialize_item(item) for item in user.inventory.items]},
    }


def serialize_encounter(encounter: Encounter | None) -> dict[str, Any] | None:
    """Serialize the active dungeon encounter for the combat UI."""
    if not encounter:
        return None
    return {
        'id': encounter.id,
        'character_id': encounter.character_id,
        'enemy_type_id': encounter.enemy_type_id,
        'name': encounter.enemy_type.name if encounter.enemy_type else None,
        'health': encounter.health,
        'max_health': encounter.max_health,
        'damage': encounter.damage,
        'level': encounter.enemy_level,
        'description': encounter.enemy_type.description if encounter.enemy_type else None,
    }
