from flask import request
from flask_restful import Resource

from backend.db.models import db
from backend.utils.route_helpers import get_json_data, require_current_user_id
from backend.utils.api_response_cache import (
    get_cached_user_data,
    get_cached_user_inventory_data,
    invalidate_user_inventory_cache,
    invalidate_user_profile_cache,
    invalidate_user_state_cache,
)


class UserResource(Resource):
    def get(self, user_id):
        """Return the requested user if the authenticated user owns it."""
        user, error_response = require_current_user_id(user_id)
        if error_response:
            return error_response
        assert user is not None
        return get_cached_user_data(user_id)

    def put(self, user_id):
        """Update a user's profile fields."""
        user, error_response = require_current_user_id(user_id)
        if error_response:
            return error_response
        assert user is not None

        data = get_json_data(request)
        if 'username' in data:
            user.username = data['username']
        if 'password' in data:
            user.password = data['password']

        db.session.commit()
        invalidate_user_profile_cache(user.id)
        return user.to_dict()

    def delete(self, user_id):
        """Delete the authenticated user's account."""
        user, error_response = require_current_user_id(user_id)
        if error_response:
            return error_response
        assert user is not None

        character_ids = [character.id for character in user.characters]
        db.session.delete(user)
        db.session.commit()
        invalidate_user_state_cache(user_id, character_ids)
        return {'message': 'User deleted'}


class UserItemsResource(Resource):
    def get(self, user_id):
        """List the contents of the user's shared inventory."""
        user, error_response = require_current_user_id(user_id)
        if error_response:
            return error_response
        assert user is not None
        return get_cached_user_inventory_data(user_id)

    def delete(self, user_id):
        """Remove all items from the user's shared inventory."""
        user, error_response = require_current_user_id(user_id)
        if error_response:
            return error_response
        assert user is not None

        removable_items = [item for item in user.items if not item.is_equipped]
        if removable_items:
            for item in removable_items:
                db.session.delete(item)
            db.session.commit()
            invalidate_user_inventory_cache(user_id)

        return {'message': 'Inventory cleared'}


def register_user_resources(api):
    api.add_resource(UserResource, '/api/users/<int:user_id>')
    api.add_resource(UserItemsResource, '/api/users/<int:user_id>/inventory')
