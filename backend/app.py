"""Application entry point for the backend API."""

from pathlib import Path

from flask import Flask, jsonify, redirect, send_from_directory
from flask_cors import CORS
from flask_restful import Api
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException

from backend.db import clear_db as clear_db_database, init_db as init_db_database
from backend.db.session import db
from backend.resources.authentication import register_auth_resources
from backend.resources.characters import register_character_resources
from backend.resources.combats import register_combat_resources
from backend.resources.items import register_item_resources
from backend.resources.users import register_user_resources
from backend.utils.app_init import (
    init_cache,
    init_config,
    init_converters,
    init_dashboard,
    init_swagger,
)


app = Flask(__name__)
basedir = Path(__file__).resolve().parent

init_config(app)
db.init_app(app)
init_cache(app)
CORS(app, resources={r"/api/*": {"origins": "*"}})
api = Api(app, prefix='/api')
init_converters(app)
init_swagger(app)


@app.errorhandler(HTTPException)
def handle_http_exception(error):
    """Return JSON for HTTP errors raised during routing or handler execution."""
    response = jsonify({'error': error.description or error.name})
    response.status_code = error.code or 500
    return response


@app.get('/')
def index():
    """Redirect direct backend visits to the API docs."""
    return redirect('/api/docs', code=302)


@app.get('/api/openapi.yaml')
def openapi_yaml():
    """Return the OpenAPI document used by Swagger UI."""
    return send_from_directory(basedir, 'openapi.yaml', mimetype='text/yaml')


@app.cli.command('clear-db')
def clear_db() -> None:
    """Drop the database tables and clear cached state."""
    try:
        clear_db_database()
        print('Database cleared')
    except (OSError, SQLAlchemyError) as error:
        print('Failed to clear database:', error)


@app.cli.command('init-db')
def init_db() -> None:
    """Create the database tables and clear cached state."""
    try:
        init_db_database()
        print('Database initialized')
    except (OSError, SQLAlchemyError) as error:
        print('Failed to initialize database:', error)

register_auth_resources(api)
register_user_resources(api)
register_character_resources(api)
register_item_resources(api)
register_combat_resources(api)

init_dashboard(app)
