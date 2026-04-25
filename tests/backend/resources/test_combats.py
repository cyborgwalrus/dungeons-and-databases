"""Combat resources for resolving dungeon encounters."""

from unittest.mock import patch

from backend.db.models import Combat
from backend.db.session import db


def test_combat_creation_returns_combat_payload(client, entities):
    """Create a combat and return the initial combat payload."""
    user = entities.create_user(username='dungeon-user', password='secret')
    character = entities.create_character(user, name='Fighter', health=120, damage=12)
    token = entities.token_for(user, character)

    with patch('backend.resources.combat_engine.random.choice', side_effect=lambda sequence: sequence[0]):
        response = client.post('/api/combats', headers=entities.auth_headers(token))

    assert response.status_code == 201
    payload = response.get_json()
    assert payload['combat']['character_id'] == character.id
    assert payload['combat']['enemy']['level'] == 1
    assert payload['character']['id'] == character.id
    assert payload['character']['health'] == payload['character']['max_health']


def test_combat_creation_returns_404_when_enemy_catalog_is_empty(client, entities):
    """Return 404 when combat creation has no enemy templates."""
    user = entities.create_user(username='stranded', password='secret')
    character = entities.create_character(user, name='Wanderer')
    token = entities.token_for(user, character)

    with patch('backend.resources.combat_engine.get_enemy_types', return_value=[]):
        response = client.post('/api/combats', headers=entities.auth_headers(token))

    assert response.status_code == 404
    assert response.get_json()['error'] == 'No enemy types available'


def test_combat_creation_returns_none_without_character(monkeypatch):
    """Directly cover the create_new_combat guard when no character is provided."""
    from backend.resources import combat_engine as combats_module

    monkeypatch.setattr(combats_module, 'get_player', lambda: None)

    assert combats_module.create_new_combat(None) is None


def test_combat_attack_victory_keeps_defeated_enemy_visible(client, entities):
    """Keep the defeated enemy visible in the victory response."""
    user = entities.create_user(username='victor', password='secret')
    character = entities.create_character(user, name='Champion', health=120, damage=100)
    token = entities.token_for(user, character)

    with patch('backend.resources.combat_engine.random.choice', side_effect=lambda sequence: sequence[0]), patch(
        'backend.resources.combat_engine.random.choice',
        side_effect=lambda sequence: sequence[0],
    ), patch('backend.resources.combat_engine.random.randint', side_effect=lambda minimum, maximum: maximum):
        combat_response = client.post('/api/combats', headers=entities.auth_headers(token))
        combat_id = combat_response.get_json()['combat']['id']

        attack_response = client.get(f'/api/combats/{combat_id}/attack', headers=entities.auth_headers(token))
        detail_response = client.get(f'/api/combats/{combat_id}', headers=entities.auth_headers(token))

    assert attack_response.status_code == 200
    payload = attack_response.get_json()
    assert payload['victory'] is True
    assert payload['player_died'] is False
    assert payload['items_dropped']
    assert payload['combat'] is not None
    assert payload['combat']['enemy']['health'] == 0
    assert payload['combat']['enemy']['name']
    assert payload['character']['health'] > 0

    assert detail_response.status_code == 200
    detail_payload = detail_response.get_json()
    assert detail_payload['id'] == combat_id
    assert detail_payload['enemy']['name']


def test_combat_attack_after_enemy_defeat_prompts_deeper(client, entities):
    """Cover the branch where attack is used after the enemy has already been cleared."""
    user = entities.create_user(username='finisher', password='secret')
    character = entities.create_character(user, name='Finisher', health=120, damage=100)
    token = entities.token_for(user, character)

    with patch('backend.resources.combat_engine.random.choice', side_effect=lambda sequence: sequence[0]):
        combat_response = client.post('/api/combats', headers=entities.auth_headers(token))

    combat_id = combat_response.get_json()['combat']['id']

    combat = db.session.get(Combat, combat_id)
    assert combat is not None
    combat.enemy_current_health = 0
    db.session.commit()

    response = client.get(f'/api/combats/{combat_id}/attack', headers=entities.auth_headers(token))

    assert response.status_code == 200
    payload = response.get_json()
    assert payload['message'] == 'You need to go deeper to face the next enemy.'
    assert payload['victory'] is False
    assert payload['player_died'] is False


