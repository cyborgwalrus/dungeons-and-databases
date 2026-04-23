"""Tests for backend application bootstrap and CLI helpers."""

import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest
from flask import Flask
from sqlalchemy.exc import SQLAlchemyError

from backend import app as app_module
import backend.db as backend_db
import backend.utils.app_init as app_init


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

    assert init_from_calls == [{'file': str(Path(app.root_path).with_name('config.cfg'))}]
    assert dashboard_module.config.password == 'override-password'
    assert bind_calls == [app]


def test_init_cli_registers_database_commands(monkeypatch):
    """init_cli should register working init-db and clear-db commands."""
    app = Flask(__name__)
    calls = {'clear': 0, 'init': 0}

    def fake_clear_db():
        calls['clear'] += 1

    def fake_init_db():
        calls['init'] += 1

    monkeypatch.setattr(backend_db, 'clear_db', fake_clear_db)
    monkeypatch.setattr(backend_db, 'init_db', fake_init_db)

    app_init.init_cli(app)

    runner = app.test_cli_runner()

    clear_result = runner.invoke(args=['clear-db'])
    init_result = runner.invoke(args=['init-db'])

    assert clear_result.exit_code == 0
    assert clear_result.output.strip() == 'Database cleared'
    assert init_result.exit_code == 0
    assert init_result.output.strip() == 'Database initialized'
    assert calls == {'clear': 1, 'init': 1}


def test_init_cli_reports_database_errors(monkeypatch):
    """init_cli should catch and report database command failures."""
    app = Flask(__name__)

    def raise_clear_db():
        raise OSError('clear failed')

    def raise_init_db():
        raise SQLAlchemyError('init failed')

    monkeypatch.setattr(backend_db, 'clear_db', raise_clear_db)
    monkeypatch.setattr(backend_db, 'init_db', raise_init_db)

    app_init.init_cli(app)

    runner = app.test_cli_runner()

    clear_result = runner.invoke(args=['clear-db'])
    init_result = runner.invoke(args=['init-db'])

    assert clear_result.exit_code == 0
    assert clear_result.output.strip() == 'Failed to clear database: clear failed'
    assert init_result.exit_code == 0
    assert init_result.output.strip() == 'Failed to initialize database: init failed'