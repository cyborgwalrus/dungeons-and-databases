from unittest.mock import patch

from backend.db.models import db


def test_combat_attack_victory_grants_loot_and_spawns_followup_encounter(client, entities):
    user = entities.create_user(username='victor', password='secret')
    character = entities.create_character(user, name='Champion', health=120, damage=100)
    token = entities.token_for(user, character)

    with patch('backend.resources.encounters.random.choice', side_effect=lambda sequence: sequence[0]), patch(
        'backend.resources.combats.random.choice',
        side_effect=lambda sequence: sequence[0],
    ), patch('backend.resources.combats.random.randint', side_effect=lambda minimum, maximum: maximum):
        encounter_response = client.post('/api/encounters', headers=entities.auth_headers(token))
        combat_id = encounter_response.get_json()['combat']['id']

        attack_response = client.post(f'/api/combats/{combat_id}/attack', headers=entities.auth_headers(token))

    assert attack_response.status_code == 200
    payload = attack_response.get_json()
    assert payload['victory'] is True
    assert payload['player_died'] is False
    assert payload['items_dropped']
    assert payload['combat'] is not None
    assert payload['character']['health'] > 0


def test_combat_attack_survives_when_enemy_lives(client, entities):
    user = entities.create_user(username='scrapper', password='secret')
    character = entities.create_character(user, name='Scout', health=100, damage=10)
    token = entities.token_for(user, character)
    initial_health = character.health

    with patch('backend.resources.encounters.random.choice', side_effect=lambda sequence: sequence[0]), patch(
        'backend.resources.combats.random.randint', side_effect=lambda minimum, maximum: minimum
    ):
        encounter_response = client.post('/api/encounters', headers=entities.auth_headers(token))
        encounter_id = encounter_response.get_json()['encounter']['id']
        combat_id = encounter_response.get_json()['combat']['id']
        attack_response = client.post(f'/api/combats/{combat_id}/attack', headers=entities.auth_headers(token))

    assert attack_response.status_code == 200
    payload = attack_response.get_json()
    assert payload['victory'] is False
    assert payload['player_died'] is False
    assert payload['items_dropped'] == []
    assert payload['encounter']['id'] == encounter_id
    assert payload['combat']['id'] == combat_id
    assert payload['character']['health'] < initial_health


def test_combat_run_failure_survives_and_keeps_combat_active(client, entities):
    user = entities.create_user(username='dodger', password='secret')
    character = entities.create_character(user, name='Runner', health=80, damage=10)
    token = entities.token_for(user, character)
    initial_health = character.health

    with patch('backend.resources.encounters.random.choice', side_effect=lambda sequence: sequence[0]), patch(
        'backend.resources.combats.random.randint', side_effect=[1, 2]
    ):
        encounter_response = client.post('/api/encounters', headers=entities.auth_headers(token))
        encounter_id = encounter_response.get_json()['encounter']['id']
        combat_id = encounter_response.get_json()['combat']['id']
        run_response = client.post(f'/api/combats/{combat_id}/run', headers=entities.auth_headers(token))

    assert run_response.status_code == 200
    payload = run_response.get_json()
    assert payload['success'] is False
    assert payload['player_died'] is False
    assert payload['dice_roll'] == 1
    assert 'damage' not in payload
    assert payload['encounter']['id'] == encounter_id
    assert payload['combat']['id'] == combat_id
    assert payload['character']['health'] == initial_health - 2


def test_combat_victory_levels_up_character_and_emits_next_level_message(client, entities):
    user = entities.create_user(username='champion', password='secret')
    character = entities.create_character(user, name='Hero', health=90, damage=100)
    token = entities.token_for(user, character)
    character.experience = 95
    db.session.commit()

    with patch('backend.resources.encounters.random.choice', side_effect=lambda sequence: sequence[0]), patch(
        'backend.resources.combats.random.choice', side_effect=lambda sequence: sequence[0]
    ), patch('backend.resources.combats.random.randint', side_effect=lambda minimum, maximum: maximum):
        encounter_response = client.post('/api/encounters', headers=entities.auth_headers(token))
        combat_id = encounter_response.get_json()['combat']['id']
        attack_response = client.post(f'/api/combats/{combat_id}/attack', headers=entities.auth_headers(token))

    assert attack_response.status_code == 200
    payload = attack_response.get_json()
    assert payload['victory'] is True
    assert 'You reached level 2!' in payload['message']
    assert 'Next level at 150 XP.' in payload['message']
    assert payload['character']['level'] == 2
    assert payload['character']['experience'] == 25


