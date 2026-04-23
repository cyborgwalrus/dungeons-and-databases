"""Database models and initialization helpers for the backend."""

from __future__ import annotations

from backend.db.models import EnemyType, ItemType, db
from backend.utils.app_init import cache
from backend.utils.game_utils import load_enemy_type_seed_data, load_item_type_seed_data


def seed_reference_data() -> None:
    """Load static item and enemy types into the database."""
    for item_type in load_item_type_seed_data():
        db.session.merge(ItemType.model_validate(item_type))
    for enemy_type in load_enemy_type_seed_data():
        db.session.merge(EnemyType.model_validate(enemy_type))
    db.session.commit()


def clear_db() -> None:
    """Drop all database objects and clear cached app data."""
    db.session.remove()
    db.drop_all()
    cache.clear()


def init_db() -> None:
    """Create database objects, seed reference data, and clear cached app data."""
    db.create_all()
    seed_reference_data()
    cache.clear()


__all__ = ['clear_db', 'init_db', 'seed_reference_data']
