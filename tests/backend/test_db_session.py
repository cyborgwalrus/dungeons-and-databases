"""Tests for SQLModel session wrapper bootstrap behavior."""

from types import SimpleNamespace

import pytest
from flask import Flask

from backend.db import session as session_module
from backend.db.session import _Database


def _counter_callback(counter, key):
    """Return a callback that increments a named counter."""

    def _callback():
        counter[key] += 1

    return _callback


def test_session_init_app_requires_database_uri():
    """init_app should fail when SQLALCHEMY_DATABASE_URI is missing."""
    app = Flask(__name__)
    database = _Database()

    with pytest.raises(RuntimeError, match='SQLALCHEMY_DATABASE_URI must be set'):
        database.init_app(app)


def test_session_create_and_drop_require_initialized_engine():
    """create_all and drop_all should reject calls before init_app."""
    database = _Database()

    with pytest.raises(RuntimeError, match='Database engine is not initialized'):
        database.create_all()

    with pytest.raises(RuntimeError, match='Database engine is not initialized'):
        database.drop_all()


def test_session_init_app_replaces_previous_bind_and_cleans_on_teardown(monkeypatch):
    """Reinitializing should clean old resources and teardown should clean new ones."""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://example/db'
    database = _Database()

    calls = {
        'old_remove': 0,
        'old_dispose': 0,
        'new_remove': 0,
        'new_dispose': 0,
    }

    database.session = SimpleNamespace(remove=_counter_callback(calls, 'old_remove'))
    database.engine = SimpleNamespace(dispose=_counter_callback(calls, 'old_dispose'))

    new_engine = SimpleNamespace(dispose=_counter_callback(calls, 'new_dispose'))
    new_session = SimpleNamespace(remove=_counter_callback(calls, 'new_remove'))

    captured = {'uri': None, 'connect_args': None, 'sessionmaker_kwargs': None}

    def fake_create_engine(uri, connect_args):
        captured['uri'] = uri
        captured['connect_args'] = connect_args
        return new_engine

    def fake_sessionmaker(**kwargs):
        captured['sessionmaker_kwargs'] = kwargs
        return 'factory'

    def fake_scoped_session(_factory):
        return new_session

    monkeypatch.setattr(session_module, 'create_engine', fake_create_engine)
    monkeypatch.setattr(session_module, 'sessionmaker', fake_sessionmaker)
    monkeypatch.setattr(session_module, 'scoped_session', fake_scoped_session)

    database.init_app(app)

    assert calls['old_remove'] == 1
    assert calls['old_dispose'] == 1
    assert captured['uri'] == 'postgresql://example/db'
    assert captured['connect_args'] == {}
    assert captured['sessionmaker_kwargs']['bind'] is new_engine
    assert captured['sessionmaker_kwargs']['expire_on_commit'] is False
    assert database.session is new_session
    assert database.engine is new_engine

    with app.app_context():
        pass

    assert calls['new_remove'] == 1
    assert calls['new_dispose'] == 1


def test_session_init_app_uses_sqlite_connect_args(monkeypatch):
    """SQLite URIs should force check_same_thread=False when creating engine."""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tmp/test.db'
    database = _Database()

    captured = {'connect_args': None}

    def fake_create_engine(_uri, connect_args):
        captured['connect_args'] = connect_args
        return SimpleNamespace(dispose=lambda: None)

    monkeypatch.setattr(session_module, 'create_engine', fake_create_engine)
    monkeypatch.setattr(session_module, 'sessionmaker', lambda **_kwargs: 'factory')
    monkeypatch.setattr(
        session_module,
        'scoped_session',
        lambda _factory: SimpleNamespace(remove=lambda: None),
    )

    database.init_app(app)

    assert captured['connect_args'] == {'check_same_thread': False}
