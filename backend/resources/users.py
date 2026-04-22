"""User profile and inventory resources for the backend API."""

from flask import request
from flask_restful import Resource

from backend.db.models import Item, User, db
from backend.db.schemas import UserUpdateRequest
from backend.utils.api_response_cache import (
    get_cached_user_data,
    get_cached_user_inventory_data,
    invalidate_user_inventory_cache,
    invalidate_user_profile_cache,
    invalidate_user_state_cache,
)
from backend.utils.route_helpers import validate_payload


class UserResource(Resource):
    """Read, update, or delete a user profile."""

    def get(self, user: User):
        """Read, update, or delete a user profile."""
        assert user.id is not None
        return get_cached_user_data(user.id)

    def put(self, user: User):
        """Update a user's profile fields."""
        assert user.id is not None
        data = request.get_json(silent=True) or {}
        payload, error_response = validate_payload(UserUpdateRequest, data)
        if error_response:
            return error_response
        assert payload is not None

        for field_name, value in payload.model_dump(exclude_unset=True).items():
            setattr(user, field_name, value)

        db.session.commit()
        invalidate_user_profile_cache(user.id)
        return user.to_response().model_dump()

    def delete(self, user: User):
        """Delete the authenticated user's account."""
        assert user.id is not None
        character_ids = [character.id for character in user.characters if character.id is not None]
        db.session.delete(user)
        db.session.commit()
        invalidate_user_state_cache(user.id, character_ids)
        return {'message': 'User deleted'}


class UserItemsResource(Resource):
    """List or clear the user's shared inventory."""

    def get(self, user: User):
        """List or clear the user's shared inventory."""
        assert user.id is not None
        return get_cached_user_inventory_data(user.id)

    def delete(self, user: User):
        """Remove all items from the user's shared inventory."""
        assert user.id is not None
        inventory_items = [
            item
            for item in Item.query.all()
            if item.user_id == user.id and not item.is_equipped
        ]
        deleted_count = 0
        for item in inventory_items:
            db.session.delete(item)
            deleted_count += 1
        if deleted_count:
            db.session.commit()
            invalidate_user_inventory_cache(user.id)

        return {'message': 'Inventory cleared'}


def register_user_resources(api):
    """Register user routes on the provided API instance."""
    api.add_resource(UserResource, '/users/<user:user>')
    api.add_resource(UserItemsResource, '/users/<user:user>/inventory')
