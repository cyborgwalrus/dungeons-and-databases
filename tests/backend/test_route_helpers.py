"""Tests for backend request-parsing and ownership helpers."""

from types import SimpleNamespace
from typing import cast

from flask import request

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


def test_route_helpers_get_json_and_error(app):
    """Parse request JSON and format JSON errors."""
    with app.test_request_context(data='not-json', content_type='application/json'):
        assert route_helpers.get_json_data(request) == {}

    assert route_helpers.json_error('boom', 418) == ({'error': 'boom'}, 418)


def test_route_helpers_parse_required_string():
    """Validate required trimmed string inputs."""
    missing_value, missing_error = route_helpers.parse_required_string({}, 'name')
    assert missing_value is None
    assert missing_error == ({'error': 'name is required'}, 400)

    trimmed_value, trimmed_error = route_helpers.parse_required_string(
        {'name': '  Rogue  '},
        'name',
    )
    assert trimmed_value == 'Rogue'
    assert trimmed_error is None


def test_route_helpers_parse_int_field():
    """Validate integer parsing and minimum checks."""
    integer_value, integer_error = route_helpers.parse_int_field({'level': '7'}, 'level')
    assert integer_value == 7
    assert integer_error is None

    missing_optional_value, missing_optional_error = route_helpers.parse_int_field(
        {},
        'bonus',
        required=False,
    )
    assert missing_optional_value is None
    assert missing_optional_error is None

    missing_required_value, missing_required_error = route_helpers.parse_int_field({}, 'bonus')
    assert missing_required_value is None
    assert missing_required_error == ({'error': 'bonus is required'}, 400)

    invalid_value, invalid_error = route_helpers.parse_int_field({'level': 'nope'}, 'level')
    assert invalid_value is None
    assert invalid_error == ({'error': 'level must be a valid integer'}, 400)

    too_small_zero_value, too_small_zero_error = route_helpers.parse_int_field(
        {'count': -1},
        'count',
        minimum=0,
    )
    assert too_small_zero_value is None
    assert too_small_zero_error == ({'error': 'count must be non-negative'}, 400)

    too_small_one_value, too_small_one_error = route_helpers.parse_int_field(
        {'count': 0},
        'count',
        minimum=1,
    )
    assert too_small_one_value is None
    assert too_small_one_error == ({'error': 'count must be a positive integer'}, 400)

    too_small_custom_value, too_small_custom_error = route_helpers.parse_int_field(
        {'count': 1},
        'count',
        minimum=2,
    )
    assert too_small_custom_value is None
    assert too_small_custom_error == ({'error': 'count must be at least 2'}, 400)


def test_route_helpers_parse_string_list():
    """Validate string list parsing and rejection of blank values."""
    parsed_list, parsed_list_error = route_helpers.parse_string_list(' sword ', 'item_type_id')
    assert parsed_list == ['sword']
    assert parsed_list_error is None

    list_value, list_error = route_helpers.parse_string_list(
        [' sword ', ' shield '],
        'item_type_id',
    )
    assert list_value == ['sword', 'shield']
    assert list_error is None

    blank_list_value, blank_list_error = route_helpers.parse_string_list(
        ['sword', ' '],
        'item_type_id',
    )
    assert blank_list_value is None
    assert blank_list_error == (
        {'error': 'item_type_id must be non-empty strings'},
        400,
    )


def test_route_helpers_user_and_character_guards(client, entities, monkeypatch):
    """Validate user and character ownership helpers."""
    assert client is not None
    owner, other, owner_character, other_character = _create_owner_and_intruder(entities)

    monkeypatch.setattr(route_helpers, 'get_current_user', lambda: None)
    missing_user, missing_user_error = route_helpers.require_current_user()
    assert missing_user is None
    assert missing_user_error == ({'error': 'Unauthorized'}, 401)

    monkeypatch.setattr(route_helpers, 'get_current_user', lambda: owner)
    owner_check, owner_check_error = route_helpers.require_current_user_id(owner.id)
    assert owner_check == owner
    assert owner_check_error is None

    mismatch_user, mismatch_error = route_helpers.require_current_user_id(other.id)
    assert mismatch_user is None
    assert mismatch_error == ({'error': 'Unauthorized'}, 401)

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


def test_route_helpers_item_mutators(entities):
    """Validate item lookup, equip, and unequip helpers."""
    owner = entities.create_user(username='owner', password='secret')
    owner_character = entities.create_character(
        owner,
        name='Carrier',
        seed_loadout=False,
    )

    first_item = entities.create_inventory_item(owner_character, 'steel_sword')
    second_item = entities.create_inventory_item(owner_character, 'steel_sword')

    first_item_lookup = route_helpers.get_item(owner_character, first_item.id)
    assert first_item_lookup is not None
    assert first_item_lookup.id == first_item.id

    unequipped_marker = route_helpers.equip_item(
        cast(Character, SimpleNamespace(equipment=[])),
        cast(Item, SimpleNamespace(slot_type=None)),
    )
    assert unequipped_marker == ({'error': 'Item cannot be equipped'}, 400)

    assert route_helpers.equip_item(owner_character, first_item) is None
    db.session.commit()
    assert route_helpers.get_item(owner_character, first_item.id) is None

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