def test_combat_deeper_after_victory_loads_next_enemy(client, entities):
    """Advance to a deeper combat after victory."""
    user = entities.create_user(username='deepdelver', password='secret')
    character = entities.create_character(user, name='Champion', health=120, damage=100)
    token = entities.token_for(user, character)

    with patch('backend.resources.combat_engine.random.choice', side_effect=lambda sequence: sequence[0]), patch(
        'backend.resources.combat_engine.random.choice',
        side_effect=lambda sequence: sequence[0],
    ), patch('backend.resources.combat_engine.random.randint', side_effect=lambda minimum, maximum: maximum):
        combat_response = client.post('/api/combats', headers=entities.auth_headers(token))
        combat_id = combat_response.get_json()['combat']['id']

        victory_response = client.get(f'/api/combats/{combat_id}/attack', headers=entities.auth_headers(token))
        deeper_response = client.get(f'/api/combats/{combat_id}/deeper', headers=entities.auth_headers(token))

    assert victory_response.status_code == 200
    victory_payload = victory_response.get_json()
    assert victory_payload['victory'] is True
    assert victory_payload['combat'] is not None
    assert victory_payload['combat']['enemy']['level'] == 1

    assert deeper_response.status_code == 200
    deeper_payload = deeper_response.get_json()
    assert deeper_payload['victory'] is False
    assert deeper_payload['combat'] is not None
    assert deeper_payload['combat']['id'] != victory_payload['combat']['id']
    assert deeper_payload['combat']['enemy']['level'] == victory_payload['combat']['enemy']['level'] + 1


def test_combat_deeper_keeps_current_health(client, entities):
    """Keep current health when moving deeper between combats."""
    user = entities.create_user(username='deeper-health', password='secret')
    character = entities.create_character(user, name='Delver', health=40, damage=100)
    token = entities.token_for(user, character)

    with patch('backend.resources.combat_engine.random.choice', side_effect=lambda sequence: sequence[0]), patch(
        'backend.resources.combat_engine.random.randint', side_effect=lambda minimum, maximum: maximum
    ):
        combat_response = client.post('/api/combats', headers=entities.auth_headers(token))
        combat_id = combat_response.get_json()['combat']['id']

    combat = db.session.get(Combat, combat_id)
    assert combat is not None
    combat.enemy_current_health = 0
    combat.character_health = 37
    db.session.commit()

    with patch('backend.resources.combat_engine.random.choice', side_effect=lambda sequence: sequence[0]):
        deeper_response = client.get(f'/api/combats/{combat_id}/deeper', headers=entities.auth_headers(token))

    assert deeper_response.status_code == 200
    payload = deeper_response.get_json()
    assert payload['combat'] is not None
    assert payload['character']['health'] == 37
    assert payload['combat']['character_health'] == 37


def test_combat_home_after_victory_returns_home_and_keeps_loot(client, entities):
    """Return home after victory without losing loot."""
    user = entities.create_user(username='homer', password='secret')
    character = entities.create_character(user, name='Champion', health=120, damage=100)
    token = entities.token_for(user, character)

    with patch('backend.resources.combat_engine.random.choice', side_effect=lambda sequence: sequence[0]), patch(
        'backend.resources.combat_engine.random.choice',
        side_effect=lambda sequence: sequence[0],
    ), patch('backend.resources.combat_engine.random.randint', side_effect=lambda minimum, maximum: maximum):
        combat_response = client.post('/api/combats', headers=entities.auth_headers(token))
        combat_id = combat_response.get_json()['combat']['id']
        victory_response = client.get(f'/api/combats/{combat_id}/attack', headers=entities.auth_headers(token))
        home_response = client.get(f'/api/combats/{combat_id}/home', headers=entities.auth_headers(token))

    assert victory_response.status_code == 200
    assert home_response.status_code == 200
    home_payload = home_response.get_json()
    assert home_payload['success'] is True
    assert home_payload['combat'] is None

    inventory_response = client.get(f'/api/users/{user.id}/inventory', headers=entities.auth_headers(token))
    assert inventory_response.status_code == 200
    inventory_items = inventory_response.get_json()
    assert inventory_items
    assert len(inventory_items) == 1


def test_combat_prevents_home_and_deeper_before_victory(client, entities):
    """Cover the precondition branches for home and deeper actions."""
    user = entities.create_user(username='tactician', password='secret')
    character = entities.create_character(user, name='Tactician', health=100, damage=100)
    token = entities.token_for(user, character)

    with patch('backend.resources.combat_engine.random.choice', side_effect=lambda sequence: sequence[0]):
        combat_response = client.post('/api/combats', headers=entities.auth_headers(token))
        combat_id = combat_response.get_json()['combat']['id']

    home_response = client.get(f'/api/combats/{combat_id}/home', headers=entities.auth_headers(token))
    deeper_response = client.get(f'/api/combats/{combat_id}/deeper', headers=entities.auth_headers(token))

    assert home_response.status_code == 400
    assert home_response.get_json()['error'] == 'You can only go home after defeating the enemy'
    assert deeper_response.status_code == 200
    assert deeper_response.get_json()['message'] == 'You can only go deeper after defeating the enemy.'


