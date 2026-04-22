from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

from types import SimpleNamespace

import pytest
from flask import Flask, request

from backend.db.models import Character, db
from backend.db import reference_data as reference_data_module
from backend import app as app_module
from backend.utils import game_utils, route_helpers
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
from backend.utils.app_cache import init_cache


def test_route_helpers_parsing_and_json_error(app):
    with app.test_request_context(data='not-json', content_type='application/json'):
        assert route_helpers.get_json_data(request) == {}

    assert route_helpers.json_error('boom', 418) == ({'error': 'boom'}, 418)

    missing_value, missing_error = route_helpers.parse_required_string({}, 'name')
    assert missing_value is None
    assert missing_error == ({'error': 'name is required'}, 400)

    trimmed_value, trimmed_error = route_helpers.parse_required_string({'name': '  Rogue  '}, 'name')
    assert trimmed_value == 'Rogue'
    assert trimmed_error is None

    integer_value, integer_error = route_helpers.parse_int_field({'level': '7'}, 'level')
    assert integer_value == 7
    assert integer_error is None

    missing_optional_value, missing_optional_error = route_helpers.parse_int_field({}, 'bonus', required=False)
    assert missing_optional_value is None
    assert missing_optional_error is None

    missing_required_value, missing_required_error = route_helpers.parse_int_field({}, 'bonus')
    assert missing_required_value is None
    assert missing_required_error == ({'error': 'bonus is required'}, 400)

    invalid_value, invalid_error = route_helpers.parse_int_field({'level': 'nope'}, 'level')
    assert invalid_value is None
    assert invalid_error == ({'error': 'level must be a valid integer'}, 400)

    too_small_zero_value, too_small_zero_error = route_helpers.parse_int_field({'count': -1}, 'count', minimum=0)
    assert too_small_zero_value is None
    assert too_small_zero_error == ({'error': 'count must be non-negative'}, 400)

    too_small_one_value, too_small_one_error = route_helpers.parse_int_field({'count': 0}, 'count', minimum=1)
    assert too_small_one_value is None
    assert too_small_one_error == ({'error': 'count must be a positive integer'}, 400)

    too_small_custom_value, too_small_custom_error = route_helpers.parse_int_field({'count': 1}, 'count', minimum=2)
    assert too_small_custom_value is None
    assert too_small_custom_error == ({'error': 'count must be at least 2'}, 400)

    parsed_list, parsed_list_error = route_helpers.parse_string_list(' sword ', 'item_type_id')
    assert parsed_list == ['sword']
    assert parsed_list_error is None

    list_value, list_error = route_helpers.parse_string_list([' sword ', ' shield '], 'item_type_id')
    assert list_value == ['sword', 'shield']
    assert list_error is None

    blank_list_value, blank_list_error = route_helpers.parse_string_list(['sword', ' '], 'item_type_id')
    assert blank_list_value is None
    assert blank_list_error == ({'error': 'item_type_id must be non-empty strings'}, 400)


def test_route_helpers_guards_and_item_mutators(client, entities, monkeypatch):
    owner = entities.create_user(username='owner', password='secret')
    other = entities.create_user(username='other', password='secret')
    owner_character = entities.create_character(owner, name='Carrier', seed_loadout=False)
    other_character = entities.create_character(other, name='Intruder', seed_loadout=False)

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
    assert missing_character_error == ({'error': 'No active character selected'}, 400)

    monkeypatch.setattr(route_helpers, 'get_character', lambda character_id=None: owner_character)
    selected_character, selected_character_error = route_helpers.require_current_character()
    assert selected_character == owner_character
    assert selected_character_error is None

    owner_character_lookup, owner_character_error = route_helpers.require_character_owner(owner_character.id)
    assert owner_character_lookup == owner_character
    assert owner_character_error is None

    missing_owner_character, missing_owner_error = route_helpers.require_character_owner(other_character.id)
    assert missing_owner_character is None
    assert missing_owner_error == ({'error': 'Character not found'}, 404)

    first_item = entities.create_inventory_item(owner_character, 'steel_sword')
    second_item = entities.create_inventory_item(owner_character, 'steel_sword')

    assert route_helpers.get_item(owner_character, first_item.id).id == first_item.id

    unequipped_marker = route_helpers.equip_item(SimpleNamespace(equipment=[]), SimpleNamespace(slot=None))
    assert unequipped_marker == ({'error': 'Item cannot be equipped'}, 400)

    assert route_helpers.equip_item(owner_character, first_item) is None
    db.session.commit()
    assert route_helpers.get_item(owner_character, first_item.id) is None

    assert route_helpers.equip_item(owner_character, second_item) is None
    db.session.commit()
    fresh_character = Character.query.get(owner_character.id)
    assert fresh_character is not None
    assert len(fresh_character.equipment) == 1
    assert fresh_character.equipment[0].item.id == second_item.id

    assert route_helpers.unequip_item(owner_character, second_item.id) is None
    db.session.commit()
    assert route_helpers.unequip_item(owner_character, second_item.id) == ({'error': 'Equipment not found'}, 404)


