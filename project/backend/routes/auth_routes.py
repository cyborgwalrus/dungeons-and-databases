from flask import Blueprint, jsonify, request
from flask_login import current_user, login_user, logout_user

from ..db.models import User, db
from ..serializers import serialize_user
from .common import get_json_data, json_error

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login/signup', methods=['POST'])
def signup():
    data = get_json_data(request)
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''

    if not username or not password:
        return json_error('username and password are required')

    if User.query.filter_by(username=username).first():
        return json_error('username already exists', 409)

    user = User()
    user.username = username
    user.password = password
    db.session.add(user)
    db.session.commit()
    login_user(user)
    return jsonify({'message': 'signup complete', 'user': serialize_user(user)}), 201


@auth_bp.route('/login/signin', methods=['POST'])
def signin():
    data = get_json_data(request)
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''

    user = User.query.filter_by(username=username, password=password).first()
    if not user:
        return json_error('invalid username or password', 401)

    login_user(user)
    return jsonify({'message': 'signin complete', 'user': serialize_user(user)})


@auth_bp.route('/login/signout', methods=['POST'])
def signout():
    logout_user()
    return jsonify({'message': 'signed out'})


@auth_bp.route('/login/me', methods=['GET'])
def me():
    user_id = current_user.get_id() if current_user.is_authenticated else None
    user = User.query.get(int(user_id)) if user_id else None
    return jsonify({'user': serialize_user(user)})