def test_combat_deeper_returns_404_when_next_enemy_cannot_be_created(client, entities):
    """Return 404 when the next combat cannot be created."""
    user = entities.create_user(username='stranded-deeper', password='secret')
    character = entities.create_character(user, name='Stranded', health=100, damage=100)
    token = entities.token_for(user, character)

    with patch('backend.resources.combat_engine.random.choice', side_effect=lambda sequence: sequence[0]):
        combat_response = client.post('/api/combats', headers=entities.auth_headers(token))

    combat_id = combat_response.get_json()['combat']['id']
    combat = db.session.get(Combat, combat_id)
    assert combat is not None
    combat.enemy_current_health = 0
    db.session.commit()

    with patch('backend.resources.combat_engine.create_new_combat', return_value=None):
        response = client.get(f'/api/combats/{combat_id}/deeper', headers=entities.auth_headers(token))

    assert response.status_code == 404
    assert response.get_json()['error'] == 'No enemy types available'


def test_combat_attack_survives_when_enemy_lives(client, entities):
    """Keep combat active when the enemy survives the attack."""
    user = entities.create_user(username='scrapper', password='secret')
    character = entities.create_character(user, name='Scout', health=100, damage=10)
    token = entities.token_for(user, character)
    initial_health = character.health

    with patch('backend.resources.combat_engine.random.choice', side_effect=lambda sequence: sequence[0]), patch(
        'backend.resources.combat_engine.random.randint', side_effect=lambda minimum, maximum: minimum
    ):
        combat_response = client.post('/api/combats', headers=entities.auth_headers(token))
        combat_id = combat_response.get_json()['combat']['id']
        attack_response = client.get(f'/api/combats/{combat_id}/attack', headers=entities.auth_headers(token))

    assert attack_response.status_code == 200
    payload = attack_response.get_json()
    assert payload['victory'] is False
    assert payload['player_died'] is False
    assert payload['items_dropped'] == []
    assert payload['combat']['id'] == combat_id
    assert payload['character']['health'] < initial_health


def test_combat_run_failure_survives_and_keeps_combat_active(client, entities):
    """Keep combat active after a failed escape that does not kill the player."""
    user = entities.create_user(username='dodger', password='secret')
    character = entities.create_character(user, name='Runner', health=80, damage=10)
    token = entities.token_for(user, character)
    initial_health = character.health

    with patch('backend.resources.combat_engine.random.choice', side_effect=lambda sequence: sequence[0]), patch(
        'backend.resources.combat_engine.random.randint', side_effect=[1, 2]
    ):
        combat_response = client.post('/api/combats', headers=entities.auth_headers(token))
        initial_health = combat_response.get_json()['character']['health']
        combat_id = combat_response.get_json()['combat']['id']
        run_response = client.get(f'/api/combats/{combat_id}/run', headers=entities.auth_headers(token))

    assert run_response.status_code == 200
    payload = run_response.get_json()
    assert payload['success'] is False
    assert payload['player_died'] is False
    assert payload['dice_roll'] == 1
    assert 'damage' not in payload
    assert payload['combat']['id'] == combat_id
    assert payload['character']['health'] == initial_health - 2


def test_combat_victory_levels_up_character_and_emits_next_level_message(client, entities):
    """Level up the character and emit the next-level message on victory."""
    user = entities.create_user(username='champion', password='secret')
    character = entities.create_character(user, name='Hero', health=90, damage=100)
    initial_health = character.health
    token = entities.token_for(user, character)
    character.experience = 95
    db.session.commit()

    with patch('backend.resources.combat_engine.random.choice', side_effect=lambda sequence: sequence[0]), patch(
        'backend.resources.combat_engine.random.choice', side_effect=lambda sequence: sequence[0]
    ), patch('backend.resources.combat_engine.random.randint', side_effect=lambda minimum, maximum: maximum):
        combat_response = client.post('/api/combats', headers=entities.auth_headers(token))
        combat_id = combat_response.get_json()['combat']['id']
        attack_response = client.get(f'/api/combats/{combat_id}/attack', headers=entities.auth_headers(token))

    assert attack_response.status_code == 200
    payload = attack_response.get_json()
    assert payload['victory'] is True
    assert 'You reached level 2!' in payload['message']
    assert 'Next level at 150 XP.' in payload['message']
    assert payload['character']['level'] == 2
    assert payload['character']['experience'] == 25
    assert payload['character']['health'] > initial_health


