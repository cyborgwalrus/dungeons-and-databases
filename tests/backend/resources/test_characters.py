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
    assert character_payload['_links']['self']['href'] == f'/api/characters/{character_id}'
    assert character_payload['_links']['self']['methods'] == ['GET', 'PUT', 'DELETE']
    assert character_payload['_links']['combat']['href'] == '/api/combats'
    assert character_payload['_links']['combat']['methods'] == ['POST']

    list_response = client.get(f'/api/users/{user.id}/characters', headers=entities.auth_headers(token))
    assert list_response.status_code == 200
    assert len(list_response.get_json()) == 1
    assert list_response.get_json()[0]['_links']['equipment']['href'] == f'/api/characters/{character_id}/equipment'
    assert list_response.get_json()[0]['_links']['equipment']['methods'] == ['GET']
    assert list_response.get_json()[0]['_links']['combat']['href'] == '/api/combats'
    assert list_response.get_json()[0]['_links']['combat']['methods'] == ['POST']

    inventory_response = client.get(f'/api/users/{user.id}/inventory', headers=entities.auth_headers(token))
    assert inventory_response.status_code == 200
    assert len(inventory_response.get_json()) == 6

    select_response = client.post(f'/api/characters/{character_id}/select', headers=entities.auth_headers(token))
    assert select_response.status_code == 200
    scoped_token = select_response.get_json()['token']
    assert select_response.get_json()['character']['state'] == 'HOME'
    assert select_response.get_json()['character']['_links']['select']['href'] == f'/api/characters/{character_id}/select'
    assert select_response.get_json()['character']['_links']['select']['methods'] == ['POST']
    assert select_response.get_json()['character']['_links']['combat']['href'] == '/api/combats'
    assert select_response.get_json()['character']['_links']['combat']['methods'] == ['POST']

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

    equip_response = client.post(f'/api/characters/{owner_character.id}/equipment/{starter_item.id}', headers=entities.auth_headers(token))
    assert equip_response.status_code == 200
    assert equip_response.get_json()['item']['id'] == starter_item.id
    assert equip_response.get_json()['item']['_links']['self']['href'] == f'/api/items/{starter_item.id}'
    assert equip_response.get_json()['item']['_links']['self']['methods'] == ['GET']

    equipment_response = client.get(
        f'/api/characters/{owner_character.id}/equipment',
        headers=entities.auth_headers(token),
    )
    assert equipment_response.status_code == 200
    assert len(equipment_response.get_json()) == 1
    assert equipment_response.get_json()[0]['_links']['unequip']['href'] == (
        f'/api/characters/{owner_character.id}/equipment/{starter_item.id}'
    )
    assert equipment_response.get_json()[0]['_links']['unequip']['methods'] == ['DELETE']

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

    assert equip_response.get_json()['item']['_links']['self']['methods'] == ['GET']
    equipment_after_unequip = client.get(
        f'/api/characters/{owner_character.id}/equipment',
        headers=entities.auth_headers(token),
    )
    assert equipment_after_unequip.status_code == 200
    assert equipment_after_unequip.get_json() == []

    inventory_after_unequip = client.get(f'/api/users/{user.id}/inventory', headers=entities.auth_headers(token))
    assert inventory_after_unequip.status_code == 200
    assert len(inventory_after_unequip.get_json()) == 7


def test_character_equipment_item_post_is_idempotent_for_equipped_item(client, entities):
    """Allow re-equipping an item that is already equipped on the same character."""
    user = entities.create_user(username='idempotent-equip', password='secret')
    character = entities.create_character(user, name='Carrier', seed_loadout=False)
    token = entities.token_for(user, character)

    starter_item = entities.create_inventory_item(character, 'steel_sword')

    first_response = client.post(
        f'/api/characters/{character.id}/equipment/{starter_item.id}',
        headers=entities.auth_headers(token),
    )
    assert first_response.status_code == 200

    second_response = client.post(
        f'/api/characters/{character.id}/equipment/{starter_item.id}',
        headers=entities.auth_headers(token),
    )
    assert second_response.status_code == 200
    assert second_response.get_json()['message'] == 'Item already equipped'
    assert second_response.get_json()['item']['id'] == starter_item.id


def test_character_equipment_actions_require_home_state(client, entities):
    """Block equip and unequip actions once the character leaves home."""
    user = entities.create_user(username='combat-lock', password='secret')
    character = entities.create_character(user, name='Guardian', seed_loadout=True)
    token = entities.token_for(user, character)
    headers = entities.auth_headers(token)

    inventory_response = client.get(f'/api/users/{user.id}/inventory', headers=headers)
    inventory_items = inventory_response.get_json()
    assert inventory_items[0]['_links']['equip']['href'] == f"/api/characters/{character.id}/equipment/{inventory_items[0]['id']}"

    equip_response = client.post(f"/api/characters/{character.id}/equipment/{inventory_items[0]['id']}", headers=headers)
    assert equip_response.status_code == 200

    combat_response = client.post('/api/combats', headers=headers)
    assert combat_response.status_code == 201
    assert combat_response.get_json()['character']['state'] == 'DUNGEON_COMBAT'
    assert 'combat' not in combat_response.get_json()['character']['_links']
    assert combat_response.get_json()['character']['_links']['equipment']['methods'] == ['GET']

    locked_inventory = client.get(f'/api/users/{user.id}/inventory', headers=headers)
    assert locked_inventory.status_code == 200
    assert all('equip' not in item['_links'] for item in locked_inventory.get_json())

    blocked_equip = client.post(
        f"/api/characters/{character.id}/equipment/{inventory_items[1]['id']}",
        headers=headers,
    )
    assert blocked_equip.status_code == 409
    assert blocked_equip.get_json()['error'] == 'Equipment can only be changed in home state'

    blocked_unequip = client.delete(
        f"/api/characters/{character.id}/equipment/{inventory_items[0]['id']}",
        headers=headers,
    )
    assert blocked_unequip.status_code == 409
    assert blocked_unequip.get_json()['error'] == 'Equipment can only be changed in home state'


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

    missing_inventory_item = client.post(f'/api/characters/{character_id}/equipment/999999', headers=headers)
    assert missing_inventory_item.status_code == 404
    assert missing_inventory_item.get_json()['error'] == 'Item not found'

    missing_equipment = client.delete(f'/api/characters/{character_id}/equipment/999999', headers=headers)
    assert missing_equipment.status_code == 404
    assert missing_equipment.get_json()['error'] == 'Item not found'

    intruder_character_lookup = client.get(f'/api/characters/{character_id}', headers=intruder_headers)
    assert intruder_character_lookup.status_code == 401
    assert intruder_character_lookup.get_json()['error'] == 'Unauthorized'