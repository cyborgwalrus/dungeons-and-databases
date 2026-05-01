"""Tests for backend app initialization helpers."""

from pathlib import Path
from types import SimpleNamespace
import sys

from flask import Flask
import pytest
import backend.utils.app_init as app_init


def test_init_cache_uses_redis_url_configuration(monkeypatch):
    """init_cache should include redis URL when present in environment."""
    app = Flask(__name__)

    monkeypatch.setenv('CACHE_TYPE', 'RedisCache')
    monkeypatch.setenv('CACHE_DEFAULT_TIMEOUT', '120')
    monkeypatch.setenv('CACHE_REDIS_URL', 'redis://localhost:6379/1')

    init_calls = {'count': 0}

    def fake_init_app(bound_app):
        assert bound_app is app
        init_calls['count'] += 1

    monkeypatch.setattr(app_init.cache, 'init_app', fake_init_app)

    app_init.init_cache(app)

    assert app.config['CACHE_TYPE'] == 'RedisCache'
    assert app.config['CACHE_DEFAULT_TIMEOUT'] == 120
    assert app.config['CACHE_REDIS_URL'] == 'redis://localhost:6379/1'
    assert init_calls['count'] == 1


def test_init_config_sets_runtime_configuration(monkeypatch):
    """init_config should honor environment overrides and instance storage."""
    app = Flask(__name__, instance_path=str(Path(app_init.__file__).resolve().parent.parent / 'instance-test'))

    monkeypatch.setenv('SECRET_KEY', 'config-secret')
    monkeypatch.setenv('AUTH_TOKEN_MAX_AGE_SECONDS', '1234')
    monkeypatch.setenv('FLASK_DEBUG', 'true')
    monkeypatch.setenv('DATABASE_URL', 'postgresql://example/db')

    app_init.init_config(app)

    assert app.config['SECRET_KEY'] == 'config-secret'
    assert app.config['AUTH_TOKEN_MAX_AGE_SECONDS'] == 1234
    assert app.config['DEBUG'] is True
    assert app.config['SQLALCHEMY_DATABASE_URI'] == 'postgresql://example/db'
    assert app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] is False


def test_init_config_requires_database_url(monkeypatch):
    """init_config should fail fast when DATABASE_URL is missing."""
    app = Flask(__name__, instance_path=str(Path(app_init.__file__).resolve().parent.parent / 'instance-test'))

    monkeypatch.setenv('SECRET_KEY', 'config-secret')
    monkeypatch.delenv('DATABASE_URL', raising=False)

    with pytest.raises(RuntimeError, match='DATABASE_URL must be set'):
        app_init.init_config(app)


def test_init_swagger_loads_template_and_configures_spec(monkeypatch):
    """init_swagger should load the OpenAPI template and pass swagger config through."""
    backend_root = Path(app_init.__file__).resolve().parents[1]
    app = Flask(__name__, root_path=str(backend_root))

    swagger_calls = {}

    class FakeSwagger:
        def __init__(self, bound_app, *, config, template):
            swagger_calls['app'] = bound_app
            swagger_calls['config'] = config
            swagger_calls['template'] = template

    monkeypatch.setattr(app_init, 'Swagger', FakeSwagger)

    swagger = app_init.init_swagger(app)

    assert isinstance(swagger, FakeSwagger)
    assert app.config['SWAGGER']['title'] == 'Dungeons & Databases API'
    assert app.config['SWAGGER']['auth'] == {}
    assert swagger_calls['app'] is app
    assert swagger_calls['config']['specs_route'] == '/api/docs'
    assert swagger_calls['config']['auth'] == {}
    assert swagger_calls['template']['openapi'].startswith('3.')


def test_init_dashboard_configures_and_binds_dashboard(monkeypatch):
    """init_dashboard should load config, override the password, and bind the app."""
    app = Flask(__name__)
    init_from_calls = []
    bind_calls = []

    def fake_init_from(**kwargs):
        init_from_calls.append(kwargs)

    def fake_bind(bound_app):
        bind_calls.append(bound_app)

    dashboard_module = SimpleNamespace(
        config=SimpleNamespace(
            password='default-password',
            init_from=fake_init_from,
        ),
        bind=fake_bind,
    )

    monkeypatch.setitem(sys.modules, 'flask_monitoringdashboard', dashboard_module)
    monkeypatch.setenv('ADMIN_PASSWORD', 'override-password')

    app_init.init_dashboard(app)

    assert init_from_calls == [{'file': str(Path(app.root_path).with_name('dashboard_config.cfg'))}]
    assert dashboard_module.config.password == 'override-password'
    assert bind_calls == [app]