def test_combat_run_success_leaves_inventory_untouched(client, entities):
    """Preserve inventory when the player escapes successfully."""
    user = entities.create_user(username='runner', password='secret')
    character = entities.create_character(user, name='Scout', health=80, damage=10)
    token = entities.token_for(user, character)
    loot_item = entities.create_inventory_item(character, 'steel_sword')

    with patch('backend.resources.combat_engine.random.choice', side_effect=lambda sequence: sequence[0]), patch(
        'backend.resources.combat_engine.random.randint', return_value=6
    ):
        combat_response = client.post('/api/combats', headers=entities.auth_headers(token))
        combat_id = combat_response.get_json()['combat']['id']
        run_response = client.get(f'/api/combats/{combat_id}/run', headers=entities.auth_headers(token))

    assert run_response.status_code == 200
    payload = run_response.get_json()
    assert payload['success'] is True
    assert payload['combat'] is None

    inventory_response = client.get(f'/api/users/{user.id}/inventory', headers=entities.auth_headers(token))
    assert inventory_response.status_code == 200
    inventory_items = inventory_response.get_json()
    assert len(inventory_items) == 1
    assert inventory_items[0]['id'] == loot_item.id


def test_combat_run_failure_can_defeat_character_and_keep_inventory(client, entities):
    """Handle a failed escape that defeats the character without clearing inventory."""
    user = entities.create_user(username='loser', password='secret')
    character = entities.create_character(user, name='Fragile', health=1, damage=10)
    token = entities.token_for(user, character)
    entities.create_inventory_item(character, 'steel_sword')

    with patch('backend.resources.combat_engine.random.choice', side_effect=lambda sequence: sequence[0]):
        combat_response = client.post('/api/combats', headers=entities.auth_headers(token))

    combat_id = combat_response.get_json()['combat']['id']
    combat = db.session.get(Combat, combat_id)
    assert combat is not None
    combat.character_health = 1
    db.session.commit()

    with patch('backend.resources.combat_engine.random.randint', side_effect=lambda minimum, maximum: minimum):
        run_response = client.get(f'/api/combats/{combat_id}/run', headers=entities.auth_headers(token))

    assert run_response.status_code == 200
    payload = run_response.get_json()
    assert payload['player_died'] is True
    assert payload['success'] is False
    assert payload['combat'] is None

    inventory_response = client.get(f'/api/users/{user.id}/inventory', headers=entities.auth_headers(token))
    assert inventory_response.status_code == 200
    inventory_items = inventory_response.get_json()
    assert len(inventory_items) == 1
    assert inventory_items[0]['id'] == 1


def test_combat_rejects_invalid_action_and_missing_combat(client, entities):
    """Reject invalid combat actions and missing combat resources."""
    user = entities.create_user(username='bystander', password='secret')
    character = entities.create_character(user, name='Watcher')
    token = entities.token_for(user, character)

    invalid_action = client.get('/api/combats/999999/dance', headers=entities.auth_headers(token))
    assert invalid_action.status_code == 404
    assert invalid_action.get_json()['error'] == 'Combat not found'

    with patch('backend.resources.combat_engine.random.choice', side_effect=lambda sequence: sequence[0]):
        combat_response = client.post('/api/combats', headers=entities.auth_headers(token))

    combat_id = combat_response.get_json()['combat']['id']
    bad_action = client.get(f'/api/combats/{combat_id}/dance', headers=entities.auth_headers(token))
    assert bad_action.status_code == 400
    assert bad_action.get_json()['error'] == 'Invalid combat action'


def test_combat_routes_require_authentication(client, entities):
    """Require authentication for combat routes."""
    user = entities.create_user(username='runner', password='secret')
    character = entities.create_character(user, name='Scout')
    token = entities.token_for(user, character)

    with patch('backend.resources.combat_engine.random.choice', side_effect=lambda sequence: sequence[0]):
        combat_response = client.post('/api/combats', headers=entities.auth_headers(token))

    combat_id = combat_response.get_json()['combat']['id']
    response = client.get(f'/api/combats/{combat_id}/attack')

    assert response.status_code == 401
    assert response.get_json()['error'] == 'Unauthorized'


def test_register_combat_resources_registers_all_routes():
    """Cover the combat route registration helper."""
    from backend.resources.combats import register_combat_resources

    calls = []

    class FakeApi:
        def add_resource(self, resource, *routes):
            calls.append((resource.__name__, routes))

    register_combat_resources(FakeApi())

    assert calls[0][0] == 'CombatResource'
    assert '/combats' in calls[0][1]
    assert '/combats/<combat:combat>' in calls[0][1]
    assert '/combats/<combat:combat>/<string:action>' in calls[0][1]