"""Tests for reference-data validation and cache invalidation."""

import json
from collections.abc import Callable
from typing import Any

import pytest

from backend.db import reference_data as reference_data_module


def test_reference_data_validation_and_cache_invalidation(tmp_path, monkeypatch):
    """Validate reference-data loading and cache invalidation helpers."""
    invalid_structure = tmp_path / 'invalid-structure.json'
    invalid_structure.write_text(json.dumps({'id': 'oops'}), encoding='utf-8')
    with pytest.raises(ValueError, match='must contain a JSON array'):
        reference_data_module.load_template_collection(invalid_structure, ('name',))

    invalid_entry = tmp_path / 'invalid-entry.json'
    invalid_entry.write_text(json.dumps([1]), encoding='utf-8')
    with pytest.raises(ValueError, match='entry 1 must be an object'):
        reference_data_module.load_template_collection(invalid_entry, ('name',))

    missing_id = tmp_path / 'missing-id.json'
    missing_id.write_text(json.dumps([{'name': 'Alpha'}]), encoding='utf-8')
    with pytest.raises(ValueError, match='entry 1 is missing an id'):
        reference_data_module.load_template_collection(missing_id, ('name',))

    duplicate_id = tmp_path / 'duplicate-id.json'
    duplicate_id.write_text(
        json.dumps([{'id': 'alpha', 'name': 'A'}, {'id': 'alpha', 'name': 'B'}]),
        encoding='utf-8',
    )
    with pytest.raises(ValueError, match='contains duplicate template id'):
        reference_data_module.load_template_collection(duplicate_id, ('name',))

    missing_field = tmp_path / 'missing-field.json'
    missing_field.write_text(json.dumps([{'id': 'alpha', 'name': 'A'}]), encoding='utf-8')
    with pytest.raises(ValueError, match='missing required field'):
        reference_data_module.load_template_collection(missing_field, ('name', 'slot'))

    assert reference_data_module.get_item_template(None) is None
    assert reference_data_module.get_item_template('   ') is None
    assert reference_data_module.get_enemy_template(None) is None
    assert reference_data_module.get_enemy_template('   ') is None

    invalidation_calls: list[tuple[Callable[..., Any], tuple[Any, ...]]] = []

    def fake_delete_memoized(function, *args):
        invalidation_calls.append((function, args))

    monkeypatch.setattr(reference_data_module.cache, 'delete_memoized', fake_delete_memoized)
    reference_data_module.invalidate_reference_data_cache()

    invalidated_names = {function.__name__ for function, _ in invalidation_calls}
    assert invalidated_names == {
        'get_item_type_data',
        'get_all_item_type_data',
        'get_enemy_type_data',
        'get_all_enemy_type_data',
    }