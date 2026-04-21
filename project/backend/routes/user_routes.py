from flask import Blueprint, jsonify, request

from ..db.models import db
from ..utils.serializers import serialize_item, serialize_user
from .common import get_json_data, require_current_user_id

user_bp = Blueprint('user', __name__)


@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Return the requested user if the authenticated user owns it."""
    user, error_response = require_current_user_id(user_id)
    if error_response:
        return error_response
    assert user is not None
    return jsonify(serialize_user(user))


@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
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
    return jsonify(serialize_user(user))


@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete the authenticated user's account."""
    user, error_response = require_current_user_id(user_id)
    if error_response:
        return error_response
    assert user is not None

    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted'})


@user_bp.route('/users/<int:user_id>/inventory', methods=['GET'])
def list_user_inventory(user_id):
    """List the contents of the user's shared inventory."""
    user, error_response = require_current_user_id(user_id)
    if error_response:
        return error_response
    assert user is not None

    if not user.inventory:
        return jsonify([])

    return jsonify([serialize_item(item) for item in user.inventory.items])


@user_bp.route('/users/<int:user_id>/inventory', methods=['DELETE'])
def clear_user_inventory(user_id):
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

    return jsonify({'message': 'Inventory cleared'})