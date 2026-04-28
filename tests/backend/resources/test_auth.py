def test_signup_signin_signout_and_me_without_character(client, entities):
    """Cover the full auth happy path without an active character."""
    signup_response = client.post(
        '/api/login/signup',
        json={'username': 'alice', 'password': 'secret'},
    )
    assert signup_response.status_code == 201
    signup_payload = signup_response.get_json()
    token = signup_payload['token']
    assert signup_payload['user']['username'] == 'alice'
    assert signup_payload['user']['state'] == 'LOGGED_IN'
    assert signup_payload['user']['_links']['self']['href'] == f"/api/users/{signup_payload['user']['id']}"
    assert signup_payload['user']['_links']['self']['methods'] == ['GET', 'PUT', 'DELETE']

    signin_response = client.post(
        '/api/login/signin',
        json={'username': 'alice', 'password': 'secret'},
    )
    assert signin_response.status_code == 200
    assert signin_response.get_json()['user']['username'] == 'alice'
    assert signin_response.get_json()['user']['state'] == 'LOGGED_IN'
    assert signin_response.get_json()['user']['_links']['self']['href'] == f"/api/users/{signup_payload['user']['id']}"
    assert signin_response.get_json()['user']['_links']['self']['methods'] == ['GET', 'PUT', 'DELETE']

    me_response = client.get('/api/login/me', headers=entities.auth_headers(token))
    assert me_response.status_code == 200
    me_payload = me_response.get_json()
    assert me_payload['user']['username'] == 'alice'
    assert me_payload['user']['state'] == 'LOGGED_IN'
    assert me_payload['character'] is None
    assert me_payload['user']['_links']['inventory']['href'] == f"/api/users/{signup_payload['user']['id']}/inventory"
    assert me_payload['user']['_links']['inventory']['methods'] == ['GET', 'DELETE']

    signout_response = client.post('/api/login/signout')
    assert signout_response.status_code == 200
    assert signout_response.get_json() == {'message': 'signed out'}


def test_signup_rejects_duplicate_username(client):
    """Reject duplicate usernames during signup."""
    first_signup = client.post('/api/login/signup', json={'username': 'alice', 'password': 'secret'})
    assert first_signup.status_code == 201

    duplicate_signup = client.post('/api/login/signup', json={'username': 'alice', 'password': 'different'})
    assert duplicate_signup.status_code == 409
    assert duplicate_signup.get_json()['error'] == 'username already exists'


def test_signin_rejects_invalid_credentials_and_login_me_requires_auth(client, entities):
    """Reject invalid signin credentials and unauthenticated profile access."""
    user = entities.create_user(username='alice', password='secret')

    invalid_username = client.post('/api/login/signin', json={'username': 'missing', 'password': 'secret'})
    assert invalid_username.status_code == 401
    assert invalid_username.get_json()['error'] == 'invalid username or password'

    invalid_password = client.post('/api/login/signin', json={'username': user.username, 'password': 'wrong'})
    assert invalid_password.status_code == 401
    assert invalid_password.get_json()['error'] == 'invalid username or password'

    unauthorized_me = client.get('/api/login/me')
    assert unauthorized_me.status_code == 401
    assert unauthorized_me.get_json()['error'] == 'Unauthorized'


def test_auth_resources_reject_missing_required_fields(client):
    """Reject auth requests with missing required fields."""
    missing_signup_username = client.post('/api/login/signup', json={'password': 'secret'})
    assert missing_signup_username.status_code == 400
    assert missing_signup_username.get_json()['error'][0]['msg'] == 'Field required'

    missing_signup_password = client.post('/api/login/signup', json={'username': 'alice'})
    assert missing_signup_password.status_code == 400
    assert missing_signup_password.get_json()['error'][0]['msg'] == 'Field required'

    missing_signin_username = client.post('/api/login/signin', json={'password': 'secret'})
    assert missing_signin_username.status_code == 400
    assert missing_signin_username.get_json()['error'][0]['msg'] == 'Field required'

    missing_signin_password = client.post('/api/login/signin', json={'username': 'alice'})
    assert missing_signin_password.status_code == 400
    assert missing_signin_password.get_json()['error'][0]['msg'] == 'Field required'