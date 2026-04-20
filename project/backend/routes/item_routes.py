from typing import Any

from flask import Blueprint, jsonify, request

from ..db.models import Character, CharacterEquipment, Item, db
from ..utils.game_utils import add_inventory_item, remove_inventory_item
from ..utils.serializers import serialize_character, serialize_item
from .common import get_item, get_item_type, get_json_data, json_error, require_current_character

item_bp = Blueprint('item', __name__)


def _equipped_items(character: Character) -> list[Item]:
    return sorted(
        [equipment.item for equipment in character.equipment if equipment.item],
        key=lambda item: ((item.item_type.slot.value if item and item.item_type and item.item_type.slot else 'zzz'), item.id or 0),
    )


def _apply_item_updates(item: Item, data: dict[str, Any]) -> tuple[Any, int] | None:
    item_type_id = data.get('item_type_id')
    if item_type_id is not None:
        item_type = get_item_type(item_type_id)
        if not item_type:
            return json_error('Item type not found', 404)
        item.item_type_id = item_type['id']

    for field, value in (
        ('name', data.get('name')),
        ('level', data.get('level')),
        ('health_bonus', data.get('health_bonus')),
        ('damage_bonus', data.get('damage_bonus')),
        ('bonus_health', data.get('bonus_health')),
        ('bonus_attack', data.get('bonus_attack')),
    ):
        if value is None:
            continue
        if field == 'name':
            item.name = value
        elif field in {'level', 'health_bonus', 'damage_bonus', 'bonus_health', 'bonus_attack'}:
            numeric_value = int(value)
            if field == 'level':
                item.level = numeric_value
            elif field in {'health_bonus', 'bonus_health'}:
                item.health_bonus = numeric_value
            else:
                item.damage_bonus = numeric_value

    if 'is_loot' in data:
        item.is_loot = bool(data['is_loot'])

    return None


def _equip_item(character: Character, item: Item) -> None:
    slot_type = item.item_type.slot if item.item_type else None
    if not slot_type:
        return

    if not character.user or not character.user.inventory:
        return

    existing_equipment = next((equipment for equipment in character.equipment if equipment.slot == slot_type), None)
    if existing_equipment:
        existing_item = existing_equipment.item
        if existing_item:
            existing_item.inventory_id = character.user.inventory.id
        db.session.delete(existing_equipment)

    item.inventory_id = None
    db.session.add(CharacterEquipment(character=character, item=item, slot=slot_type))


def _item_response(item: Item | None, status: int = 200) -> tuple[Any, int]:
    return jsonify(serialize_item(item)), status


def _message_response(message: str, status: int = 200) -> tuple[Any, int]:
    return jsonify({'message': message}), status


def _get_item_or_error(character: Character, item_id: int, message: str = 'Item not found') -> tuple[Item | None, tuple[Any, int] | None]:
    item = get_item(character, item_id)
    if not item:
        return None, json_error(message, 404)
    return item, None


@item_bp.route('/items/', methods=['POST'])
def create_item():
    character, error_response = require_current_character()
    if error_response:
        return error_response
    assert character is not None
    data = get_json_data(request)

    if isinstance(data, list):
        source_ids = data
    else:
        source_id = data.get('item_type_id', data.get('item_id'))
        source_ids = [source_id] if source_id is not None else []

    if not source_ids:
        return json_error('item_type_id is required')

    try:
        source_ids = [int(source_id) for source_id in source_ids]
    except (TypeError, ValueError):
        return json_error('item_type_id must be an integer')

    created_items: list[Item] = []
    for source_id in source_ids:
        item_type = get_item_type(source_id)
        if not item_type:
            return json_error('Item not found', 404)
        item = add_inventory_item(character, source_id, copy_from_item=False)
        created_items.append(item)

    db.session.commit()
    return jsonify([serialize_item(item) for item in created_items]), 201


@item_bp.route('/items/<int:item_id>', methods=['GET'])
def get_item_route(item_id: int):
    character, error_response = require_current_character()
    if error_response:
        return error_response
    assert character is not None
    item, error_response = _get_item_or_error(character, item_id)
    if error_response:
        return error_response
    return _item_response(item)


@item_bp.route('/items/<int:item_id>', methods=['PUT'])
def update_item(item_id: int):
    character, error_response = require_current_character()
    if error_response:
        return error_response
    assert character is not None
    item, error_response = _get_item_or_error(character, item_id)
    if error_response:
        return error_response
    assert item is not None

    data = get_json_data(request)
    error_response = _apply_item_updates(item, data)
    if error_response:
        return error_response

    if 'is_equipped' in data:
        return json_error('Use the character equipment endpoints to equip or unequip items', 400)

    db.session.commit()
    db.session.expire(character)
    return jsonify({'message': 'Item updated', 'item': serialize_item(item), 'character': serialize_character(character, include_inventory=True)})


@item_bp.route('/items/<int:item_id>', methods=['DELETE'])
def remove_item(item_id: int):
    character, error_response = require_current_character()
    if error_response:
        return error_response
    assert character is not None
    inventory_item = remove_inventory_item(character, item_id)

    if not inventory_item:
        return json_error('Item not in inventory', 404)

    db.session.commit()
    return _message_response('Item removed from inventory')
