"""User profile and inventory resources for the backend API."""

from flask import request
from flask_restful import Resource

from backend.db.models import User, db
from backend.utils.route_helpers import (
    get_json_data,
    parse_required_string,
)
from backend.utils.api_response_cache import (
    get_cached_user_data,
    get_cached_user_inventory_data,
    invalidate_user_inventory_cache,
    invalidate_user_profile_cache,
    invalidate_user_state_cache,
)


class UserResource(Resource):
    """Read, update, or delete a user profile."""

    def get(self, user: User):
        """Read, update, or delete a user profile."""
        return get_cached_user_data(user.id)

    def put(self, user: User):
        """Update a user's profile fields."""
        data = get_json_data(request)
        if 'username' in data:
            username, error_response = parse_required_string(data, 'username')
            if error_response:
                return error_response
            assert username is not None
            user.username = username
        if 'password' in data:
            password, error_response = parse_required_string(data, 'password')
            if error_response:
                return error_response
            assert password is not None
            user.password = password

        db.session.commit()
        invalidate_user_profile_cache(user.id)
        return user.to_dict()

    def delete(self, user: User):
        """Delete the authenticated user's account."""
        character_ids = [character.id for character in user.characters]
        db.session.delete(user)
        db.session.commit()
        invalidate_user_state_cache(user.id, character_ids)
        return {'message': 'User deleted'}


class UserItemsResource(Resource):
    """List or clear the user's shared inventory."""

    def get(self, user: User):
        """List or clear the user's shared inventory."""
        return get_cached_user_inventory_data(user.id)

    def delete(self, user: User):
        """Remove all items from the user's shared inventory."""
        removable_items = [item for item in user.items if not item.is_equipped]
        if removable_items:
            for item in removable_items:
                db.session.delete(item)
            db.session.commit()
            invalidate_user_inventory_cache(user.id)

        return {'message': 'Inventory cleared'}


def register_user_resources(api):
    """Register user routes on the provided API instance."""
    api.add_resource(UserResource, '/users/<user:user>')
    api.add_resource(UserItemsResource, '/users/<user:user>/inventory')
