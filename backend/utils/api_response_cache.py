from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from sqlalchemy.orm import selectinload

from backend.db.models import Character, CharacterEquipment, Item, User, UserInventory
from backend.utils.app_cache import cache


def _load_user_state(user_id: int) -> User | None:
    return User.query.options(
        selectinload(User.characters).selectinload(Character.equipment).selectinload(CharacterEquipment.item).selectinload(Item.item_type),
        selectinload(User.inventory).selectinload(UserInventory.items).selectinload(Item.item_type),
    ).get(user_id)


def _load_character_state(character_id: int, user_id: int) -> Character | None:
    return Character.query.options(
        selectinload(Character.user).selectinload(User.inventory).selectinload(UserInventory.items).selectinload(Item.item_type),
        selectinload(Character.equipment).selectinload(CharacterEquipment.item).selectinload(Item.item_type),
    ).filter_by(id=character_id, user_id=user_id).first()


@cache.memoize(timeout=600)
def get_cached_user_data(user_id: int) -> dict[str, Any] | None:
    """Return a cached serialized user profile."""
    user = _load_user_state(user_id)
    return user.to_dict() if user else None


@cache.memoize(timeout=600)
def get_cached_user_characters_data(user_id: int) -> list[dict[str, Any]]:
    """Return a cached list of serialized characters for the user."""
    user = _load_user_state(user_id)
    if not user:
        return []
    return [character.to_dict() for character in user.characters]


@cache.memoize(timeout=600)
def get_cached_user_inventory_data(user_id: int) -> list[dict[str, Any]]:
    """Return a cached list of serialized inventory items for the user."""
    user = _load_user_state(user_id)
    if not user or not user.inventory:
        return []
    return [item.to_dict() for item in user.inventory.items]


@cache.memoize(timeout=300)
def get_cached_character_data(character_id: int, user_id: int) -> dict[str, Any] | None:
    """Return a cached serialized character snapshot."""
    character = _load_character_state(character_id, user_id)
    return character.to_dict() if character else None


@cache.memoize(timeout=300)
def get_cached_character_equipment_data(character_id: int, user_id: int) -> list[dict[str, Any]]:
    """Return a cached serialized equipment list for a character."""
    character = _load_character_state(character_id, user_id)
    if not character:
        return []
    return [equipment.item.to_dict() for equipment in character.equipment if equipment.item]


def invalidate_user_state_cache(user_id: int, character_ids: Iterable[int] | None = None) -> None:
    """Invalidate cached user, inventory, character list, and character snapshots."""
    cache.delete_memoized(get_cached_user_data, user_id)
    cache.delete_memoized(get_cached_user_characters_data, user_id)
    cache.delete_memoized(get_cached_user_inventory_data, user_id)

    if character_ids is None:
        character_ids = [character.id for character in Character.query.filter_by(user_id=user_id).all()]

    for character_id in character_ids:
        cache.delete_memoized(get_cached_character_data, character_id, user_id)
        cache.delete_memoized(get_cached_character_equipment_data, character_id, user_id)