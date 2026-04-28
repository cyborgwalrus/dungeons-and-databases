"""Inventory resources for creating, reading, and deleting items."""

from __future__ import annotations

from flask import request
from flask_restful import Resource

from backend.db.models import Item
from backend.db.session import db
from backend.db.schemas import ItemCreateRequest
from backend.utils.game_utils import add_inventory_item, get_player as get_current_character
from backend.utils.hypermedia import inject_collection_links, inject_response_links
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
        return inject_collection_links(
            [item.to_response().model_dump() for item in created_items],
            user_id=character.user_id,
            character_id=character.id,
            character_state=character.state,
            equipped=False,
        ), 201


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
        active_character = get_current_character()
        return inject_response_links(
            item.to_response().model_dump(),
            user_id=item.user_id,
            character_id=None if active_character is None else active_character.id,
            character_state=None if active_character is None else active_character.state,
            equipped=False,
        )

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
    api.add_resource(ItemListResource, '/items', endpoint='item_list')
    api.add_resource(ItemResource, '/items/<item:item>', endpoint='item_detail')
