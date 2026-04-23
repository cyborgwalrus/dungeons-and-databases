from unittest.mock import patch


def test_combat_creation_returns_combat_payload(client, entities):
    user = entities.create_user(username='dungeon-user', password='secret')
    character = entities.create_character(user, name='Fighter', health=120, damage=12)
    token = entities.token_for(user, character)

    with patch('backend.resources.encounters.random.choice', side_effect=lambda sequence: sequence[0]):
        response = client.post('/api/combats', headers=entities.auth_headers(token))

    assert response.status_code == 201
    payload = response.get_json()
    assert payload['combat']['character_id'] == character.id
    assert payload['combat']['enemy_level'] == 1
    assert payload['character']['id'] == character.id


def test_combat_creation_returns_404_when_enemy_catalog_is_empty(client, entities):
    user = entities.create_user(username='stranded', password='secret')
    character = entities.create_character(user, name='Wanderer')
    token = entities.token_for(user, character)

    with patch('backend.resources.encounters.get_enemy_types', return_value=[]):
        response = client.post('/api/combats', headers=entities.auth_headers(token))

    assert response.status_code == 404
    assert response.get_json()['error'] == 'No enemy types available'