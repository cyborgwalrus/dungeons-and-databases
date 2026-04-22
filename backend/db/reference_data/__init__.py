"""Load and cache item and enemy reference data from JSON templates."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from backend.utils.app_cache import cache


_REFERENCE_DATA_DIR = Path(__file__).resolve().parent
_ITEM_TYPES_PATH = _REFERENCE_DATA_DIR / 'item_types.json'
_ENEMY_TYPES_PATH = _REFERENCE_DATA_DIR / 'enemy_types.json'


def load_template_collection(
    path: Path,
    required_fields: tuple[str, ...],
) -> tuple[dict[str, Any], ...]:
    """Load and validate a collection of template dictionaries from JSON."""
    with path.open('r', encoding='utf-8') as file:
        raw_templates = json.load(file)

    if not isinstance(raw_templates, list):
        raise ValueError(f'{path.name} must contain a JSON array')

    templates: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for index, raw_template in enumerate(raw_templates, start=1):
        if not isinstance(raw_template, dict):
            raise ValueError(f'{path.name} entry {index} must be an object')

        template_id = str(raw_template.get('id', '')).strip()
        if not template_id:
            raise ValueError(f'{path.name} entry {index} is missing an id')
        if template_id in seen_ids:
            raise ValueError(
                f'{path.name} contains duplicate template id {template_id!r}'
            )

        for field_name in required_fields:
            if field_name not in raw_template:
                raise ValueError(
                    f'{path.name} entry {index} is missing required field {field_name!r}'
                )

        template = dict(raw_template)
        template['id'] = template_id
        templates.append(template)
        seen_ids.add(template_id)

    return tuple(templates)


@lru_cache(maxsize=1)
def _load_item_templates() -> tuple[dict[str, Any], ...]:
    return load_template_collection(_ITEM_TYPES_PATH, ('name', 'slot', 'health', 'damage'))


@lru_cache(maxsize=1)
def _load_enemy_templates() -> tuple[dict[str, Any], ...]:
    return load_template_collection(_ENEMY_TYPES_PATH, ('name', 'description', 'health', 'damage'))


def get_all_item_templates() -> list[dict[str, Any]]:
    """Return all item templates as mutable dictionaries."""
    return [dict(template) for template in _load_item_templates()]


def get_item_template(template_id: str | None) -> dict[str, Any] | None:
    """Return a single item template by slug or ``None`` when missing."""
    if template_id is None:
        return None
    normalized_id = str(template_id).strip()
    if not normalized_id:
        return None
    for template in _load_item_templates():
        if template['id'] == normalized_id:
            return dict(template)
    return None


def get_all_enemy_templates() -> list[dict[str, Any]]:
    """Return all enemy templates as mutable dictionaries."""
    return [dict(template) for template in _load_enemy_templates()]


def get_enemy_template(template_id: str | None) -> dict[str, Any] | None:
    """Return a single enemy template by slug or ``None`` when missing."""
    if template_id is None:
        return None
    normalized_id = str(template_id).strip()
    if not normalized_id:
        return None
    for template in _load_enemy_templates():
        if template['id'] == normalized_id:
            return dict(template)
    return None


def load_reference_data() -> None:
    """Warm and validate the in-memory JSON template collections."""
    get_all_item_templates()
    get_all_enemy_templates()


@cache.memoize(timeout=3600)
def get_item_type_data(item_type_id: str) -> dict[str, Any] | None:
    """Fetch a cached item template record by slug."""
    return get_item_template(item_type_id)


@cache.memoize(timeout=3600)
def get_all_item_type_data() -> list[dict[str, Any]]:
    """Fetch all cached item template records."""
    return get_all_item_templates()


@cache.memoize(timeout=3600)
def get_enemy_type_data(enemy_type_id: str) -> dict[str, Any] | None:
    """Fetch a cached enemy template record by slug."""
    return get_enemy_template(enemy_type_id)


@cache.memoize(timeout=3600)
def get_all_enemy_type_data() -> list[dict[str, Any]]:
    """Fetch all cached enemy template records."""
    return get_all_enemy_templates()


def invalidate_reference_data_cache() -> None:
    """Clear cached reference-data lookups for items and enemies."""
    cache.delete_memoized(get_item_type_data)
    cache.delete_memoized(get_all_item_type_data)
    cache.delete_memoized(get_enemy_type_data)
    cache.delete_memoized(get_all_enemy_type_data)
