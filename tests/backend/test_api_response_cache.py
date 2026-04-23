"""Tests for API response cache reads and invalidation helpers."""

from collections import Counter
from collections.abc import Callable
from typing import Any

from backend.db.models import db
from backend.utils import route_helpers
from backend.utils.api_response_cache import (
    cache,
    get_cached_character_data,
    get_cached_character_equipment_data,
    get_cached_user_characters_data,
    get_cached_user_data,
    get_cached_user_inventory_data,
    invalidate_user_characters_cache,
    invalidate_user_inventory_cache,
    invalidate_user_profile_cache,
    invalidate_user_state_cache,
)


def test_api_response_cache_reads_through(entities):
    """Read cached user, character, and inventory payloads."""
    owner = entities.create_user(username='cache-owner', password='secret')
    character = entities.create_character(owner, name='Keeper', seed_loadout=False)

    equipped_item = entities.create_inventory_item(character, 'steel_sword')
    hidden_item = entities.create_inventory_item(character, 'iron_shield')

    assert route_helpers.equip_item(character, equipped_item) is None
    db.session.commit()

    user_payload = get_cached_user_data(owner.id)
    assert user_payload is not None
    assert user_payload['username'] == owner.username

    characters_payload = get_cached_user_characters_data(owner.id)
    assert len(characters_payload) == 1
    assert characters_payload[0]['id'] == character.id

    inventory_payload = get_cached_user_inventory_data(owner.id)
    assert len(inventory_payload) == 1
    assert inventory_payload[0]['id'] == hidden_item.id

    character_payload = get_cached_character_data(character.id, owner.id)
    assert character_payload is not None
    assert character_payload['id'] == character.id

    equipment_payload = get_cached_character_equipment_data(character.id, owner.id)
    assert len(equipment_payload) == 1
    assert equipment_payload[0]['id'] == equipped_item.id


def test_api_response_cache_invalidation(entities, monkeypatch):
    """Invalidate all cache layers and record memoized function calls."""
    owner = entities.create_user(username='cache-owner', password='secret')
    character = entities.create_character(owner, name='Keeper', seed_loadout=False)

    equipped_item = entities.create_inventory_item(character, 'steel_sword')
    entities.create_inventory_item(character, 'iron_shield')

    assert route_helpers.equip_item(character, equipped_item) is None
    db.session.commit()

    memoized_calls: list[tuple[Callable[..., Any], tuple[Any, ...]]] = []

    def fake_delete_memoized(function, *args):
        memoized_calls.append((function, args))

    monkeypatch.setattr(cache, 'delete_memoized', fake_delete_memoized)

    invalidate_user_profile_cache(owner.id)
    invalidate_user_inventory_cache(owner.id)
    invalidate_user_characters_cache(owner.id, [character.id])
    invalidate_user_state_cache(owner.id)

    function_names = [function.__name__ for function, _ in memoized_calls]
    assert Counter(function_names) == Counter(
        {
            'get_cached_user_data': 2,
            'get_cached_user_inventory_data': 2,
            'get_cached_user_characters_data': 2,
            'get_cached_character_data': 2,
            'get_cached_character_equipment_data': 2,
        }
    )