def test_combat_run_success_clears_loot_flags(client, entities):
    user = entities.create_user(username='runner', password='secret')
    character = entities.create_character(user, name='Scout', health=80, damage=10)
    token = entities.token_for(user, character)
    loot_item = entities.create_inventory_item(character, 'steel_sword', is_loot=True)

    with patch('backend.resources.encounters.random.choice', side_effect=lambda sequence: sequence[0]), patch(
        'backend.resources.combats.random.randint', return_value=6
    ):
        encounter_response = client.post('/api/encounters', headers=entities.auth_headers(token))
        combat_id = encounter_response.get_json()['combat']['id']
        run_response = client.post(f'/api/combats/{combat_id}/run', headers=entities.auth_headers(token))

    assert run_response.status_code == 200
    payload = run_response.get_json()
    assert payload['success'] is True
    assert payload['encounter'] is None
    assert payload['combat'] is None

    inventory_response = client.get(f'/api/users/{user.id}/inventory', headers=entities.auth_headers(token))
    assert inventory_response.status_code == 200
    inventory_items = inventory_response.get_json()
    assert len(inventory_items) == 1
    assert inventory_items[0]['id'] == loot_item.id
    assert inventory_items[0]['is_loot'] is False


def test_combat_run_failure_can_defeat_character_and_clear_loot(client, entities):
    user = entities.create_user(username='loser', password='secret')
    character = entities.create_character(user, name='Fragile', health=1, damage=10)
    token = entities.token_for(user, character)
    entities.create_inventory_item(character, 'steel_sword', is_loot=True)

    with patch('backend.resources.encounters.random.choice', side_effect=lambda sequence: sequence[0]), patch(
        'backend.resources.combats.random.randint', side_effect=lambda minimum, maximum: minimum
    ):
        encounter_response = client.post('/api/encounters', headers=entities.auth_headers(token))
        combat_id = encounter_response.get_json()['combat']['id']
        run_response = client.post(f'/api/combats/{combat_id}/run', headers=entities.auth_headers(token))

    assert run_response.status_code == 200
    payload = run_response.get_json()
    assert payload['player_died'] is True
    assert payload['success'] is False
    assert payload['encounter'] is None
    assert payload['combat'] is None

    inventory_response = client.get(f'/api/users/{user.id}/inventory', headers=entities.auth_headers(token))
    assert inventory_response.status_code == 200
    assert inventory_response.get_json() == []


def test_combat_rejects_invalid_action_and_missing_combat(client, entities):
    user = entities.create_user(username='bystander', password='secret')
    character = entities.create_character(user, name='Watcher')
    token = entities.token_for(user, character)

    invalid_action = client.post('/api/combats/999999/dance', headers=entities.auth_headers(token))
    assert invalid_action.status_code == 404
    assert invalid_action.get_json()['error'] == 'Combat not found'

    with patch('backend.resources.encounters.random.choice', side_effect=lambda sequence: sequence[0]):
        encounter_response = client.post('/api/encounters', headers=entities.auth_headers(token))

    combat_id = encounter_response.get_json()['combat']['id']
    bad_action = client.post(f'/api/combats/{combat_id}/dance', headers=entities.auth_headers(token))
    assert bad_action.status_code == 400
    assert bad_action.get_json()['error'] == 'Invalid combat action'


def test_combat_routes_require_authentication(client, entities):
    user = entities.create_user(username='runner', password='secret')
    character = entities.create_character(user, name='Scout')
    token = entities.token_for(user, character)

    with patch('backend.resources.encounters.random.choice', side_effect=lambda sequence: sequence[0]):
        encounter_response = client.post('/api/encounters', headers=entities.auth_headers(token))

    combat_id = encounter_response.get_json()['combat']['id']
    response = client.post(f'/api/combats/{combat_id}/attack')

    assert response.status_code == 401
    assert response.get_json()['error'] == 'Unauthorized'