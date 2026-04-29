"""Application bootstrap helpers for the backend API."""

from __future__ import annotations

import os
from pathlib import Path

from flasgger import Swagger
from flask_caching import Cache
from flask import Flask
import yaml

from backend.utils.url_converters import (
    CombatConverter,
    CharacterConverter,
    ItemConverter,
    UserConverter,
)


cache = Cache()


def init_cache(app: Flask) -> None:
    """Configure and attach the shared Flask cache instance."""
    cache_type = os.environ.get('CACHE_TYPE', 'SimpleCache')
    cache_config = {
        'CACHE_TYPE': cache_type,
        'CACHE_DEFAULT_TIMEOUT': int(os.environ.get('CACHE_DEFAULT_TIMEOUT', '3600')),
    }

    redis_url = os.environ.get('CACHE_REDIS_URL') or os.environ.get('REDIS_URL')
    if redis_url:
        cache_config['CACHE_REDIS_URL'] = redis_url

    app.config.update(cache_config)
    cache.init_app(app)


def init_config(app: Flask) -> None:
    """Apply the runtime configuration required by the backend app."""
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        raise RuntimeError('SECRET_KEY must be set')

    app.config['SECRET_KEY'] = secret_key
    app.config['AUTH_TOKEN_MAX_AGE_SECONDS'] = int(
        os.environ.get('AUTH_TOKEN_MAX_AGE_SECONDS', 60 * 60 * 24 * 30)
    )
    app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', '').lower() in {'1', 'true', 'yes', 'on'}

    database_uri = os.environ.get('DATABASE_URL')
    if database_uri:
        app.config['SQLALCHEMY_DATABASE_URI'] = database_uri.replace('postgres://', 'postgresql://', 1)
    else:
        database_path = os.path.join(app.instance_path, 'game.db')
        os.makedirs(app.instance_path, exist_ok=True)
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


def init_swagger(app: Flask) -> Swagger:
    """Configure Swagger UI and return the initialized instance."""
    app.config['SWAGGER'] = {
        'title': 'Dungeons & Databases API',
        'uiversion': 3,
        'openapi': '3.0.3',
    }

    swagger_path = Path(app.root_path) / 'openapi.yaml'
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
    return Swagger(app, config=swagger_config, template=swagger_template)


def init_dashboard(app: Flask) -> None:
    """Initialize the monitoring dashboard integration."""
    import flask_monitoringdashboard as dashboard  # pylint: disable=import-outside-toplevel

    dashboard.config.init_from(file=str(Path(app.root_path).with_name('config.cfg')))
    dashboard.config.password = os.environ.get('ADMIN_PASSWORD', dashboard.config.password)
    dashboard.bind(app)


def init_converters(app: Flask) -> None:
    """Register custom URL converters used by the backend routes."""
    app.url_map.converters.update(
        {
            'user': UserConverter,
            'character': CharacterConverter,
            'item': ItemConverter,
            'combat': CombatConverter,
        }
    )
