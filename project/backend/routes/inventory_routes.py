from typing import Any

from flask import Blueprint, jsonify, request

from ..game_utils import add_inventory_item, apply_item_type_stats, clear_player_equipment, clear_player_inventory, remove_inventory_item, get_upgraded_item
from ..db.models import Character, Item, db
from ..serializers import serialize_character, serialize_item
from .common import get_character, get_item, get_item_type, get_json_data, json_error

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
        item.item_type_id = item_type.id

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


def _copy_upgraded_item_state(target_item: Item, upgraded_item: Item) -> None:
    target_item.level = upgraded_item.level
    target_item.is_loot = upgraded_item.is_loot
    target_item.item_type_id = upgraded_item.item_type_id
    apply_item_type_stats(target_item, upgraded_item.item_type)


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


def _build_reforge_groups(character: Character) -> dict[tuple[int, int], list[dict[str, Any]]]:
    groups: dict[tuple[int, int], list[dict[str, Any]]] = {}
    for inventory_item in Item.query.filter_by(owner_id=character.id, is_equipped=False).all():
        groups.setdefault((inventory_item.item_type_id, inventory_item.level), []).append({'kind': 'inventory', 'row': inventory_item})
    for equipped_item in Item.query.filter_by(owner_id=character.id, is_equipped=True).all():
        groups.setdefault((equipped_item.item_type_id, equipped_item.level), []).append({'kind': 'equipped', 'row': equipped_item})
    return groups


def _find_reforge_source(groups: dict[tuple[int, int], list[dict[str, Any]]]) -> dict[str, Any] | None:
    return next((group[0] for group in groups.values() if len(group) >= 3), None)


def _consume_reforge_items(items_to_consume: list[dict[str, Any]], source_row: Any) -> None:
    for entry in items_to_consume:
        if entry['row'] is not source_row:
            db.session.delete(entry['row'])


def _apply_reforge_result(character: Character, source_row: Item | None, upgraded_item: Item) -> tuple[Any, int] | None:
    if source_row:
        _copy_upgraded_item_state(source_row, upgraded_item)
        db.session.delete(upgraded_item)
        return None

    new_item = add_inventory_item(character, upgraded_item.item_type_id)
    if not new_item:
        return json_error('Unable to create upgraded item', 500)

    _copy_upgraded_item_state(new_item, upgraded_item)
    db.session.delete(upgraded_item)
    return None


def _reforge_next_batch(character: Character) -> bool | tuple[Any, int] | None:
    groups = _build_reforge_groups(character)
    if not groups:
        return None

    upgrade_source = _find_reforge_source(groups)
    if not upgrade_source:
        return None

    group_key = (upgrade_source['row'].item_type_id, upgrade_source['row'].level)
    items_to_consume = groups[group_key][:3]
    source_row = next((entry['row'] for entry in items_to_consume if entry['kind'] == 'equipped'), None)
    _consume_reforge_items(items_to_consume, source_row)

    upgraded = get_upgraded_item(upgrade_source['row'])
    if not upgraded:
        return json_error('Unable to reforge item', 500)

    error_response = _apply_reforge_result(character, source_row, upgraded)
    if error_response:
        return error_response

    db.session.commit()
    return True


@inventory_bp.route('/characters/<int:character_id>/inventory/', methods=['GET'])
def get_inventory(character_id: int):
    character = get_character(character_id)
    return jsonify([serialize_item(item) for item in character.inventory if not item.is_equipped])


@inventory_bp.route('/characters/<int:character_id>/inventory/equipped', methods=['GET'])
def get_equipped(character_id: int):
    character = get_character(character_id)
    return jsonify([serialize_item(item) for item in _equipped_items(character)])


@inventory_bp.route('/characters/<int:character_id>/inventory/items', methods=['GET'])
def get_all_items(character_id: int):
    character = get_character(character_id)
    return jsonify([serialize_item(item) for item in character.inventory])


@inventory_bp.route('/characters/<int:character_id>/inventory/', methods=['POST'])
def add_item_to_inventory(character_id: int, item_id: int | None = None):
    character = get_character(character_id)
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
    character = get_character(character_id)
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
    character = get_character(character_id)
    clear_player_inventory(character)
    clear_player_equipment(character)
    db.session.commit()
    return jsonify({'message': 'Inventory cleared'})


@inventory_bp.route('/characters/<int:character_id>/inventory/<int:item_id>', methods=['GET'])
def get_inventory_item(character_id: int, item_id: int):
    character = get_character(character_id)
    item, error_response = _get_item_or_error(character, item_id)
    if error_response:
        return error_response
    return _item_response(item)


@inventory_bp.route('/characters/<int:character_id>/inventory/<int:item_id>', methods=['POST'])
def duplicate_inventory_item(character_id: int, item_id: int):
    character = get_character(character_id)
    item = get_item(character, item_id)
    if not item:
        item_type = get_item_type(item_id)
        if not item_type:
            return json_error('Item not found', 404)
        item = add_inventory_item(character, item_type.id, copy_from_item=False)
    else:
        item = add_inventory_item(character, item.id, copy_from_item=True)

    db.session.commit()
    return _item_response(item, 201)


@inventory_bp.route('/characters/<int:character_id>/inventory/<int:item_id>', methods=['PUT'])
def update_inventory_item(character_id: int, item_id: int):
    character = get_character(character_id)
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
    character = get_character(character_id)
    inventory_item = remove_inventory_item(character, item_id)

    if not inventory_item:
        return json_error('Item not in inventory', 404)

    db.session.commit()
    return _message_response('Item removed from inventory')


@inventory_bp.route('/forge/reforge_all/<int:character_id>', methods=['POST'])
def reforge_all_items(character_id: int) -> Any:
    character = get_character(character_id)
    made_changes = False

    while True:
        result = _reforge_next_batch(character)
        if result is None:
            break
        if result is not True:
            return result

        made_changes = True

    if not made_changes:
        return json_error('No items to reforge')

    db.session.expire(character)
    return _player_response(character, 'Reforge all complete')