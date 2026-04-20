from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from ..db.models import User, db
from ..utils.game_utils import get_current_user as get_authenticated_user, get_player, issue_auth_token
from ..utils.serializers import serialize_user
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
    user.password = generate_password_hash(password)
    db.session.add(user)
    db.session.commit()
    token = issue_auth_token(user.id)
    return jsonify({'message': 'signup complete', 'user': serialize_user(user), 'token': token}), 201


@auth_bp.route('/login/signin', methods=['POST'])
def signin():
    data = get_json_data(request)
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''

    user = User.query.filter_by(username=username).first()
    if not user:
        return json_error('invalid username or password', 401)

    password_matches = False
    try:
        password_matches = check_password_hash(user.password, password)
    except (TypeError, ValueError):
        password_matches = False

    if not password_matches:
        return json_error('invalid username or password', 401)

    token = issue_auth_token(user.id)
    return jsonify({'message': 'signin complete', 'user': serialize_user(user), 'token': token})


@auth_bp.route('/login/signout', methods=['POST'])
def signout():
    return jsonify({'message': 'signed out'})


@auth_bp.route('/login/me', methods=['GET'])
def me():
    user = get_authenticated_user()
    if not user:
        return json_error('Unauthorized', 401)
    character = get_player()
    return jsonify({'user': serialize_user(user), 'character': None if not character else character.to_dict(include_inventory=True)})