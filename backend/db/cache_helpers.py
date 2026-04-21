from typing import Any

from backend.db.models import EnemyType, ItemType
from backend.utils.app_cache import cache


@cache.memoize(timeout=3600)
def get_item_type_data(item_type_id: int) -> dict[str, Any] | None:
    """Fetch a cached item type record by ID."""
    item_type = ItemType.query.get(item_type_id)
    return item_type.to_dict() if item_type else None


@cache.memoize(timeout=3600)
def get_all_item_type_data() -> list[dict[str, Any]]:
    """Fetch all cached item type records."""
    return [item_type.to_dict() for item_type in ItemType.query.all()]


@cache.memoize(timeout=3600)
def get_enemy_type_data(enemy_type_id: int) -> dict[str, Any] | None:
    """Fetch a cached enemy type record by ID."""
    enemy_type = EnemyType.query.get(enemy_type_id)
    return enemy_type.to_dict() if enemy_type else None


@cache.memoize(timeout=3600)
def get_all_enemy_type_data() -> list[dict[str, Any]]:
    """Fetch all cached enemy type records."""
    return [enemy_type.to_dict() for enemy_type in EnemyType.query.all()]


def invalidate_reference_data_cache() -> None:
    """Clear cached reference-data lookups for items and enemies."""
    cache.delete_memoized(get_item_type_data)
    cache.delete_memoized(get_all_item_type_data)
    cache.delete_memoized(get_enemy_type_data)
    cache.delete_memoized(get_all_enemy_type_data)
