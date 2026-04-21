from flask import request
from flask_restful import Resource
from werkzeug.security import check_password_hash, generate_password_hash

from backend.db.models import User, db
from backend.utils.game_utils import get_current_user as get_authenticated_user, get_player, issue_auth_token
from backend.utils.route_helpers import get_json_data, json_error


class SignupResource(Resource):
    def post(self):
        """Create a new user account and return an auth token."""
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
        db.session.flush()
        user.ensure_inventory()
        db.session.commit()
        token = issue_auth_token(user.id)
        return {'message': 'signup complete', 'user': user.to_dict(), 'token': token}, 201


class SigninResource(Resource):
    def post(self):
        """Authenticate a user and return an auth token."""
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
        return {'message': 'signin complete', 'user': user.to_dict(), 'token': token}


class SignoutResource(Resource):
    def post(self):
        """Return a sign-out response for the client to clear local auth state.
            Note: This does not invalidate the token on the server, but the client should discard it."""
        return {'message': 'signed out'}


class MeResource(Resource):
    def get(self):
        """Return the current authenticated user and active character, if any."""
        user = get_authenticated_user()
        if not user:
            return json_error('Unauthorized', 401)
        character = get_player()
        return {'user': user.to_dict(), 'character': None if not character else character.to_dict()}


def register_auth_resources(api):
    api.add_resource(SignupResource, '/api/login/signup')
    api.add_resource(SigninResource, '/api/login/signin')
    api.add_resource(SignoutResource, '/api/login/signout')
    api.add_resource(MeResource, '/api/login/me')
