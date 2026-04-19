from flask import Blueprint, jsonify, request
from flask_login import current_user, logout_user

from ..db.models import User, db
from ..utils.serializers import serialize_user
from .common import get_json_data, json_error

user_bp = Blueprint('user', __name__)


@user_bp.route('/users/', methods=['GET'])
def list_users():
    return jsonify([serialize_user(user) for user in User.query.all()])


@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return json_error('User not found', 404)
    return jsonify(serialize_user(user))


@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return json_error('User not found', 404)

    data = get_json_data(request)
    if 'username' in data:
        user.username = data['username']
    if 'password' in data:
        user.password = data['password']

    db.session.commit()
    return jsonify(serialize_user(user))


@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return json_error('User not found', 404)

    db.session.delete(user)
    db.session.commit()
    current_user_id = current_user.get_id()
    if current_user.is_authenticated and current_user_id and int(current_user_id) == user_id:
        logout_user()
    return jsonify({'message': 'User deleted'})