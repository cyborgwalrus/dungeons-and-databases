def test_character_creation_listing_and_selection_flow(client, entities):
    """Cover character creation, listing, and selection flows."""
    user = entities.create_user(username='player', password='secret')
    token = entities.token_for(user)

    create_response = client.post(
        f'/api/users/{user.id}/characters',
        headers=entities.auth_headers(token),
        json={'name': 'Mage', 'level': 2, 'health': 50, 'damage': 14},
    )
    assert create_response.status_code == 201
    character_payload = create_response.get_json()
    character_id = character_payload['id']
    assert character_payload['state'] == 'HOME'

    list_response = client.get(f'/api/users/{user.id}/characters', headers=entities.auth_headers(token))
    assert list_response.status_code == 200
    assert len(list_response.get_json()) == 1

    inventory_response = client.get(f'/api/users/{user.id}/inventory', headers=entities.auth_headers(token))
    assert inventory_response.status_code == 200
    assert len(inventory_response.get_json()) == 6

    select_response = client.post(f'/api/characters/{character_id}/select', headers=entities.auth_headers(token))
    assert select_response.status_code == 200
    scoped_token = select_response.get_json()['token']
    assert select_response.get_json()['character']['state'] == 'HOME'

    me_response = client.get('/api/login/me', headers=entities.auth_headers(scoped_token))
    assert me_response.status_code == 200
    assert me_response.get_json()['character']['id'] == character_id
    assert me_response.get_json()['user']['state'] == 'CHARACTER_SELECTED'


def test_character_update_validation_and_equipment_round_trip(client, entities):
    """Cover character updates, equip, and unequip flows."""
    user = entities.create_user(username='gear-user', password='secret')
    token = entities.token_for(user)

    create_response = client.post(
        f'/api/users/{user.id}/characters',
        headers=entities.auth_headers(token),
        json={'name': 'Rogue'},
    )
    character_id = create_response.get_json()['id']

    invalid_update = client.put(
        f'/api/characters/{character_id}',
        headers=entities.auth_headers(token),
        json={'level': 0},
    )
    assert invalid_update.status_code == 400
    assert invalid_update.get_json()['error'][0]['msg'] == 'Input should be greater than or equal to 1'

    valid_update = client.put(
        f'/api/characters/{character_id}',
        headers=entities.auth_headers(token),
        json={'health': 80, 'damage': 18, 'level': 3},
    )
    assert valid_update.status_code == 200
    updated_character = valid_update.get_json()
    assert updated_character['health'] == 80
    assert updated_character['damage'] == 18
    assert updated_character['level'] == 3

    owner_character = entities.create_character(user, name='Temp', seed_loadout=False)
    starter_item = entities.create_inventory_item(owner_character, 'steel_sword')

    equip_response = client.post(
        f'/api/characters/{owner_character.id}/equipment',
        headers=entities.auth_headers(token),
        json={'item_id': starter_item.id},
    )
    assert equip_response.status_code == 200
    assert equip_response.get_json()['item']['id'] == starter_item.id

    equipment_response = client.get(
        f'/api/characters/{owner_character.id}/equipment',
        headers=entities.auth_headers(token),
    )
    assert equipment_response.status_code == 200
    assert len(equipment_response.get_json()) == 1

    inventory_after_equip = client.get(f'/api/users/{user.id}/inventory', headers=entities.auth_headers(token))
    assert inventory_after_equip.status_code == 200

    inventory_items = inventory_after_equip.get_json()
    assert len(inventory_items) == 6
    assert starter_item.id not in {item['id'] for item in inventory_items}

    unequip_response = client.delete(
        f'/api/characters/{owner_character.id}/equipment/{starter_item.id}',
        headers=entities.auth_headers(token),
    )
    assert unequip_response.status_code == 200
    assert unequip_response.get_json()['message'] == 'Item unequipped'

    equipment_after_unequip = client.get(
        f'/api/characters/{owner_character.id}/equipment',
        headers=entities.auth_headers(token),
    )
    assert equipment_after_unequip.status_code == 200
    assert equipment_after_unequip.get_json() == []

    inventory_after_unequip = client.get(f'/api/users/{user.id}/inventory', headers=entities.auth_headers(token))
    assert inventory_after_unequip.status_code == 200
    assert len(inventory_after_unequip.get_json()) == 7


