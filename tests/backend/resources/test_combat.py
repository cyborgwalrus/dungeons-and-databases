from unittest.mock import patch

from backend.db.models import db


def test_combat_attack_victory_keeps_defeated_enemy_visible(client, entities):
    user = entities.create_user(username='victor', password='secret')
    character = entities.create_character(user, name='Champion', health=120, damage=100)
    token = entities.token_for(user, character)

    with patch('backend.resources.encounters.random.choice', side_effect=lambda sequence: sequence[0]), patch(
        'backend.resources.combats.random.choice',
        side_effect=lambda sequence: sequence[0],
    ), patch('backend.resources.combats.random.randint', side_effect=lambda minimum, maximum: maximum):
        combat_response = client.post('/api/combats', headers=entities.auth_headers(token))
        combat_id = combat_response.get_json()['combat']['id']

        attack_response = client.get(f'/api/combats/{combat_id}/attack', headers=entities.auth_headers(token))
        detail_response = client.get(f'/api/combats/{combat_id}', headers=entities.auth_headers(token))

    assert attack_response.status_code == 200
    payload = attack_response.get_json()
    assert payload['victory'] is True
    assert payload['player_died'] is False
    assert payload['items_dropped']
    assert payload['combat'] is not None
    assert payload['combat']['enemy_current_health'] == 0
    assert payload['character']['health'] > 0

    assert detail_response.status_code == 200
    assert detail_response.get_json()['id'] == combat_id


def test_combat_deeper_after_victory_loads_next_enemy(client, entities):
    user = entities.create_user(username='deepdelver', password='secret')
    character = entities.create_character(user, name='Champion', health=120, damage=100)
    token = entities.token_for(user, character)

    with patch('backend.resources.encounters.random.choice', side_effect=lambda sequence: sequence[0]), patch(
        'backend.resources.combats.random.choice',
        side_effect=lambda sequence: sequence[0],
    ), patch('backend.resources.combats.random.randint', side_effect=lambda minimum, maximum: maximum):
        combat_response = client.post('/api/combats', headers=entities.auth_headers(token))
        combat_id = combat_response.get_json()['combat']['id']

        victory_response = client.get(f'/api/combats/{combat_id}/attack', headers=entities.auth_headers(token))
        deeper_response = client.get(f'/api/combats/{combat_id}/deeper', headers=entities.auth_headers(token))

    assert victory_response.status_code == 200
    victory_payload = victory_response.get_json()
    assert victory_payload['victory'] is True
    assert victory_payload['combat'] is not None

    assert deeper_response.status_code == 200
    deeper_payload = deeper_response.get_json()
    assert deeper_payload['victory'] is False
    assert deeper_payload['combat'] is not None
    assert deeper_payload['combat']['id'] != victory_payload['combat']['id']
    assert deeper_payload['combat']['enemy_level'] == victory_payload['combat']['enemy_level'] + 1


def test_combat_home_after_victory_returns_home_and_keeps_loot(client, entities):
    user = entities.create_user(username='homer', password='secret')
    character = entities.create_character(user, name='Champion', health=120, damage=100)
    token = entities.token_for(user, character)

    with patch('backend.resources.encounters.random.choice', side_effect=lambda sequence: sequence[0]), patch(
        'backend.resources.combats.random.choice',
        side_effect=lambda sequence: sequence[0],
    ), patch('backend.resources.combats.random.randint', side_effect=lambda minimum, maximum: maximum):
        combat_response = client.post('/api/combats', headers=entities.auth_headers(token))
        combat_id = combat_response.get_json()['combat']['id']
        victory_response = client.get(f'/api/combats/{combat_id}/attack', headers=entities.auth_headers(token))
        home_response = client.get(f'/api/combats/{combat_id}/home', headers=entities.auth_headers(token))

    assert victory_response.status_code == 200
    assert home_response.status_code == 200
    home_payload = home_response.get_json()
    assert home_payload['success'] is True
    assert home_payload['combat'] is None

    inventory_response = client.get(f'/api/users/{user.id}/inventory', headers=entities.auth_headers(token))
    assert inventory_response.status_code == 200
    inventory_items = inventory_response.get_json()
    assert inventory_items
    assert len(inventory_items) == 1


def test_combat_attack_survives_when_enemy_lives(client, entities):
    user = entities.create_user(username='scrapper', password='secret')
    character = entities.create_character(user, name='Scout', health=100, damage=10)
    token = entities.token_for(user, character)
    initial_health = character.health

    with patch('backend.resources.encounters.random.choice', side_effect=lambda sequence: sequence[0]), patch(
        'backend.resources.combats.random.randint', side_effect=lambda minimum, maximum: minimum
    ):
        combat_response = client.post('/api/combats', headers=entities.auth_headers(token))
        combat_id = combat_response.get_json()['combat']['id']
        attack_response = client.get(f'/api/combats/{combat_id}/attack', headers=entities.auth_headers(token))

    assert attack_response.status_code == 200
    payload = attack_response.get_json()
    assert payload['victory'] is False
    assert payload['player_died'] is False
    assert payload['items_dropped'] == []
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
        combat_response = client.post('/api/combats', headers=entities.auth_headers(token))
        combat_id = combat_response.get_json()['combat']['id']
        run_response = client.get(f'/api/combats/{combat_id}/run', headers=entities.auth_headers(token))

    assert run_response.status_code == 200
    payload = run_response.get_json()
    assert payload['success'] is False
    assert payload['player_died'] is False
    assert payload['dice_roll'] == 1
    assert 'damage' not in payload
    assert payload['combat']['id'] == combat_id
    assert payload['character']['health'] == initial_health - 2


