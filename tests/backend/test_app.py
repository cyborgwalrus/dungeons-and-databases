"""Tests for backend application bootstrap and CLI helpers."""

import importlib.util
from pathlib import Path
import sys

import pytest
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from backend import app as app_module


def test_app_module_cli_commands_and_missing_secret_guard(app, monkeypatch):
    """Exercise the backend CLI commands and missing secret guard."""
    missing_secret_path = Path(__file__).resolve().parents[2] / 'backend' / 'app.py'
    monkeypatch.delenv('SECRET_KEY', raising=False)
    spec = importlib.util.spec_from_file_location('backend.app', missing_secret_path)
    assert spec is not None
    assert spec.loader is not None
    missing_secret_module = importlib.util.module_from_spec(spec)
    original_backend_app = sys.modules.get('backend.app')

    with pytest.raises(RuntimeError, match='SECRET_KEY must be set'):
        sys.modules['backend.app'] = missing_secret_module
        try:
            spec.loader.exec_module(missing_secret_module)
        finally:
            if original_backend_app is not None:
                sys.modules['backend.app'] = original_backend_app

    runner = app.test_cli_runner()
    init_result = runner.invoke(app_module.init_db)
    clear_result = runner.invoke(app_module.clear_db)

    assert init_result.exit_code == 0
    assert clear_result.exit_code == 0


def test_app_module_cli_reports_database_errors(app, monkeypatch):
    """Exercise the failure branches for the top-level CLI wrappers."""
    def raise_clear_db():
        raise OSError('clear failed')

    def raise_init_db():
        raise SQLAlchemyError('init failed')

    monkeypatch.setattr(app_module, 'clear_db_database', raise_clear_db)
    monkeypatch.setattr(app_module, 'init_db_database', raise_init_db)

    runner = app.test_cli_runner()
    clear_result = runner.invoke(app_module.clear_db)
    init_result = runner.invoke(app_module.init_db)

    assert clear_result.exit_code == 0
    assert clear_result.output.strip() == 'Failed to clear database: clear failed'
    assert init_result.exit_code == 0
    assert init_result.output.strip() == 'Failed to initialize database: init failed'


def test_app_http_exception_handler_and_openapi_endpoint(app):
    """Validate HTTPException JSON formatting and the raw OpenAPI route."""
    with app.app_context():
        response = app_module.handle_http_exception(HTTPException(description='boom'))

    assert response.status_code == 500
    assert response.get_json() == {'error': 'boom'}

    client = app.test_client()
    openapi_response = client.get('/api/openapi.yaml')
    assert openapi_response.status_code == 200
    assert openapi_response.mimetype == 'text/yaml'


def test_app_docs_page_renders_swagger_ui(app):
    """The Swagger UI page should render with a valid JS config."""
    client = app.test_client()
    docs_response = client.get('/api/docs')

    assert docs_response.status_code == 200
    body = docs_response.get_data(as_text=True)
    assert 'SwaggerUIBundle' in body
    assert 'url: "/api/apispec_1.json"' in body
    assert 'let auth_config = {};' in body
