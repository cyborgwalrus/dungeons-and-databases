from flask import request
from flask_restful import Resource

from ..db.models import db
from ..utils.serializers import serialize_item, serialize_user
from .common import get_json_data, require_current_user_id


class UserResource(Resource):
    def get(self, user_id):
        """Return the requested user if the authenticated user owns it."""
        user, error_response = require_current_user_id(user_id)
        if error_response:
            return error_response
        assert user is not None
        return serialize_user(user)

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
        return serialize_user(user)

    def delete(self, user_id):
        """Delete the authenticated user's account."""
        user, error_response = require_current_user_id(user_id)
        if error_response:
            return error_response
        assert user is not None

        db.session.delete(user)
        db.session.commit()
        return {'message': 'User deleted'}


class UserInventoryResource(Resource):
    def get(self, user_id):
        """List the contents of the user's shared inventory."""
        user, error_response = require_current_user_id(user_id)
        if error_response:
            return error_response
        assert user is not None

        if not user.inventory:
            return []

        return [serialize_item(item) for item in user.inventory.items]

    def delete(self, user_id):
        """Remove all items from the user's shared inventory."""
        user, error_response = require_current_user_id(user_id)
        if error_response:
            return error_response
        assert user is not None

        if user.inventory:
            removable_items = list(user.inventory.items)
            for item in removable_items:
                user.inventory.items.remove(item)
                db.session.delete(item)
            db.session.commit()

        return {'message': 'Inventory cleared'}


def register_user_resources(api):
    api.add_resource(UserResource, '/api/users/<int:user_id>')
    api.add_resource(UserInventoryResource, '/api/users/<int:user_id>/inventory')