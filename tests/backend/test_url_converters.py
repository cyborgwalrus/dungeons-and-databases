"""Focused tests for custom URL converter helper and ownership branches."""

from types import SimpleNamespace

import pytest
from werkzeug.exceptions import NotFound, Unauthorized
from werkzeug.routing import Map

from backend.utils import url_converters
from backend.utils.url_converters import (
    CharacterConverter,
    CombatConverter,
    ItemConverter,
    OwnedModelConverter,
)


def test_owned_model_converter_helper_methods_cover_fallback_paths():
    """Validate id serialization and helper error formatting paths."""
    converter = OwnedModelConverter(Map())

    assert converter.to_url(SimpleNamespace(id=42)) == '42'
    assert converter.to_url('raw-value') == 'raw-value'

    assert converter._parse_int('7') == 7

    with pytest.raises(NotFound) as invalid_error:
        converter._parse_int('not-an-int')
    assert invalid_error.value.description == 'Object not found'

    with pytest.raises(NotFound) as type_error:
        converter._parse_int(None)
    assert type_error.value.description == 'Object not found'

    not_found = converter._not_found()
    assert isinstance(not_found, NotFound)
    assert not_found.description == 'Object not found'


def test_character_converter_requires_authenticated_user(entities, monkeypatch):
    """Character conversion should reject requests without an authenticated user."""
    owner = entities.create_user(username='converter-owner', password='secret')
    character = entities.create_character(owner, name='Converter Hero', seed_loadout=False)
    converter = CharacterConverter(Map())

    monkeypatch.setattr(url_converters, 'get_current_user', lambda: None)

    with pytest.raises(Unauthorized) as unauthorized_error:
        converter.to_python(str(character.id))
    assert unauthorized_error.value.description == 'Unauthorized'


def test_item_converter_not_found_and_ownership_branches(entities, monkeypatch):
    """Item conversion should handle missing IDs and ownership mismatch."""
    owner = entities.create_user(username='item-owner', password='secret')
    intruder = entities.create_user(username='item-intruder', password='secret')
    owner_character = entities.create_character(owner, name='Owner Character', seed_loadout=False)
    owned_item = entities.create_inventory_item(owner_character, 'steel_sword')
    converter = ItemConverter(Map())

    monkeypatch.setattr(url_converters, 'get_current_user', lambda: owner)
    with pytest.raises(NotFound) as not_found_error:
        converter.to_python('999999')
    assert not_found_error.value.description == 'Item not found'

    monkeypatch.setattr(url_converters, 'get_current_user', lambda: intruder)
    with pytest.raises(Unauthorized) as unauthorized_error:
        converter.to_python(str(owned_item.id))
    assert unauthorized_error.value.description == 'Unauthorized'


def test_item_converter_requires_authenticated_user(entities, monkeypatch):
    """Item conversion should reject requests without an authenticated user."""
    owner = entities.create_user(username='item-auth-owner', password='secret')
    owner_character = entities.create_character(owner, name='Auth Carrier', seed_loadout=False)
    owned_item = entities.create_inventory_item(owner_character, 'steel_sword')
    converter = ItemConverter(Map())

    monkeypatch.setattr(url_converters, 'get_current_user', lambda: None)
    with pytest.raises(Unauthorized) as unauthorized_error:
        converter.to_python(str(owned_item.id))
    assert unauthorized_error.value.description == 'Unauthorized'


def test_combat_converter_requires_active_character_match(entities, monkeypatch):
    """Combat conversion should reject missing or mismatched active character."""
    owner = entities.create_user(username='combat-owner', password='secret')
    owner_character = entities.create_character(owner, name='Fighter', seed_loadout=False)
    other_character = entities.create_character(owner, name='Alt Fighter', seed_loadout=False)
    _, combat = entities.create_encounter(owner_character)
    converter = CombatConverter(Map())

    monkeypatch.setattr(url_converters, 'get_current_user', lambda: owner)

    monkeypatch.setattr(url_converters, 'get_player', lambda: None)
    with pytest.raises(NotFound) as not_found_error:
        converter.to_python(str(combat.id))
    assert not_found_error.value.description == 'Combat not found'

    monkeypatch.setattr(url_converters, 'get_player', lambda: other_character)
    with pytest.raises(Unauthorized) as unauthorized_error:
        converter.to_python(str(combat.id))
    assert unauthorized_error.value.description == 'Unauthorized'
