"""Tests for backend request-parsing and ownership helpers."""

from types import SimpleNamespace
from typing import cast

from backend.db.models import Character, Item
from backend.db.session import db
from backend.utils import route_helpers


def _create_owner_and_intruder(entities):
    """Create two users and their characters for guard tests."""
    owner = entities.create_user(username='owner', password='secret')
    other = entities.create_user(username='other', password='secret')
    owner_character = entities.create_character(
        owner,
        name='Carrier',
        seed_loadout=False,
    )
    other_character = entities.create_character(
        other,
        name='Intruder',
        seed_loadout=False,
    )
    return owner, other, owner_character, other_character


def test_get_json_and_error():
    """Format JSON errors for the shared helper."""
    assert route_helpers.json_error('boom', 418) == ({'error': 'boom'}, 418)


def test_get_character_by_id(entities):
    """Cover the explicit character-id lookup branch."""
    user = entities.create_user(username='lookup', password='secret')
    character = entities.create_character(user, name='Lookup', seed_loadout=False)

    assert route_helpers.get_character(character.id) == character


def test_user_and_character_guards(client, entities, monkeypatch):
    """Validate user and character ownership helpers."""
    assert client is not None
    owner_character_data = _create_owner_and_intruder(entities)
    owner = owner_character_data[0]
    owner_character = owner_character_data[2]
    other_character = owner_character_data[3]

    monkeypatch.setattr(route_helpers, 'get_current_user', lambda: None)
    missing_user, missing_user_error = route_helpers.require_current_user()
    assert missing_user is None
    assert missing_user_error == ({'error': 'Unauthorized'}, 401)

    monkeypatch.setattr(route_helpers, 'get_character', lambda character_id=None: None)
    missing_character, missing_character_error = route_helpers.require_current_character()
    assert missing_character is None
    assert missing_character_error == (
        {'error': 'No active character selected'},
        400,
    )

    monkeypatch.setattr(route_helpers, 'get_character', lambda character_id=None: owner_character)
    selected_character, selected_character_error = route_helpers.require_current_character()
    assert selected_character == owner_character
    assert selected_character_error is None

    monkeypatch.setattr(route_helpers, 'get_current_user', lambda: owner)

    owner_character_lookup, owner_character_error = route_helpers.require_character_owner(
        owner_character.id,
    )
    assert owner_character_lookup == owner_character
    assert owner_character_error is None

    missing_owner_character, missing_owner_error = route_helpers.require_character_owner(
        other_character.id,
    )
    assert missing_owner_character is None
    assert missing_owner_error == ({'error': 'Unauthorized'}, 401)


def test_item_mutators(entities):
    """Validate item lookup, equip, and unequip helpers."""
    owner = entities.create_user(username='owner', password='secret')
    owner_character = entities.create_character(
        owner,
        name='Carrier',
        seed_loadout=False,
    )

    first_item = entities.create_inventory_item(owner_character, 'steel_sword')
    second_item = entities.create_inventory_item(owner_character, 'steel_sword')

    unequipped_marker = route_helpers.equip_item(
        cast(Character, SimpleNamespace(equipment=[])),
        cast(Item, SimpleNamespace(slot_type=None)),
    )
    assert unequipped_marker == ({'error': 'Item cannot be equipped'}, 400)

    assert route_helpers.equip_item(owner_character, first_item) is None
    db.session.commit()

    assert route_helpers.equip_item(owner_character, second_item) is None
    db.session.commit()
    fresh_character = db.session.get(Character, owner_character.id)
    assert fresh_character is not None
    assert len(fresh_character.equipment) == 1
    assert fresh_character.equipment[0].item.id == second_item.id

    assert route_helpers.unequip_item(owner_character, second_item.id) is None
    db.session.commit()
    assert route_helpers.unequip_item(owner_character, second_item.id) == (
        {'error': 'Equipment not found'},
        404,
    )