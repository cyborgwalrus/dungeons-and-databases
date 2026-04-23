"""Tests for cache bootstrap helper configuration branches."""

from flask import Flask

from backend.utils import app_cache


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

    monkeypatch.setattr(app_cache.cache, 'init_app', fake_init_app)

    app_cache.init_cache(app)

    assert app.config['CACHE_TYPE'] == 'RedisCache'
    assert app.config['CACHE_DEFAULT_TIMEOUT'] == 120
    assert app.config['CACHE_REDIS_URL'] == 'redis://localhost:6379/1'
    assert init_calls['count'] == 1
