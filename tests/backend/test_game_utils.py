"""Tests for backend authentication and inventory helpers."""

from types import SimpleNamespace

import pytest

from backend.db.models import Character, db
from backend.utils import game_utils, route_helpers


def test_game_utils_auth_helpers(app, entities, monkeypatch):
    """Validate auth token parsing and current-user helpers."""
    owner = entities.create_user(username='mage', password='secret')
    other = entities.create_user(username='rogue', password='secret')
    owner_character = entities.create_character(
        owner,
        name='Mage',
        seed_loadout=False,
    )
    other_character = entities.create_character(
        other,
        name='Rogue',
        seed_loadout=False,
    )

    token = game_utils.issue_auth_token(owner.id, owner_character.id)

    with app.test_request_context(headers={'Authorization': f'Bearer {token}'}):
        payload = game_utils.get_request_auth_payload()
        assert payload == {'user_id': owner.id, 'character_id': owner_character.id}

        current_user = game_utils.get_current_user()
        assert current_user is not None
        assert current_user.id == owner.id

        current_player = game_utils.get_player()
        assert current_player is not None
        assert current_player.id == owner_character.id

    with app.test_request_context(headers={'Authorization': 'Bearer not-a-token'}):
        assert game_utils.get_request_auth_payload() is None

    with app.test_request_context():
        assert game_utils.get_request_auth_payload() is None

    wrong_owner_token = game_utils.issue_auth_token(owner.id, other_character.id)
    with app.test_request_context(headers={'Authorization': f'Bearer {wrong_owner_token}'}):
        assert game_utils.get_player() is None

    monkeypatch.setitem(app.config, 'SECRET_KEY', None)
    with app.app_context():
        with pytest.raises(RuntimeError, match='SECRET_KEY is required for token auth'):
            game_utils.issue_auth_token(owner.id, owner_character.id)


def test_game_utils_inventory_helpers(entities):
    """Validate inventory item creation and cleanup helpers."""
    owner = entities.create_user(username='owner', password='secret')
    owner_character = entities.create_character(
        owner,
        name='Carrier',
        seed_loadout=False,
    )

    invalid_item = game_utils.add_inventory_item(owner_character, 'missing-item')
    assert invalid_item is None

    scaled_item = game_utils.add_inventory_item(owner_character, 'steel_sword', level=3)
    assert scaled_item is not None
    db.session.commit()
    assert scaled_item.level == 3
    assert scaled_item.user_id == owner.id

    removed_by_type = game_utils.remove_inventory_item(owner_character, 'steel_sword')
    assert removed_by_type is not None
    assert removed_by_type.id == scaled_item.id
    db.session.commit()

    equipped_item = entities.create_inventory_item(owner_character, 'iron_helmet')
    assert route_helpers.equip_item(owner_character, equipped_item) is None
    db.session.commit()
    assert game_utils.remove_inventory_item(owner_character, equipped_item.id) is None

    entities.create_inventory_item(owner_character, 'ruby_necklace', is_loot=True)
    plain_item = entities.create_inventory_item(owner_character, 'linen_armor', is_loot=False)
    game_utils.clear_loot_flags(owner_character)
    db.session.commit()

    fresh_owner = Character.query.get(owner_character.id)
    assert fresh_owner is not None
    assert all(not item.is_loot for item in fresh_owner.user.items)

    fresh_loot = entities.create_inventory_item(owner_character, 'silver_ring', is_loot=True)
    game_utils.destroy_loot_items(owner_character)
    db.session.commit()

    remaining_ids = {
        item.id for item in Character.query.get(owner_character.id).user.items
    }
    assert fresh_loot.id not in remaining_ids
    assert plain_item.id in remaining_ids
    assert equipped_item.id in remaining_ids
    assert game_utils.remove_inventory_item(
        SimpleNamespace(user=None, user_id=owner.id),
        1,
    ) is None
    game_utils.clear_loot_flags(SimpleNamespace(user=None))
    game_utils.destroy_loot_items(SimpleNamespace(user=None))