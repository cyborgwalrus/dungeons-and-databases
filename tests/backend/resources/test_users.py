def test_user_endpoints_require_authentication(client, entities):
    """Require authentication for user endpoints."""
    user = entities.create_user(username='owner', password='secret')

    response = client.get(f'/api/users/{user.id}')

    assert response.status_code == 401
    assert response.get_json()['error'] == 'Unauthorized'


def test_user_endpoints_enforce_ownership_and_allow_profile_updates(client, entities):
    """Enforce user ownership while allowing profile updates."""
    owner = entities.create_user(username='owner', password='secret')
    intruder = entities.create_user(username='intruder', password='secret')
    owner_token = entities.token_for(owner)

    forbidden_get = client.get(f'/api/users/{intruder.id}', headers=entities.auth_headers(owner_token))
    assert forbidden_get.status_code == 401
    assert forbidden_get.get_json()['error'] == 'Unauthorized'

    get_response = client.get(f'/api/users/{owner.id}', headers=entities.auth_headers(owner_token))
    assert get_response.status_code == 200
    assert get_response.get_json()['username'] == 'owner'

    update_response = client.put(
        f'/api/users/{owner.id}',
        headers=entities.auth_headers(owner_token),
        json={'username': 'owner-updated'},
    )
    assert update_response.status_code == 200
    assert update_response.get_json()['username'] == 'owner-updated'

    delete_response = client.delete(f'/api/users/{owner.id}', headers=entities.auth_headers(owner_token))
    assert delete_response.status_code == 200
    assert delete_response.get_json()['message'] == 'User deleted'

    deleted_lookup = client.get(f'/api/users/{owner.id}', headers=entities.auth_headers(owner_token))
    assert deleted_lookup.status_code == 401
    assert deleted_lookup.get_json()['error'] == 'Unauthorized'


def test_user_inventory_clear_preserves_equipped_items(client, entities):
    """Clear only unequipped inventory items."""
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


def test_user_routes_reject_intruder_access_and_deleted_user_inventory_reads(client, entities):
    """Reject intruder access and deleted-user inventory lookups."""
    user = entities.create_user(username='profile-user', password='secret')
    observer = entities.create_user(username='observer', password='secret')
    observer_headers = entities.auth_headers(entities.token_for(observer))
    token = entities.token_for(user)
    headers = entities.auth_headers(token)

    unauthorized_character_list = client.get(f'/api/users/{observer.id}/characters', headers=headers)
    assert unauthorized_character_list.status_code == 401
    assert unauthorized_character_list.get_json()['error'] == 'Unauthorized'

    unauthorized_inventory = client.get(f'/api/users/{observer.id}/inventory', headers=headers)
    assert unauthorized_inventory.status_code == 401
    assert unauthorized_inventory.get_json()['error'] == 'Unauthorized'

    entities.create_character(user, name='ToDelete', seed_loadout=False)
    delete_response = client.delete(f'/api/users/{user.id}', headers=headers)
    assert delete_response.status_code == 200
    assert delete_response.get_json()['message'] == 'User deleted'

    deleted_character_list = client.get(f'/api/users/{user.id}/characters', headers=observer_headers)
    assert deleted_character_list.status_code == 404
    assert deleted_character_list.get_json()['error'] == 'User not found'

    deleted_inventory_lookup = client.get(f'/api/users/{user.id}/inventory', headers=observer_headers)
    assert deleted_inventory_lookup.status_code == 404
    assert deleted_inventory_lookup.get_json()['error'] == 'User not found'