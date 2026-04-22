def test_auth_resources_reject_missing_required_fields(client):
    missing_signup_username = client.post('/api/login/signup', json={'password': 'secret'})
    assert missing_signup_username.status_code == 400
    assert missing_signup_username.get_json()['error'] == 'username is required'

    missing_signup_password = client.post('/api/login/signup', json={'username': 'alice'})
    assert missing_signup_password.status_code == 400
    assert missing_signup_password.get_json()['error'] == 'password is required'

    missing_signin_username = client.post('/api/login/signin', json={'password': 'secret'})
    assert missing_signin_username.status_code == 400
    assert missing_signin_username.get_json()['error'] == 'username is required'

    missing_signin_password = client.post('/api/login/signin', json={'username': 'alice'})
    assert missing_signin_password.status_code == 400
    assert missing_signin_password.get_json()['error'] == 'password is required'


def test_user_and_character_resources_reject_unauthorized_or_invalid_updates(client, entities):
    owner = entities.create_user(username='owner', password='secret')
    intruder = entities.create_user(username='intruder', password='secret')
    owner_token = entities.token_for(owner)
    intruder_token = entities.token_for(intruder)

    owner_headers = entities.auth_headers(owner_token)
    intruder_headers = entities.auth_headers(intruder_token)

    assert client.get(f'/api/users/{owner.id}', headers=intruder_headers).status_code == 401
    assert client.put(f'/api/users/{owner.id}', headers=intruder_headers, json={'username': 'hijacked'}).status_code == 401

    create_response = client.post(f'/api/users/{owner.id}/characters', headers=owner_headers, json={'name': 'Hero'})
    character_id = create_response.get_json()['id']

    assert client.get(f'/api/users/{intruder.id}/characters', headers=owner_headers).status_code == 401
    assert client.post(f'/api/users/{intruder.id}/characters', headers=owner_headers, json={'name': 'Hero'}).status_code == 401
    assert client.get(f'/api/characters/{character_id}', headers=intruder_headers).status_code == 404

    negative_health = client.put(f'/api/characters/{character_id}', headers=owner_headers, json={'health': -1})
    assert negative_health.status_code == 400
    assert negative_health.get_json()['error'] == 'health must be non-negative'

    negative_damage = client.put(f'/api/characters/{character_id}', headers=owner_headers, json={'damage': -1})
    assert negative_damage.status_code == 400
    assert negative_damage.get_json()['error'] == 'damage must be non-negative'

    invalid_integer = client.put(f'/api/characters/{character_id}', headers=owner_headers, json={'level': 'bad'})
    assert invalid_integer.status_code == 400
    assert invalid_integer.get_json()['error'] == 'health, damage, and level must be valid integers'

    missing_item_id = client.post(f'/api/characters/{character_id}/equipment', headers=owner_headers, json={})
    assert missing_item_id.status_code == 400
    assert missing_item_id.get_json()['error'] == 'item_id is required'

    invalid_item_id = client.post(f'/api/characters/{character_id}/equipment', headers=owner_headers, json={'item_id': 0})
    assert invalid_item_id.status_code == 400
    assert invalid_item_id.get_json()['error'] == 'item_id must be a positive integer'

    missing_inventory_item = client.post(
        f'/api/characters/{character_id}/equipment',
        headers=owner_headers,
        json={'item_id': 999999},
    )
    assert missing_inventory_item.status_code == 404
    assert missing_inventory_item.get_json()['error'] == 'Item not found in inventory'

    missing_equipment = client.delete(f'/api/characters/{character_id}/equipment/999999', headers=owner_headers)
    assert missing_equipment.status_code == 404
    assert missing_equipment.get_json()['error'] == 'Equipment not found'


def test_item_resources_reject_invalid_payloads_and_missing_inventory_items(client, entities):
    user = entities.create_user(username='item-user', password='secret')
    character = entities.create_character(user, name='Carrier', seed_loadout=False)
    token = entities.token_for(user, character)
    headers = entities.auth_headers(token)

    missing_item_type = client.post('/api/items', headers=headers, json={})
    assert missing_item_type.status_code == 400
    assert missing_item_type.get_json()['error'] == 'item_type_id is required'

    blank_item_type = client.post('/api/items', headers=headers, json=['steel_sword', ' '])
    assert blank_item_type.status_code == 400
    assert blank_item_type.get_json()['error'] == 'item_type_id must be non-empty strings'

    missing_catalog_item = client.post('/api/items', headers=headers, json=['missing-item'])
    assert missing_catalog_item.status_code == 404
    assert missing_catalog_item.get_json()['error'] == 'Item not found'

    create_response = client.post('/api/items', headers=headers, json={'item_type_id': 'steel_sword'})
    assert create_response.status_code == 201
    item_id = create_response.get_json()[0]['id']

    item_lookup = client.get(f'/api/items/{item_id}', headers=headers)
    assert item_lookup.status_code == 200
    assert item_lookup.get_json()['id'] == item_id

    equipment_response = client.post(
        f'/api/characters/{character.id}/equipment',
        headers=headers,
        json={'item_id': item_id},
    )
    assert equipment_response.status_code == 200

    delete_equipped_item = client.delete(f'/api/items/{item_id}', headers=headers)
    assert delete_equipped_item.status_code == 404
    assert delete_equipped_item.get_json()['error'] == 'Item not in inventory'

    missing_item_lookup = client.get('/api/items/999999', headers=headers)
    assert missing_item_lookup.status_code == 404
    assert missing_item_lookup.get_json()['error'] == 'Item not found'