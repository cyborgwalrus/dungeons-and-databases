"""Tests for in-memory reference data helpers."""

import backend.db.reference_data.enemy_types as enemy_types
import backend.db.reference_data.item_types as item_types


def test_reference_data_helpers_return_expected_records():
    """Validate the in-memory lookup helpers."""
    assert item_types.get(None) is None
    assert item_types.get('   ') is None
    assert enemy_types.get(None) is None
    assert enemy_types.get('   ') is None

    item_template = item_types.get('steel_sword')
    assert item_template == {
        'id': 'steel_sword',
        'name': 'Steel Sword',
        'slot': 'weapon',
        'health': 0,
        'damage': 10,
    }

    enemy_template = enemy_types.get('orc')
    assert enemy_template == {
        'id': 'orc',
        'name': 'Orc',
        'description': 'A brutish orc',
        'health': 35,
        'damage': 8,
    }

    assert item_types.get_all() == [dict(template) for template in item_types.ITEM_TYPES]
    assert enemy_types.get_all() == [dict(template) for template in enemy_types.ENEMY_TYPES]
