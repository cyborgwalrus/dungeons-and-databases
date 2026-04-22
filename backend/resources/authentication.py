"""Login and session resources for the backend API."""

from flask import request
from flask_restful import Resource
from werkzeug.security import check_password_hash, generate_password_hash

from backend.db.models import User, db
from backend.utils.game_utils import get_current_user, get_player, issue_auth_token
from backend.utils.route_helpers import get_json_data, json_error, parse_required_string


class SignupResource(Resource):
    """Create a new account and return an auth token."""

    def post(self):
        """Create a new account and return an auth token."""
        data = get_json_data(request)
        username, error_response = parse_required_string(data, 'username')
        if error_response:
            return error_response
        password, error_response = parse_required_string(data, 'password')
        if error_response:
            return error_response
        assert username is not None
        assert password is not None

        if User.query.filter_by(username=username).first():
            return json_error('username already exists', 409)

        user = User()
        user.username = username
        user.password = generate_password_hash(password)
        db.session.add(user)
        db.session.flush()
        db.session.commit()
        token = issue_auth_token(user.id)
        return {'message': 'signup complete', 'user': user.to_dict(), 'token': token}, 201


class SigninResource(Resource):
    """Authenticate an existing user and return an auth token."""

    def post(self):
        """Authenticate an existing user and return an auth token."""
        data = get_json_data(request)
        username, error_response = parse_required_string(data, 'username')
        if error_response:
            return error_response
        password, error_response = parse_required_string(data, 'password')
        if error_response:
            return error_response
        assert username is not None
        assert password is not None

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
    """Return a client-side sign-out response."""

    def post(self):
        """Return a client-side sign-out response."""
        return {'message': 'signed out'}


class MeResource(Resource):
    """Return the authenticated user and active character."""

    def get(self):
        """Return the authenticated user and active character."""
        user = get_current_user()
        if not user:
            return json_error('Unauthorized', 401)
        character = get_player()
        return {'user': user.to_dict(), 'character': None if not character else character.to_dict()}


def register_auth_resources(api):
    """Register authentication routes on the provided API instance."""
    api.add_resource(SignupResource, '/api/login/signup')
    api.add_resource(SigninResource, '/api/login/signin')
    api.add_resource(SignoutResource, '/api/login/signout')
    api.add_resource(MeResource, '/api/login/me')
