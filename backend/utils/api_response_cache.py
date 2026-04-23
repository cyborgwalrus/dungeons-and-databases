"""Cache lookups and invalidation helpers for API responses."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from sqlalchemy.orm import selectinload

from backend.db.models import Character, EquipmentSlot, Item, User
from backend.utils.app_init import cache


_CHARACTER_EQUIPMENT_OPTIONS = selectinload(
    Character.equipment
).selectinload(EquipmentSlot.item)


def _load_user_state(user_id: int) -> User | None:
    return User.query.get(user_id)


def _load_user_characters_state(user_id: int) -> User | None:
    return User.query.options(
        selectinload(User.characters).options(_CHARACTER_EQUIPMENT_OPTIONS),
    ).get(user_id)


def _load_user_inventory_state(user_id: int) -> User | None:
    return User.query.get(user_id)


def _load_character_state(character_id: int, user_id: int) -> Character | None:
    return Character.query.options(
        _CHARACTER_EQUIPMENT_OPTIONS,
    ).filter_by(id=character_id, user_id=user_id).first()


@cache.memoize(timeout=600)
def get_cached_user_data(user_id: int) -> dict[str, Any] | None:
    """Return a cached serialized user profile."""
    user = _load_user_state(user_id)
    return user.to_response().model_dump() if user else None


@cache.memoize(timeout=600)
def get_cached_user_characters_data(user_id: int) -> list[dict[str, Any]]:
    """Return a cached list of serialized characters for the user."""
    user = _load_user_characters_state(user_id)
    if not user:
        return []
    return [character.to_response().model_dump() for character in user.characters]


@cache.memoize(timeout=600)
def get_cached_user_inventory_data(user_id: int) -> list[dict[str, Any]]:
    """Return a cached list of serialized inventory items for the user."""
    user = _load_user_inventory_state(user_id)
    if not user:
        return []
    equipped_item_ids = {
        equipment.item_id
        for equipment in EquipmentSlot.query.join(Item).filter(Item.user_id == user_id).all()
    }
    return [
        item.to_response().model_dump()
        for item in Item.query.filter_by(user_id=user_id).all()
        if item.id not in equipped_item_ids
    ]


@cache.memoize(timeout=300)
def get_cached_character_data(character_id: int, user_id: int) -> dict[str, Any] | None:
    """Return a cached serialized character snapshot."""
    character = _load_character_state(character_id, user_id)
    return character.to_response().model_dump() if character else None


@cache.memoize(timeout=300)
def get_cached_character_equipment_data(character_id: int, user_id: int) -> list[dict[str, Any]]:
    """Return a cached serialized equipment list for a character."""
    character = _load_character_state(character_id, user_id)
    if not character:
        return []
    return [
        equipment.item.to_response().model_dump()
        for equipment in character.equipment
        if equipment.item
    ]


def invalidate_user_profile_cache(user_id: int) -> None:
    """Invalidate the cached user profile only."""
    cache.delete_memoized(get_cached_user_data, user_id)


def invalidate_user_inventory_cache(user_id: int) -> None:
    """Invalidate the cached user inventory only."""
    cache.delete_memoized(get_cached_user_inventory_data, user_id)


def _invalidate_character_snapshots(
    user_id: int,
    character_ids: Iterable[int] | None = None,
) -> None:
    cache.delete_memoized(get_cached_user_characters_data, user_id)

    if character_ids is None:
        character_ids = [
            character.id
            for character in Character.query.filter_by(user_id=user_id).all()
        ]

    for character_id in character_ids:
        cache.delete_memoized(
            get_cached_character_data,
            character_id,
            user_id,
        )
        cache.delete_memoized(
            get_cached_character_equipment_data,
            character_id,
            user_id,
        )


def invalidate_user_characters_cache(
    user_id: int,
    character_ids: Iterable[int] | None = None,
) -> None:
    """Invalidate the cached character list and character snapshots for a user."""
    _invalidate_character_snapshots(user_id, character_ids)


def invalidate_user_state_cache(
    user_id: int,
    character_ids: Iterable[int] | None = None,
) -> None:
    """Invalidate all cached user-scoped data."""
    invalidate_user_profile_cache(user_id)
    invalidate_user_inventory_cache(user_id)
    _invalidate_character_snapshots(user_id, character_ids)