def test_combat_victory_levels_up_character_and_emits_next_level_message(client, entities):
    user = entities.create_user(username='champion', password='secret')
    character = entities.create_character(user, name='Hero', health=90, damage=100)
    initial_health = character.health
    token = entities.token_for(user, character)
    character.experience = 95
    db.session.commit()

    with patch('backend.resources.encounters.random.choice', side_effect=lambda sequence: sequence[0]), patch(
        'backend.resources.combats.random.choice', side_effect=lambda sequence: sequence[0]
    ), patch('backend.resources.combats.random.randint', side_effect=lambda minimum, maximum: maximum):
        combat_response = client.post('/api/combats', headers=entities.auth_headers(token))
        combat_id = combat_response.get_json()['combat']['id']
        attack_response = client.get(f'/api/combats/{combat_id}/attack', headers=entities.auth_headers(token))

    assert attack_response.status_code == 200
    payload = attack_response.get_json()
    assert payload['victory'] is True
    assert 'You reached level 2!' in payload['message']
    assert 'Next level at 150 XP.' in payload['message']
    assert payload['character']['level'] == 2
    assert payload['character']['experience'] == 25
    assert payload['character']['health'] > initial_health


def test_combat_run_success_leaves_inventory_untouched(client, entities):
    user = entities.create_user(username='runner', password='secret')
    character = entities.create_character(user, name='Scout', health=80, damage=10)
    token = entities.token_for(user, character)
    loot_item = entities.create_inventory_item(character, 'steel_sword')

    with patch('backend.resources.encounters.random.choice', side_effect=lambda sequence: sequence[0]), patch(
        'backend.resources.combats.random.randint', return_value=6
    ):
        combat_response = client.post('/api/combats', headers=entities.auth_headers(token))
        combat_id = combat_response.get_json()['combat']['id']
        run_response = client.get(f'/api/combats/{combat_id}/run', headers=entities.auth_headers(token))

    assert run_response.status_code == 200
    payload = run_response.get_json()
    assert payload['success'] is True
    assert payload['combat'] is None

    inventory_response = client.get(f'/api/users/{user.id}/inventory', headers=entities.auth_headers(token))
    assert inventory_response.status_code == 200
    inventory_items = inventory_response.get_json()
    assert len(inventory_items) == 1
    assert inventory_items[0]['id'] == loot_item.id


def test_combat_run_failure_can_defeat_character_and_keep_inventory(client, entities):
    user = entities.create_user(username='loser', password='secret')
    character = entities.create_character(user, name='Fragile', health=1, damage=10)
    token = entities.token_for(user, character)
    entities.create_inventory_item(character, 'steel_sword')

    with patch('backend.resources.encounters.random.choice', side_effect=lambda sequence: sequence[0]), patch(
        'backend.resources.combats.random.randint', side_effect=lambda minimum, maximum: minimum
    ):
        combat_response = client.post('/api/combats', headers=entities.auth_headers(token))
        combat_id = combat_response.get_json()['combat']['id']
        run_response = client.get(f'/api/combats/{combat_id}/run', headers=entities.auth_headers(token))

    assert run_response.status_code == 200
    payload = run_response.get_json()
    assert payload['player_died'] is True
    assert payload['success'] is False
    assert payload['combat'] is None

    inventory_response = client.get(f'/api/users/{user.id}/inventory', headers=entities.auth_headers(token))
    assert inventory_response.status_code == 200
    inventory_items = inventory_response.get_json()
    assert len(inventory_items) == 1
    assert inventory_items[0]['id'] == 1


def test_combat_rejects_invalid_action_and_missing_combat(client, entities):
    user = entities.create_user(username='bystander', password='secret')
    character = entities.create_character(user, name='Watcher')
    token = entities.token_for(user, character)

    invalid_action = client.get('/api/combats/999999/dance', headers=entities.auth_headers(token))
    assert invalid_action.status_code == 404
    assert invalid_action.get_json()['error'] == 'Combat not found'

    with patch('backend.resources.encounters.random.choice', side_effect=lambda sequence: sequence[0]):
        combat_response = client.post('/api/combats', headers=entities.auth_headers(token))

    combat_id = combat_response.get_json()['combat']['id']
    bad_action = client.get(f'/api/combats/{combat_id}/dance', headers=entities.auth_headers(token))
    assert bad_action.status_code == 400
    assert bad_action.get_json()['error'] == 'Invalid combat action'


def test_combat_routes_require_authentication(client, entities):
    user = entities.create_user(username='runner', password='secret')
    character = entities.create_character(user, name='Scout')
    token = entities.token_for(user, character)

    with patch('backend.resources.encounters.random.choice', side_effect=lambda sequence: sequence[0]):
        combat_response = client.post('/api/combats', headers=entities.auth_headers(token))

    combat_id = combat_response.get_json()['combat']['id']
    response = client.get(f'/api/combats/{combat_id}/attack')

    assert response.status_code == 401
    assert response.get_json()['error'] == 'Unauthorized'