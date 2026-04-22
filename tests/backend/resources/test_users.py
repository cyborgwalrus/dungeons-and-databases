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