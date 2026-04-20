from typing import Any

from ..db.models import Character, Encounter, Item, ItemType, User


ITEM_SLOT_ORDER = {
    'helmet': 0,
    'armor': 1,
    'weapon': 2,
    'shield': 3,
    'ring': 4,
    'necklace': 5,
}


def _slot_value(item: Any) -> str | None:
    if not item or not item.item_type or not item.item_type.slot:
        return None
    return item.item_type.slot.value


def _sort_key(item: Any) -> tuple[int, int]:
    slot_value = _slot_value(item)
    return (ITEM_SLOT_ORDER.get(slot_value, 999) if slot_value is not None else 999, item.id or 0)


def serialize_item_type(item_type: ItemType | None) -> dict[str, Any] | None:
    if not item_type:
        return None
    return {
        'id': item_type.id,
        'name': item_type.name,
        'slot': item_type.slot.value if item_type.slot else None,
        'base_health_bonus': item_type.base_health_bonus,
        'base_damage_bonus': item_type.base_damage_bonus,
    }


def serialize_item(item: Item | None) -> dict[str, Any] | None:
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
        'health_bonus': item.health_bonus or 0,
        'damage_bonus': item.damage_bonus or 0,
        'item_type': serialize_item_type(item.item_type),
    }


def serialize_character(character: Character | None, include_inventory: bool = False) -> dict[str, Any] | None:
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
    if not user:
        return None
    return {
        'id': user.id,
        'username': user.username,
        'characters': [serialize_character(character) for character in user.characters],
        'inventory': None if not user.inventory else {'id': user.inventory.id, 'user_id': user.inventory.user_id, 'items': [serialize_item(item) for item in user.inventory.items]},
    }


def serialize_encounter(encounter: Encounter | None) -> dict[str, Any] | None:
    if not encounter:
        return None
    return {
        'id': encounter.id,
        'character_id': encounter.character_id,
        'enemy_type_id': encounter.enemy_type_id,
        'name': encounter.enemy_type.name if encounter.enemy_type else None,
        'health': encounter.enemy_health,
        'max_health': encounter.enemy_max_health,
        'damage': encounter.enemy_damage,
        'level': encounter.enemy_level,
        'description': encounter.enemy_type.description if encounter.enemy_type else None,
    }
