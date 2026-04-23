"""Item template seed data kept in memory."""

from __future__ import annotations

from typing import Any


ITEM_TYPES: tuple[dict[str, object], ...] = (
    {
        'id': 'steel_sword',
        'name': 'Steel Sword',
        'slot': 'weapon',
        'health': 0,
        'damage': 10,
    },
    {
        'id': 'linen_armor',
        'name': 'Linen Armor',
        'slot': 'armor',
        'health': 10,
        'damage': 0,
    },
    {
        'id': 'iron_helmet',
        'name': 'Iron Helmet',
        'slot': 'helmet',
        'health': 8,
        'damage': 0,
    },
    {
        'id': 'ruby_necklace',
        'name': 'Ruby Necklace',
        'slot': 'necklace',
        'health': 5,
        'damage': 4,
    },
    {
        'id': 'silver_ring',
        'name': 'Silver Ring',
        'slot': 'ring',
        'health': 4,
        'damage': 5,
    },
    {
        'id': 'iron_shield',
        'name': 'Iron Shield',
        'slot': 'shield',
        'health': 9,
        'damage': 0,
    },
)


def get(item_type_id: str | None) -> dict[str, Any] | None:
    """Return one item template by id or ``None`` when missing."""
    if item_type_id is None:
        return None
    normalized_id = str(item_type_id).strip()
    if not normalized_id:
        return None
    for template in ITEM_TYPES:
        if template['id'] == normalized_id:
            return dict(template)
    return None


def get_all() -> list[dict[str, Any]]:
    """Return all item templates as mutable dictionaries."""
    return [dict(template) for template in ITEM_TYPES]
