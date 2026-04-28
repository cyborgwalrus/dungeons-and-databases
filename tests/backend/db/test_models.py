"""Tests for backend database model behavior."""

from backend.db.models import Character, Combat, EquipmentSlot
from backend.db.schemas import CharacterResponse, CombatEnemyResponse, CombatResponse, ItemResponse, UserResponse
from backend.db.session import db
from backend.utils import route_helpers


def test_character_level_up_and_combat_scaling(entities):
    """Validate core character progression math and level-up gating."""
    user = entities.create_user(username='hero', password='secret')
    character = entities.create_character(
        user,
        name='Hero',
        seed_loadout=False,
        level=1,
        health=100,
        damage=10,
    )

    assert character.can_level_up() is False
    assert character.gain_experience(0) == 0
    assert character.gain_experience(-5) == 0
    assert character.experience == 0

    character.experience = character.experience_to_next_level
    assert character.can_level_up() is True
    assert character.level_up() is True

    assert character.level == 2
    assert character.experience == 0
    assert character.damage == 13
    assert character.health == 106
    assert character.max_health == 110


def test_user_owns_character_helper(entities):
    """Validate the user ownership helper on the model."""
    owner = entities.create_user(username='owner', password='secret')
    other = entities.create_user(username='other', password='secret')
    owner_character = entities.create_character(owner, name='Owner', seed_loadout=False)
    entities.create_character(other, name='Other', seed_loadout=False)

    assert owner.owns_character(owner_character.id) is True
    assert owner.owns_character(999999) is False


def test_character_level_up_accounts_for_equipment_bonus(entities):
    """Validate that equipped item bonuses affect max health during leveling."""
    user = entities.create_user(username='guardian', password='secret')
    character = entities.create_character(
        user,
        name='Guardian',
        seed_loadout=False,
        level=1,
        health=100,
        damage=10,
    )

    shield = entities.create_inventory_item(character, 'iron_shield')
    assert route_helpers.equip_item(character, shield) is None
    db.session.commit()

    assert character.bonus_health == 9
    assert character.max_health == 109

    character.experience = character.experience_to_next_level
    assert character.level_up() is True
    assert character.level == 2
    assert character.max_health == 119
    assert character.health == 106


def test_equipment_slot_and_item_response_helpers(entities):
    """Validate item and equipment response models round-trip data."""
    user = entities.create_user(username='collector', password='secret')
    character = entities.create_character(user, name='Collector', seed_loadout=False)
    item = entities.create_inventory_item(character, 'steel_sword')

    assert item.is_equipped is False
    item_response = item.to_response()
    assert item_response.id == item.id
    assert item_response.item_type_id == 'steel_sword'

    assert route_helpers.equip_item(character, item) is None
    db.session.commit()

    refreshed_character = db.session.get(Character, character.id)
    assert refreshed_character is not None
    equipment = refreshed_character.equipment[0]
    assert isinstance(equipment, EquipmentSlot)
    assert equipment.matches_item(item.id) is True
    assert equipment.to_response().item_id == item.id


def test_combat_response_includes_enemy_snapshot(entities):
    """Validate the combat response exposes a nested enemy view model."""
    user = entities.create_user(username='combat-view', password='secret')
    character = entities.create_character(user, name='Combatant', seed_loadout=False)
    combat = entities.create_encounter(character)

    response = combat.to_response()

    assert isinstance(combat, Combat)
    assert response.enemy.type_id == combat.enemy_type_id
    assert response.enemy.name == combat.enemy['name']
    assert response.enemy.health == combat.enemy_current_health
    assert response.enemy.max_health == combat.enemy_max_health


def test_response_models_accept_hypermedia_links():
    """Validate that serialized response schemas accept `_links`."""
    user_response = UserResponse.model_validate(
        {
            'id': 1,
            'username': 'hero',
            'state': 'LOGGED_IN',
            '_links': {'self': {'href': '/api/users/1', 'methods': ['GET', 'PUT', 'DELETE']}},
        }
    )
    assert user_response.links == {'self': {'href': '/api/users/1', 'methods': ['GET', 'PUT', 'DELETE']}}

    character_response = CharacterResponse.model_validate(
        {
            'id': 2,
            'user_id': 1,
            'name': 'Hero',
            'level': 1,
            'experience': 0,
            'experience_to_next_level': 100,
            'max_health': 100,
            'health': 100,
            'damage': 10,
            'state': 'HOME',
            'bonus_health': 0,
            'bonus_damage': 0,
            '_links': {'self': {'href': '/api/characters/2', 'methods': ['GET', 'PUT', 'DELETE']}},
        }
    )
    assert character_response.links == {'self': {'href': '/api/characters/2', 'methods': ['GET', 'PUT', 'DELETE']}}

    item_response = ItemResponse.model_validate(
        {
            'id': 3,
            'name': 'Sword',
            'item_type_id': 'steel_sword',
            'level': 1,
            'slot_type': 'weapon',
            'health': 0,
            'damage': 5,
            '_links': {'self': {'href': '/api/items/3', 'methods': ['GET', 'DELETE']}},
        }
    )
    assert item_response.links == {'self': {'href': '/api/items/3', 'methods': ['GET', 'DELETE']}}

    combat_response = CombatResponse.model_validate(
        {
            'id': 4,
            'character_id': 2,
            'character_health': 90,
            'enemy': {
                'type_id': 'orc',
                'name': 'Orc',
                'description': None,
                'level': 1,
                'health': 12,
                'max_health': 12,
                'damage': 3,
                'base_health': 12,
                'base_damage': 3,
                '_links': {'self': {'href': '/api/enemy-types/orc', 'methods': ['GET']}},
            },
            '_links': {'self': {'href': '/api/combats/4', 'methods': ['GET']}},
        }
    )
    assert combat_response.links == {'self': {'href': '/api/combats/4', 'methods': ['GET']}}
    assert isinstance(combat_response.enemy, CombatEnemyResponse)
    assert combat_response.enemy.links == {'self': {'href': '/api/enemy-types/orc', 'methods': ['GET']}}
