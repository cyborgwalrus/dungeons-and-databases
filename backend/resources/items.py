"""Inventory resources for creating, reading, and deleting items."""

from __future__ import annotations

from flask import request
from flask_restful import Resource

from backend.db.models import Item, db
from backend.utils.game_utils import add_inventory_item, remove_inventory_item
from backend.utils.route_helpers import (
    get_json_data,
    json_error,
    parse_string_list,
    require_current_character,
    require_item,
)
from backend.utils.api_response_cache import invalidate_user_inventory_cache


class ItemListResource(Resource):
    """Create one or more inventory items for the current character."""

    def post(self):
        """Create one or more inventory items for the current character."""
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

        source_ids, error_response = parse_string_list(source_ids, 'item_type_id')
        if error_response:
            return error_response
        assert source_ids is not None

        created_items: list[Item] = []
        for source_id in source_ids:
            item = add_inventory_item(character, source_id)
            if not item:
                return json_error('Item not found', 404)
            created_items.append(item)

        db.session.commit()
        invalidate_user_inventory_cache(character.user_id)
        return [item.to_dict() for item in created_items], 201


class ItemResource(Resource):
    """Read or delete a single inventory item."""

    def get(self, item_id: int):
        """Read or delete a single inventory item."""
        character, error_response = require_current_character()
        if error_response:
            return error_response
        assert character is not None
        item, error_response = require_item(character, item_id)
        if error_response:
            return error_response
        return item.to_dict()

    def delete(self, item_id: int):
        """Remove an item from the current character's inventory."""
        character, error_response = require_current_character()
        if error_response:
            return error_response
        assert character is not None
        inventory_item = remove_inventory_item(character, item_id)

        if not inventory_item:
            return json_error('Item not in inventory', 404)

        db.session.commit()
        invalidate_user_inventory_cache(character.user_id)
        return {'message': 'Item removed from inventory'}


def register_item_resources(api):
    """Register item routes on the provided API instance."""
    api.add_resource(ItemListResource, '/items')
    api.add_resource(ItemResource, '/items/<int:item_id>')
