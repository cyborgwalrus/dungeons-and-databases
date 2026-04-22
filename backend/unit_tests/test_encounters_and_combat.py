from unittest.mock import patch


def test_encounter_creation_returns_combat_payload(client, entities):
    user = entities.create_user(username='dungeon-user', password='secret')
    character = entities.create_character(user, name='Fighter', health=120, damage=12)
    token = entities.token_for(user, character)

    with patch('backend.resources.encounters.random.choice', side_effect=lambda sequence: sequence[0]):
        response = client.post('/api/encounters', headers=entities.auth_headers(token))

    assert response.status_code == 201
    payload = response.get_json()
    assert payload['encounter']['character_id'] == character.id
    assert payload['combat']['character_id'] == character.id
    assert payload['character']['id'] == character.id


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
    assert payload['combat']['id'] != combat_id
    assert payload['character']['health'] > 0


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