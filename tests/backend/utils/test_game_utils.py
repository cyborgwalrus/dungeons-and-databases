"""Tests for backend authentication helpers."""

import pytest

from backend.utils import game_utils


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

    with app.test_request_context(headers={'Authorization': 'Bearer   '}):
        assert game_utils.get_request_auth_payload() is None

    with app.test_request_context(headers={'Authorization': f'Bearer {token}'}):
        monkeypatch.setitem(app.config, 'AUTH_TOKEN_MAX_AGE_SECONDS', 'not-an-int')
        assert game_utils.get_request_auth_payload() is None
    monkeypatch.setitem(app.config, 'AUTH_TOKEN_MAX_AGE_SECONDS', 60 * 60 * 24 * 30)

    bad_payload_token = game_utils.get_auth_serializer().dumps({'user_id': 'nope', 'character_id': 'still-nope'})
    with app.test_request_context(headers={'Authorization': f'Bearer {bad_payload_token}'}):
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
