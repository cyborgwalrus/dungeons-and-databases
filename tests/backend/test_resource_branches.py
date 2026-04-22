def test_user_profile_update_and_delete_paths(client, entities):
    user = entities.create_user(username='profile-user', password='secret')
    token = entities.token_for(user)
    headers = entities.auth_headers(token)

    username_update = client.put(f'/api/users/{user.id}', headers=headers, json={'username': 'profile-user-updated'})
    assert username_update.status_code == 200
    assert username_update.get_json()['username'] == 'profile-user-updated'

    password_update = client.put(f'/api/users/{user.id}', headers=headers, json={'password': 'new-secret'})
    assert password_update.status_code == 200
    assert password_update.get_json()['username'] == 'profile-user-updated'

    inventory_clear_empty = client.delete(f'/api/users/{user.id}/inventory', headers=headers)
    assert inventory_clear_empty.status_code == 200
    assert inventory_clear_empty.get_json()['message'] == 'Inventory cleared'

    entities.create_character(user, name='ToDelete', seed_loadout=False)
    delete_response = client.delete(f'/api/users/{user.id}', headers=headers)
    assert delete_response.status_code == 200
    assert delete_response.get_json()['message'] == 'User deleted'

    deleted_user_lookup = client.get(f'/api/users/{user.id}', headers=headers)
    assert deleted_user_lookup.status_code == 404
    assert deleted_user_lookup.get_json()['error'] == 'User not found'

    deleted_character_list = client.get(f'/api/users/{user.id}/characters', headers=headers)
    assert deleted_character_list.status_code == 404
    assert deleted_character_list.get_json()['error'] == 'User not found'

    deleted_inventory_lookup = client.get(f'/api/users/{user.id}/inventory', headers=headers)
    assert deleted_inventory_lookup.status_code == 404
    assert deleted_inventory_lookup.get_json()['error'] == 'User not found'


def test_character_list_and_equipment_branches(client, entities):
    user = entities.create_user(username='character-user', password='secret')
    intruder = entities.create_user(username='intruder', password='secret')
    token = entities.token_for(user)
    headers = entities.auth_headers(token)
    intruder_headers = entities.auth_headers(entities.token_for(intruder))

    unauthorized_list = client.get(f'/api/users/{intruder.id}/characters', headers=headers)
    assert unauthorized_list.status_code == 404
    assert unauthorized_list.get_json()['error'] == 'User not found'

    create_response = client.post(
        f'/api/users/{user.id}/characters',
        headers=headers,
        json={'name': 'Hero', 'level': '2', 'health': '80', 'damage': '15'},
    )
    assert create_response.status_code == 201
    character_id = create_response.get_json()['id']

    list_response = client.get(f'/api/users/{user.id}/characters', headers=headers)
    assert list_response.status_code == 200
    assert list_response.get_json()[0]['id'] == character_id

    invalid_level = client.post(f'/api/users/{user.id}/characters', headers=headers, json={'name': 'Bad', 'level': 0})
    assert invalid_level.status_code == 400
    assert invalid_level.get_json()['error'][0]['msg'] == 'Input should be greater than or equal to 1'

    invalid_health = client.post(f'/api/users/{user.id}/characters', headers=headers, json={'name': 'Bad', 'health': -1})
    assert invalid_health.status_code == 400
    assert invalid_health.get_json()['error'][0]['msg'] == 'Input should be greater than or equal to 0'

    invalid_damage = client.post(f'/api/users/{user.id}/characters', headers=headers, json={'name': 'Bad', 'damage': -1})
    assert invalid_damage.status_code == 400
    assert invalid_damage.get_json()['error'][0]['msg'] == 'Input should be greater than or equal to 0'

    character_lookup = client.get(f'/api/characters/{character_id}', headers=headers)
    assert character_lookup.status_code == 200
    assert character_lookup.get_json()['id'] == character_id

    missing_character = client.get('/api/characters/999999', headers=headers)
    assert missing_character.status_code == 404
    assert missing_character.get_json()['error'] == 'Character not found'

    selection = client.post(f'/api/characters/{character_id}/select', headers=headers)
    assert selection.status_code == 200
    scoped_token = selection.get_json()['token']

    heal_response = client.post(f'/api/characters/{character_id}/full_heal', headers=entities.auth_headers(scoped_token))
    assert heal_response.status_code == 200
    assert heal_response.get_json()['health'] == heal_response.get_json()['max_health']

    equipment_missing = client.get(f'/api/characters/{character_id}/equipment', headers=headers)
    assert equipment_missing.status_code == 200
    assert equipment_missing.get_json() == []

    no_item_payload = client.post(f'/api/characters/{character_id}/equipment', headers=headers, json={})
    assert no_item_payload.status_code == 400
    assert no_item_payload.get_json()['error'][0]['msg'] == 'Field required'

    inventory_character = entities.create_character(user, name='Carrier', seed_loadout=False)
    positive_item_id = entities.create_inventory_item(inventory_character, 'steel_sword').id
    equip_response = client.post(
        f'/api/characters/{inventory_character.id}/equipment',
        headers=headers,
        json={'item_id': positive_item_id},
    )
    assert equip_response.status_code == 200

    item_not_found = client.post(f'/api/characters/{inventory_character.id}/equipment', headers=headers, json={'item_id': 999999})
    assert item_not_found.status_code == 404
    assert item_not_found.get_json()['error'] == 'Item not found in inventory'

    unequip_response = client.delete(f'/api/characters/{inventory_character.id}/equipment/{positive_item_id}', headers=headers)
    assert unequip_response.status_code == 200
    assert unequip_response.get_json()['message'] == 'Item unequipped'

    missing_unequip = client.delete(f'/api/characters/{inventory_character.id}/equipment/999999', headers=headers)
    assert missing_unequip.status_code == 404
    assert missing_unequip.get_json()['error'] == 'Item not found'

    assert client.get(f'/api/characters/{character_id}', headers=intruder_headers).status_code == 404