def test_character_delete_returns_token_when_active_character_is_removed(client, entities):
    """Return a replacement token when deleting the active character."""
    user = entities.create_user(username='deleter', password='secret')
    token = entities.token_for(user)

    create_response = client.post(
        f'/api/users/{user.id}/characters',
        headers=entities.auth_headers(token),
        json={'name': 'Target'},
    )
    character_id = create_response.get_json()['id']

    select_response = client.post(f'/api/characters/{character_id}/select', headers=entities.auth_headers(token))
    scoped_token = select_response.get_json()['token']

    delete_response = client.delete(f'/api/characters/{character_id}', headers=entities.auth_headers(scoped_token))
    assert delete_response.status_code == 200
    assert delete_response.get_json()['message'] == 'Character deleted'
    assert 'token' in delete_response.get_json()

    me_response = client.get('/api/login/me', headers=entities.auth_headers(delete_response.get_json()['token']))
    assert me_response.status_code == 200
    assert me_response.get_json()['user']['state'] == 'LOGGED_IN'


def test_character_endpoints_reject_invalid_payloads_and_ownership_errors(client, entities):
    """Reject invalid character payloads and ownership violations."""
    user = entities.create_user(username='character-user', password='secret')
    intruder = entities.create_user(username='intruder', password='secret')
    token = entities.token_for(user)
    headers = entities.auth_headers(token)
    intruder_headers = entities.auth_headers(entities.token_for(intruder))

    create_response = client.post(
        f'/api/users/{user.id}/characters',
        headers=headers,
        json={'name': 'Hero', 'level': '2', 'health': '80', 'damage': '15'},
    )
    assert create_response.status_code == 201
    character_id = create_response.get_json()['id']

    invalid_level = client.put(f'/api/characters/{character_id}', headers=headers, json={'level': 0})
    assert invalid_level.status_code == 400
    assert invalid_level.get_json()['error'][0]['msg'] == 'Input should be greater than or equal to 1'

    invalid_health = client.put(f'/api/characters/{character_id}', headers=headers, json={'health': -1})
    assert invalid_health.status_code == 400
    assert invalid_health.get_json()['error'][0]['msg'] == 'Input should be greater than or equal to 0'

    invalid_damage = client.put(f'/api/characters/{character_id}', headers=headers, json={'damage': -1})
    assert invalid_damage.status_code == 400
    assert invalid_damage.get_json()['error'][0]['msg'] == 'Input should be greater than or equal to 0'

    invalid_integer = client.put(f'/api/characters/{character_id}', headers=headers, json={'level': 'bad'})
    assert invalid_integer.status_code == 400
    assert invalid_integer.get_json()['error'][0]['msg'] == 'Input should be a valid integer, unable to parse string as an integer'

    missing_character = client.get('/api/characters/999999', headers=headers)
    assert missing_character.status_code == 404
    assert missing_character.get_json()['error'] == 'Character not found'

    missing_item_id = client.post(f'/api/characters/{character_id}/equipment', headers=headers, json={})
    assert missing_item_id.status_code == 400
    assert missing_item_id.get_json()['error'][0]['msg'] == 'Field required'

    invalid_item_id = client.post(f'/api/characters/{character_id}/equipment', headers=headers, json={'item_id': 0})
    assert invalid_item_id.status_code == 400
    assert invalid_item_id.get_json()['error'][0]['msg'] == 'Input should be greater than or equal to 1'

    missing_inventory_item = client.post(
        f'/api/characters/{character_id}/equipment',
        headers=headers,
        json={'item_id': 999999},
    )
    assert missing_inventory_item.status_code == 404
    assert missing_inventory_item.get_json()['error'] == 'Item not found in inventory'

    missing_equipment = client.delete(f'/api/characters/{character_id}/equipment/999999', headers=headers)
    assert missing_equipment.status_code == 404
    assert missing_equipment.get_json()['error'] == 'Item not found'

    intruder_character_lookup = client.get(f'/api/characters/{character_id}', headers=intruder_headers)
    assert intruder_character_lookup.status_code == 401
    assert intruder_character_lookup.get_json()['error'] == 'Unauthorized'