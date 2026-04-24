"""Inventory resources for creating, reading, and deleting items."""

from __future__ import annotations

from flask import request
from flask_restful import Resource

from backend.db.models import Item
from backend.db.session import db
from backend.db.schemas import ItemCreateRequest
from backend.utils.game_utils import add_inventory_item
from backend.utils.route_helpers import json_error, require_current_character, validate_payload
from backend.utils.api_response_cache import invalidate_user_inventory_cache


class ItemListResource(Resource):
    """Create one or more inventory items for the current character."""

    def post(self):
        """Create one or more inventory items for the current character.

        Returns:
            The created inventory items, or a JSON error response when the
            request payload is invalid or an item type cannot be found.
        """
        character, error_response = require_current_character()
        if error_response:
            return error_response
        assert character is not None
        data = request.get_json(silent=True) or {}

        if isinstance(data, list):
            source_ids = data
        else:
            source_id = data.get('item_type_id', data.get('item_id'))
            source_ids = [source_id] if source_id is not None else [None]

        created_items: list[Item] = []
        for source_id in source_ids:
            payload_data = {} if source_id is None else {'item_type_id': source_id}
            payload, error_response = validate_payload(ItemCreateRequest, payload_data)
            if error_response:
                return error_response
            assert payload is not None

            item = add_inventory_item(character, payload.item_type_id)
            if not item:
                return json_error('Item not found', 404)
            created_items.append(item)

        db.session.commit()
        invalidate_user_inventory_cache(character.user_id)
        return [item.to_response().model_dump() for item in created_items], 201


class ItemResource(Resource):
    """Read or delete a single inventory item."""

    def get(self, item: Item):
        """Return a single inventory item when it is not equipped.

        Args:
            item: The inventory item resolved from the route.

        Returns:
            The serialized inventory item, or a JSON error response when the
            item is currently equipped.
        """
        if item.is_equipped:
            return json_error('Item not found', 404)
        return item.to_response().model_dump()

    def delete(self, item: Item):
        """Remove an item from the current character's inventory.

        Args:
            item: The inventory item resolved from the route.

        Returns:
            A success message when the item is removed, or a JSON error
            response when the item is currently equipped.
        """
        if item.is_equipped:
            return json_error('Item not in inventory', 404)

        db.session.delete(item)
        db.session.commit()
        invalidate_user_inventory_cache(item.user_id)
        return {'message': 'Item removed from inventory'}


def register_item_resources(api):
    """Register item routes on the provided API instance."""
    api.add_resource(ItemListResource, '/items')
    api.add_resource(ItemResource, '/items/<item:item>')
