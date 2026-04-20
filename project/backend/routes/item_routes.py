from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify, request

from ..db.models import Character, Item, db
from ..utils.game_utils import add_inventory_item, remove_inventory_item
from ..utils.serializers import serialize_item
from .common import get_item, get_json_data, json_error, require_current_character

item_bp = Blueprint('item', __name__)


def _item_response(item: Item | None, status: int = 200) -> tuple[Any, int]:
    return jsonify(serialize_item(item)), status


def _message_response(message: str, status: int = 200) -> tuple[Any, int]:
    return jsonify({'message': message}), status


def _get_item_or_error(character: Character, item_id: int, message: str = 'Item not found') -> tuple[Item | None, tuple[Any, int] | None]:
    item = get_item(character, item_id)
    if not item:
        return None, json_error(message, 404)
    return item, None


@item_bp.route('/items', methods=['POST'])
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
        item = add_inventory_item(character, source_id)
        if not item:
            return json_error('Item not found', 404)
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
