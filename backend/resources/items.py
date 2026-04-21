from __future__ import annotations

from flask import request
from flask_restful import Resource

from backend.db.models import Item, db
from backend.utils.game_utils import add_inventory_item, remove_inventory_item
from backend.utils.route_helpers import get_item, get_json_data, json_error, require_current_character
from backend.utils.serializers import serialize_item


class ItemListResource(Resource):
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

        try:
            source_ids = [int(source_id) for source_id in source_ids]
            if any(sid <= 0 for sid in source_ids):
                return json_error('item_type_id must be positive integers')
        except (TypeError, ValueError):
            return json_error('item_type_id must be a valid integer')

        created_items: list[Item] = []
        for source_id in source_ids:
            item = add_inventory_item(character, source_id)
            if not item:
                return json_error('Item not found', 404)
            created_items.append(item)

        db.session.commit()
        return [serialize_item(item) for item in created_items], 201


class ItemResource(Resource):
    def get(self, item_id: int):
        """Return a single inventory item owned by the current character."""
        character, error_response = require_current_character()
        if error_response:
            return error_response
        assert character is not None
        item = get_item(character, item_id)
        if not item:
            return json_error('Item not found', 404)
        return serialize_item(item)

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
        return {'message': 'Item removed from inventory'}


def register_item_resources(api):
    api.add_resource(ItemListResource, '/api/items')
    api.add_resource(ItemResource, '/api/items/<int:item_id>')
