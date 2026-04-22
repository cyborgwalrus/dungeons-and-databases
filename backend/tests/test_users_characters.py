def test_user_endpoints_enforce_ownership_and_allow_profile_updates(client, entities):
    owner = entities.create_user(username='owner', password='secret')
    intruder = entities.create_user(username='intruder', password='secret')
    owner_token = entities.token_for(owner)

    forbidden_get = client.get(f'/api/users/{intruder.id}', headers=entities.auth_headers(owner_token))
    assert forbidden_get.status_code == 401

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


def test_character_creation_listing_selection_and_heal_flow(client, entities):
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

    list_response = client.get(f'/api/users/{user.id}/characters', headers=entities.auth_headers(token))
    assert list_response.status_code == 200
    assert len(list_response.get_json()) == 1

    inventory_response = client.get(f'/api/users/{user.id}/inventory', headers=entities.auth_headers(token))
    assert inventory_response.status_code == 200
    assert len(inventory_response.get_json()) == 6

    select_response = client.post(f'/api/characters/{character_id}/select', headers=entities.auth_headers(token))
    assert select_response.status_code == 200
    scoped_token = select_response.get_json()['token']

    me_response = client.get('/api/login/me', headers=entities.auth_headers(scoped_token))
    assert me_response.status_code == 200
    assert me_response.get_json()['character']['id'] == character_id

    heal_response = client.post(f'/api/characters/{character_id}/full_heal', headers=entities.auth_headers(token))
    assert heal_response.status_code == 200
    healed_character = heal_response.get_json()
    assert healed_character['health'] == healed_character['max_health']


def test_character_update_validation_and_equipment_round_trip(client, entities):
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
    assert invalid_update.get_json()['error'] == 'level must be at least 1'

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