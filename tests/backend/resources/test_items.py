def test_item_creation_get_and_delete_supports_batch_payloads(client, entities):
    """Create, fetch, and delete inventory items with batch payloads."""
    user = entities.create_user(username='item-user', password='secret')
    character = entities.create_character(user, name='Carrier', seed_loadout=False)
    token = entities.token_for(user, character)

    create_response = client.post(
        '/api/items',
        headers=entities.auth_headers(token),
        json=['steel_sword', 'iron_shield'],
    )
    assert create_response.status_code == 201
    created_items = create_response.get_json()
    assert len(created_items) == 2

    item_id = created_items[0]['id']
    get_response = client.get(f'/api/items/{item_id}', headers=entities.auth_headers(token))
    assert get_response.status_code == 200
    assert get_response.get_json()['id'] == item_id

    delete_response = client.delete(f'/api/items/{item_id}', headers=entities.auth_headers(token))
    assert delete_response.status_code == 200
    assert delete_response.get_json()['message'] == 'Item removed from inventory'

    missing_response = client.get(f'/api/items/{item_id}', headers=entities.auth_headers(token))
    assert missing_response.status_code == 404


def test_item_resources_validate_payloads_and_equipped_item_guards(client, entities):
    """Validate item payloads and reject equipped-item mutations."""
    user = entities.create_user(username='item-user', password='secret')
    character = entities.create_character(user, name='Carrier', seed_loadout=False)
    token = entities.token_for(user, character)
    headers = entities.auth_headers(token)

    missing_item_type = client.post('/api/items', headers=headers, json={})
    assert missing_item_type.status_code == 400
    assert missing_item_type.get_json()['error'][0]['msg'] == 'Field required'

    blank_item_type = client.post('/api/items', headers=headers, json=['steel_sword', ' '])
    assert blank_item_type.status_code == 400
    assert blank_item_type.get_json()['error'][0]['msg'] == 'String should have at least 1 character'

    missing_catalog_item = client.post('/api/items', headers=headers, json=['missing-item'])
    assert missing_catalog_item.status_code == 404
    assert missing_catalog_item.get_json()['error'] == 'Item not found'

    create_response = client.post('/api/items', headers=headers, json={'item_type_id': 'steel_sword'})
    assert create_response.status_code == 201
    item_id = create_response.get_json()[0]['id']

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