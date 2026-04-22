def test_item_creation_get_and_delete_supports_batch_payloads(client, entities):
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