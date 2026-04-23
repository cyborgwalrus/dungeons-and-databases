"""Tests for JSON-backed reference data helpers."""

from backend.utils.game_utils import (
    get_enemy_type,
    get_enemy_types,
    get_item_type,
    get_item_types,
    load_enemy_type_seed_data,
    load_item_type_seed_data,
)


def test_reference_data_helpers_return_expected_records():
    """Validate the JSON-backed lookup helpers."""
    assert get_item_type(None) is None
    assert get_item_type('   ') is None
    assert get_enemy_type(None) is None
    assert get_enemy_type('   ') is None

    item_template = get_item_type('steel_sword')
    assert item_template == {
        'id': 'steel_sword',
        'name': 'Steel Sword',
        'slot_type': 'weapon',
        'health': 0,
        'damage': 10,
    }

    enemy_template = get_enemy_type('orc')
    assert enemy_template == {
        'id': 'orc',
        'name': 'Orc',
        'description': 'A brutish orc',
        'base_health': 35,
        'base_damage': 8,
    }

    assert get_item_types() == [dict(template) for template in load_item_type_seed_data()]
    assert get_enemy_types() == [dict(template) for template in load_enemy_type_seed_data()]
