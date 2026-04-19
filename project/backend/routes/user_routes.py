from flask import Blueprint, jsonify, request
from flask_login import current_user, logout_user

from ..db.models import db
from ..utils.serializers import serialize_user
from .common import get_json_data, require_current_user, require_current_user_id

user_bp = Blueprint('user', __name__)


@user_bp.route('/users/', methods=['GET'])
def list_users():
    user, error_response = require_current_user()
    if error_response:
        return error_response
    assert user is not None
    return jsonify([serialize_user(user)])


@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user, error_response = require_current_user_id(user_id)
    if error_response:
        return error_response
    assert user is not None
    return jsonify(serialize_user(user))


@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
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
    user, error_response = require_current_user_id(user_id)
    if error_response:
        return error_response
    assert user is not None

    db.session.delete(user)
    db.session.commit()
    current_user_id = current_user.get_id()
    if current_user.is_authenticated and current_user_id and int(current_user_id) == user_id:
        logout_user()
    return jsonify({'message': 'User deleted'})