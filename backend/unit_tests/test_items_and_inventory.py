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


def test_inventory_clear_preserves_equipped_items(client, entities):
    user = entities.create_user(username='inventory-user', password='secret')
    character = entities.create_character(user, name='Keeper', seed_loadout=True)
    token = entities.token_for(user, character)

    inventory_response = client.get(f'/api/users/{user.id}/inventory', headers=entities.auth_headers(token))
    inventory_items = inventory_response.get_json()
    assert len(inventory_items) == 6

    equipped_source = inventory_items[0]
    equip_response = client.post(
        f'/api/characters/{character.id}/equipment',
        headers=entities.auth_headers(token),
        json={'item_id': equipped_source['id']},
    )
    assert equip_response.status_code == 200

    extra_item_response = client.post(
        '/api/items',
        headers=entities.auth_headers(token),
        json={'item_type_id': 'iron_helmet'},
    )
    assert extra_item_response.status_code == 201

    clear_response = client.delete(f'/api/users/{user.id}/inventory', headers=entities.auth_headers(token))
    assert clear_response.status_code == 200
    assert clear_response.get_json()['message'] == 'Inventory cleared'

    inventory_after_clear = client.get(f'/api/users/{user.id}/inventory', headers=entities.auth_headers(token))
    assert inventory_after_clear.status_code == 200
    assert inventory_after_clear.get_json() == []

    equipment_response = client.get(f'/api/characters/{character.id}/equipment', headers=entities.auth_headers(token))
    assert equipment_response.status_code == 200
    assert len(equipment_response.get_json()) == 1