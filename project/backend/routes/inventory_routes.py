from typing import Any

from flask import Blueprint, jsonify, request

from ..utils.game_utils import add_inventory_item, clear_player_equipment, clear_player_inventory, remove_inventory_item
from ..db.models import Character, Item, db
from ..utils.serializers import serialize_character, serialize_item
from .common import get_item, get_item_type, get_json_data, json_error, require_character_owner

inventory_bp = Blueprint('inventory', __name__)


def _equipped_items(character: Character) -> list[Item]:
    return sorted(
        [item for item in character.inventory if item.is_equipped],
        key=lambda item: ((item.item_type.slot.value if item.item_type and item.item_type.slot else 'zzz'), item.id or 0),
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
    if 'is_equipped' in data:
        item.is_equipped = bool(data['is_equipped'])

    return None


def _equip_item(character: Character, item: Item) -> None:
    slot_type = item.item_type.slot if item.item_type else None
    if slot_type:
        for equipped_item in _equipped_items(character):
            if equipped_item.id != item.id and equipped_item.item_type and equipped_item.item_type.slot == slot_type:
                equipped_item.is_equipped = False
    item.is_equipped = True


def _item_response(item: Item | None, status: int = 200) -> tuple[Any, int]:
    return jsonify(serialize_item(item)), status


def _player_response(character: Character, message: str, status: int = 200) -> tuple[Any, int]:
    return jsonify({'message': message, 'player': serialize_character(character, include_inventory=True)}), status


def _message_response(message: str, status: int = 200) -> tuple[Any, int]:
    return jsonify({'message': message}), status


def _get_item_or_error(character: Character, item_id: int, message: str = 'Item not found') -> tuple[Item | None, tuple[Any, int] | None]:
    item = get_item(character, item_id)
    if not item:
        return None, json_error(message, 404)
    return item, None


def _upgrade_reforge_item(item: Item) -> None:
    item.level = (item.level or 0) + 1
    item.health_bonus = (item.health_bonus or 0) * 2
    item.damage_bonus = (item.damage_bonus or 0) * 2
    if item.item_type and item.item_type.name:
        item.name = item.item_type.name


def _reforge_once(character: Character) -> bool:
    grouped_items: dict[tuple[int, int], list[Item]] = {}
    for item in sorted(character.inventory, key=lambda value: (value.item_type_id, value.level, 0 if value.is_equipped else 1, value.id or 0)):
        grouped_items.setdefault((item.item_type_id, item.level), []).append(item)

    for items in grouped_items.values():
        if len(items) < 3:
            continue

        selected_items = sorted(items, key=lambda value: (0 if value.is_equipped else 1, value.id or 0))[:3]
        source_item = next((value for value in selected_items if value.is_equipped), selected_items[0])

        for item in selected_items:
            if item.id != source_item.id:
                character.inventory.remove(item)
                db.session.delete(item)

        _upgrade_reforge_item(source_item)
        return True

    return False


def _equip_best_items(character: Character) -> bool:
    slot_order = ['helmet', 'armor', 'weapon', 'shield', 'ring', 'necklace']
    changed = False

    equipped_by_slot: dict[str, Item] = {}
    for equipped_item in _equipped_items(character):
        slot_value = equipped_item.item_type.slot.value if equipped_item.item_type and equipped_item.item_type.slot else None
        if slot_value and slot_value not in equipped_by_slot:
            equipped_by_slot[slot_value] = equipped_item

    for slot_value in slot_order:
        best_item = None
        best_score = -1

        for inventory_item in [item for item in character.inventory if not item.is_equipped]:
            item_slot = inventory_item.item_type.slot.value if inventory_item.item_type and inventory_item.item_type.slot else None
            if item_slot != slot_value:
                continue

            attack = inventory_item.damage_bonus or 0
            health = inventory_item.health_bonus or 0
            score = (attack * 10 + health) if slot_value == 'weapon' else (health * 10 + attack)
            if score > best_score:
                best_score = score
                best_item = inventory_item

        if not best_item:
            continue

        current_item = equipped_by_slot.get(slot_value)
        current_attack = current_item.damage_bonus if current_item else 0
        current_health = current_item.health_bonus if current_item else 0
        current_score = ((current_attack * 10 + current_health) if slot_value == 'weapon' else (current_health * 10 + current_attack)) if current_item else -1

        if best_score > current_score:
            _equip_item(character, best_item)
            equipped_by_slot[slot_value] = best_item
            changed = True

    return changed


@inventory_bp.route('/characters/<int:character_id>/inventory/', methods=['GET'])
def get_inventory(character_id: int):
    character, error_response = require_character_owner(character_id)
    if error_response:
        return error_response
    assert character is not None
    return jsonify([serialize_item(item) for item in character.inventory if not item.is_equipped])


@inventory_bp.route('/characters/<int:character_id>/inventory/equipped', methods=['GET'])
def get_equipped(character_id: int):
    character, error_response = require_character_owner(character_id)
    if error_response:
        return error_response
    assert character is not None
    return jsonify([serialize_item(item) for item in _equipped_items(character)])


@inventory_bp.route('/characters/<int:character_id>/inventory/items', methods=['GET'])
def get_all_items(character_id: int):
    character, error_response = require_character_owner(character_id)
    if error_response:
        return error_response
    assert character is not None
    return jsonify([serialize_item(item) for item in character.inventory])


@inventory_bp.route('/characters/<int:character_id>/inventory/', methods=['POST'])
def add_item_to_inventory(character_id: int, item_id: int | None = None):
    character, error_response = require_character_owner(character_id)
    if error_response:
        return error_response
    assert character is not None
    data = get_json_data(request)
    source_id = data.get('item_type_id', data.get('item_id', item_id))

    if source_id is None:
        return json_error('item_type_id is required')

    item = add_inventory_item(character, int(source_id), copy_from_item=False)
    if not item:
        return json_error('Item not found', 404)

    db.session.commit()
    return _item_response(item, 201)


@inventory_bp.route('/characters/<int:character_id>/inventory/', methods=['PUT'])
def update_inventory(character_id: int):
    character, error_response = require_character_owner(character_id)
    if error_response:
        return error_response
    assert character is not None
    data = get_json_data(request)
    item_id = data.get('item_id')
    if item_id is None:
        return json_error('item_id is required')

    item = get_item(character, item_id)
    if not item:
        return json_error('Item not found', 404)

    if data.get('is_equipped') is False:
        item.is_equipped = False
    else:
        _equip_item(character, item)

    db.session.commit()
    db.session.expire(character)
    return _player_response(character, 'Inventory updated')


@inventory_bp.route('/characters/<int:character_id>/inventory/', methods=['DELETE'])
def clear_inventory(character_id: int):
    character, error_response = require_character_owner(character_id)
    if error_response:
        return error_response
    assert character is not None
    clear_player_inventory(character)
    clear_player_equipment(character)
    db.session.commit()
    return jsonify({'message': 'Inventory cleared'})


@inventory_bp.route('/characters/<int:character_id>/inventory/unequip_all', methods=['POST'])
def unequip_all(character_id: int) -> Any:
    character, error_response = require_character_owner(character_id)
    if error_response:
        return error_response
    assert character is not None

    clear_player_equipment(character)
    db.session.commit()
    db.session.expire(character)
    return _player_response(character, 'Unequipped all items')


@inventory_bp.route('/characters/<int:character_id>/inventory/<int:item_id>', methods=['GET'])
def get_inventory_item(character_id: int, item_id: int):
    character, error_response = require_character_owner(character_id)
    if error_response:
        return error_response
    assert character is not None
    item, error_response = _get_item_or_error(character, item_id)
    if error_response:
        return error_response
    return _item_response(item)


@inventory_bp.route('/characters/<int:character_id>/inventory/<int:item_id>', methods=['POST'])
def duplicate_inventory_item(character_id: int, item_id: int):
    character, error_response = require_character_owner(character_id)
    if error_response:
        return error_response
    assert character is not None
    item = get_item(character, item_id)
    if not item:
        item_type = get_item_type(item_id)
        if not item_type:
            return json_error('Item not found', 404)
        item = add_inventory_item(character, item_type['id'], copy_from_item=False)
    else:
        item = add_inventory_item(character, item.id, copy_from_item=True)

    db.session.commit()
    return _item_response(item, 201)


@inventory_bp.route('/characters/<int:character_id>/inventory/<int:item_id>', methods=['PUT'])
def update_inventory_item(character_id: int, item_id: int):
    character, error_response = require_character_owner(character_id)
    if error_response:
        return error_response
    assert character is not None
    item, error_response = _get_item_or_error(character, item_id)
    if error_response:
        return error_response

    data = get_json_data(request)
    error_response = _apply_item_updates(item, data)
    if error_response:
        return error_response

    db.session.commit()
    db.session.expire(character)
    return jsonify({'message': 'Item updated', 'item': serialize_item(item), 'player': serialize_character(character, include_inventory=True)})


@inventory_bp.route('/characters/<int:character_id>/inventory/<int:item_id>', methods=['DELETE'])
def remove_inventory_item_route(character_id: int, item_id: int):
    character, error_response = require_character_owner(character_id)
    if error_response:
        return error_response
    assert character is not None
    inventory_item = remove_inventory_item(character, item_id)

    if not inventory_item:
        return json_error('Item not in inventory', 404)

    db.session.commit()
    return _message_response('Item removed from inventory')


@inventory_bp.route('/characters/<int:character_id>/inventory/equip_best_items', methods=['POST'])
def equip_best_items(character_id: int) -> Any:
    character, error_response = require_character_owner(character_id)
    if error_response:
        return error_response
    assert character is not None

    changed = _equip_best_items(character)
    db.session.commit()
    db.session.expire(character)

    message = 'Best items equipped' if changed else 'No better items found'
    return _player_response(character, message)


@inventory_bp.route('/forge/reforge_all/<int:character_id>', methods=['POST'])
def reforge_all_items(character_id: int) -> Any:
    character, error_response = require_character_owner(character_id)
    if error_response:
        return error_response
    assert character is not None
    made_changes = False

    while True:
        if not _reforge_once(character):
            break

        made_changes = True

    if not made_changes:
        return json_error('No items to reforge')

    db.session.commit()
    return _player_response(character, 'Reforge all complete')