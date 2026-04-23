"""Application entry point for the backend API."""

import os
from pathlib import Path

import yaml
from flasgger import Swagger
from flask import Flask, jsonify, send_from_directory
from flask_restful import Api
import flask_monitoringdashboard as dashboard
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException

from backend.db import clear_db, init_db
from backend.db.models import db
from backend.resources.authentication import register_auth_resources
from backend.resources.characters import register_character_resources
from backend.resources.combats import register_combat_resources
from backend.resources.items import register_item_resources
from backend.resources.users import register_user_resources
from backend.utils.app_cache import init_cache
from backend.utils.url_converters import (
    CombatConverter,
    CharacterConverter,
    ItemConverter,
    UserConverter,
)


app = Flask(__name__)
secret_key = os.environ.get('SECRET_KEY')
if not secret_key:
    raise RuntimeError('SECRET_KEY must be set')
app.config['SECRET_KEY'] = secret_key
app.config['AUTH_TOKEN_MAX_AGE_SECONDS'] = int(
    os.environ.get('AUTH_TOKEN_MAX_AGE_SECONDS', 60 * 60 * 24 * 30)
)
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', '').lower() in {'1', 'true', 'yes', 'on'}

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
database_path = os.path.join(app.instance_path, 'game.db')
os.makedirs(app.instance_path, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database, cache and api
db.init_app(app)
init_cache(app)
app.config['SWAGGER'] = {
    'title': 'Dungeons & Databases API',
    'uiversion': 3,
    'openapi': '3.0.3',
}
app.url_map.converters.update(
    {
        'user': UserConverter,
        'character': CharacterConverter,
        'item': ItemConverter,
        'combat': CombatConverter,
    }
)
api = Api(app, prefix='/api')
swagger_path = Path(__file__).with_name('openapi.yaml')
swagger_template = yaml.safe_load(swagger_path.read_text(encoding='utf-8'))
swagger_config = {
    'headers': [],
    'specs': [
        {
            'endpoint': 'apispec_1',
            'route': '/api/apispec_1.json',
            'rule_filter': lambda rule: False,
            'model_filter': lambda tag: False,
        }
    ],
    'static_url_path': '/flasgger_static',
    'swagger_ui': True,
    'specs_route': '/api/docs',
}
Swagger(app, config=swagger_config, template=swagger_template)


@app.errorhandler(HTTPException)
def handle_http_exception(error):
    """Return JSON for HTTP errors raised during routing or handler execution."""
    response = jsonify({'error': error.description or error.name})
    response.status_code = error.code or 500
    return response


@app.get('/api/openapi.yaml')
def openapi_yaml():
    """Return the OpenAPI document used by Swagger UI."""
    return send_from_directory(basedir, 'openapi.yaml', mimetype='text/yaml')


def register_db_commands(app: Flask) -> None:
    """Register database maintenance commands on the Flask app."""

    @app.cli.command('clear-db')
    def clear_db_command() -> None:
        try:
            clear_db()
            print('Database cleared')
        except (OSError, SQLAlchemyError) as error:
            print('Failed to clear database:', error)

    @app.cli.command('init-db')
    def init_db_command() -> None:
        try:
            init_db()
            print('Database initialized')
        except (OSError, SQLAlchemyError) as error:
            print('Failed to initialize database:', error)

register_auth_resources(api)
register_user_resources(api)
register_character_resources(api)
register_item_resources(api)
register_combat_resources(api)
register_db_commands(app)

dashboard.config.init_from(file=str(Path(__file__).with_name('config.cfg')))
dashboard.config.password = os.environ.get('ADMIN_PASSWORD', dashboard.config.password)
dashboard.bind(app)