def test_game_utils_auth_and_inventory_helpers(app, entities, monkeypatch):
    owner = entities.create_user(username='mage', password='secret')
    other = entities.create_user(username='rogue', password='secret')
    owner_character = entities.create_character(owner, name='Mage', seed_loadout=False)
    other_character = entities.create_character(other, name='Rogue', seed_loadout=False)

    token = game_utils.issue_auth_token(owner.id, owner_character.id)

    with app.test_request_context(headers={'Authorization': f'Bearer {token}'}):
        payload = game_utils.get_request_auth_payload()
        assert payload == {'user_id': owner.id, 'character_id': owner_character.id}
        assert game_utils.get_current_user().id == owner.id
        assert game_utils.get_player().id == owner_character.id

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
            game_utils._get_auth_serializer()

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

    loot_item = entities.create_inventory_item(owner_character, 'ruby_necklace', is_loot=True)
    plain_item = entities.create_inventory_item(owner_character, 'linen_armor', is_loot=False)
    game_utils.clear_loot_flags(owner_character)
    db.session.commit()

    fresh_owner = Character.query.get(owner_character.id)
    assert fresh_owner is not None
    assert all(not item.is_loot for item in fresh_owner.user.items)

    fresh_loot = entities.create_inventory_item(owner_character, 'silver_ring', is_loot=True)
    game_utils.destroy_loot_items(owner_character)
    db.session.commit()

    remaining_ids = {item.id for item in Character.query.get(owner_character.id).user.items}
    assert fresh_loot.id not in remaining_ids
    assert plain_item.id in remaining_ids
    assert equipped_item.id in remaining_ids
    assert game_utils.remove_inventory_item(SimpleNamespace(user=None, user_id=owner.id), 1) is None
    game_utils.clear_loot_flags(SimpleNamespace(user=None))
    game_utils.destroy_loot_items(SimpleNamespace(user=None))


def test_api_response_cache_helpers_and_invalidation(app, entities, monkeypatch):
    owner = entities.create_user(username='cache-owner', password='secret')
    character = entities.create_character(owner, name='Keeper', seed_loadout=False)

    equipped_item = entities.create_inventory_item(character, 'steel_sword')
    hidden_item = entities.create_inventory_item(character, 'iron_shield', is_loot=True)

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

    memoized_calls: list[tuple[object, tuple[object, ...]]] = []

    def fake_delete_memoized(function, *args):
        memoized_calls.append((function, args))

    monkeypatch.setattr(cache, 'delete_memoized', fake_delete_memoized)

    invalidate_user_profile_cache(owner.id)
    invalidate_user_inventory_cache(owner.id)
    invalidate_user_characters_cache(owner.id, [character.id])
    invalidate_user_state_cache(owner.id)

    function_names = {function.__name__ for function, _ in memoized_calls}
    assert 'get_cached_user_data' in function_names
    assert 'get_cached_user_inventory_data' in function_names
    assert 'get_cached_user_characters_data' in function_names
    assert 'get_cached_character_data' in function_names
    assert 'get_cached_character_equipment_data' in function_names


