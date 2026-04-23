"""Enemy template seed data kept in memory."""

from __future__ import annotations

from typing import Any


ENEMY_TYPES: tuple[dict[str, object], ...] = (
    {
        'id': 'goblin',
        'name': 'Goblin',
        'description': 'A weak goblin',
        'health': 20,
        'damage': 5,
    },
    {
        'id': 'slime',
        'name': 'Slime',
        'description': 'A sticky slime',
        'health': 14,
        'damage': 4,
    },
    {
        'id': 'skeleton',
        'name': 'Skeleton',
        'description': 'A rattling skeleton',
        'health': 18,
        'damage': 6,
    },
    {
        'id': 'wolf',
        'name': 'Wolf',
        'description': 'A hungry wolf',
        'health': 22,
        'damage': 7,
    },
    {
        'id': 'orc',
        'name': 'Orc',
        'description': 'A brutish orc',
        'health': 35,
        'damage': 8,
    },
    {
        'id': 'bandit',
        'name': 'Bandit',
        'description': 'A road bandit',
        'health': 28,
        'damage': 9,
    },
    {
        'id': 'mage',
        'name': 'Mage',
        'description': 'A rogue mage',
        'health': 24,
        'damage': 11,
    },
)


def get(enemy_type_id: str | None) -> dict[str, Any] | None:
    """Return one enemy template by id or ``None`` when missing."""
    if enemy_type_id is None:
        return None
    normalized_id = str(enemy_type_id).strip()
    if not normalized_id:
        return None
    for template in ENEMY_TYPES:
        if template['id'] == normalized_id:
            return dict(template)
    return None


def get_all() -> list[dict[str, Any]]:
    """Return all enemy templates as mutable dictionaries."""
    return [dict(template) for template in ENEMY_TYPES]
