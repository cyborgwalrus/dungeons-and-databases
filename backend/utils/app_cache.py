"""Shared cache instance and initialization helper."""

import os

from flask_caching import Cache


cache = Cache()


def init_cache(app) -> None:
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