def test_init_cache_reads_environment_overrides(monkeypatch):
    app = Flask(__name__)
    monkeypatch.setenv('CACHE_TYPE', 'SimpleCache')
    monkeypatch.setenv('CACHE_DEFAULT_TIMEOUT', '123')
    monkeypatch.setenv('CACHE_REDIS_URL', 'redis://localhost:6379/0')

    init_cache(app)

    assert app.config['CACHE_TYPE'] == 'SimpleCache'
    assert app.config['CACHE_DEFAULT_TIMEOUT'] == 123
    assert app.config['CACHE_REDIS_URL'] == 'redis://localhost:6379/0'


def test_app_module_cli_commands_and_missing_secret_guard(app, monkeypatch):
    missing_secret_path = Path(__file__).resolve().parents[1] / 'app.py'
    monkeypatch.delenv('SECRET_KEY', raising=False)
    spec = importlib.util.spec_from_file_location('backend.app', missing_secret_path)
    assert spec is not None
    assert spec.loader is not None
    missing_secret_module = importlib.util.module_from_spec(spec)
    original_backend_app = sys.modules.get('backend.app')

    with pytest.raises(RuntimeError, match='SECRET_KEY must be set'):
        sys.modules['backend.app'] = missing_secret_module
        try:
            spec.loader.exec_module(missing_secret_module)
        finally:
            if original_backend_app is not None:
                sys.modules['backend.app'] = original_backend_app

    removed_paths: list[str] = []
    monkeypatch.setattr(app_module.os.path, 'exists', lambda path: True)
    monkeypatch.setattr(app_module.os, 'remove', lambda path: removed_paths.append(path))

    runner = app.test_cli_runner()
    init_result = runner.invoke(app_module.init_db)
    delete_result = runner.invoke(app_module.delete_db)

    assert init_result.exit_code == 0
    assert delete_result.exit_code == 0
    assert removed_paths and removed_paths[0].endswith('game.db')


def test_reference_data_validation_and_cache_invalidation(tmp_path, monkeypatch):
    invalid_structure = tmp_path / 'invalid-structure.json'
    invalid_structure.write_text(json.dumps({'id': 'oops'}), encoding='utf-8')
    with pytest.raises(ValueError, match='must contain a JSON array'):
        reference_data_module._load_template_collection(invalid_structure, ('name',))

    invalid_entry = tmp_path / 'invalid-entry.json'
    invalid_entry.write_text(json.dumps([1]), encoding='utf-8')
    with pytest.raises(ValueError, match='entry 1 must be an object'):
        reference_data_module._load_template_collection(invalid_entry, ('name',))

    missing_id = tmp_path / 'missing-id.json'
    missing_id.write_text(json.dumps([{'name': 'Alpha'}]), encoding='utf-8')
    with pytest.raises(ValueError, match='entry 1 is missing an id'):
        reference_data_module._load_template_collection(missing_id, ('name',))

    duplicate_id = tmp_path / 'duplicate-id.json'
    duplicate_id.write_text(json.dumps([{'id': 'alpha', 'name': 'A'}, {'id': 'alpha', 'name': 'B'}]), encoding='utf-8')
    with pytest.raises(ValueError, match='contains duplicate template id'):
        reference_data_module._load_template_collection(duplicate_id, ('name',))

    missing_field = tmp_path / 'missing-field.json'
    missing_field.write_text(json.dumps([{'id': 'alpha', 'name': 'A'}]), encoding='utf-8')
    with pytest.raises(ValueError, match='missing required field'):
        reference_data_module._load_template_collection(missing_field, ('name', 'slot'))

    assert reference_data_module.get_item_template(None) is None
    assert reference_data_module.get_item_template('   ') is None
    assert reference_data_module.get_enemy_template(None) is None
    assert reference_data_module.get_enemy_template('   ') is None

    invalidation_calls: list[object] = []

    def fake_delete_memoized(function, *args):
        invalidation_calls.append(function)

    monkeypatch.setattr(reference_data_module.cache, 'delete_memoized', fake_delete_memoized)
    reference_data_module.invalidate_reference_data_cache()

    invalidated_names = {function.__name__ for function in invalidation_calls}
    assert invalidated_names == {
        'get_item_type_data',
        'get_all_item_type_data',
        'get_enemy_type_data',
        'get_all_enemy_type_data',
    }