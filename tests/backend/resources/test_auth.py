def test_signup_signin_signout_and_me_without_character(client, entities):
    signup_response = client.post(
        '/api/login/signup',
        json={'username': 'alice', 'password': 'secret'},
    )
    assert signup_response.status_code == 201
    signup_payload = signup_response.get_json()
    token = signup_payload['token']
    assert signup_payload['user']['username'] == 'alice'

    signin_response = client.post(
        '/api/login/signin',
        json={'username': 'alice', 'password': 'secret'},
    )
    assert signin_response.status_code == 200
    assert signin_response.get_json()['user']['username'] == 'alice'

    me_response = client.get('/api/login/me', headers=entities.auth_headers(token))
    assert me_response.status_code == 200
    me_payload = me_response.get_json()
    assert me_payload['user']['username'] == 'alice'
    assert me_payload['character'] is None

    signout_response = client.post('/api/login/signout')
    assert signout_response.status_code == 200
    assert signout_response.get_json() == {'message': 'signed out'}


def test_signup_rejects_duplicate_username(client):
    first_signup = client.post('/api/login/signup', json={'username': 'alice', 'password': 'secret'})
    assert first_signup.status_code == 201

    duplicate_signup = client.post('/api/login/signup', json={'username': 'alice', 'password': 'different'})
    assert duplicate_signup.status_code == 409
    assert duplicate_signup.get_json()['error'] == 'username already exists'


def test_signin_rejects_invalid_credentials_and_login_me_requires_auth(client, entities):
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